// pages.jsx
// GO!CS pages: landing, generating, test chat, share, public chat.

const { useState, useEffect, useRef } = React;

function GocsLogo({ size = 22 }) {
  return (
    <span className="gocs-logo" style={{ fontSize: size }}>
      GO<span className="gocs-bang">!</span>CS
    </span>
  );
}

function NavBar({ onTry, showLinks = false }) {
  return (
    <header className="gocs-nav">
      <div className="gocs-nav-left">
        <GocsLogo />
        <span className="gocs-tag">Accurate AI Customer Service</span>
      </div>
      <nav className="gocs-nav-right">
        {showLinks && <a className="gocs-nav-link" href="#">Examples</a>}
        {showLinks && <a className="gocs-nav-link" href="#">Pricing</a>}
        {showLinks && <a className="gocs-nav-link" href="#">Docs</a>}
        <button className="gocs-btn gocs-btn-ghost" onClick={onTry}>Sign in</button>
        <button className="gocs-btn gocs-btn-primary gocs-btn-sm" onClick={onTry}>Try Now</button>
      </nav>
    </header>
  );
}

function Footer() {
  return (
    <footer className="gocs-footer">
      <div className="gocs-footer-inner">
        <GocsLogo size={16} />
        <span>© 2026 GO!CS - Accurate AI customer service, in minutes.</span>
        <div className="gocs-footer-links">
          <a href="#">Privacy</a><a href="#">Terms</a><a href="#">Contact</a>
        </div>
      </div>
    </footer>
  );
}

