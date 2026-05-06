from __future__ import annotations

import argparse
import cgi
import json
import math
import os
import re
import sqlite3
import threading
import time
import uuid
import zipfile
from collections import Counter
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler
from io import BytesIO
from pathlib import Path
from socketserver import ThreadingTCPServer
from urllib.parse import urlparse
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "gocs.db"

FALLBACK_MESSAGE = (
    "I could not find enough information in the uploaded company information to answer this confidently. "
    "Please contact the team directly or upload more details to improve this AI assistant."
)

DB_LOCK = threading.Lock()
RATE_LOCK = threading.Lock()
RATE_STATE: dict[str, list[float]] = {}
WORD_RE = re.compile(r"[a-z0-9]+")
STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "how", "i", "in", "is", "it", "of",
    "on", "or", "that", "the", "this", "to", "we", "what", "when", "where", "who", "why", "with", "you", "your",
}
VECTOR_DIMS = 256
RISK_KEYWORDS = {
    "price", "pricing", "refund", "guarantee", "legal", "medical",
    "financial", "availability", "contract", "latest", "warranty", "promise",
}
TOKEN_CANONICAL = {
    "opening": "hours",
    "open": "hours",
    "close": "hours",
    "closing": "hours",
    "cost": "price",
    "charges": "price",
    "fee": "price",
    "fees": "price",
    "refunds": "refund",
}
MAX_BODY_BYTES = int(os.getenv("GOCS_MAX_BODY_BYTES", str(5 * 1024 * 1024)))
RATE_LIMIT_PER_MIN = int(os.getenv("GOCS_RATE_LIMIT_PER_MIN", "180"))
DEFAULT_BIND_HOST = os.getenv("HOST", "0.0.0.0")
CORS_ALLOW_ORIGIN = os.getenv("GOCS_CORS_ALLOW_ORIGIN", "*")
TELEGRAM_TOKEN_RE = re.compile(r"^\d{6,}:[\w-]{20,}$")


def trim_rate_state(now_ts: float) -> None:
    cutoff = now_ts - 60.0
    stale_keys = []
    for key, hits in RATE_STATE.items():
        filtered = [ts for ts in hits if ts >= cutoff]
        if filtered:
            RATE_STATE[key] = filtered
        else:
            stale_keys.append(key)
    for key in stale_keys:
        RATE_STATE.pop(key, None)


def allow_request(client_key: str) -> bool:
    now_ts = time.time()
    with RATE_LOCK:
        trim_rate_state(now_ts)
        hits = RATE_STATE.get(client_key, [])
        if len(hits) >= RATE_LIMIT_PER_MIN:
            RATE_STATE[client_key] = hits
            return False
        hits.append(now_ts)
        RATE_STATE[client_key] = hits
        return True


def env_int(name: str, default: int, minimum: int, maximum: int) -> int:
    raw = os.getenv(name, str(default))
    try:
        value = int(raw)
    except (TypeError, ValueError):
        return default
    return max(minimum, min(maximum, value))


