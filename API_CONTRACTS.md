# GO!CS API Contracts (Mock-First)

## 1) Contract Conventions

- Base path: `/api` unless endpoint explicitly starts outside API (widget script).
- Content type: `application/json` for JSON endpoints.
- Auth (MVP): none required for test/public token routes.
- Time format: ISO 8601 UTC string.
- ID format: UUID for internal IDs, opaque string for `public_token`.

### Standard Success Envelope

```json
{
  "ok": true,
  "data": {},
  "meta": {
    "request_id": "req_01JZ6A8F3R5Y9N2K4M7P",
    "timestamp": "2026-05-07T10:12:33.124Z"
  }
}
```

### Standard Error Envelope

```json
{
  "ok": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Input validation failed",
    "details": [
      {
        "field": "message",
        "issue": "required"
      }
    ]
  },
  "meta": {
    "request_id": "req_01JZ6A8F3R5Y9N2K4M7P",
    "timestamp": "2026-05-07T10:12:33.124Z"
  }
}
```

### Error Codes

- `VALIDATION_ERROR` -> 400
- `NOT_FOUND` -> 404
- `BOT_NOT_READY` -> 409
- `UNSUPPORTED_MEDIA_TYPE` -> 415
- `RATE_LIMITED` -> 429
- `TELEGRAM_CONNECT_FAILED` -> 502
- `INTERNAL_ERROR` -> 500

## 2) POST `/api/generate-bot`

Create a bot from uploaded file and/or pasted text.

### Request

Content type: `multipart/form-data`

Fields:

- `file` (optional, binary)
- `pasted_text` (optional, string)
- `owner_email` (optional, string)
- `business_type` (optional, enum): `auto|restaurant|ecommerce|legal|education|beauty|clinic|property|service_business|others`
- `tone` (optional, enum): `professional|friendly|luxury|casual|short_direct`
- `settings` (optional, JSON string)

Validation:

- At least one of `file` or `pasted_text` is required.

### Response 201

```json
{
  "ok": true,
  "data": {
    "bot_id": "1c3d1bf9-2d35-45c2-8d45-84ea174f8364",
    "public_token": "bot_pk_9f7r2a8m",
    "status": "processing",
    "test_url": "/bot/bot_pk_9f7r2a8m/test",
    "share_url": "/bot/bot_pk_9f7r2a8m/share",
    "suggested_questions": [],
    "fallback_message": "I could not find enough information in the uploaded company information to answer this confidently. Please contact the team directly or upload more details to improve this AI assistant."
  },
  "meta": {
    "request_id": "req_01JZ6AG5M5FQK9GX8A7S",
    "timestamp": "2026-05-07T10:15:03.124Z"
  }
}
```

### Error Examples

400:

```json
{
  "ok": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Either file or pasted_text is required",
    "details": [
      {
        "field": "file|pasted_text",
        "issue": "missing_both"
      }
    ]
  },
  "meta": {
    "request_id": "req_01JZ6AHNPAQ8WQ70H5B1",
    "timestamp": "2026-05-07T10:15:10.124Z"
  }
}
```

415:

```json
{
  "ok": false,
  "error": {
    "code": "UNSUPPORTED_MEDIA_TYPE",
    "message": "Unsupported file type. Allowed: pdf, docx, txt",
    "details": [
      {
        "field": "file",
        "issue": "unsupported_extension"
      }
    ]
  },
  "meta": {
    "request_id": "req_01JZ6AJ6M1R5VQ7HK7CQ",
    "timestamp": "2026-05-07T10:15:19.124Z"
  }
}
```

## 3) GET `/api/bot/:publicToken`

Fetch bot profile and readiness for test/share pages.

### Path Params

- `publicToken` (required, string)

### Response 200

