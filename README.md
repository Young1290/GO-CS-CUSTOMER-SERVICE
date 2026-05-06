# GO!CS Prototype

Lightweight frontend prototype for GO!CS flow: `Upload -> Generate -> Test -> Share`.

This repo is intentionally backend-free and optimized for quick product/demo iteration.

## 1) Quick Start

### Prerequisites

- Python 3.9+ available in `PATH`
- Internet access for CDN assets (React, ReactDOM, Babel, Google Fonts)

### Run

```bash
python main.py --port 3000
```

Open:

```text
http://127.0.0.1:3000
```

Stop server with `Ctrl+C`.

## 2) How This Prototype Works

- `main.py` serves files from repo root and provides SPA fallback to `index.html`.
- Unknown frontend routes resolve to the single-page app.
- Built-in backend endpoints are available under `/api/*` and `/widget/*`.
- Frontend is loaded via script tags in `index.html` and compiled in-browser using Babel.
- Session state is stored in browser `localStorage` under `gocs_demo_session`.
- SQLite database is auto-initialized at startup as `gocs.db`.

## 3) Route Map

### Core user flow

1. `/` - Landing/upload flow
2. `/generating/:sessionId` - Generation progress simulation
3. `/bot/:publicToken/test` - Internal test chat
4. `/bot/:publicToken/share` - Sharing options
5. `/chat/:publicToken` - Public chat page

### Route behavior details

- `:sessionId` and `:publicToken` are parsed from URL path.
- Invalid/unknown paths fall back to `/` (landing page) in client route parser.
- Browser refresh works on deep links because server always falls back to `index.html`.

## 4) Project File Guide

- `main.py` - Local HTTP server + SPA route fallback
- `index.html` - Entry HTML + CDN dependency loading
- `app.jsx` - App shell, route parsing, navigation, and service wiring (`api` mode by default)
- `pages.jsx` - Landing/generation/chat/share/public page components
- `chat-data.jsx` - Mock knowledge base and matching logic
- `gocs-service.jsx` - Service interface with both mock and API adapters; generate flow supports multipart (`file`) and JSON fallback.
- `gocs.css` - All prototype styling
- `browser-window.jsx`, `tweaks-panel.jsx` - Demo chrome and tweak controls

## 5) Known Limits (Current State)

1. No auth/workspace/billing layer yet.
2. File upload parsing/chunking is simplified (basic ingestion + heuristic retrieval).
3. Retrieval uses lightweight local vector similarity (hashed embedding) with keyword fallback; no external vector DB yet.
4. Telegram connection is stored as placeholder config; no external Telegram API registration yet.
5. WhatsApp/Facebook options are placeholder UI only.
6. Widget endpoint returns bootstrap JS only (no production widget bundle).
7. External CDN dependency means offline mode is not supported by default.
8. Uses in-browser Babel transform (fine for prototype, not production).

File extraction note:
1. `txt/md/csv/json/log` uploads are parsed directly.
2. `pdf` extraction is attempted when `pypdf` is installed; otherwise fallback decoding is used.

## 6) Execution Checklist (Demo)

1. Start server and open `/`.
2. Upload a file or paste text (over minimum length) and click generate.
3. Confirm transition to `/generating/:sessionId`.
4. Wait for auto-transition to `/bot/:publicToken/test`.
5. Ask known questions (hours/menu/location) and verify confidence badges.
6. Go to share page and validate:
   - public link copy
   - widget snippet copy
   - Telegram token validation behavior
7. Open `/chat/:publicToken` and test public chat response.

For operations and troubleshooting, see [RUNBOOK.md](/d:/LDE%20Customer%20Service/RUNBOOK.md).

## 7) Next Implementation Steps

1. Add embedding/vector retrieval and confidence calibration.
2. Expand document ingestion quality (DOCX/XLSX + stronger PDF extraction).
3. Add auth/org workspace model for bot ownership.
4. Implement Telegram real API registration + webhook verification.
5. Implement production widget bundle and hosted assets under `/widget/*`.
6. Add test coverage:
   - route parsing and navigation
   - fallback/retrieval behavior
   - share/connect form validation
7. Productionize frontend build (Vite/Next/etc.) and remove in-browser Babel.
8. Add observability (API logs, latency, error rates, fallback rate, unsafe query rate).