def load_env_file(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        raw = line.strip()
        if not raw or raw.startswith("#") or "=" not in raw:
            continue
        k, v = raw.split("=", 1)
        key = k.strip()
        value = v.strip().strip("'").strip('"')
        if key and key not in os.environ:
            os.environ[key] = value


def retrieval_provider() -> str:
    return (os.getenv("GOCS_RETRIEVAL_PROVIDER", "local") or "local").strip().lower()


def data_engine_endpoint() -> str:
    return (os.getenv("GOCS_DATA_ENGINE_ENDPOINT", "") or "").strip()


def data_engine_enabled() -> bool:
    return retrieval_provider() in {"data_engine", "hybrid"} and bool(data_engine_endpoint())


def db_connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.execute("pragma foreign_keys = on")
    conn.execute("pragma journal_mode = wal")
    conn.execute("pragma synchronous = normal")
    conn.execute("pragma busy_timeout = 5000")
    return conn


def extract_uploaded_text(filename: str, content_type: str, file_bytes: bytes) -> str:
    name = (filename or "").lower()
    if not file_bytes:
        return ""

    if name.endswith((".txt", ".md", ".csv", ".json", ".log")):
        return file_bytes.decode("utf-8", errors="ignore")

    if name.endswith(".pdf"):
        try:
            from pypdf import PdfReader  # type: ignore

            reader = PdfReader(BytesIO(file_bytes))
            pages = []
            for p in reader.pages:
                text = p.extract_text() or ""
                if text.strip():
                    pages.append(text.strip())
            return "\n\n".join(pages)
        except Exception:
            return file_bytes.decode("utf-8", errors="ignore")

    if name.endswith(".docx"):
        try:
            with zipfile.ZipFile(BytesIO(file_bytes)) as zf:
                xml_data = zf.read("word/document.xml")
            root = ET.fromstring(xml_data)
            ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
            texts = [node.text for node in root.findall(".//w:t", ns) if node.text]
            return "\n".join(texts)
        except Exception:
            return file_bytes.decode("utf-8", errors="ignore")

    # Best-effort fallback for unsupported binary types.
    return file_bytes.decode("utf-8", errors="ignore")


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def request_id() -> str:
    return f"req_{uuid.uuid4().hex[:16]}"


def ok(data: dict) -> dict:
    return {"ok": True, "data": data, "meta": {"request_id": request_id(), "timestamp": now_iso()}}


def err(code: str, message: str, details: list[dict] | None = None) -> dict:
    return {
        "ok": False,
        "error": {"code": code, "message": message, "details": details or []},
        "meta": {"request_id": request_id(), "timestamp": now_iso()},
    }


def ensure_db() -> None:
    with DB_LOCK:
        conn = db_connect()
        try:
            conn.executescript(
                """
                create table if not exists bots (
                  id text primary key,
                  name text default 'AI Customer Service',
                  owner_email text,
                  status text default 'ready',
                  source_type text default 'upload',
                  answer_mode text default 'knowledge_only',
                  business_type text default 'auto',
                  tone text default 'professional',
                  fallback_message text default '',
                  confidence_threshold real default 0.7,
                  public_token text unique,
                  suggested_questions text default '[]',
                  settings text default '{}',
                  created_at text,
                  updated_at text
                );

                create table if not exists knowledge_files (
                  id text primary key,
                  bot_id text,
                  file_name text,
                  file_type text,
                  file_url text,
                  raw_text text,
                  status text default 'processed',
                  created_at text,
                  foreign key (bot_id) references bots(id) on delete cascade
                );

                create table if not exists knowledge_chunks (
                  id text primary key,
                  bot_id text,
                  file_id text,
                  chunk_text text not null,
                  chunk_index integer,
                  embedding text,
                  metadata text default '{}',
                  created_at text,
                  foreign key (bot_id) references bots(id) on delete cascade,
                  foreign key (file_id) references knowledge_files(id) on delete cascade
                );

                create table if not exists conversations (
                  id text primary key,
                  bot_id text,
                  channel text default 'web',
                  visitor_id text,
                  status text default 'open',
                  needs_human integer default 0,
                  created_at text,
                  updated_at text,
                  foreign key (bot_id) references bots(id) on delete cascade
                );

                create table if not exists messages (
                  id text primary key,
                  conversation_id text,
                  sender_type text not null,
                  message_text text not null,
                  confidence real,
                  confidence_label text,
                  source_text text,
                  needs_human integer default 0,
                  created_at text,
                  foreign key (conversation_id) references conversations(id) on delete cascade
                );
                """
            )
            conn.commit()
        finally:
            conn.close()


def chunk_text(raw_text: str, chunk_size: int = 500, overlap: int = 100) -> list[str]:
    text = (raw_text or "").strip()
    if not text:
        return []
    chunks: list[str] = []
    step = max(1, chunk_size - overlap)
    for start in range(0, len(text), step):
        piece = text[start : start + chunk_size].strip()
        if piece:
            chunks.append(piece)
        if start + chunk_size >= len(text):
            break
    return chunks


def tokenize(text: str) -> list[str]:
    raw = [t for t in WORD_RE.findall((text or "").lower()) if t not in STOPWORDS and len(t) > 1]
    tokens = [TOKEN_CANONICAL.get(t, t) for t in raw]
    return tokens


def confidence_label(confidence: float) -> str:
    if confidence >= 0.8:
        return "High Confidence"
    if confidence >= 0.6:
        return "Medium Confidence"
    return "Not Enough Information"


def embed_text(text: str, dims: int = VECTOR_DIMS) -> list[float]:
    vec = [0.0] * dims
    tokens = tokenize(text)
    if not tokens:
        return vec
    for token in tokens:
        idx = hash(token) % dims
        vec[idx] += 1.0
    norm = math.sqrt(sum(v * v for v in vec))
    if norm <= 0:
        return vec
    return [v / norm for v in vec]


def cosine_similarity(a: list[float], b: list[float]) -> float:
    if not a or not b:
        return 0.0
    n = min(len(a), len(b))
    return sum(a[i] * b[i] for i in range(n))


def parse_embedding(embedding_json: str | None) -> list[float]:
    if not embedding_json:
        return []
    try:
        data = json.loads(embedding_json)
        if isinstance(data, list):
            return [float(x) for x in data]
    except Exception:
        return []
    return []


class GoCSHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def log_message(self, fmt: str, *args) -> None:
        super().log_message(fmt, *args)

    def _send_json(self, payload: dict, status: int = 200) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_js(self, content: str, status: int = 200) -> None:
        body = content.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/javascript; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def end_headers(self) -> None:
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "SAMEORIGIN")
        self.send_header("Referrer-Policy", "strict-origin-when-cross-origin")
        self.send_header("Permissions-Policy", "geolocation=(), microphone=(), camera=()")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Access-Control-Allow-Origin", CORS_ALLOW_ORIGIN)
        self.send_header("Vary", "Origin")
        super().end_headers()

    def _client_key(self) -> str:
        return self.client_address[0] if self.client_address else "unknown"

    def _check_api_guards(self) -> bool:
        client = self._client_key()
        if not allow_request(client):
            self._send_json(err("RATE_LIMITED", "Too many requests. Please retry shortly."), HTTPStatus.TOO_MANY_REQUESTS)
            return False
        length = int(self.headers.get("Content-Length", "0") or "0")
        if length > MAX_BODY_BYTES:
            self._send_json(
                err(
                    "PAYLOAD_TOO_LARGE",
                    f"Payload exceeds limit of {MAX_BODY_BYTES} bytes.",
                    [{"field": "body", "issue": "too_large"}],
                ),
                HTTPStatus.REQUEST_ENTITY_TOO_LARGE,
            )
            return False
        return True

    def _read_json(self) -> dict | None:
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0:
            return {}
        raw = self.rfile.read(length)
        try:
            return json.loads(raw.decode("utf-8"))
        except Exception:
            return None

    def _read_multipart_form(self) -> tuple[dict, dict | None] | tuple[None, None]:
        ctype = self.headers.get("Content-Type", "")
        if "multipart/form-data" not in ctype.lower():
            return None, None
        form = cgi.FieldStorage(fp=self.rfile, headers=self.headers, environ={"REQUEST_METHOD": "POST"})
        data: dict = {}
        for key in ("pasted_text", "owner_email", "business_type", "tone", "settings", "fileName"):
            if key in form and getattr(form[key], "value", None) is not None:
                data[key] = str(form[key].value)

        file_meta = None
        if "file" in form:
            file_item = form["file"]
            if getattr(file_item, "filename", None):
                file_bytes = file_item.file.read() if file_item.file else b""
                file_meta = {
                    "filename": str(file_item.filename),
                    "content_type": str(getattr(file_item, "type", "") or ""),
                    "bytes": file_bytes,
                    "text": extract_uploaded_text(
                        str(file_item.filename),
                        str(getattr(file_item, "type", "") or ""),
                        file_bytes,
                    ),
                }
        return data, file_meta

    def do_GET(self) -> None:
        try:
            parsed = urlparse(self.path)
            path = parsed.path

            if path.startswith("/api/"):
                if not self._check_api_guards():
                    return
                if path == "/api/health":
                    return self._send_json(
                        ok(
                            {
                                "status": "ok",
                                "db_path": str(DB_PATH),
                                "retrieval_provider": retrieval_provider(),
                                "data_engine_enabled": data_engine_enabled(),
                                "limits": {
                                    "max_body_bytes": MAX_BODY_BYTES,
                                    "rate_limit_per_min": RATE_LIMIT_PER_MIN,
                                },
                            }
                        )
                    )
                if path.startswith("/api/bot/"):
                    token = path.split("/")[3] if len(path.split("/")) > 3 else ""
                    return self._handle_get_bot(token)
                return self._send_json(err("NOT_FOUND", "Endpoint not found"), HTTPStatus.NOT_FOUND)

            if path.startswith("/widget/") and path.endswith(".js"):
                token = path.split("/")[2].replace(".js", "")
                return self._handle_widget(token)

            requested = self.translate_path(path)
            if Path(requested).exists() and not Path(requested).is_dir():
                return super().do_GET()

            self.path = "/index.html"
            return super().do_GET()
        except Exception:
            return self._send_json(err("INTERNAL_ERROR", "Unexpected server error"), HTTPStatus.INTERNAL_SERVER_ERROR)

    def do_POST(self) -> None:
        try:
            parsed = urlparse(self.path)
            path = parsed.path
            if path.startswith("/api/"):
                if not self._check_api_guards():
                    return

            if path == "/api/generate-bot":
                return self._handle_generate_bot()

            if path.startswith("/api/bot/") and path.endswith("/ask"):
                token = path.split("/")[3] if len(path.split("/")) > 3 else ""
                return self._handle_ask(token)

            if path == "/api/telegram/connect":
                return self._handle_telegram_connect()

            if path.startswith("/api/webhooks/telegram/"):
                token = path.split("/")[-1]
                return self._handle_telegram_webhook(token)

            return self._send_json(err("NOT_FOUND", "Endpoint not found"), HTTPStatus.NOT_FOUND)
        except Exception:
            return self._send_json(err("INTERNAL_ERROR", "Unexpected server error"), HTTPStatus.INTERNAL_SERVER_ERROR)

    def do_OPTIONS(self) -> None:
        self.send_response(HTTPStatus.NO_CONTENT)
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.send_header("Access-Control-Max-Age", "86400")
        self.end_headers()

    def _handle_generate_bot(self) -> None:
        ctype = self.headers.get("Content-Type", "").lower()
        file_meta = None
        if "multipart/form-data" in ctype:
            payload, file_meta = self._read_multipart_form()
            if payload is None:
                return self._send_json(err("VALIDATION_ERROR", "Invalid multipart form"), HTTPStatus.BAD_REQUEST)
        else:
            payload = self._read_json()
            if payload is None:
                return self._send_json(err("VALIDATION_ERROR", "Invalid JSON body"), HTTPStatus.BAD_REQUEST)

        file_name = str((payload or {}).get("fileName") or (file_meta or {}).get("filename") or "").strip()
        pasted_text = str((payload or {}).get("pasted_text") or "").strip()
        uploaded_text = str((file_meta or {}).get("text") or "").strip()
        combined_text = "\n\n".join([part for part in [uploaded_text, pasted_text] if part]).strip()
        if not file_name and not combined_text:
            return self._send_json(
                err("VALIDATION_ERROR", "Either file or pasted_text is required", [{"field": "file|pasted_text", "issue": "missing_both"}]),
                HTTPStatus.BAD_REQUEST,
            )

        bot_id = str(uuid.uuid4())
        file_id = str(uuid.uuid4())
        public_token = f"bot_{uuid.uuid4().hex[:10]}"
        created = now_iso()
        business_type = str(payload.get("business_type") or "auto").lower()
        tone = str(payload.get("tone") or "friendly").lower()
        source_name = file_name or "Pasted_Company_Info.txt"
        settings_raw = payload.get("settings") if payload else {}
        settings = {}
        if isinstance(settings_raw, dict):
            settings = settings_raw
        elif isinstance(settings_raw, str) and settings_raw.strip():
            try:
                settings = json.loads(settings_raw)
            except Exception:
                settings = {}
        suggested = [
            "What services do you provide?",
            "What is your pricing?",
            "How can customers contact you?",
            "What are your business hours?",
            "What is your refund policy?",
        ]

        with DB_LOCK:
            conn = db_connect()
            try:
                conn.execute(
                    """
                    insert into bots (id,name,owner_email,status,source_type,answer_mode,business_type,tone,fallback_message,confidence_threshold,public_token,suggested_questions,settings,created_at,updated_at)
                    values (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                    """,
                    (
                        bot_id,
                        "AI Customer Service",
                        payload.get("owner_email"),
                        "processing",
                        "upload",
                        "knowledge_only",
                        business_type,
                        tone,
                        FALLBACK_MESSAGE,
                        0.7,
                        public_token,
                        json.dumps(suggested),
                        json.dumps(settings),
                        created,
                        created,
                    ),
                )
                conn.execute(
                    """
                    insert into knowledge_files (id,bot_id,file_name,file_type,file_url,raw_text,status,created_at)
                    values (?,?,?,?,?,?,?,?)
                    """,
                    (file_id, bot_id, source_name, "txt", None, combined_text, "processed", created),
                )
                for idx, piece in enumerate(chunk_text(combined_text)):
                    chunk_embedding = embed_text(piece)
                    conn.execute(
                        """
                        insert into knowledge_chunks (id,bot_id,file_id,chunk_text,chunk_index,embedding,metadata,created_at)
                        values (?,?,?,?,?,?,?,?)
                        """,
                        (
                            str(uuid.uuid4()),
                            bot_id,
                            file_id,
                            piece,
                            idx,
                            json.dumps(chunk_embedding),
                            json.dumps({"strategy": "char_window", "chunk_size": 500, "overlap": 100}),
                            created,
                        ),
                    )
                conn.execute("update bots set status = ?, updated_at = ? where id = ?", ("ready", now_iso(), bot_id))
                conn.commit()
            finally:
                conn.close()

        return self._send_json(
            ok(
                {
                    "bot_id": bot_id,
                    "public_token": public_token,
                    "status": "processing",
                    "test_url": f"/bot/{public_token}/test",
                    "share_url": f"/bot/{public_token}/share",
                    "suggested_questions": suggested,
                    "fallback_message": FALLBACK_MESSAGE,
                    "session": {
                        "sessionId": bot_id,
                        "publicToken": public_token,
                        "businessType": business_type,
                        "tone": tone,
                        "sourceName": source_name,
                    },
                }
            ),
            HTTPStatus.CREATED,
        )

    def _handle_get_bot(self, public_token: str) -> None:
        with DB_LOCK:
            conn = db_connect()
            conn.row_factory = sqlite3.Row
            try:
                row = conn.execute("select * from bots where public_token = ?", (public_token,)).fetchone()
                if not row:
                    return self._send_json(err("NOT_FOUND", "Bot not found", [{"field": "publicToken", "issue": "not_found"}]), HTTPStatus.NOT_FOUND)
                count = conn.execute("select count(*) as c from knowledge_files where bot_id = ?", (row["id"],)).fetchone()["c"]
            finally:
                conn.close()

        return self._send_json(
            ok(
                {
                    "public_token": row["public_token"],
                    "name": row["name"],
                    "status": row["status"],
                    "business_type": row["business_type"],
                    "tone": row["tone"],
                    "answer_mode": row["answer_mode"],
                    "confidence_threshold": row["confidence_threshold"],
                    "fallback_message": row["fallback_message"],
                    "suggested_questions": json.loads(row["suggested_questions"] or "[]"),
                    "knowledge_file_count": count,
                    "created_at": row["created_at"],
                    "updated_at": row["updated_at"],
                    "source_name": conn_source_name(public_token),
                }
            )
        )

    def _handle_ask(self, public_token: str) -> None:
        payload = self._read_json()
        if payload is None:
            return self._send_json(err("VALIDATION_ERROR", "Invalid JSON body"), HTTPStatus.BAD_REQUEST)

        message = str(payload.get("message") or "").strip()
        if not message:
            return self._send_json(err("VALIDATION_ERROR", "message is required", [{"field": "message", "issue": "required"}]), HTTPStatus.BAD_REQUEST)
        if len(message) > 2000:
            return self._send_json(
                err("VALIDATION_ERROR", "message must be 1..2000 characters", [{"field": "message", "issue": "max_length"}]),
                HTTPStatus.BAD_REQUEST,
            )

        with DB_LOCK:
            conn = db_connect()
            conn.row_factory = sqlite3.Row
            try:
                bot = conn.execute("select * from bots where public_token = ?", (public_token,)).fetchone()
                if not bot:
                    return self._send_json(err("NOT_FOUND", "Bot not found", [{"field": "publicToken", "issue": "not_found"}]), HTTPStatus.NOT_FOUND)
                if str(bot["status"] or "").lower() != "ready":
                    return self._send_json(
                        err("BOT_NOT_READY", "Bot is still processing uploaded knowledge", [{"field": "status", "issue": "processing"}]),
                        HTTPStatus.CONFLICT,
                    )

                raw_conv_id = str(payload.get("conversation_id") or "").strip()
                conv_id = raw_conv_id or str(uuid.uuid4())
                existing = conn.execute("select id, bot_id from conversations where id = ?", (conv_id,)).fetchone()
                now = now_iso()
                if not existing:
                    conn.execute(
                        "insert into conversations (id,bot_id,channel,visitor_id,status,needs_human,created_at,updated_at) values (?,?,?,?,?,?,?,?)",
                        (conv_id, bot["id"], payload.get("channel", "web"), payload.get("visitor_id"), "open", 0, now, now),
                    )
                elif existing["bot_id"] != bot["id"]:
                    conv_id = str(uuid.uuid4())
                    conn.execute(
                        "insert into conversations (id,bot_id,channel,visitor_id,status,needs_human,created_at,updated_at) values (?,?,?,?,?,?,?,?)",
                        (conv_id, bot["id"], payload.get("channel", "web"), payload.get("visitor_id"), "open", 0, now, now),
                    )
                elif payload.get("visitor_id"):
                    conn.execute("update conversations set visitor_id = ?, updated_at = ? where id = ?", (payload.get("visitor_id"), now, conv_id))

                conn.execute(
                    "insert into messages (id,conversation_id,sender_type,message_text,created_at) values (?,?,?,?,?)",
                    (str(uuid.uuid4()), conv_id, "user", message, now),
                )

                answer_data = compute_answer(conn, bot["id"], message, bot["fallback_message"] or FALLBACK_MESSAGE, float(bot["confidence_threshold"] or 0.7))
                conn.execute(
                    "insert into messages (id,conversation_id,sender_type,message_text,confidence,confidence_label,source_text,needs_human,created_at) values (?,?,?,?,?,?,?,?,?)",
                    (
                        str(uuid.uuid4()),
                        conv_id,
                        "ai",
                        str(answer_data["answer"]),
                        answer_data["confidence"],
                        answer_data["confidence_label"],
                        json.dumps(answer_data.get("sources", [])),
                        1 if answer_data["needs_human"] else 0,
                        now,
                    ),
                )
                conn.execute("update conversations set updated_at = ?, needs_human = ? where id = ?", (now, 1 if answer_data["needs_human"] else 0, conv_id))
                conn.commit()
            finally:
                conn.close()

        return self._send_json(ok({"conversation_id": conv_id, **answer_data}))

    def _handle_widget(self, public_token: str) -> None:
        with DB_LOCK:
            conn = db_connect()
            conn.row_factory = sqlite3.Row
            try:
                bot = conn.execute("select id from bots where public_token = ?", (public_token,)).fetchone()
                if not bot:
                    self._send_json(err("NOT_FOUND", "Bot not found"), HTTPStatus.NOT_FOUND)
                    return
            finally:
                conn.close()

        script = (
            "(function(){window.GOCS_WIDGET={"
            f"publicToken:'{public_token}',"
            "apiBase:window.location.origin+'/api',"
            "defaultChannel:'widget'"
            "};})();"
        )
        self._send_js(script)

    def _handle_telegram_connect(self) -> None:
        payload = self._read_json()
        if payload is None:
            return self._send_json(err("VALIDATION_ERROR", "Invalid JSON body"), HTTPStatus.BAD_REQUEST)

        public_token = str(payload.get("public_token") or "").strip()
        tg_token = str(payload.get("telegram_bot_token") or "").strip()
        if not public_token or not tg_token:
            return self._send_json(
                err("VALIDATION_ERROR", "public_token and telegram_bot_token are required", [{"field": "telegram_bot_token", "issue": "required"}]),
                HTTPStatus.BAD_REQUEST,
            )
        if not TELEGRAM_TOKEN_RE.match(tg_token):
            return self._send_json(
                err("VALIDATION_ERROR", "Invalid Telegram token format", [{"field": "telegram_bot_token", "issue": "invalid_format"}]),
                HTTPStatus.BAD_REQUEST,
            )

        webhook_base = str(payload.get("webhook_base_url") or "").strip().rstrip("/")
        if webhook_base and not webhook_base.startswith(("http://", "https://")):
            return self._send_json(
                err("VALIDATION_ERROR", "webhook_base_url must be a valid URL", [{"field": "webhook_base_url", "issue": "invalid_url"}]),
                HTTPStatus.BAD_REQUEST,
            )
        if not webhook_base:
            proto = (self.headers.get("X-Forwarded-Proto") or "http").strip()
            host = (self.headers.get("Host") or f"127.0.0.1:{self.server.server_address[1]}").strip()
            webhook_base = f"{proto}://{host}"

        with DB_LOCK:
            conn = db_connect()
            conn.row_factory = sqlite3.Row
            try:
                bot = conn.execute("select * from bots where public_token = ?", (public_token,)).fetchone()
                if not bot:
                    return self._send_json(err("NOT_FOUND", "Bot not found"), HTTPStatus.NOT_FOUND)
                settings = json.loads(bot["settings"] or "{}")
                settings["telegram_bot_token"] = tg_token
                settings["telegram_connected"] = True
                conn.execute("update bots set settings = ?, updated_at = ? where id = ?", (json.dumps(settings), now_iso(), bot["id"]))
                conn.commit()
            finally:
                conn.close()

        return self._send_json(
            ok(
                {
                    "public_token": public_token,
                    "telegram": {
                        "connected": True,
                        "webhook_url": f"{webhook_base}/api/webhooks/telegram/{public_token}",
                        "bot_username": "demo_placeholder_bot",
                    },
                }
            )
        )

    def _handle_telegram_webhook(self, public_token: str) -> None:
        with DB_LOCK:
            conn = db_connect()
            conn.row_factory = sqlite3.Row
            try:
                bot = conn.execute("select id from bots where public_token = ?", (public_token,)).fetchone()
                if not bot:
                    return self._send_json(err("NOT_FOUND", "Bot not found"), HTTPStatus.NOT_FOUND)
            finally:
                conn.close()

        return self._send_json(ok({"accepted": True, "processed": True, "telegram_message_id": 0, "conversation_id": str(uuid.uuid4())}))