```json
{
  "ok": true,
  "data": {
    "public_token": "bot_pk_9f7r2a8m",
    "name": "AI Customer Service",
    "status": "ready",
    "business_type": "restaurant",
    "tone": "professional",
    "answer_mode": "knowledge_only",
    "confidence_threshold": 0.7,
    "fallback_message": "I am not fully sure based on the information I have. Let me forward this to a human team member.",
    "suggested_questions": [
      "What services do you provide?",
      "What is your pricing?"
    ],
    "knowledge_file_count": 1,
    "created_at": "2026-05-07T10:15:03.124Z",
    "updated_at": "2026-05-07T10:16:41.124Z"
  },
  "meta": {
    "request_id": "req_01JZ6AN8Q39A2P7D1E4M",
    "timestamp": "2026-05-07T10:16:45.124Z"
  }
}
```

### Error Example

404:

```json
{
  "ok": false,
  "error": {
    "code": "NOT_FOUND",
    "message": "Bot not found",
    "details": [
      {
        "field": "publicToken",
        "issue": "not_found"
      }
    ]
  },
  "meta": {
    "request_id": "req_01JZ6APVZ8MW4PBX2KKZ",
    "timestamp": "2026-05-07T10:16:55.124Z"
  }
}
```

## 4) POST `/api/bot/:publicToken/ask`

Ask bot a question in test/public/widget/telegram channels.

### Request

```json
{
  "message": "What is your pricing?",
  "visitor_id": "visitor_123",
  "channel": "web",
  "conversation_id": "conv_01JZ6ARPN7X4XG8Q2Z6V",
  "locale": "en"
}
```

Fields:

- `message` (required, string, 1..2000)
- `visitor_id` (optional, string)
- `channel` (optional, enum): `web|widget|telegram`
- `conversation_id` (optional, string)
- `locale` (optional, BCP-47 string)

### Response 200 (Answered)

```json
{
  "ok": true,
  "data": {
    "conversation_id": "conv_01JZ6ARPN7X4XG8Q2Z6V",
    "answer": "Based on our current pricing sheet, the starter package is RM120 per month.",
    "confidence": 0.86,
    "confidence_label": "High Confidence",
    "status": "answered",
    "source_used": true,
    "needs_human": false,
    "sources": [
      {
        "file_name": "pricing.pdf",
        "chunk_id": "chunk_01JZ6AT4A0H8N8W6FY9M"
      }
    ]
  },
  "meta": {
    "request_id": "req_01JZ6ATP7RP4T2S9R7XQ",
    "timestamp": "2026-05-07T10:17:21.124Z"
  }
}
```

### Response 200 (Fallback)

```json
{
  "ok": true,
  "data": {
    "conversation_id": "conv_01JZ6AVFQWNP5ME0H9V2",
    "answer": "I could not find enough information in the uploaded company information to answer this confidently. Please contact the team directly or upload more details to improve this AI assistant.",
    "confidence": 0.42,
    "confidence_label": "Not Enough Information",
    "status": "fallback",
    "source_used": false,
    "needs_human": true,
    "sources": []
  },
  "meta": {
    "request_id": "req_01JZ6AX32GQ7VQ5DF9W8",
    "timestamp": "2026-05-07T10:17:36.124Z"
  }
}
```

### Error Examples

400:

```json
{
  "ok": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Input validation failed",
    "details": [
      {
        "field": "message",
        "issue": "required"
      }
    ]
  },
  "meta": {
    "request_id": "req_01JZ6AZDCP5NSE75Y6QV",
    "timestamp": "2026-05-07T10:17:50.124Z"
  }
}
```

409:

```json
{
  "ok": false,
  "error": {
    "code": "BOT_NOT_READY",
    "message": "Bot is still processing uploaded knowledge",
    "details": [
      {
        "field": "status",
        "issue": "processing"
      }
    ]
  },
  "meta": {
    "request_id": "req_01JZ6B1M50E8ZF3WENW2",
    "timestamp": "2026-05-07T10:18:03.124Z"
  }
}
```

## 5) GET `/widget/:publicToken.js`

Return embeddable widget bootstrap script.

### Query Params

- `theme` (optional): `light|dark|auto`
- `position` (optional): `bottom-right|bottom-left`

### Response 200

Content type: `application/javascript`

```javascript
(function () {
  window.GOCS_WIDGET = {
    publicToken: "bot_pk_9f7r2a8m",
    apiBase: "https://gocs.ai/api",
    defaultChannel: "widget"
  };
})();
```

### Error Response

If token is invalid, return JSON error with 404:

