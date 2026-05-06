# GO!CS Prototype Runbook

## Scope

Operational guide for running, validating, and deployment-smoke checking the current GO!CS prototype.

## Start / Stop

Local run:

```bash
python main.py --host 127.0.0.1 --port 3000
```

Deployment-like run:

```bash
python main.py --host 0.0.0.0 --port 3000
```

Stop with `Ctrl+C`.

## Runtime Config

Set via `.env` or host environment:

1. `HOST` (default: `0.0.0.0`)
2. `PORT` (default: `3000`)
3. `GOCS_RATE_LIMIT_PER_MIN` (default: `180`)
4. `GOCS_MAX_BODY_BYTES` (default: `5242880`)
5. `GOCS_CORS_ALLOW_ORIGIN` (default: `*`)
6. `GOCS_RETRIEVAL_PROVIDER=local|data_engine|hybrid`
7. `GOCS_DATA_ENGINE_ENDPOINT=<future endpoint>`

Current retrieval behavior:

1. `local` uses in-process vector+keyword retrieval.
2. `data_engine`/`hybrid` are integration-ready and currently fallback to local retrieval until Data Engine wiring is added.

## Health & API Sanity

PowerShell health check:

```powershell
Invoke-RestMethod http://127.0.0.1:3000/api/health
```

Expected fields:

1. `status=ok`
2. `retrieval_provider`
3. `data_engine_enabled`
4. `limits.max_body_bytes`
5. `limits.rate_limit_per_min`

## Automated Smoke

Run full API milestone smoke:

```bash
python scripts/smoke_milestone_apis.py --base-url http://127.0.0.1:3000
```

Covers:

1. `POST /api/generate-bot`
2. `GET /api/bot/:publicToken`
3. `POST /api/bot/:publicToken/ask`
4. `POST /api/telegram/connect`
5. `GET /widget/:publicToken.js`

## Route Verification

Open each route and confirm SPA fallback works:

1. `/`
2. `/generating/session-demo-001`
3. `/bot/sakura-ramen-9k2x/test`
4. `/bot/sakura-ramen-9k2x/share`
5. `/chat/sakura-ramen-9k2x`

## Manual Demo Validation

1. On `/`, upload any file or paste long text (>30 chars).
2. Click `Generate my AI customer service`.
3. Confirm transition `/generating/:sessionId -> /bot/:publicToken/test`.
4. In test chat, ask:
   - `What are your business hours?`
   - `What is your refund policy?`
5. On share page:
   - verify public link copy
   - verify widget snippet copy
   - test Telegram token validation (invalid then valid format)
6. Open `/chat/:publicToken` and verify public chat responses.

## Deployment Checklist

1. `python -m py_compile main.py scripts/smoke_milestone_apis.py` passes.
2. `scripts/smoke_milestone_apis.py` passes against target runtime URL.
3. `.env` contains production-safe values (no dev placeholders).
4. CORS origin narrowed from `*` when deploying publicly.
5. Reverse proxy/TLS is configured upstream (if exposed internet-facing).

## Known Failure Modes

1. Blank page or broken scripts:
   - Cause: CDN blocked/offline.
   - Action: restore internet, reload page.
2. `Address already in use`:
   - Cause: selected port occupied.
   - Action: run with another port (for example `--port 3001`).
3. Deep-link 404 on non-`main.py` server:
   - Cause: missing SPA fallback.
   - Action: route unknown paths to `index.html`.
4. Unexpected throttling (429):
   - Cause: `GOCS_RATE_LIMIT_PER_MIN` too low for current load.
   - Action: increase limit and restart.
5. Request rejected as too large (413):
   - Cause: body exceeds `GOCS_MAX_BODY_BYTES`.
   - Action: raise limit or reduce upload size.
