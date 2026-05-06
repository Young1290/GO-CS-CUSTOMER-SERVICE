from __future__ import annotations

import argparse
import json
import sqlite3
import threading
import time
import uuid
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler
from pathlib import Path
from socketserver import ThreadingTCPServer
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "gocs.db"

FALLBACK_MESSAGE = (
    "I could not find enough information in the uploaded company information to answer this confidently. "
    "Please contact the team directly or upload more details to improve this AI assistant."
)

DB_LOCK = threading.Lock()


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
        conn = sqlite3.connect(DB_PATH)
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

    def _read_json(self) -> dict | None:
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0:
            return {}
        raw = self.rfile.read(length)
        try:
            return json.loads(raw.decode("utf-8"))
        except Exception:
            return None

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path

        if path.startswith("/api/"):
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

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path

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

    def _handle_generate_bot(self) -> None:
        payload = self._read_json()
        if payload is None:
            return self._send_json(err("VALIDATION_ERROR", "Invalid JSON body"), HTTPStatus.BAD_REQUEST)

        file_name = str(payload.get("fileName") or "").strip()
        pasted_text = str(payload.get("pasted_text") or "").strip()
        if not file_name and len(pasted_text) < 20:
            return self._send_json(
                err("VALIDATION_ERROR", "Either fileName or pasted_text is required", [{"field": "fileName|pasted_text", "issue": "missing_both"}]),
                HTTPStatus.BAD_REQUEST,
            )

        bot_id = str(uuid.uuid4())
        file_id = str(uuid.uuid4())
        public_token = f"bot_{uuid.uuid4().hex[:10]}"
        created = now_iso()
        business_type = str(payload.get("business_type") or "auto").lower()
        tone = str(payload.get("tone") or "friendly").lower()
        source_name = file_name or "Pasted_Company_Info.txt"
        settings = payload.get("settings") or {}
        suggested = [
            "What services do you provide?",
            "What is your pricing?",
            "How can customers contact you?",
            "What are your business hours?",
            "What is your refund policy?",
        ]

        with DB_LOCK:
            conn = sqlite3.connect(DB_PATH)
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
                        "ready",
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
                    (file_id, bot_id, source_name, "txt", None, pasted_text or "Uploaded file placeholder text", "processed", created),
                )
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
            conn = sqlite3.connect(DB_PATH)
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

        with DB_LOCK:
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            try:
                bot = conn.execute("select * from bots where public_token = ?", (public_token,)).fetchone()
                if not bot:
                    return self._send_json(err("NOT_FOUND", "Bot not found", [{"field": "publicToken", "issue": "not_found"}]), HTTPStatus.NOT_FOUND)

                conv_id = payload.get("conversation_id") or str(uuid.uuid4())
                existing = conn.execute("select id from conversations where id = ?", (conv_id,)).fetchone()
                now = now_iso()
                if not existing:
                    conn.execute(
                        "insert into conversations (id,bot_id,channel,visitor_id,status,needs_human,created_at,updated_at) values (?,?,?,?,?,?,?,?)",
                        (conv_id, bot["id"], payload.get("channel", "web"), payload.get("visitor_id"), "open", 0, now, now),
                    )

                conn.execute(
                    "insert into messages (id,conversation_id,sender_type,message_text,created_at) values (?,?,?,?,?)",
                    (str(uuid.uuid4()), conv_id, "user", message, now),
                )

                answer_data = compute_answer(message)
                conn.execute(
                    "insert into messages (id,conversation_id,sender_type,message_text,confidence,confidence_label,source_text,needs_human,created_at) values (?,?,?,?,?,?,?,?,?)",
                    (
                        str(uuid.uuid4()),
                        conv_id,
                        "ai",
                        " ".join(answer_data["answer"]) if isinstance(answer_data["answer"], list) else str(answer_data["answer"]),
                        answer_data["confidence"],
                        answer_data["confidence_label"],
                        answer_data["source_text"],
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

        with DB_LOCK:
            conn = sqlite3.connect(DB_PATH)
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
                        "webhook_url": f"/api/webhooks/telegram/{public_token}",
                        "bot_username": "demo_placeholder_bot",
                    },
                }
            )
        )

    def _handle_telegram_webhook(self, public_token: str) -> None:
        with DB_LOCK:
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            try:
                bot = conn.execute("select id from bots where public_token = ?", (public_token,)).fetchone()
                if not bot:
                    return self._send_json(err("NOT_FOUND", "Bot not found"), HTTPStatus.NOT_FOUND)
            finally:
                conn.close()

        return self._send_json(ok({"accepted": True, "processed": True, "telegram_message_id": 0, "conversation_id": str(uuid.uuid4())}))


def conn_source_name(public_token: str) -> str | None:
    conn = sqlite3.connect(DB_PATH)
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


def compute_answer(message: str) -> dict:
    lower = message.lower()
    if "hour" in lower or "open" in lower:
        return {
            "answer": [
                "We're open every day:",
                "Mon-Thu: 11:30 AM to 9:30 PM",
                "Fri-Sat: 11:30 AM to 10:30 PM",
                "Sun: 12:00 PM to 9:00 PM",
            ],
            "confidence": 0.9,
            "confidence_label": "High Confidence",
            "status": "answered",
            "source_used": True,
            "needs_human": False,
            "source_text": "Sakura_Ramen_Info.pdf · page 1 - Hours",
        }

    if "menu" in lower or "ramen" in lower:
        return {
            "answer": ["We serve Tonkotsu Shio, Spicy Miso, Yuzu Shoyu, and Vegan Shiitake."],
            "confidence": 0.82,
            "confidence_label": "High Confidence",
            "status": "answered",
            "source_used": True,
            "needs_human": False,
            "source_text": "Sakura_Ramen_Info.pdf · page 3 - Menu",
        }

    risk_keywords = ["price", "refund", "guarantee", "legal", "medical", "financial", "availability", "contract", "warranty", "latest"]
    if any(k in lower for k in risk_keywords):
        return {
            "answer": [FALLBACK_MESSAGE],
            "confidence": 0.45,
            "confidence_label": "Not Enough Information",
            "status": "fallback",
            "source_used": False,
            "needs_human": True,
            "source_text": None,
        }

    return {
        "answer": [FALLBACK_MESSAGE],
        "confidence": 0.4,
        "confidence_label": "Not Enough Information",
        "status": "fallback",
        "source_used": False,
        "needs_human": True,
        "source_text": None,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run GO!CS prototype locally (frontend + API + DB).")
    parser.add_argument("--port", type=int, default=3000, help="HTTP port (default: 3000)")
    args = parser.parse_args()

    ensure_db()

    with ThreadingTCPServer(("127.0.0.1", args.port), GoCSHandler) as httpd:
        print(f"GO!CS prototype running at http://127.0.0.1:{args.port}")
        print(f"SQLite database ready at: {DB_PATH}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped.")


if __name__ == "__main__":
    main()
