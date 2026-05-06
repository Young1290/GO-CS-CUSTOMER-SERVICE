// gocs-service.jsx
// Stable service interface for mock-now / API-later implementation.

const GOCS_SESSION_STORAGE_KEY = 'gocs_demo_session';

function gocsNowMeta() {
  return {
    request_id: `req_${Date.now().toString(36)}`,
    timestamp: new Date().toISOString(),
  };
}

function gocsSuccess(data) {
  return { ok: true, data, meta: gocsNowMeta() };
}

function gocsError(code, message, details = []) {
  return { ok: false, error: { code, message, details }, meta: gocsNowMeta() };
}

function normalizeEnvelope(body, res = null) {
  if (body && typeof body === 'object' && typeof body.ok === 'boolean') {
    return body;
  }
  if (res && res.ok) {
    return gocsSuccess(body || {});
  }
  const status = res?.status || 0;
  return gocsError('API_ERROR', `API request failed${status ? ` (${status})` : ''}.`);
}

function serializeSettings(settings) {
  if (!settings || typeof settings !== 'object') return null;
  try {
    return JSON.stringify(settings);
  } catch (e) {
    return null;
  }
}

function appendIfPresent(formData, key, value) {
  if (value === undefined || value === null) return;
  const str = String(value);
  if (!str.trim()) return;
  formData.append(key, str);
}

function readSessionFallback() {
  try {
    return JSON.parse(localStorage.getItem(GOCS_SESSION_STORAGE_KEY)) || null;
  } catch (e) {
    return null;
  }
}

function writeSession(session) {
  localStorage.setItem(GOCS_SESSION_STORAGE_KEY, JSON.stringify(session));
}

function createMockAdapter() {
  return {
    async generateBot(payload) {
      await new Promise((r) => setTimeout(r, 500));
      const hasInput = Boolean(payload.fileName || (payload.pasted_text && payload.pasted_text.trim().length > 20));
      if (!hasInput) {
        return gocsError('VALIDATION_ERROR', 'Please upload a file or paste enough information to continue.', [
          { field: 'file|pasted_text', issue: 'missing_both' },
        ]);
      }

      const session = {
        sessionId: `session-${Date.now().toString(36)}`,
        publicToken: `token-${Date.now().toString(36)}`,
        businessType: (payload.business_type || 'auto').toLowerCase(),
        tone: (payload.tone || 'friendly').toLowerCase(),
        sourceName: payload.fileName || 'Pasted_Company_Info.txt',
      };
      writeSession(session);

      return gocsSuccess({
        bot_id: session.sessionId,
        public_token: session.publicToken,
        status: 'processing',
        test_url: `/bot/${session.publicToken}/test`,
        share_url: `/bot/${session.publicToken}/share`,
        suggested_questions: (window.SAKURA_QA || []).slice(0, 5).map((q) => q.q),
        fallback_message: (window.FALLBACK_LINES || []).join(' '),
        session,
      });
    },

    async getBotInfo({ publicToken }) {
      await new Promise((r) => setTimeout(r, 150));
      const s = readSessionFallback() || {
        businessType: 'auto',
        tone: 'friendly',
        sourceName: 'Sakura_Ramen_Info.pdf',
      };
      return gocsSuccess({
        name: 'AI Customer Service',
        status: 'ready',
        business_type: s.businessType,
        tone: s.tone,
        suggested_questions: (window.SAKURA_QA || []).slice(0, 5).map((q) => q.q),
        knowledge_file_count: 1,
        public_token: publicToken,
        source_name: s.sourceName,
      });
    },

    async askBot({ publicToken, message }) {
      await new Promise((r) => setTimeout(r, 700 + Math.random() * 350));
      if (!message || !message.trim()) {
        return gocsError('VALIDATION_ERROR', 'message is required', [{ field: 'message', issue: 'required' }]);
      }

      const match = window.findKnowledgeMatch ? window.findKnowledgeMatch(message) : null;
      const risk = window.isRiskQuestion ? window.isRiskQuestion(message) : false;

      if (!match) {
        return gocsSuccess({
          answer: window.FALLBACK_LINES,
          confidence: 0.4,
          confidence_label: 'Not Enough Information',
          status: 'fallback',
          source_used: false,
          needs_human: true,
          source_text: null,
        });
      }

      if (risk && match.confidence !== 'high') {
        return gocsSuccess({
          answer: window.FALLBACK_LINES,
          confidence: 0.55,
          confidence_label: 'Not Enough Information',
          status: 'fallback',
          source_used: false,
          needs_human: true,
          source_text: null,
        });
      }

      const score = match.confidence === 'high' ? 0.9 : match.confidence === 'medium' ? 0.7 : 0.5;
      return gocsSuccess({
        answer: match.a,
        confidence: score,
        confidence_label: score >= 0.8 ? 'High Confidence' : score >= 0.6 ? 'Medium Confidence' : 'Not Enough Information',
        status: 'answered',
        source_used: Boolean(match.source),
        needs_human: score < 0.6,
        source_text: match.source || null,
      });
    },

    async connectTelegram({ public_token, telegram_bot_token }) {
      await new Promise((r) => setTimeout(r, 200));
      const valid = /^\d{6,}:[\w-]{20,}$/.test((telegram_bot_token || '').trim());
      if (!valid) {
        return gocsError('VALIDATION_ERROR', 'Invalid token format.', [
          { field: 'telegram_bot_token', issue: 'invalid_format' },
        ]);
      }
      return gocsSuccess({
        public_token,
        telegram: {
          connected: true,
          webhook_url: `https://gocs.ai/api/webhooks/telegram/${public_token}`,
          bot_username: 'demo_placeholder_bot',
        },
      });
    },

    getWidgetSnippet({ publicToken }) {
      return `<script src="https://gocs.ai/widget/${publicToken}.js"></script>`;
    },
  };
}

