import streamlit as st

st.set_page_config(
    page_title="SmartInvest BI-AI Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Mono:wght@300;400;500&display=swap');

/* ── Global reset ── */
html, body, [class*="css"] {
    font-family: 'DM Mono', monospace;
}

/* ── Background ── */
.stApp {
    background: #07080f;
    background-image:
        radial-gradient(ellipse 80% 50% at 50% -10%, rgba(0,200,120,0.12) 0%, transparent 70%),
        radial-gradient(ellipse 40% 30% at 90% 80%, rgba(0,150,255,0.07) 0%, transparent 60%);
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: #0d0f1a !important;
    border-right: 1px solid rgba(0,200,120,0.15);
}
[data-testid="stSidebar"] * { color: #a0aec0 !important; }
[data-testid="stSidebar"] .stSelectbox label,
[data-testid="stSidebar"] a { color: #00c878 !important; }

/* ── Hero section ── */
.hero-wrapper {
    padding: 3.5rem 0 2.5rem 0;
    text-align: center;
}
.hero-badge {
    display: inline-block;
    font-family: 'DM Mono', monospace;
    font-size: 0.7rem;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: #00c878;
    border: 1px solid rgba(0,200,120,0.35);
    border-radius: 2px;
    padding: 4px 14px;
    margin-bottom: 1.4rem;
    background: rgba(0,200,120,0.06);
}
.hero-title {
    font-family: 'Syne', sans-serif;
    font-size: clamp(2.4rem, 5vw, 4.2rem);
    font-weight: 800;
    line-height: 1.08;
    letter-spacing: -0.03em;
    color: #eef2f7;
    margin: 0 0 0.5rem 0;
}
.hero-title span {
    background: linear-gradient(90deg, #00c878 0%, #00aaff 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}
.hero-sub {
    font-family: 'DM Mono', monospace;
    font-size: 0.92rem;
    color: #5a6a80;
    margin-top: 1rem;
    letter-spacing: 0.01em;
}

/* ── Divider ── */
.divider {
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(0,200,120,0.3), transparent);
    margin: 2rem 0;
}

/* ── Module cards ── */
.module-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 1rem;
    margin-top: 0.5rem;
}
.module-card {
    background: rgba(255,255,255,0.025);
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 6px;
    padding: 1.4rem 1.6rem;
    transition: border-color 0.2s, background 0.2s;
    position: relative;
    overflow: hidden;
}
.module-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    border-radius: 6px 6px 0 0;
}
.module-card.green::before  { background: linear-gradient(90deg, #00c878, transparent); }
.module-card.blue::before   { background: linear-gradient(90deg, #00aaff, transparent); }
.module-card.purple::before { background: linear-gradient(90deg, #a78bfa, transparent); }
.module-card.amber::before  { background: linear-gradient(90deg, #f59e0b, transparent); }

.module-card:hover {
    border-color: rgba(0,200,120,0.25);
    background: rgba(0,200,120,0.04);
}
.card-icon  { font-size: 1.6rem; margin-bottom: 0.6rem; }
.card-title {
    font-family: 'Syne', sans-serif;
    font-size: 0.95rem;
    font-weight: 700;
    color: #dde4ef;
    margin-bottom: 0.35rem;
    letter-spacing: 0.01em;
}
.card-desc  { font-size: 0.76rem; color: #485668; line-height: 1.6; }

/* ── Status bar ── */
.status-bar {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 2rem;
    padding: 0.9rem 1.5rem;
    background: rgba(0,200,120,0.04);
    border: 1px solid rgba(0,200,120,0.12);
    border-radius: 4px;
    margin-top: 2.5rem;
    flex-wrap: wrap;
}
.status-item { display: flex; align-items: center; gap: 0.5rem; }
.status-dot  {
    width: 7px; height: 7px; border-radius: 50%;
    background: #00c878;
    box-shadow: 0 0 6px #00c878;
    animation: pulse 2s infinite;
}
@keyframes pulse {
    0%, 100% { opacity: 1; }
    50%       { opacity: 0.4; }
}
.status-label { font-size: 0.72rem; color: #4a5a6a; letter-spacing: 0.08em; text-transform: uppercase; }
.status-value { font-size: 0.72rem; color: #00c878; font-weight: 500; }

/* ── Sidebar brand ── */
.sidebar-brand {
    padding: 1.2rem 0 1rem 0;
    text-align: center;
    border-bottom: 1px solid rgba(0,200,120,0.1);
    margin-bottom: 1rem;
}
.sidebar-brand-name {
    font-family: 'Syne', sans-serif;
    font-size: 1.05rem;
    font-weight: 800;
    color: #eef2f7 !important;
    letter-spacing: 0.04em;
}
.sidebar-brand-tag {
    font-size: 0.65rem;
    color: #00c878 !important;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    margin-top: 2px;
}
</style>
""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div class="sidebar-brand">
        <div class="sidebar-brand-name">SmartInvest</div>
        <div class="sidebar-brand-tag">BI · AI · Platform</div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("**Navigation**")
    st.markdown("""
    - 🏠 Home  
    - 📈 Market Prices  
    - 📊 Trading Volumes  
    - 🏆 Asset Performance  
    - 🌐 Macro Indicators  
    """)
    st.divider()
    st.markdown("<span style='font-size:0.72rem;color:#2a3a4a;'>v1.0.0 — 2025</span>", unsafe_allow_html=True)

# ── Hero ──────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero-wrapper">
    <div class="hero-badge">BI · AI · Real-time Analytics</div>
    <h1 class="hero-title">Smart<span>Invest</span> Dashboard</h1>
    <p class="hero-sub">Financial intelligence powered by data & AI — explore, analyze, decide.</p>
</div>
""", unsafe_allow_html=True)

st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

# ── Module cards ──────────────────────────────────────────────────────────────
st.markdown("""
<div class="module-grid">

  <div class="module-card green">
    <div class="card-icon">📈</div>
    <div class="card-title">Market Prices</div>
    <div class="card-desc">Track real-time and historical price movements across all monitored assets. Identify trends, supports & resistances.</div>
  </div>

  <div class="module-card blue">
    <div class="card-icon">📊</div>
    <div class="card-title">Trading Volumes</div>
    <div class="card-desc">Analyze liquidity and volume patterns. Detect unusual activity and confirm breakouts with volume context.</div>
  </div>

  <div class="module-card purple">
    <div class="card-icon">🏆</div>
    <div class="card-title">Asset Performance</div>
    <div class="card-desc">Compare returns, volatility and risk-adjusted metrics across your portfolio. Rank assets by multiple performance indicators.</div>
  </div>

  <div class="module-card amber">
    <div class="card-icon">🌐</div>
    <div class="card-title">Macro Indicators</div>
    <div class="card-desc">Monitor key macroeconomic signals — rates, inflation, GDP — and understand their impact on market dynamics.</div>
  </div>

</div>
""", unsafe_allow_html=True)

# ── Status bar ────────────────────────────────────────────────────────────────
st.markdown("""
<div class="status-bar">
    <div class="status-item">
        <div class="status-dot"></div>
        <span class="status-label">Database</span>
        <span class="status-value">Connected</span>
    </div>
    <div class="status-item">
        <span class="status-label">Engine</span>
        <span class="status-value">PostgreSQL</span>
    </div>
    <div class="status-item">
        <span class="status-label">Interface</span>
        <span class="status-value">Streamlit</span>
    </div>
    <div class="status-item">
        <span class="status-label">AI Layer</span>
        <span class="status-value">Active</span>
    </div>
</div>
""", unsafe_allow_html=True)