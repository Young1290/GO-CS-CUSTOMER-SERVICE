// app.jsx - GO!CS prototype shell with route state + mock service.

const { useState, useEffect } = React;

const ACCENTS = {
  Emerald: { accent: '#10B981', ink: '#064E3B', tint: '#ECFDF5' },
  Indigo: { accent: '#4F46E5', ink: '#312E81', tint: '#EEF2FF' },
  Sky: { accent: '#0EA5E9', ink: '#0C4A6E', tint: '#F0F9FF' },
  Orange: { accent: '#F97316', ink: '#7C2D12', tint: '#FFF7ED' },
  Ink: { accent: '#0A0B0D', ink: '#0A0B0D', tint: '#F2F4F7' },
};

const TWEAK_DEFAULTS = /*EDITMODE-BEGIN*/{
  accent: 'Emerald',
  tone: 'Friendly',
  businessType: 'Restaurant',
  showWidget: true,
}/*EDITMODE-END*/;

const DEFAULT_SESSION = {
  sessionId: 'session-demo-001',
  publicToken: 'sakura-ramen-9k2x',
  businessType: 'auto',
  tone: 'friendly',
  sourceName: 'Sakura_Ramen_Info.pdf',
};

const SESSION_STORAGE_KEY = window.GOCS_SESSION_STORAGE_KEY || 'gocs_demo_session';

function getStoredSession() {
  try {
    return JSON.parse(localStorage.getItem(SESSION_STORAGE_KEY)) || DEFAULT_SESSION;
  } catch (e) {
    return DEFAULT_SESSION;
  }
}

function parseRoute(pathname) {
  const path = pathname || '/';
  if (path === '/') return { page: 'landing', params: {} };
  if (path.startsWith('/generating/')) return { page: 'generating', params: { sessionId: path.split('/')[2] || '' } };
  if (path.startsWith('/bot/') && path.endsWith('/test')) return { page: 'chat', params: { publicToken: path.split('/')[2] || '' } };
  if (path.startsWith('/bot/') && path.endsWith('/share')) return { page: 'share', params: { publicToken: path.split('/')[2] || '' } };
  if (path.startsWith('/chat/')) return { page: 'publicChat', params: { publicToken: path.split('/')[2] || '' } };
  return { page: 'landing', params: {} };
}

