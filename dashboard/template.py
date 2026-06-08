HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>VocalLabs · Outreach Pipeline</title>
<style>
/* ── Reset & base ─────────────────────────────────────────────────────────── */
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
:root{
  --bg:        #13151a;
  --bg2:       #1a1d24;
  --bg3:       #21252f;
  --border:    #2a2f3d;
  --border2:   #343a4a;
  --text:      #d4d8e8;
  --text2:     #8892aa;
  --text3:     #5a6278;
  --accent:    #6c8ef5;
  --accent2:   #4f6fe0;
  --green:     #4ade80;
  --green2:    #16a34a;
  --yellow:    #facc15;
  --yellow2:   #a16207;
  --red:       #f87171;
  --red2:      #b91c1c;
  --purple:    #a78bfa;
  --cyan:      #67e8f9;
  --orange:    #fb923c;
  --glow:      rgba(108,142,245,0.15);
  --radius:    10px;
  --radius-sm: 6px;
  --font:      'Inter',system-ui,-apple-system,sans-serif;
  --font-mono: 'JetBrains Mono','Fira Code','Cascadia Code',monospace;
}
html{height:100%;scroll-behavior:smooth}
body{
  font-family:var(--font);
  background:var(--bg);
  color:var(--text);
  min-height:100vh;
  line-height:1.6;
  font-size:14px;
  overflow-x:hidden;
}

/* ── Scrollbar ────────────────────────────────────────────────────────────── */
::-webkit-scrollbar{width:6px;height:6px}
::-webkit-scrollbar-track{background:var(--bg2)}
::-webkit-scrollbar-thumb{background:var(--border2);border-radius:3px}
::-webkit-scrollbar-thumb:hover{background:var(--accent)}

/* ── Layout ───────────────────────────────────────────────────────────────── */
.app{display:grid;grid-template-columns:260px 1fr;grid-template-rows:60px 1fr;min-height:100vh}
.header{
  grid-column:1/-1;
  display:flex;align-items:center;gap:12px;padding:0 24px;
  background:var(--bg2);border-bottom:1px solid var(--border);
  position:sticky;top:0;z-index:100;
}
.sidebar{
  background:var(--bg2);border-right:1px solid var(--border);
  padding:20px 0;overflow-y:auto;
}
.main{padding:24px;overflow-y:auto;display:flex;flex-direction:column;gap:20px}

/* ── Header ──────────────────────────────────────────────────────────────── */
.logo{
  font-size:18px;font-weight:700;color:var(--accent);
  display:flex;align-items:center;gap:8px;letter-spacing:-0.3px;
}
.logo-dot{color:var(--green)}
.header-badge{
  margin-left:auto;display:flex;align-items:center;gap:8px;
}
.status-dot{
  width:8px;height:8px;border-radius:50%;
  background:var(--text3);transition:background .3s;
}
.status-dot.running{background:var(--green);box-shadow:0 0 8px var(--green);animation:pulse-dot 1.5s infinite}
.status-dot.done{background:var(--accent)}
.status-dot.error{background:var(--red)}
@keyframes pulse-dot{0%,100%{opacity:1}50%{opacity:.4}}
.status-label{font-size:12px;color:var(--text2)}

/* ── Input card ───────────────────────────────────────────────────────────── */
.input-card{
  background:var(--bg2);border:1px solid var(--border);
  border-radius:var(--radius);padding:20px 24px;
}
.input-card h2{font-size:13px;font-weight:600;color:var(--text2);
  text-transform:uppercase;letter-spacing:.8px;margin-bottom:16px}
