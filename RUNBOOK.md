# GO!CS Prototype Runbook

## Scope

Operational guide for running and validating this prototype locally.

## Start / Stop

Run:

```bash
python main.py --port 3000
```

Health check in browser:

```text
http://127.0.0.1:3000
```

Stop with `Ctrl+C`.

## Preflight Checks

1. Python command works: `python --version`
2. Port is free (if needed on Windows): `netstat -ano | findstr :3000`
3. Internet is available (CDN scripts/fonts are required)

## Route Verification

Open each route directly and confirm it loads:

1. `/`
2. `/generating/session-demo-001`
3. `/bot/sakura-ramen-9k2x/test`
4. `/bot/sakura-ramen-9k2x/share`
5. `/chat/sakura-ramen-9k2x`

Expected behavior:

- All routes return app UI (SPA fallback works).
- Core backend endpoints are reachable:
  - `GET /api/health`
  - `POST /api/generate-bot`
  - `GET /api/bot/:publicToken`
  - `POST /api/bot/:publicToken/ask`
  - `GET /widget/:publicToken.js`

## Retrieval Provider Config

Optional `.env` keys:

1. `GOCS_RETRIEVAL_PROVIDER=local|data_engine|hybrid`
2. `GOCS_DATA_ENGINE_ENDPOINT=<future endpoint>`

Current behavior:

1. `local` uses in-process vector+keyword retrieval.
2. `data_engine`/`hybrid` are integration-ready modes and currently fallback to local retrieval until Data Engine client is wired.

## Demo Validation Script (Manual)

1. On `/`, upload any file name or paste long text (>30 chars).
2. Click `Generate my AI customer service`.
3. Verify progress page appears then transitions automatically.
4. In test chat, ask:
   - `What are your business hours?` (high confidence expected)
   - `What is your refund policy?` (fallback expected)
5. On share page:
   - Test copy buttons
   - Test Telegram token validation:
     - invalid input -> inline error
     - valid pattern like `123456:ABC_DEF-ghiJKLmnopQRSTuvwx` -> placeholder success
6. Open public chat and verify responses render.

## Known Failure Modes

1. Blank page or broken scripts:
   - Cause: CDN blocked/offline.
   - Action: restore internet, reload page.
2. `Address already in use` on startup:
   - Cause: selected port already occupied.
   - Action: run with another port, e.g. `python main.py --port 3001`.
3. Deep link issues:
   - Cause: using another static server without SPA fallback.
   - Action: use `main.py` server from this repo.
4. Data unexpectedly persists between runs:
   - Cause: browser localStorage (`gocs_demo_session`).
   - Action: clear localStorage or open an incognito window.

## Handoff Notes

This runbook reflects the current mock architecture (no real backend integrations).  
If API integration lands, update:

1. health checks
2. route/API verification
3. failure modes
4. recovery steps