```json
{
  "ok": false,
  "error": {
    "code": "NOT_FOUND",
    "message": "Bot not found",
    "details": []
  },
  "meta": {
    "request_id": "req_01JZ6B3XD3SRSRZ0CQ8Y",
    "timestamp": "2026-05-07T10:18:17.124Z"
  }
}
```

## 6) POST `/api/telegram/connect`

Connect Telegram bot token to a GO!CS bot and register webhook.

### Request

```json
{
  "public_token": "bot_pk_9f7r2a8m",
  "telegram_bot_token": "123456789:AAExampleToken",
  "webhook_base_url": "https://gocs.ai"
}
```

Fields:

- `public_token` (required, string)
- `telegram_bot_token` (required, string)
- `webhook_base_url` (optional, string URL)

### Response 200

```json
{
  "ok": true,
  "data": {
    "public_token": "bot_pk_9f7r2a8m",
    "telegram": {
      "connected": true,
      "webhook_url": "https://gocs.ai/api/webhooks/telegram/bot_pk_9f7r2a8m",
      "bot_username": "my_store_support_bot"
    }
  },
  "meta": {
    "request_id": "req_01JZ6B6B1AKY7RGE2M4S",
    "timestamp": "2026-05-07T10:18:35.124Z"
  }
}
```

### Error Examples

400:

```json
{
  "ok": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "telegram_bot_token is required",
    "details": [
      {
        "field": "telegram_bot_token",
        "issue": "required"
      }
    ]
  },
  "meta": {
    "request_id": "req_01JZ6B87Q6P7V66R5GKB",
    "timestamp": "2026-05-07T10:18:49.124Z"
  }
}
```

502:

```json
{
  "ok": false,
  "error": {
    "code": "TELEGRAM_CONNECT_FAILED",
    "message": "Failed to verify Telegram token or set webhook",
    "details": [
      {
        "field": "telegram_bot_token",
        "issue": "telegram_api_rejected"
      }
    ]
  },
  "meta": {
    "request_id": "req_01JZ6BAZQ9YJJ17R2CN3",
    "timestamp": "2026-05-07T10:18:58.124Z"
  }
}
```

## 7) POST `/api/webhooks/telegram/:publicToken`

Telegram webhook receiver. Consumes Telegram update payload and routes text messages to ask pipeline.

### Path Params

- `publicToken` (required, string)

### Request (Telegram update excerpt)

```json
{
  "update_id": 923456001,
  "message": {
    "message_id": 77,
    "from": {
      "id": 44112233,
      "is_bot": false,
      "first_name": "Nora"
    },
    "chat": {
      "id": 44112233,
      "type": "private"
    },
    "date": 1778149212,
    "text": "Do you open on Sunday?"
  }
}
```

### Response 200

```json
{
  "ok": true,
  "data": {
    "accepted": true,
    "processed": true,
    "telegram_message_id": 77,
    "conversation_id": "conv_01JZ6BDK0SRHQ5XJ9SP7"
  },
  "meta": {
    "request_id": "req_01JZ6BCZ27H0BPY2BGH2",
    "timestamp": "2026-05-07T10:19:20.124Z"
  }
}
```

### Error Example

404:

```json
{
  "ok": false,
  "error": {
    "code": "NOT_FOUND",
    "message": "Bot not found",
    "details": [
      {
        "field": "publicToken",
        "issue": "not_found"
      }
    ]
  },
  "meta": {
    "request_id": "req_01JZ6BFA4NJ1EJY3E3P7",
    "timestamp": "2026-05-07T10:19:34.124Z"
  }
}
```

## 8) Mock-First Notes for Backend Integration

- Keep response envelopes stable (`ok/data/meta` and `ok/error/meta`) across all handlers.
- Frontend should branch by `data.status` for ask responses: `answered|fallback`.
- Confidence labels must follow PRD logic:
  - `High Confidence`: `0.80 - 1.00`
  - `Medium Confidence`: `0.60 - 0.79`
  - `Not Enough Information`: `< 0.60`
- Ask API must enforce knowledge-only behavior and no guessing fallback.
- Web widget and Telegram both reuse the same ask engine with channel set accordingly.