.input-row{display:flex;gap:10px;align-items:center;flex-wrap:wrap}
.domain-input{
  flex:1;min-width:200px;
  background:var(--bg3);border:1px solid var(--border2);
  color:var(--text);border-radius:var(--radius-sm);
  padding:9px 14px;font-family:var(--font-mono);font-size:14px;
  outline:none;transition:border .2s,box-shadow .2s;
}
.domain-input:focus{border-color:var(--accent);box-shadow:0 0 0 3px var(--glow)}
.domain-input::placeholder{color:var(--text3)}
.count-input{
  width:70px;
  background:var(--bg3);border:1px solid var(--border2);
  color:var(--text);border-radius:var(--radius-sm);
  padding:9px 10px;font-size:14px;text-align:center;
  outline:none;transition:border .2s;
}
.count-input:focus{border-color:var(--accent)}
.count-label{font-size:12px;color:var(--text3);white-space:nowrap}
.btn{
  display:inline-flex;align-items:center;gap:7px;
  padding:9px 20px;border-radius:var(--radius-sm);
  border:none;cursor:pointer;font-size:14px;font-weight:600;
  transition:all .15s;white-space:nowrap;
}
.btn-primary{background:var(--accent);color:#fff}
.btn-primary:hover:not(:disabled){background:var(--accent2);transform:translateY(-1px);box-shadow:0 4px 16px var(--glow)}
.btn-primary:active{transform:translateY(0)}
.btn-primary:disabled{opacity:.4;cursor:not-allowed;transform:none}
.btn-danger{background:var(--red2);color:#fff}
.btn-danger:hover{background:var(--red)}
.btn-success{background:var(--green2);color:#fff}
.btn-success:hover{background:var(--green)}
.btn-ghost{background:transparent;border:1px solid var(--border2);color:var(--text2)}
.btn-ghost:hover{border-color:var(--accent);color:var(--accent)}
.btn-sm{padding:6px 14px;font-size:12px}

/* ── Stage pipeline ───────────────────────────────────────────────────────── */
.stages-bar{
  background:var(--bg2);border:1px solid var(--border);
  border-radius:var(--radius);padding:20px 24px;
}
.stages-bar h2{font-size:13px;font-weight:600;color:var(--text2);
  text-transform:uppercase;letter-spacing:.8px;margin-bottom:18px}
.stages-track{display:flex;align-items:center;gap:0;position:relative}
.stage-item{
  flex:1;display:flex;flex-direction:column;align-items:center;gap:8px;
  position:relative;
}
.stage-item:not(:last-child)::after{
  content:'';position:absolute;top:19px;left:50%;width:100%;height:2px;
  background:var(--border2);z-index:0;transition:background .5s;
}
.stage-item.done:not(:last-child)::after{background:var(--green)}
.stage-item.active:not(:last-child)::after{
  background:linear-gradient(90deg,var(--accent),var(--border2));
  animation:shimmer 1.5s infinite;
}
@keyframes shimmer{0%{opacity:.7}50%{opacity:1}100%{opacity:.7}}
.stage-circle{
  width:38px;height:38px;border-radius:50%;
  background:var(--bg3);border:2px solid var(--border2);
  display:flex;align-items:center;justify-content:center;
  font-size:16px;z-index:1;position:relative;
  transition:all .4s cubic-bezier(.34,1.56,.64,1);
}
.stage-item.active .stage-circle{
  border-color:var(--accent);
  box-shadow:0 0 0 6px rgba(108,142,245,.15),0 0 20px rgba(108,142,245,.3);
  animation:bounce-in .4s cubic-bezier(.34,1.56,.64,1);
}
.stage-item.done .stage-circle{
  background:var(--green2);border-color:var(--green);
  box-shadow:0 0 12px rgba(74,222,128,.3);
}
.stage-item.error .stage-circle{border-color:var(--red);box-shadow:0 0 12px rgba(248,113,113,.3)}
.stage-item.skipped .stage-circle{opacity:.4}
.stage-item.cancelled .stage-circle{border-color:var(--yellow)}
@keyframes bounce-in{0%{transform:scale(.7)}100%{transform:scale(1)}}
.stage-label{font-size:11px;font-weight:600;color:var(--text2);text-align:center;letter-spacing:.3px}
.stage-sublabel{font-size:10px;color:var(--text3);text-align:center}
.stage-count{
  font-size:11px;font-weight:700;color:var(--green);
  background:rgba(74,222,128,.08);border:1px solid rgba(74,222,128,.2);
  padding:1px 7px;border-radius:10px;
}

/* ── Metrics row ─────────────────────────────────────────────────────────── */
.metrics{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}
.metric-card{
  background:var(--bg2);border:1px solid var(--border);
  border-radius:var(--radius);padding:16px 18px;
  transition:border-color .3s;
}
.metric-card.active{border-color:var(--accent)}
.metric-card.green{border-color:var(--green2)}
.metric-label{font-size:11px;color:var(--text3);text-transform:uppercase;letter-spacing:.7px;margin-bottom:6px}
.metric-value{font-size:28px;font-weight:700;color:var(--text);line-height:1;font-variant-numeric:tabular-nums}
.metric-value.green{color:var(--green)}
.metric-value.yellow{color:var(--yellow)}
.metric-value.accent{color:var(--accent)}

/* ── Contacts table ───────────────────────────────────────────────────────── */
.contacts-card{
  background:var(--bg2);border:1px solid var(--border);
  border-radius:var(--radius);flex:1;display:flex;flex-direction:column;
}
.card-header{
  display:flex;align-items:center;justify-content:space-between;
  padding:14px 20px;border-bottom:1px solid var(--border);
}
.card-title{font-size:13px;font-weight:600;color:var(--text2);
  text-transform:uppercase;letter-spacing:.8px}
.card-badge{
  font-size:11px;font-weight:700;padding:2px 9px;border-radius:10px;
  background:var(--bg3);color:var(--accent);border:1px solid var(--border2);
}
.table-wrap{overflow-x:auto;flex:1}
table{width:100%;border-collapse:collapse}
thead tr{background:var(--bg3)}
th{
  padding:10px 14px;text-align:left;
  font-size:11px;font-weight:600;color:var(--text3);
  text-transform:uppercase;letter-spacing:.6px;
  border-bottom:1px solid var(--border);white-space:nowrap;
}
td{padding:10px 14px;border-bottom:1px solid rgba(42,47,61,.6);font-size:13px;vertical-align:middle}
tbody tr{transition:background .15s}
tbody tr:hover{background:rgba(108,142,245,.04)}
tbody tr:last-child td{border-bottom:none}
.tr-new{animation:row-slide-in .4s cubic-bezier(.34,1.2,.64,1)}
@keyframes row-slide-in{from{opacity:0;transform:translateX(-10px)}to{opacity:1;transform:none}}
.badge{
  display:inline-flex;align-items:center;gap:4px;
  font-size:11px;font-weight:600;padding:2px 8px;border-radius:8px;white-space:nowrap;
}
.badge-green{background:rgba(74,222,128,.1);color:var(--green);border:1px solid rgba(74,222,128,.2)}
.badge-blue{background:rgba(108,142,245,.1);color:var(--accent);border:1px solid rgba(108,142,245,.2)}
.badge-yellow{background:rgba(250,204,21,.1);color:var(--yellow);border:1px solid rgba(250,204,21,.2)}
.badge-red{background:rgba(248,113,113,.1);color:var(--red);border:1px solid rgba(248,113,113,.2)}
.badge-dim{background:var(--bg3);color:var(--text3);border:1px solid var(--border)}
.empty-state{
  text-align:center;padding:48px 20px;color:var(--text3);
  font-size:13px;line-height:2;
}
.empty-icon{font-size:32px;margin-bottom:8px}

/* ── Sidebar: log panel ───────────────────────────────────────────────────── */
.sidebar-title{
  font-size:11px;font-weight:600;color:var(--text3);
  text-transform:uppercase;letter-spacing:.8px;
  padding:0 18px 10px;
}
.log-list{
  display:flex;flex-direction:column;gap:1px;
  padding:0 0 12px;max-height:calc(100vh - 120px);overflow-y:auto;
}
.log-entry{
  padding:5px 18px;font-size:11px;font-family:var(--font-mono);
  line-height:1.5;border-left:2px solid transparent;
  animation:log-in .2s ease;
}
@keyframes log-in{from{opacity:0;transform:translateX(-4px)}to{opacity:1;transform:none}}
.log-entry.ok{color:var(--green);border-left-color:var(--green)}
.log-entry.warn{color:var(--yellow);border-left-color:var(--yellow)}
.log-entry.error{color:var(--red);border-left-color:var(--red)}
.log-entry.info{color:var(--text2)}
.log-ts{color:var(--text3);margin-right:6px;font-size:10px}

/* ── Confirmation modal ───────────────────────────────────────────────────── */
.modal-overlay{
  position:fixed;inset:0;background:rgba(0,0,0,.7);
  display:flex;align-items:center;justify-content:center;
  z-index:200;opacity:0;pointer-events:none;
  transition:opacity .2s;backdrop-filter:blur(4px);
}
.modal-overlay.visible{opacity:1;pointer-events:all}
.modal{
  background:var(--bg2);border:1px solid var(--border2);
  border-radius:14px;padding:28px 32px;max-width:620px;width:90%;
  max-height:80vh;overflow-y:auto;
  transform:translateY(20px) scale(.97);transition:transform .25s cubic-bezier(.34,1.2,.64,1);
  box-shadow:0 20px 60px rgba(0,0,0,.5);
}
.modal-overlay.visible .modal{transform:none}
.modal-title{
  font-size:17px;font-weight:700;margin-bottom:6px;
  display:flex;align-items:center;gap:10px;
}
.modal-subtitle{font-size:13px;color:var(--text2);margin-bottom:20px}
.modal-table{width:100%;border-collapse:collapse;margin-bottom:24px}
.modal-table th{
  font-size:11px;font-weight:600;color:var(--text3);
  text-transform:uppercase;letter-spacing:.5px;
  padding:8px 10px;border-bottom:1px solid var(--border);text-align:left;
}
.modal-table td{padding:8px 10px;font-size:12px;border-bottom:1px solid rgba(42,47,61,.5)}
.modal-table tr:last-child td{border-bottom:none}
.modal-actions{display:flex;gap:10px;justify-content:flex-end}

/* ── Progress bar ─────────────────────────────────────────────────────────── */
.progress-container{
  background:var(--bg2);border:1px solid var(--border);
  border-radius:var(--radius);padding:14px 20px;
  display:none;
}
.progress-container.visible{display:block}
.progress-label{font-size:12px;color:var(--text2);margin-bottom:8px}
.progress-track{height:4px;background:var(--bg3);border-radius:2px;overflow:hidden}
.progress-fill{
  height:100%;background:linear-gradient(90deg,var(--accent),var(--purple));
  border-radius:2px;transition:width .4s ease;width:0%;
}
.progress-fill.shimmer-anim{
  background-size:200% 100%;
  animation:progress-shimmer 1.5s infinite;
  background:linear-gradient(90deg,var(--accent),var(--purple),var(--accent));
}
@keyframes progress-shimmer{0%{background-position:200% 0}100%{background-position:-200% 0}}

/* ── Ticker / live indicator ──────────────────────────────────────────────── */
.live-badge{
  display:inline-flex;align-items:center;gap:6px;
  font-size:11px;font-weight:700;color:var(--green);
  background:rgba(74,222,128,.08);border:1px solid rgba(74,222,128,.2);
  padding:3px 9px;border-radius:10px;
  opacity:0;transition:opacity .3s;
}
.live-badge.visible{opacity:1}
.live-pulse{
  width:6px;height:6px;border-radius:50%;background:var(--green);
  animation:pulse-dot 1.2s infinite;
}

/* ── Connection state ─────────────────────────────────────────────────────── */
.conn-banner{
  position:fixed;bottom:16px;right:16px;
  background:var(--bg3);border:1px solid var(--border2);
  border-radius:8px;padding:8px 14px;font-size:12px;
  color:var(--text2);display:flex;align-items:center;gap:8px;
  opacity:0;transform:translateY(10px);
  transition:all .25s;pointer-events:none;z-index:300;
}
.conn-banner.visible{opacity:1;transform:none}

/* ── Animations ───────────────────────────────────────────────────────────── */
@keyframes fade-in{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:none}}
.fade-in{animation:fade-in .3s ease forwards}

/* ── Responsive ───────────────────────────────────────────────────────────── */
@media(max-width:900px){
  .app{grid-template-columns:1fr;grid-template-rows:60px auto 1fr}
  .sidebar{display:none}
  .metrics{grid-template-columns:repeat(2,1fr)}
}
</style>
</head>
<body>
<div class="app">

<!-- ── Header ─────────────────────────────────────────────────────────────── -->
<header class="header">
  <div class="logo">
    <span>🚀</span>
    <span>VocalLabs<span class="logo-dot">.</span></span>
  </div>
  <span style="color:var(--text3);font-size:13px;margin-left:4px">Outreach Pipeline</span>
  <div class="header-badge">
    <div class="live-badge" id="liveBadge"><div class="live-pulse"></div>LIVE</div>
    &nbsp;
    <div class="status-dot" id="statusDot"></div>
    <span class="status-label" id="statusLabel">Idle</span>
  </div>
</header>

<!-- ── Sidebar ─────────────────────────────────────────────────────────────── -->
<aside class="sidebar">
  <div class="sidebar-title">Activity Log</div>
  <div class="log-list" id="logList">
    <div class="log-entry info" style="opacity:.5">
      <span class="log-ts">—</span>Waiting for pipeline…
    </div>
  </div>
</aside>

<!-- ── Main ───────────────────────────────────────────────────────────────── -->
<main class="main">

  <!-- Input -->
  <div class="input-card fade-in">
    <h2>New Run</h2>
    <div class="input-row">
      <input id="domainInput" class="domain-input"
             placeholder="stripe.com" type="text" autocomplete="off" spellcheck="false"/>
      <span class="count-label">Lookalikes:</span>
      <input id="countInput" class="count-input" type="number" value="15" min="5" max="50"/>
      <button class="btn btn-primary" id="runBtn" onclick="startRun()">
        <span>▶</span> Run Pipeline
      </button>
    </div>
  </div>

  <!-- Stage track -->
  <div class="stages-bar fade-in">
    <h2>Pipeline Stages</h2>
    <div class="stages-track">
      <div class="stage-item" id="stage-1" data-stage="1">
        <div class="stage-circle">🌊</div>
        <div class="stage-label">Ocean.io</div>
        <div class="stage-sublabel">Lookalike Cos</div>
        <div class="stage-count" id="s1count" style="display:none"></div>
      </div>
      <div class="stage-item" id="stage-2" data-stage="2">
        <div class="stage-circle">🔍</div>
        <div class="stage-label">Prospeo</div>
        <div class="stage-sublabel">Decision-makers</div>
        <div class="stage-count" id="s2count" style="display:none"></div>
      </div>
      <div class="stage-item" id="stage-3" data-stage="3">
        <div class="stage-circle">📧</div>
        <div class="stage-label">Eazyreach</div>
        <div class="stage-sublabel">Email Resolve</div>
        <div class="stage-count" id="s3count" style="display:none"></div>
      </div>
      <div class="stage-item" id="stage-4" data-stage="4">
        <div class="stage-circle">✉️</div>
        <div class="stage-label">Brevo</div>
        <div class="stage-sublabel">Send Outreach</div>
        <div class="stage-count" id="s4count" style="display:none"></div>
      </div>
    </div>
  </div>

  <!-- Progress -->
  <div class="progress-container" id="progressContainer">
    <div class="progress-label" id="progressLabel">Initialising…</div>
    <div class="progress-track"><div class="progress-fill" id="progressFill"></div></div>
  </div>

  <!-- Metrics -->
  <div class="metrics fade-in">
    <div class="metric-card" id="m-companies">
      <div class="metric-label">Companies</div>
      <div class="metric-value accent" id="mv-companies">0</div>
    </div>
    <div class="metric-card" id="m-contacts">
      <div class="metric-label">Contacts Found</div>
      <div class="metric-value" id="mv-contacts">0</div>
    </div>
    <div class="metric-card" id="m-emails">
      <div class="metric-label">Emails Resolved</div>
      <div class="metric-value yellow" id="mv-emails">0</div>
    </div>
    <div class="metric-card" id="m-sent">
      <div class="metric-label">Emails Sent</div>
      <div class="metric-value green" id="mv-sent">0</div>
    </div>
  </div>

  <!-- Contacts table -->
  <div class="contacts-card fade-in">
    <div class="card-header">
      <span class="card-title">Contacts</span>
      <span class="card-badge" id="contactsBadge">0</span>
    </div>
    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>#</th>
            <th>Name</th>
            <th>Title</th>
            <th>Company</th>
            <th>Email</th>
            <th>Status</th>
            <th>Sent</th>
          </tr>
        </thead>
        <tbody id="contactsBody">
          <tr><td colspan="7">
            <div class="empty-state">
              <div class="empty-icon">🎯</div>
              Enter a seed domain above and click <strong>Run Pipeline</strong> to begin.
            </div>
          </td></tr>
        </tbody>
      </table>
    </div>
  </div>

</main>
</div>

<!-- ── Confirmation modal ──────────────────────────────────────────────────── -->
<div class="modal-overlay" id="confirmModal">
  <div class="modal">
    <div class="modal-title">
      <span>⚡</span>
      <span>Ready to Send</span>
    </div>
    <div class="modal-subtitle" id="confirmSubtitle">
      Review the contacts below before sending.
    </div>
    <table class="modal-table">
      <thead>
        <tr>
          <th>#</th><th>Name</th><th>Title</th><th>Company</th><th>Email</th>
        </tr>
      </thead>
      <tbody id="confirmBody"></tbody>
    </table>
    <div class="modal-actions">
      <button class="btn btn-ghost btn-sm" onclick="sendConfirm(false)">Cancel</button>
      <button class="btn btn-success btn-sm" onclick="sendConfirm(true)">
        <span>✉️</span> Send All Emails
      </button>
    </div>
  </div>
</div>

<!-- ── Connection banner ───────────────────────────────────────────────────── -->
<div class="conn-banner" id="connBanner">
  <span id="connIcon">⚡</span>
  <span id="connMsg">Connecting…</span>
</div>

<script>
// ── State ─────────────────────────────────────────────────────────────────────
const st = {
  running:   false,
  contacts:  {},   // keyed by email or index
  companies: 0,
  emails:    0,
  sent:      0,
  stage:     0,
};
let evtSource   = null;
let reconnTimer = null;
let rowIndex    = 0;

// ── SSE connection ─────────────────────────────────────────────────────────────
function connectSSE() {
  if (evtSource) { evtSource.close(); evtSource = null; }

  showBanner('⚡', 'Connecting to pipeline…', false);
  evtSource = new EventSource('/events');

  evtSource.onopen = () => {
    hideBanner();
    clearTimeout(reconnTimer);
  };

  evtSource.onmessage = (e) => {
    let ev;
    try { ev = JSON.parse(e.data); } catch { return; }
    handleEvent(ev);
  };

  evtSource.onerror = () => {
    showBanner('⚠️', 'Connection lost — reconnecting…', true);
    evtSource.close();
    evtSource = null;
    reconnTimer = setTimeout(connectSSE, 3000);
  };
}

// ── Event handler ──────────────────────────────────────────────────────────────
function handleEvent(ev) {
  switch(ev.type) {
    case 'ping': break;

    case 'state_snapshot':
      applySnapshot(ev.state);
      break;

    case 'pipeline_start':
      st.running = true;
      resetUI(ev.seed);
      setStatus('running', `Running: ${ev.seed}`);
      setLive(true);
      showProgress(0, 'Stage 1 · Ocean.io — finding lookalike companies…');
      break;

    case 'stage_start':
      setStageState(ev.stage, 'active');
      const prog = ((ev.stage - 1) / 4) * 100;
      showProgress(prog, `Stage ${ev.stage} · ${ev.name} — ${ev.desc}`);
      addLog(`Stage ${ev.stage}: ${ev.name} started`, 'info');
      break;

    case 'stage_done':
      setStageState(ev.stage, 'done');
      setProgress((ev.stage / 4) * 100);
      if (ev.stage === 1 && ev.companies) {
        updateMetric('companies', ev.companies.length);
        st.companies = ev.companies.length;
      }
      if (ev.stage === 2 && ev.contacts) {
        updateMetric('contacts', ev.contacts.length);
        ev.contacts.forEach(addContactRow);
      }
      if (ev.stage === 3 && ev.contacts) {
        ev.contacts.forEach(updateContactEmail);
        const resolved = ev.contacts.filter(c => c.email).length;
        updateMetric('emails', resolved);
        st.emails = resolved;
      }
      if (ev.stage === 4) {
        updateMetric('sent', ev.sent || 0);
        setStageCount(4, `${ev.sent || 0} sent`);
      }
      addLog(`Stage ${ev.stage} done`, 'ok');
      break;

    case 'log':
      addLog(ev.msg, ev.level);
      break;

    case 'email_sent':
      updateContactSent(ev.email, ev.message_id);
      st.sent = (st.sent || 0) + 1;
      updateMetric('sent', st.sent);
      break;

    case 'confirm_needed':
      showConfirmModal(ev.contacts, ev.count);
      break;

    case 'confirm_result':
      hideConfirmModal();
      if (!ev.approved) addLog('Send cancelled by user', 'warn');
      break;

    case 'complete':
      st.running = false;
      setStatus('done', `Done — ${ev.sent || 0} email(s) sent`);
      setLive(false);
      setProgress(100);
      if (!ev.cancelled) addLog(`Pipeline complete: ${ev.sent || 0} sent, ${ev.failed || 0} failed`, 'ok');
      document.getElementById('runBtn').disabled = false;
      document.getElementById('progressContainer').classList.add('visible');
      break;

    case 'error':
      st.running = false;
      setStatus('error', 'Error');
      setLive(false);
      addLog(`Error: ${ev.message}`, 'error');
      document.getElementById('runBtn').disabled = false;
      break;
  }
}

// ── Apply snapshot (on reconnect / page load) ──────────────────────────────────
function applySnapshot(s) {
  if (!s) return;
  updateMetric('companies', (s.companies || []).length);
  updateMetric('contacts',  (s.contacts  || []).length);
  updateMetric('emails',    (s.contacts  || []).filter(c => c.email).length);
  updateMetric('sent',      s.sent || 0);

  const stages = s.stages || {};
  [1,2,3,4].forEach(n => {
    if (stages[n]) setStageState(n, stages[n]);
  });

  if ((s.contacts || []).length > 0 && rowIndex === 0) {
    document.getElementById('contactsBody').innerHTML = '';
    s.contacts.forEach(addContactRow);
    s.contacts.forEach(c => { if (c.email) updateContactEmail(c); });
    s.contacts.forEach(c => { if (c.send_status === 'SENT') updateContactSent(c.email, c.message_id); });
  }

  if (s.running) {
    setStatus('running', `Running: ${s.seed}`);
    setLive(true);
    document.getElementById('runBtn').disabled = true;
    showProgress(0, 'Pipeline running…');
  } else if (s.done && !s.error) {
    setStatus('done', `Done — ${s.sent || 0} email(s) sent`);
  } else if (s.error) {
    setStatus('error', 'Error');
  }

  if (s.confirm_needed && (s.confirm_contacts || []).length > 0) {
    showConfirmModal(s.confirm_contacts, s.confirm_contacts.length);
  }

  (s.logs || []).slice(-40).forEach(l => addLog(l.msg, l.level, false));
}

// ── UI helpers ─────────────────────────────────────────────────────────────────
function resetUI(seed) {
  rowIndex = 0;
  st.sent = 0;
  document.getElementById('contactsBody').innerHTML = '<tr><td colspan="7"><div class="empty-state"><div class="empty-icon">⏳</div>Searching for contacts…</div></td></tr>';
  document.getElementById('contactsBadge').textContent = '0';
  updateMetric('companies', 0);
  updateMetric('contacts',  0);
  updateMetric('emails',    0);
  updateMetric('sent',      0);
  [1,2,3,4].forEach(n => setStageState(n, 'idle'));
  [1,2,3,4].forEach(n => { const el = document.getElementById(`s${n}count`); if(el) el.style.display='none'; });
  document.getElementById('logList').innerHTML = '';
  document.getElementById('progressContainer').classList.add('visible');
}

function setStatus(state, label) {
  const dot   = document.getElementById('statusDot');
  const lbl   = document.getElementById('statusLabel');
  dot.className = `status-dot ${state}`;
  lbl.textContent = label;
}

function setLive(on) {
  document.getElementById('liveBadge').classList.toggle('visible', on);
}

function setStageState(n, state) {
  const el = document.getElementById(`stage-${n}`);
  if (!el) return;
  el.className = `stage-item ${state}`;
}

function setStageCount(n, text) {
  const el = document.getElementById(`s${n}count`);
  if (!el) return;
  el.textContent = text;
  el.style.display = 'inline';
}

function updateMetric(key, val) {
  const el = document.getElementById(`mv-${key}`);
  if (el) el.textContent = val;
  setStageCount(
    {companies:1, contacts:2, emails:3, sent:4}[key],
    val
  );
}

function showProgress(pct, label) {
  const c = document.getElementById('progressContainer');
  c.classList.add('visible');
  document.getElementById('progressLabel').textContent = label || '';
  setProgress(pct);
}

function setProgress(pct) {
  const fill = document.getElementById('progressFill');
  fill.style.width = `${Math.min(100, pct)}%`;
  if (pct < 100) fill.classList.add('shimmer-anim');
  else fill.classList.remove('shimmer-anim');
}

// ── Contact table ─────────────────────────────────────────────────────────────
function addContactRow(contact) {
  const tbody = document.getElementById('contactsBody');
  // Remove empty state
  if (tbody.querySelector('.empty-state')) tbody.innerHTML = '';

  const idx = ++rowIndex;
  const id  = `row-${escId(contact.email || idx)}`;
  if (document.getElementById(id)) return;  // already exists

  const tr = document.createElement('tr');
  tr.id = id;
  tr.className = 'tr-new';
  tr.innerHTML = `
    <td style="color:var(--text3)">${idx}</td>
    <td><strong>${esc(contact.full_name || '—')}</strong></td>
    <td><span style="color:var(--text2)">${esc(contact.job_title || '—')}</span></td>
    <td>${esc(contact.company_name || contact.company_domain || '—')}</td>
    <td class="email-cell" id="email-${escId(contact.email || idx)}">
      ${contact.email ? `<span class="badge badge-blue">${esc(contact.email)}</span>` : '<span style="color:var(--text3)">—</span>'}
    </td>
    <td class="status-cell" id="status-${escId(contact.email || idx)}">
      ${emailStatusBadge(contact.email_status)}
    </td>
    <td class="sent-cell" id="sent-${escId(contact.email || idx)}">
      <span style="color:var(--text3)">—</span>
    </td>`;
  tbody.appendChild(tr);
  document.getElementById('contactsBadge').textContent = rowIndex;
}

function updateContactEmail(contact) {
  if (!contact.email) return;
  const emailCell  = document.getElementById(`email-${escId(contact.email)}`);
  const statusCell = document.getElementById(`status-${escId(contact.email)}`);
  if (emailCell && !emailCell.querySelector('.badge-green')) {
    emailCell.innerHTML = `<span class="badge badge-green">✓ ${esc(contact.email)}</span>`;
  }
  if (statusCell) {
    statusCell.innerHTML = emailStatusBadge(contact.email_status || 'VERIFIED');
  }
}

function updateContactSent(email, messageId) {
  if (!email) return;
  const cell = document.getElementById(`sent-${escId(email)}`);
  if (cell) {
    cell.innerHTML = `<span class="badge badge-green">✉️ Sent</span>`;
    cell.closest('tr').style.background = 'rgba(74,222,128,.03)';
  }
}

function emailStatusBadge(status) {
  if (!status || status === '—') return '<span style="color:var(--text3)">—</span>';
  if (status === 'VERIFIED')   return '<span class="badge badge-green">✓ Verified</span>';
  if (status === 'NOT_FOUND')  return '<span class="badge badge-dim">Not found</span>';
  if (status.startsWith('ERROR') || status.startsWith('HTTP'))
                               return `<span class="badge badge-red">${esc(status)}</span>`;
  return `<span class="badge badge-yellow">${esc(status)}</span>`;
}

// ── Log ────────────────────────────────────────────────────────────────────────
function addLog(msg, level, scroll=true) {
  if (!msg) return;
  const list  = document.getElementById('logList');
  const entry = document.createElement('div');
  const lvl   = (level === 'ok' || level === 'success') ? 'ok'
              : (level === 'warn' || level === 'warning') ? 'warn'
              : (level === 'error') ? 'error' : 'info';
  entry.className = `log-entry ${lvl}`;
  const ts = new Date().toTimeString().slice(0,8);
  entry.innerHTML = `<span class="log-ts">${ts}</span>${esc(msg)}`;
  list.appendChild(entry);
  // Keep last 120 entries
  while (list.children.length > 120) list.removeChild(list.firstChild);
  if (scroll) entry.scrollIntoView({block:'end',behavior:'smooth'});
}

// ── Confirmation modal ─────────────────────────────────────────────────────────
function showConfirmModal(contacts, count) {
  document.getElementById('confirmSubtitle').textContent =
    `${count} email(s) are ready to send. Confirm to proceed.`;
  const tbody = document.getElementById('confirmBody');
  tbody.innerHTML = '';
  (contacts || []).forEach((c, i) => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td style="color:var(--text3)">${i+1}</td>
      <td><strong>${esc(c.full_name||'—')}</strong></td>
      <td style="color:var(--text2)">${esc(c.job_title||'—')}</td>
      <td>${esc(c.company_name||'—')}</td>
      <td><span class="badge badge-blue">${esc(c.email||'—')}</span></td>`;
    tbody.appendChild(tr);
  });
  document.getElementById('confirmModal').classList.add('visible');
}

function hideConfirmModal() {
  document.getElementById('confirmModal').classList.remove('visible');
}

async function sendConfirm(approved) {
  hideConfirmModal();
  await fetch('/confirm', {
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body: JSON.stringify({approved})
  });
  if (approved) addLog('Confirmed — sending emails…', 'ok');
  else          addLog('Send cancelled', 'warn');
}

// ── Banner ────────────────────────────────────────────────────────────────────
let bannerTimer = null;
function showBanner(icon, msg, persist=false) {
  const b = document.getElementById('connBanner');
  document.getElementById('connIcon').textContent = icon;
  document.getElementById('connMsg').textContent  = msg;
  b.classList.add('visible');
  clearTimeout(bannerTimer);
  if (!persist) bannerTimer = setTimeout(hideBanner, 3000);
}
function hideBanner() {
  document.getElementById('connBanner').classList.remove('visible');
}

// ── Run pipeline ─────────────────────────────────────────────────────────────
async function startRun() {
  const domain = document.getElementById('domainInput').value.trim();
  const count  = parseInt(document.getElementById('countInput').value) || 15;
  if (!domain) {
    document.getElementById('domainInput').focus();
    document.getElementById('domainInput').style.borderColor = 'var(--red)';
    setTimeout(() => document.getElementById('domainInput').style.borderColor = '', 1500);
    return;
  }
  document.getElementById('runBtn').disabled = true;
  document.getElementById('domainInput').style.borderColor = '';
  addLog(`Starting pipeline for ${domain}…`, 'info');

  try {
    const res = await fetch('/run', {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify({domain, count})
    });
    const data = await res.json();
    if (!res.ok) {
      addLog(`Error: ${data.error || res.statusText}`, 'error');
      document.getElementById('runBtn').disabled = false;
    }
  } catch(err) {
    addLog(`Request failed: ${err}`, 'error');
    document.getElementById('runBtn').disabled = false;
  }
}

// Allow Enter key in input
document.getElementById('domainInput').addEventListener('keydown', e => {
  if (e.key === 'Enter' && !document.getElementById('runBtn').disabled) startRun();
});

// ── Utils ──────────────────────────────────────────────────────────────────────
function esc(s) {
  if (!s) return '';
  return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}
function escId(s) {
  return String(s).replace(/[^a-zA-Z0-9]/g, '_');
}

// ── Init ───────────────────────────────────────────────────────────────────────
connectSSE();
</script>
</body>
</html>"""