function App() {
  const service = React.useMemo(() => window.createGocsService({ mode: 'api' }), []);
  const [t, setTweak] = useTweaks(TWEAK_DEFAULTS);
  const initial = parseRoute(window.location.pathname);
  const [page, setPage] = useState(initial.page);
  const [routeParams, setRouteParams] = useState(initial.params);
  const [session, setSession] = useState(getStoredSession());

  useEffect(() => {
    const a = ACCENTS[t.accent] || ACCENTS.Emerald;
    const root = document.querySelector('.gocs-root');
    if (root) {
      root.style.setProperty('--gocs-accent', a.accent);
      root.style.setProperty('--gocs-accent-ink', a.ink);
      root.style.setProperty('--gocs-accent-tint', a.tint);
    }
  }, [t.accent]);

  useEffect(() => {
    const onPop = () => {
      const parsed = parseRoute(window.location.pathname);
      setPage(parsed.page);
      setRouteParams(parsed.params);
    };
    window.addEventListener('popstate', onPop);
    return () => window.removeEventListener('popstate', onPop);
  }, []);

  const navigate = (toPage, params = {}) => {
    let path = '/';
    const token = params.publicToken || session.publicToken;
    const sessionId = params.sessionId || session.sessionId;
    if (toPage === 'landing') path = '/';
    if (toPage === 'generating') path = `/generating/${sessionId}`;
    if (toPage === 'chat') path = `/bot/${token}/test`;
    if (toPage === 'share') path = `/bot/${token}/share`;
    if (toPage === 'publicChat') path = `/chat/${token}`;
    window.history.pushState({}, '', path);
    setPage(toPage);
    setRouteParams(params);
  };

  const url = window.location.pathname.replace(/^\//, '') || 'gocs.ai';

  const tabTitle = {
    landing: 'GO!CS - Accurate AI Customer Service',
    generating: 'Creating your AI · GO!CS',
    chat: 'Test chat · GO!CS',
    share: 'Share your AI · GO!CS',
    publicChat: 'Public Chat · GO!CS',
  }[page] || 'GO!CS';

  const [narrow, setNarrow] = useState(window.innerWidth < 900);
  useEffect(() => {
    const onR = () => setNarrow(window.innerWidth < 900);
    window.addEventListener('resize', onR);
    return () => window.removeEventListener('resize', onR);
  }, []);

  const PageEl = (
    <div className="gocs-root" key={page}>
      <div className="gocs-page-enter" style={{ display: 'flex', flexDirection: 'column', minHeight: '100%' }}>
        {page === 'landing' && (
          <>
            <NavBar onTry={() => document.querySelector('.gocs-upload-card')?.scrollIntoView({ behavior: 'smooth', block: 'start' })} />
            <LandingPage
              service={service}
              onGenerateStart={(nextSession) => {
                setSession(nextSession);
                setTweak('tone', nextSession.tone.charAt(0).toUpperCase() + nextSession.tone.slice(1));
                navigate('generating', { sessionId: nextSession.sessionId, publicToken: nextSession.publicToken });
              }}
              tone={t.tone}
              setTone={(v) => setTweak('tone', v)}
              businessType={t.businessType}
              setBusinessType={(v) => setTweak('businessType', v)}
            />
          </>
        )}

        {page === 'generating' && (
          <GeneratingPage
            session={session}
            service={service}
            onDone={() => navigate('chat', { publicToken: session.publicToken })}
          />
        )}

        {page === 'chat' && (
          <>
            <NavBar onTry={() => navigate('landing')} />
            <TestChatPage
              publicToken={routeParams.publicToken || session.publicToken}
              service={service}
              onShare={() => navigate('share', { publicToken: session.publicToken })}
              onAddInfo={() => navigate('landing')}
            />
          </>
        )}

        {page === 'share' && (
          <>
            <NavBar onTry={() => navigate('landing')} />
            <SharePage
              publicToken={routeParams.publicToken || session.publicToken}
              service={service}
              onBack={() => navigate('chat', { publicToken: session.publicToken })}
              onOpenPublic={() => navigate('publicChat', { publicToken: session.publicToken })}
            />
          </>
        )}

        {page === 'publicChat' && (
          <PublicChatPage
            publicToken={routeParams.publicToken || session.publicToken}
            service={service}
            onBackHome={() => navigate('landing')}
          />
        )}
      </div>
    </div>
  );

  const stageStyle = {
    minHeight: '100vh',
    width: '100%',
    background: narrow ? '#fff' : 'radial-gradient(ellipse at top, #f1f5f9 0%, #e2e8f0 100%)',
    display: 'flex', alignItems: narrow ? 'stretch' : 'center', justifyContent: 'center',
    padding: narrow ? 0 : 28,
  };

  return (
    <div style={stageStyle}>
      {narrow ? (
        <div style={{ width: '100%', minHeight: '100vh', background: 'white', overflow: 'auto' }}>
          {PageEl}
        </div>
      ) : (
        <ChromeWindow
          tabs={[{ title: tabTitle }]}
          url={url || 'gocs.ai'}
          width={Math.min(1280, window.innerWidth - 56)}
          height={Math.min(820, window.innerHeight - 56)}
        >
          {PageEl}
        </ChromeWindow>
      )}

      <TweaksPanel>
        <TweakSection label="Brand" />
        <TweakColor
          label="Accent"
          value={ACCENTS[t.accent]?.accent}
          options={Object.values(ACCENTS).map((a) => a.accent)}
          onChange={(hex) => {
            const name = Object.keys(ACCENTS).find((k) => ACCENTS[k].accent === hex);
            if (name) setTweak('accent', name);
          }}
        />
        <TweakSection label="Voice" />
        <TweakRadio label="Tone" value={t.tone} options={['Professional', 'Friendly', 'Luxury']} onChange={(v) => setTweak('tone', v)} />
        <TweakSelect label="Business" value={t.businessType} options={['Restaurant', 'Ecommerce', 'Legal', 'Education', 'Services']} onChange={(v) => setTweak('businessType', v)} />
        <TweakSection label="Flow" />
        <TweakRadio
          label="Page"
          value={page}
          options={['landing', 'generating', 'chat', 'share', 'publicChat']}
          onChange={(v) => navigate(v, { publicToken: session.publicToken, sessionId: session.sessionId })}
        />
      </TweaksPanel>
    </div>
  );
}

ReactDOM.createRoot(document.getElementById('root')).render(<App />);
