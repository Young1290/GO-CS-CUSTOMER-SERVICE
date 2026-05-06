#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.parse
import urllib.request


class SmokeTestError(Exception):
    pass


def http_json(method: str, url: str, payload: dict | None = None) -> tuple[int, dict, dict]:
    data = None
    headers = {"Accept": "application/json"}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    req = urllib.request.Request(url=url, method=method, data=data, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            body = resp.read().decode("utf-8")
            return resp.status, json.loads(body), dict(resp.headers)
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        parsed = {}
        try:
            parsed = json.loads(body)
        except json.JSONDecodeError:
            pass
        return e.code, parsed, dict(e.headers)
    except urllib.error.URLError as e:
        raise SmokeTestError(f"Network error calling {url}: {e}") from e


def http_text(method: str, url: str) -> tuple[int, str, dict]:
    req = urllib.request.Request(url=url, method=method, headers={"Accept": "*/*"})
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return resp.status, resp.read().decode("utf-8"), dict(resp.headers)
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", errors="replace"), dict(e.headers)
    except urllib.error.URLError as e:
        raise SmokeTestError(f"Network error calling {url}: {e}") from e


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise SmokeTestError(message)


def run_smoke(base_url: str, telegram_token: str) -> None:
    print(f"[1/5] POST {base_url}/api/generate-bot")
    status, body, _ = http_json(
        "POST",
        f"{base_url}/api/generate-bot",
        payload={
            "pasted_text": "We are ACME Support. Business hours are 9am to 6pm. Contact us anytime.",
            "owner_email": "qa-smoke@example.com",
            "business_type": "service_business",
            "tone": "friendly",
            "settings": {"smoke": True},
        },
    )
    assert_true(status == 201, f"Expected 201 from generate-bot, got {status}. Body: {body}")
    assert_true(body.get("ok") is True, f"generate-bot returned non-ok body: {body}")
    data = body.get("data", {})
    public_token = data.get("public_token")
    assert_true(bool(public_token), f"Missing public_token in generate-bot response: {body}")
    print(f"  PASS generate-bot public_token={public_token}")

    print(f"[2/5] GET {base_url}/api/bot/{public_token}")
    status, body, _ = http_json("GET", f"{base_url}/api/bot/{public_token}")
    assert_true(status == 200, f"Expected 200 from bot info, got {status}. Body: {body}")
    assert_true(body.get("ok") is True, f"bot info returned non-ok body: {body}")
    bot_data = body.get("data", {})
    assert_true(bot_data.get("public_token") == public_token, "bot info public_token mismatch")
    print("  PASS bot info")

    print(f"[3/5] POST {base_url}/api/bot/{public_token}/ask")
    status, body, _ = http_json(
        "POST",
        f"{base_url}/api/bot/{public_token}/ask",
        payload={"message": "What are your opening hours?", "channel": "web"},
    )
    assert_true(status == 200, f"Expected 200 from ask, got {status}. Body: {body}")
    assert_true(body.get("ok") is True, f"ask returned non-ok body: {body}")
    ask_data = body.get("data", {})
    assert_true(bool(ask_data.get("answer")), "ask response missing answer")
    assert_true(ask_data.get("status") in {"answered", "fallback"}, f"ask status invalid: {ask_data}")
    print(f"  PASS ask status={ask_data.get('status')}")

    print(f"[4/5] POST {base_url}/api/telegram/connect")
    status, body, _ = http_json(
        "POST",
        f"{base_url}/api/telegram/connect",
        payload={
            "public_token": public_token,
            "telegram_bot_token": telegram_token,
            "webhook_base_url": base_url,
        },
    )
    assert_true(status == 200, f"Expected 200 from telegram connect, got {status}. Body: {body}")
    assert_true(body.get("ok") is True, f"telegram connect returned non-ok body: {body}")
    tg = body.get("data", {}).get("telegram", {})
    assert_true(tg.get("connected") is True, f"telegram not connected: {body}")
    print("  PASS telegram connect")

    print(f"[5/5] GET {base_url}/widget/{public_token}.js")
    status, text, headers = http_text("GET", f"{base_url}/widget/{public_token}.js")
    assert_true(status == 200, f"Expected 200 from widget js, got {status}. Body: {text[:300]}")
    assert_true("publicToken" in text and public_token in text, "widget script missing publicToken marker")
    content_type = headers.get("Content-Type", "")
    assert_true("javascript" in content_type, f"Unexpected widget content type: {content_type}")
    print("  PASS widget js")

    print("\nSmoke test completed successfully.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Milestone API smoke test: generate-bot, bot info, ask, telegram connect, widget js."
    )
    parser.add_argument(
        "--base-url",
        default="http://127.0.0.1:3000",
        help="Running server base URL (default: http://127.0.0.1:3000)",
    )
    parser.add_argument(
        "--telegram-token",
        default="123456:abcdefghijklmnopqrstuvwxyzABCD",
        help="Telegram token used for connect API validation",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    base_url = args.base_url.rstrip("/")
    try:
        run_smoke(base_url=base_url, telegram_token=args.telegram_token)
        return 0
    except SmokeTestError as e:
        print(f"\nSmoke test FAILED: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