function LandingPage({ service, onGenerateStart, tone, businessType, setBusinessType, setTone }) {
  const [fileName, setFileName] = useState(null);
  const [fileObj, setFileObj] = useState(null);
  const [pasteMode, setPasteMode] = useState(false);
  const [pasteText, setPasteText] = useState('');
  const [dragOver, setDragOver] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [rules, setRules] = useState({
    onlyUploaded: true,
    noGuess: true,
    askHuman: true,
    autoLang: true,
    shortReplies: true,
  });
  const fileInput = useRef(null);

  const fakeUpload = (file) => {
    if (!file) {
      setFileObj(null);
      setFileName(null);
      return;
    }
    setFileObj(file);
    setFileName(file.name || 'Sakura_Ramen_Info.pdf');
  };
  const ready = Boolean(fileName || (pasteMode && pasteText.trim().length > 30));

  const formatApiError = (res) => {
    const message = res?.error?.message || 'Unable to create generation session. Please try again.';
    const code = res?.error?.code ? ` [${res.error.code}]` : '';
    const details = Array.isArray(res?.error?.details) && res.error.details.length
      ? ` ${res.error.details.map((d) => `${d.field}: ${d.issue}`).join(', ')}`
      : '';
    return `${message}${code}${details}`;
  };

  const handleGenerate = async () => {
    if (!ready || submitting) return;
    setSubmitting(true);
    setError('');
    try {
      const res = await service.generateBot({
        file: fileObj,
        fileName,
        pasted_text: pasteText,
        business_type: businessType,
        tone,
        settings: rules,
      });
      if (!res.ok) {
        setError(formatApiError(res));
        setSubmitting(false);
        return;
      }
      onGenerateStart(res.data.session);
    } catch (e) {
      setError(e.message || 'Unable to create generation session. Please try again.');
      setSubmitting(false);
    }
  };

  return (
    <div className="gocs-page">
      <main className="gocs-main">
        <section className="gocs-hero">
          <div className="gocs-eyebrow"><span className="gocs-dot" /> No hallucinations · Only your information</div>
          <h1 className="gocs-h1">
            Upload your company info.<br />
            <span className="gocs-h1-accent">Generate AI customer service</span> instantly.
          </h1>
          <p className="gocs-sub">
            GO!CS turns your FAQ, price list, menu, SOP, or product catalog into a
            customer service AI that only answers from your real information.
          </p>
        </section>

        <section className="gocs-upload-wrap">
          <div className="gocs-upload-card">
            {!pasteMode ? (
              <div
                className={`gocs-drop ${dragOver ? 'is-over' : ''} ${fileName ? 'is-filled' : ''}`}
                onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
                onDragLeave={() => setDragOver(false)}
                onDrop={(e) => { e.preventDefault(); setDragOver(false); fakeUpload(e.dataTransfer.files?.[0] || null); }}
                onClick={() => !fileName && fileInput.current?.click()}
              >
                <input ref={fileInput} type="file" hidden onChange={(e) => fakeUpload(e.target.files?.[0] || null)} />
                {fileName ? (
                  <div className="gocs-file">
                    <div className="gocs-file-icon">
                      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" /><path d="M14 2v6h6" /></svg>
                    </div>
                    <div className="gocs-file-meta">
                      <div className="gocs-file-name">{fileName}</div>
                      <div className="gocs-file-sub">Ready for generation</div>
                    </div>
                    <button className="gocs-file-x" onClick={(e) => { e.stopPropagation(); setFileName(null); setFileObj(null); }} aria-label="Remove">
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><path d="M18 6L6 18M6 6l12 12" /></svg>
                    </button>
                  </div>
                ) : (
                  <>
                    <div className="gocs-drop-icon" aria-hidden>
                      <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" /><polyline points="17 8 12 3 7 8" /><line x1="12" y1="3" x2="12" y2="15" /></svg>
                    </div>
                    <div className="gocs-drop-title">Drop your company document here</div>
                    <div className="gocs-drop-sub">PDF, DOCX, TXT · FAQ, price list, menu, SOP, policy</div>
                    <div className="gocs-drop-actions">
                      <button className="gocs-btn gocs-btn-primary" onClick={(e) => { e.stopPropagation(); fileInput.current?.click(); }}>Choose file</button>
                      <button className="gocs-btn gocs-btn-ghost" onClick={(e) => { e.stopPropagation(); setPasteMode(true); }}>Paste text instead</button>
                    </div>
                  </>
                )}
              </div>
            ) : (
              <div className="gocs-paste">
                <div className="gocs-paste-head">
                  <span>Paste your company information</span>
                  <button className="gocs-link" onClick={() => setPasteMode(false)}>← Use a file instead</button>
                </div>
                <textarea className="gocs-textarea" placeholder="Paste your FAQ, menu, price list, business hours, return policy..." value={pasteText} onChange={(e) => setPasteText(e.target.value)} />
                <div className="gocs-paste-foot">{pasteText.length} characters</div>
              </div>
            )}

            <div className="gocs-rules">
              <div className="gocs-rules-title">AI answer rules</div>
              <div className="gocs-rules-grid">
                {[
                  ['onlyUploaded', 'Only answer using my uploaded information'],
                  ['noGuess', "Don't guess when information is missing"],
                  ['askHuman', 'Ask for human support when unsure'],
                  ['autoLang', "Reply in the customer's language"],
                  ['shortReplies', 'Keep replies short and customer-friendly'],
                ].map(([k, label]) => (
                  <label key={k} className="gocs-check">
                    <input type="checkbox" checked={rules[k]} onChange={(e) => setRules({ ...rules, [k]: e.target.checked })} />
                    <span className="gocs-check-box" aria-hidden><svg viewBox="0 0 16 16" width="11" height="11"><path d="M3 8l3 3 7-7" stroke="white" strokeWidth="2.5" fill="none" strokeLinecap="round" strokeLinejoin="round" /></svg></span>
                    <span>{label}</span>
                  </label>
                ))}
              </div>
            </div>

            <div className="gocs-options">
              <div className="gocs-opt">
                <label>Business type</label>
                <div className="gocs-select-wrap">
                  <select value={businessType} onChange={(e) => setBusinessType(e.target.value)}>
                    {['Auto detect', 'Restaurant', 'Ecommerce', 'Legal', 'Education', 'Services', 'Other'].map((o) => <option key={o}>{o}</option>)}
                  </select>
                  <svg viewBox="0 0 24 24" width="14" height="14" stroke="currentColor" strokeWidth="2" fill="none"><polyline points="6 9 12 15 18 9" /></svg>
                </div>
              </div>
              <div className="gocs-opt">
                <label>Tone</label>
                <div className="gocs-segment">
                  {['Professional', 'Friendly', 'Luxury', 'Casual'].map((option) => <button key={option} className={`gocs-seg-btn ${tone === option ? 'is-active' : ''}`} onClick={() => setTone(option)}>{option}</button>)}
                </div>
              </div>
            </div>

            <button className="gocs-btn gocs-btn-primary gocs-btn-lg gocs-cta" disabled={!ready || submitting} onClick={handleGenerate}>
              {submitting ? 'Creating session...' : 'Generate my AI customer service'}
            </button>
            {error && <div className="gocs-inline-error">{error}</div>}
            <div className="gocs-trust">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" /></svg>
              Your AI will only answer based on the information you provide.
            </div>
          </div>
        </section>
      </main>
      <Footer />
    </div>
  );
}