async function fetchJson(url, options = {}) {
  try {
    const res = await fetch(url, options);
    const contentType = res.headers.get('content-type') || '';
    let body = null;
    if (contentType.includes('application/json')) {
      body = await res.json();
    } else {
      const text = await res.text();
      try {
        body = text ? JSON.parse(text) : null;
      } catch (e) {
        body = text ? { message: text } : null;
      }
    }
    return normalizeEnvelope(body, res);
  } catch (e) {
    return gocsError('NETWORK_ERROR', e?.message || 'Unable to reach API server.');
  }
}

function createApiAdapter() {
  return {
    async generateBot(payload) {
      const apiPayload = {
        fileName: payload.fileName,
        pasted_text: payload.pasted_text,
        owner_email: payload.owner_email,
        business_type: payload.business_type,
        tone: payload.tone,
        settings: payload.settings,
      };
      let result;
      if (payload.file instanceof File) {
        const formData = new FormData();
        formData.append('file', payload.file, payload.file.name || payload.fileName || 'upload.txt');
        appendIfPresent(formData, 'pasted_text', payload.pasted_text);
        appendIfPresent(formData, 'owner_email', payload.owner_email);
        appendIfPresent(formData, 'business_type', payload.business_type);
        appendIfPresent(formData, 'tone', payload.tone);
        const settingsJson = serializeSettings(payload.settings);
        if (settingsJson) formData.append('settings', settingsJson);
        result = await fetchJson('/api/generate-bot', {
          method: 'POST',
          body: formData,
        });
      } else {
        result = await fetchJson('/api/generate-bot', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(apiPayload),
        });
      }
      if (result.ok && result.data?.session) {
        writeSession(result.data.session);
      }
      return result;
    },

    async getBotInfo({ publicToken }) {
      return fetchJson(`/api/bot/${publicToken}`);
    },

    async askBot({ publicToken, message, visitor_id = 'web_visitor', channel = 'web', conversation_id = null }) {
      return fetchJson(`/api/bot/${publicToken}/ask`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message, visitor_id, channel, conversation_id }),
      });
    },

    async connectTelegram({ public_token, telegram_bot_token, webhook_base_url }) {
      return fetchJson('/api/telegram/connect', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ public_token, telegram_bot_token, webhook_base_url }),
      });
    },

    getWidgetSnippet({ publicToken }) {
      return `<script src="${window.location.origin}/widget/${publicToken}.js"></script>`;
    },
  };
}

function createGocsService({ mode = 'mock' } = {}) {
  return mode === 'api' ? createApiAdapter() : createMockAdapter();
}

Object.assign(window, { createGocsService, GOCS_SESSION_STORAGE_KEY });