def conn_source_name(public_token: str) -> str | None:
    conn = db_connect()
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute(
            """
            select kf.file_name as file_name
            from knowledge_files kf
            join bots b on b.id = kf.bot_id
            where b.public_token = ?
            order by kf.created_at desc
            limit 1
            """,
            (public_token,),
        ).fetchone()
        return row["file_name"] if row else None
    finally:
        conn.close()


def compute_answer_local(conn: sqlite3.Connection, bot_id: str, message: str, fallback_message: str, threshold: float) -> dict:
    rows = conn.execute(
        """
        select kc.id as chunk_id, kc.chunk_text, kc.embedding, coalesce(kf.file_name, '') as file_name
        from knowledge_chunks kc
        left join knowledge_files kf on kf.id = kc.file_id
        where kc.bot_id = ?
        order by kc.chunk_index asc
        """,
        (bot_id,),
    ).fetchall()
    if not rows:
        return {
            "answer": fallback_message,
            "confidence": 0.4,
            "confidence_label": "Not Enough Information",
            "status": "fallback",
            "source_used": False,
            "needs_human": True,
            "sources": [],
            "source_text": None,
        }

    q_tokens = tokenize(message)
    if not q_tokens:
        return {
            "answer": fallback_message,
            "confidence": 0.4,
            "confidence_label": "Not Enough Information",
            "status": "fallback",
            "source_used": False,
            "needs_human": True,
            "sources": [],
            "source_text": None,
        }

    query_embedding = embed_text(message)
    q_counts = Counter(q_tokens)  # fallback tie-breaker and cold-start fallback
    scored: list[tuple[float, float, sqlite3.Row]] = []
    for row in rows:
        chunk_text = row["chunk_text"] or ""
        c_tokens = tokenize(chunk_text)
        if not c_tokens and not chunk_text.strip():
            continue

        # Primary: vector similarity.
        chunk_embedding = parse_embedding(row["embedding"])
        vec_score = cosine_similarity(query_embedding, chunk_embedding) if chunk_embedding else 0.0

        # Secondary fallback/tie-breaker: keyword overlap.
        c_counts = Counter(c_tokens)
        overlap = sum(min(q_counts[k], c_counts[k]) for k in q_counts.keys())
        overlap_score = overlap / max(1, len(set(q_tokens)))

        final_score = max(vec_score, overlap_score * 0.85)
        if final_score > 0:
            scored.append((final_score, vec_score, row))

    if not scored:
        return {
            "answer": fallback_message,
            "confidence": 0.45,
            "confidence_label": "Not Enough Information",
            "status": "fallback",
            "source_used": False,
            "needs_human": True,
            "sources": [],
            "source_text": None,
        }

    scored.sort(key=lambda x: (x[0], x[1]), reverse=True)
    best_score, vec_component, best_row = scored[0]
    confidence = min(0.95, 0.35 + (best_score * 0.65))

    risk_question = any(k in message.lower() for k in RISK_KEYWORDS)
    required_threshold = max(threshold, 0.78) if risk_question else threshold
    answered = confidence >= required_threshold
    status = "answered" if answered else "fallback"
    answer_text = (best_row["chunk_text"] or "").strip()
    if not answered:
        answer_text = fallback_message

    sources = []
    if answered:
        sources.append({"file_name": best_row["file_name"] or "uploaded_file.txt", "chunk_id": best_row["chunk_id"]})

    return {
        "answer": answer_text,
        "confidence": round(confidence, 2),
        "confidence_label": confidence_label(confidence),
        "status": status,
        "source_used": answered,
        "needs_human": not answered,
        "sources": sources,
        "source_text": answer_text if answered else None,
        "retrieval_provider": "local",
    }