function GeneratingPage({ session, onDone }) {
  const STEPS = [
    'Reading your company information',
    'Understanding your business',
    'Building your AI knowledge base',
    'Preparing customer replies',
    'Setting up your AI assistant',
  ];

  const [step, setStep] = useState(0);
  const [failed, setFailed] = useState(false);
  const injectFailure = window.GOCS_DEMO_GENERATING_FAILURE === true;

  useEffect(() => {
    if (failed) return;
    if (step >= STEPS.length) {
      const t = setTimeout(onDone, 500);
      return () => clearTimeout(t);
    }
    const t = setTimeout(() => {
      if (injectFailure && step === 1) {
        setFailed(true);
        return;
      }
      setStep(step + 1);
    }, 750);
    return () => clearTimeout(t);
  }, [step, failed, injectFailure]);

  const retry = () => {
    setFailed(false);
    setStep(0);
  };

  const pct = Math.min(100, (step / STEPS.length) * 100);

  return (
    <div className="gocs-page gocs-page-center">
      <div className="gocs-gen-card">
        <div className="gocs-gen-spin">
          <svg width="44" height="44" viewBox="0 0 50 50">
            <circle cx="25" cy="25" r="20" stroke="rgba(0,0,0,0.08)" strokeWidth="3" fill="none" />
            <circle cx="25" cy="25" r="20" stroke="var(--gocs-accent)" strokeWidth="3" fill="none" strokeLinecap="round" strokeDasharray="125.6" strokeDashoffset={125.6 - (pct / 100) * 125.6} style={{ transform: 'rotate(-90deg)', transformOrigin: 'center', transition: 'stroke-dashoffset 0.4s ease' }} />
          </svg>
        </div>
        <h2 className="gocs-gen-title">Creating your AI customer service...</h2>
        <p className="gocs-gen-sub">This usually takes less than a minute.</p>
        <ul className="gocs-gen-steps">
          {STEPS.map((s, i) => (
            <li key={s} className={i < step ? 'is-done' : i === step && !failed ? 'is-active' : ''}>
              <span className="gocs-gen-icon">
                {i < step ? <svg width="14" height="14" viewBox="0 0 16 16"><path d="M3 8l3 3 7-7" stroke="currentColor" strokeWidth="2.5" fill="none" strokeLinecap="round" strokeLinejoin="round" /></svg> : i === step && !failed ? <span className="gocs-gen-pulse" /> : <span className="gocs-gen-pip" />}
              </span>
              <span>{s}</span>
            </li>
          ))}
        </ul>
        <div className="gocs-gen-bar"><div style={{ width: `${pct}%` }} /></div>
        {failed && (
          <div className="gocs-inline-error gocs-inline-error-center">
            File processing failed once. Please retry.
            <button className="gocs-btn gocs-btn-ghost gocs-btn-sm" onClick={retry}>Retry</button>
          </div>
        )}
        <div className="gocs-gen-foot">
          <GocsLogo size={13} />
          <span>{session?.sourceName || 'Company_Info.pdf'}</span>
        </div>
      </div>
    </div>
  );
}

function ConfidenceBadge({ level }) {
  if (!level) return null;
  const map = {
    high: { label: 'High confidence', cls: 'high' },
    medium: { label: 'Medium confidence', cls: 'med' },
    low: { label: 'Not enough information', cls: 'low' },
  };
  const c = map[level];
  return <span className={`gocs-badge gocs-badge-${c.cls}`}><span className="gocs-badge-dot" />{c.label}</span>;
}

function scoreToLevel(score, status) {
  if (status === 'fallback') return 'low';
  if (score >= 0.8) return 'high';
  if (score >= 0.6) return 'medium';
  return 'low';
}