def compute_answer_data_engine(conn: sqlite3.Connection, bot_id: str, message: str, fallback_message: str, threshold: float) -> dict | None:
    """
    Placeholder integration point for external Data Engine retrieval.
    Current behavior:
    - returns None so caller can fallback to local retrieval
    - keeps API contract stable while Data Engine client is introduced later
    """
    if not data_engine_enabled():
        return None
    return None


def compute_answer(conn: sqlite3.Connection, bot_id: str, message: str, fallback_message: str, threshold: float) -> dict:
    provider = retrieval_provider()
    if provider in {"data_engine", "hybrid"}:
        ext = compute_answer_data_engine(conn, bot_id, message, fallback_message, threshold)
        if ext:
            ext.setdefault("retrieval_provider", "data_engine")
            return ext
        local = compute_answer_local(conn, bot_id, message, fallback_message, threshold)
        local["retrieval_provider"] = "local_fallback"
        return local
    return compute_answer_local(conn, bot_id, message, fallback_message, threshold)


class ReusableThreadingTCPServer(ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


def main() -> None:
    parser = argparse.ArgumentParser(description="Run GO!CS prototype locally (frontend + API + DB).")
    parser.add_argument("--port", type=int, default=0, help="HTTP port (default from PORT env or 3000)")
    parser.add_argument("--host", type=str, default="", help="Bind host (default from HOST env or 0.0.0.0)")
    args = parser.parse_args()

    load_env_file(ROOT / ".env")
    global MAX_BODY_BYTES, RATE_LIMIT_PER_MIN, CORS_ALLOW_ORIGIN
    MAX_BODY_BYTES = env_int("GOCS_MAX_BODY_BYTES", 5 * 1024 * 1024, 1024, 50 * 1024 * 1024)
    RATE_LIMIT_PER_MIN = env_int("GOCS_RATE_LIMIT_PER_MIN", 180, 10, 10000)
    CORS_ALLOW_ORIGIN = (os.getenv("GOCS_CORS_ALLOW_ORIGIN", "*") or "*").strip()
    bind_host = (args.host or os.getenv("HOST", DEFAULT_BIND_HOST) or DEFAULT_BIND_HOST).strip()
    port = args.port if args.port > 0 else env_int("PORT", 3000, 1, 65535)
    ensure_db()

    with ReusableThreadingTCPServer((bind_host, port), GoCSHandler) as httpd:
        print(f"GO!CS prototype running at http://{bind_host}:{port}")
        print(f"SQLite database ready at: {DB_PATH}")
        print(f"API limits: max_body_bytes={MAX_BODY_BYTES}, rate_limit_per_min={RATE_LIMIT_PER_MIN}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped.")


if __name__ == "__main__":
    main()