function TestChatPage({ publicToken, service, onShare, onAddInfo }) {
  const [messages, setMessages] = useState([window.SAKURA_GREETING]);
  const [input, setInput] = useState('');
  const [thinking, setThinking] = useState(false);
  const [feedback, setFeedback] = useState({});
  const scrollRef = useRef(null);

  const lastConfidence = [...messages].reverse().find((m) => m.role === 'ai' && m.confidence)?.confidence || null;

  useEffect(() => {
    if (scrollRef.current) scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
  }, [messages, thinking]);

  const ask = async (text) => {
    const prompt = (text || '').trim();
    if (!prompt || thinking) return;
    setMessages((m) => [...m, { role: 'user', text: prompt }]);
    setInput('');
    setThinking(true);
    try {
      const result = await service.askBot({
        publicToken,
        message: prompt,
        channel: 'web',
      });
      if (!result.ok) {
        setMessages((m) => [...m, {
          role: 'ai',
          text: [result.error?.message || 'Request failed. Please try again.'],
          confidence: 'low',
          source: null,
        }]);
        return;
      }
      const payload = result.data;
      setMessages((m) => [...m, {
        role: 'ai',
        text: Array.isArray(payload.answer) ? payload.answer : [payload.answer],
        confidence: scoreToLevel(payload.confidence, payload.status),
        source: payload.source_text,
      }]);
    } finally {
      setThinking(false);
    }
  };

  const remainingChips = (window.SAKURA_QA || []).slice(0, 5).filter((qa) => !messages.some((m) => m.role === 'user' && m.text === qa.q));

  return (
    <div className="gocs-page gocs-page-chat">
      <div className="gocs-chat-head">
        <div>
          <div className="gocs-chat-eyebrow"><span className="gocs-pulse-dot" /> AI is ready · trained on uploaded information</div>
          <h1 className="gocs-chat-h1">Your AI customer service is ready.</h1>
          <p className="gocs-chat-sub">Ask a few questions to see how it responds. It only answers based on available information.</p>
        </div>
        <div className="gocs-chat-actions">
          <button className="gocs-btn gocs-btn-ghost" onClick={onAddInfo}>Add more information</button>
          <button className="gocs-btn gocs-btn-primary" onClick={onShare}>Share AI</button>
        </div>
      </div>

      <div className="gocs-chat-grid">
        <div className="gocs-chat-card">
          <div className="gocs-chat-card-head">
            <div className="gocs-chat-avatar">SR</div>
            <div className="gocs-chat-id">
              <div className="gocs-chat-id-name">Sakura Ramen Assistant</div>
              <div className="gocs-chat-id-meta"><span className="gocs-online" /> Online · usually replies instantly</div>
            </div>
            <div className="gocs-chat-id-tag">Preview</div>
          </div>

          <div className="gocs-chat-stream" ref={scrollRef}>
            {messages.map((m, i) => (
              m.role === 'ai' ? (
                <div key={i} className="gocs-msg gocs-msg-ai">
                  <div className="gocs-msg-avatar">SR</div>
                  <div className="gocs-msg-body">
                    <div className="gocs-msg-bubble">
                      {(Array.isArray(m.text) ? m.text : [m.text]).map((line, j) => <div key={j} className="gocs-msg-line">{line}</div>)}
                    </div>
                    {m.confidence && (
                      <div className="gocs-msg-foot">
                        <ConfidenceBadge level={m.confidence} />
                        {m.source && <span className="gocs-msg-source">{m.source}</span>}
                        <div className="gocs-msg-fb">
                          <button className={feedback[i] === 'good' ? 'is-on' : ''} onClick={() => setFeedback({ ...feedback, [i]: 'good' })} title="Correct">👍</button>
                          <button className={feedback[i] === 'bad' ? 'is-on' : ''} onClick={() => setFeedback({ ...feedback, [i]: 'bad' })} title="Not correct">👎</button>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              ) : (
                <div key={i} className="gocs-msg gocs-msg-user"><div className="gocs-msg-bubble">{m.text}</div></div>
              )
            ))}
            {thinking && <div className="gocs-msg gocs-msg-ai"><div className="gocs-msg-avatar">SR</div><div className="gocs-msg-bubble gocs-msg-thinking"><span /><span /><span /></div></div>}
          </div>

          {remainingChips.length > 0 && (
            <div className="gocs-chips">
              <span className="gocs-chips-label">Try asking:</span>
              {remainingChips.map((qa) => <button key={qa.q} className="gocs-chip" onClick={() => ask(qa.q)}>{qa.q}</button>)}
            </div>
          )}

          <form className="gocs-chat-input" onSubmit={(e) => { e.preventDefault(); ask(input); }}>
            <input placeholder="Ask a customer question..." value={input} onChange={(e) => setInput(e.target.value)} />
            <button className="gocs-btn gocs-btn-primary gocs-btn-icon" type="submit" disabled={!input.trim()}>→</button>
          </form>
        </div>

        <aside className="gocs-side">
          <div className="gocs-side-card">
            <div className="gocs-side-h">AI answer status</div>
            <div className="gocs-side-now">
              {lastConfidence ? <ConfidenceBadge level={lastConfidence} /> : <span className="gocs-side-idle">Waiting for first question...</span>}
            </div>
            <div className="gocs-side-rule">This AI only answers from your uploaded information.</div>
          </div>

          <div className="gocs-side-card gocs-side-stats">
            <div className="gocs-side-h">Session</div>
            <div className="gocs-side-stats-grid">
              <div><div className="gocs-stat-n">{messages.filter((m) => m.role === 'user').length}</div><div className="gocs-stat-l">Questions</div></div>
              <div><div className="gocs-stat-n">{messages.filter((m) => m.confidence === 'high').length}</div><div className="gocs-stat-l">Confident</div></div>
              <div><div className="gocs-stat-n">{messages.filter((m) => m.confidence === 'low').length}</div><div className="gocs-stat-l">Not enough</div></div>
            </div>
          </div>

          <div className="gocs-side-cta">
            <div className="gocs-side-cta-t">Looks good?</div>
            <div className="gocs-side-cta-d">Share a public link or embed it on your site.</div>
            <button className="gocs-btn gocs-btn-primary gocs-btn-block" onClick={onShare}>Go live →</button>
          </div>
        </aside>
      </div>
    </div>
  );
}

function ShareCard({ icon, title, sub, children, recommended, soon }) {
  return (
    <div className={`gocs-share-card ${recommended ? 'is-rec' : ''} ${soon ? 'is-soon' : ''}`}>
      {recommended && <span className="gocs-rec-tag">Recommended</span>}
      {soon && <span className="gocs-soon-tag">Coming soon</span>}
      <div className="gocs-share-icon">{icon}</div>
      <div className="gocs-share-title">{title}</div>
      <div className="gocs-share-sub">{sub}</div>
      <div className="gocs-share-body">{children}</div>
    </div>
  );
}

async function copyText(value) {
  try {
    if (navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(value);
      return true;
    }
  } catch (e) {}
  try {
    const ta = document.createElement('textarea');
    ta.value = value;
    document.body.appendChild(ta);
    ta.select();
    document.execCommand('copy');
    document.body.removeChild(ta);
    return true;
  } catch (e) {
    return false;
  }
}

function CopyField({ value, label = 'Copy' }) {
  const [copied, setCopied] = useState(false);
  const onCopy = async () => {
    const ok = await copyText(value);
    setCopied(ok);
    setTimeout(() => setCopied(false), 1200);
  };

  return (
    <div className="gocs-copy">
      <code>{value}</code>
      <button className="gocs-btn gocs-btn-primary gocs-btn-sm" onClick={onCopy}>{copied ? 'Copied' : label}</button>
    </div>
  );
}

function SharePage({ publicToken, service, onBack, onOpenPublic }) {
  const [telegramToken, setTelegramToken] = useState('');
  const [telegramState, setTelegramState] = useState({ type: '', msg: '' });
  const widgetSnippet = service.getWidgetSnippet({ publicToken });

  const connectTelegram = async () => {
    const res = await service.connectTelegram({
      public_token: publicToken,
      telegram_bot_token: telegramToken.trim(),
      webhook_base_url: 'https://gocs.ai',
    });
    if (!res.ok) {
      setTelegramState({ type: 'error', msg: res.error?.message || 'Unable to connect Telegram token.' });
      return;
    }
    setTelegramState({ type: 'ok', msg: 'Telegram placeholder connected. Real integration can be added later.' });
  };

  return (
    <div className="gocs-page">
      <div className="gocs-share-head">
        <button className="gocs-link" onClick={onBack}>← Back to test chat</button>
        <div className="gocs-share-banner">
          <div className="gocs-share-banner-emoji">✓</div>
          <div>
            <div className="gocs-share-banner-t">Your AI customer service is ready to use.</div>
            <div className="gocs-share-banner-d">Pick how you want customers to reach it.</div>
          </div>
        </div>
      </div>

      <div className="gocs-share-grid">
        <ShareCard recommended icon="🔗" title="Share a public link" sub="Send this link to your team or customers to test the AI.">
          <CopyField value={`https://gocs.ai/chat/${publicToken}`} label="Copy link" />
          <button className="gocs-btn gocs-btn-ghost gocs-btn-sm" onClick={onOpenPublic}>Open public page</button>
        </ShareCard>

        <ShareCard recommended icon="</>" title="Add to your website" sub="Paste this snippet before </body> on any page.">
          <CopyField value={widgetSnippet} label="Copy code" />
        </ShareCard>

        <ShareCard icon="✈" title="Connect Telegram" sub="Customers chat with your AI inside Telegram.">
          <div className="gocs-input-row">
            <input placeholder="Paste your Telegram bot token" value={telegramToken} onChange={(e) => setTelegramToken(e.target.value)} />
            <button className="gocs-btn gocs-btn-primary gocs-btn-sm" onClick={connectTelegram}>Connect</button>
          </div>
          <div className="gocs-paste-foot">Demo placeholder only. Real Telegram webhook is not connected in this prototype.</div>
          {telegramState.msg && <div className={`gocs-inline-${telegramState.type === 'ok' ? 'success' : 'error'}`}>{telegramState.msg}</div>}
        </ShareCard>

        <ShareCard soon icon="💬" title="WhatsApp" sub="Reach customers on WhatsApp Business.">
          <button className="gocs-btn gocs-btn-ghost gocs-btn-block">Request setup</button>
        </ShareCard>

        <ShareCard soon icon="💬" title="Facebook Messenger" sub="Talk to customers from your Facebook page.">
          <button className="gocs-btn gocs-btn-ghost gocs-btn-block">Request setup</button>
        </ShareCard>
      </div>

      <Footer />
    </div>
  );
}

function PublicChatPage({ publicToken, service, onBackHome }) {
  const [messages, setMessages] = useState([{ role: 'ai', text: 'Hi! Ask me anything about menu, hours, reservation, or location.' }]);
  const [input, setInput] = useState('');
  const [thinking, setThinking] = useState(false);
  const streamRef = useRef(null);

  useEffect(() => {
    if (streamRef.current) streamRef.current.scrollTop = streamRef.current.scrollHeight;
  }, [messages, thinking]);

  const ask = async (text) => {
    const prompt = text.trim();
    if (!prompt || thinking) return;
    setMessages((m) => [...m, { role: 'user', text: prompt }]);
    setInput('');
    setThinking(true);
    const res = await service.askBot({
      publicToken,
      message: prompt,
      channel: 'web',
    });
    const answer = res.ok ? res.data.answer : (res.error?.message || 'Request failed.');
    setMessages((m) => [...m, { role: 'ai', text: Array.isArray(answer) ? answer.join(' ') : answer }]);
    setThinking(false);
  };

  return (
    <div className="gocs-page gocs-page-chat">
      <div className="gocs-chat-head">
        <div>
          <h1 className="gocs-chat-h1">Sakura Ramen AI Assistant</h1>
          <p className="gocs-chat-sub">This public assistant answers from uploaded business information only.</p>
        </div>
        <button className="gocs-btn gocs-btn-ghost" onClick={onBackHome}>Back to GO!CS</button>
      </div>

      <div className="gocs-chat-card" style={{ maxWidth: 720, margin: '0 auto', width: '100%' }}>
        <div className="gocs-chat-stream" ref={streamRef}>
          {messages.map((m, idx) => (
            <div key={idx} className={`gocs-msg ${m.role === 'user' ? 'gocs-msg-user' : 'gocs-msg-ai'}`}>
              <div className="gocs-msg-bubble">{m.text}</div>
            </div>
          ))}
          {thinking && <div className="gocs-msg gocs-msg-ai"><div className="gocs-msg-bubble gocs-msg-thinking"><span /><span /><span /></div></div>}
        </div>
        <form className="gocs-chat-input" onSubmit={(e) => { e.preventDefault(); ask(input); }}>
          <input placeholder="Ask a question..." value={input} onChange={(e) => setInput(e.target.value)} />
          <button className="gocs-btn gocs-btn-primary gocs-btn-icon" type="submit" disabled={!input.trim()}>→</button>
        </form>
      </div>
    </div>
  );
}

Object.assign(window, { LandingPage, GeneratingPage, TestChatPage, SharePage, PublicChatPage, NavBar });
