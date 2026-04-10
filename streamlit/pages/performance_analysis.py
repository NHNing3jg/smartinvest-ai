# ==========================================================
# Page 2 — Performance Analysis
# SmartInvest BI-AI Dashboard
# ==========================================================

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
from sqlalchemy import create_engine
from datetime import timedelta

# ----------------------------------------------------------
# PAGE CONFIG
# ----------------------------------------------------------

st.set_page_config(
    page_title="Performance Analysis — SmartInvest",
    page_icon="🏆",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ----------------------------------------------------------
# CUSTOM CSS
# ----------------------------------------------------------

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Mono:wght@300;400;500&display=swap');

html, body, [class*="css"] { font-family: 'DM Mono', monospace; }

.stApp {
    background: #07080f;
    background-image:
        radial-gradient(ellipse 80% 50% at 50% -10%, rgba(0,200,120,0.09) 0%, transparent 70%),
        radial-gradient(ellipse 40% 30% at 10% 90%, rgba(167,139,250,0.06) 0%, transparent 60%);
}
[data-testid="stSidebar"] {
    background: #0d0f1a !important;
    border-right: 1px solid rgba(0,200,120,0.15);
}

/* ── Page header ── */
.page-header { padding: 1.8rem 0 1rem 0; }
.page-badge {
    display: inline-block; font-size: 0.68rem; letter-spacing: 0.18em;
    text-transform: uppercase; color: #a78bfa;
    border: 1px solid rgba(167,139,250,0.3); border-radius: 2px;
    padding: 3px 12px; background: rgba(167,139,250,0.06); margin-bottom: 0.8rem;
}
.page-title {
    font-family: 'Syne', sans-serif; font-size: 2.2rem; font-weight: 800;
    color: #eef2f7; letter-spacing: -0.02em; margin: 0;
}
.page-subtitle { font-size: 0.8rem; color: #3a4a5a; margin-top: 0.4rem; }

/* ── KPI cards ── */
.kpi-row { display: flex; gap: 0.85rem; margin: 1.5rem 0; flex-wrap: wrap; }
.kpi-card {
    flex: 1; min-width: 150px;
    background: rgba(255,255,255,0.025);
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 6px; padding: 1rem 1.2rem;
    position: relative; overflow: hidden;
}
.kpi-card::after {
    content: ''; position: absolute;
    top: 0; left: 0; right: 0; height: 2px;
}
.kpi-card.purple::after { background: linear-gradient(90deg,#a78bfa,transparent); }
.kpi-card.green::after  { background: linear-gradient(90deg,#00c878,transparent); }
.kpi-card.red::after    { background: linear-gradient(90deg,#ff4d6d,transparent); }
.kpi-card.amber::after  { background: linear-gradient(90deg,#f59e0b,transparent); }
.kpi-card.blue::after   { background: linear-gradient(90deg,#00aaff,transparent); }

.kpi-label { font-size: 0.65rem; letter-spacing: 0.12em; text-transform: uppercase; color: #3a4a5a; margin-bottom: 0.35rem; }
.kpi-value { font-family: 'Syne', sans-serif; font-size: 1.4rem; font-weight: 700; color: #eef2f7; }
.kpi-delta { font-size: 0.72rem; margin-top: 0.25rem; }
.kpi-delta.pos { color: #00c878; } .kpi-delta.neg { color: #ff4d6d; } .kpi-delta.neu { color: #a78bfa; }

/* ── Section titles ── */
.section-title {
    font-family: 'Syne', sans-serif; font-size: 0.85rem; font-weight: 700;
    color: #8898aa; letter-spacing: 0.1em; text-transform: uppercase;
    margin: 1.8rem 0 0.8rem 0; display: flex; align-items: center; gap: 0.5rem;
}
.section-title::after {
    content: ''; flex: 1; height: 1px;
    background: linear-gradient(90deg, rgba(255,255,255,0.07), transparent);
}

/* ── Chart container ── */
.chart-container {
    background: rgba(255,255,255,0.02);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 6px; padding: 0.5rem 0.5rem 0 0.5rem; margin-bottom: 1rem;
}

/* ── Sidebar brand ── */
.sidebar-brand { padding: 1.2rem 0 1rem 0; text-align: center; border-bottom: 1px solid rgba(0,200,120,0.1); margin-bottom: 1rem; }
.sidebar-brand-name { font-family: 'Syne', sans-serif; font-size: 1.05rem; font-weight: 800; color: #eef2f7 !important; }
.sidebar-brand-tag  { font-size: 0.65rem; color: #a78bfa !important; letter-spacing: 0.15em; text-transform: uppercase; }

/* ── Rank badges ── */
.rank-table { width: 100%; border-collapse: collapse; }
.rank-table td { padding: 0.5rem 0.6rem; font-size: 0.78rem; border-bottom: 1px solid rgba(255,255,255,0.04); }
.rank-badge {
    display: inline-block; width: 22px; height: 22px; border-radius: 50%;
    text-align: center; line-height: 22px; font-size: 0.7rem; font-weight: 700;
}
.rank-1 { background: #f59e0b; color: #07080f; }
.rank-2 { background: #94a3b8; color: #07080f; }
.rank-3 { background: #b45309; color: #fff; }
.rank-n { background: rgba(255,255,255,0.07); color: #8898aa; }
</style>
""", unsafe_allow_html=True)

# ----------------------------------------------------------
# DATABASE
# ----------------------------------------------------------

DB_USER     = "postgres"
DB_PASSWORD = "postgres"
DB_HOST     = "localhost"
DB_PORT     = "5432"
DB_NAME     = "smartinvest_dw"

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

@st.cache_resource(show_spinner=False)
def get_engine():
    return create_engine(DATABASE_URL)

@st.cache_data(ttl=300, show_spinner=False)
def load_returns():
    df = pd.read_sql("SELECT * FROM smartinvest.v_market_returns_daily ORDER BY date_id", get_engine())
    df["date_id"] = pd.to_datetime(df["date_id"])
    return df

@st.cache_data(ttl=300, show_spinner=False)
def load_cum_returns():
    return pd.read_sql("SELECT * FROM smartinvest.v_market_cum_return", get_engine())

# ----------------------------------------------------------
# LOAD DATA
# ----------------------------------------------------------

with st.spinner("Loading performance data…"):
    try:
        returns_df = load_returns()
        cum_df     = load_cum_returns()
    except Exception as e:
        st.error(f"⚠️ Database connection error: {e}")
        st.stop()

# ----------------------------------------------------------
# SIDEBAR
# ----------------------------------------------------------

with st.sidebar:
    st.markdown("""
    <div class="sidebar-brand">
        <div class="sidebar-brand-name">SmartInvest</div>
        <div class="sidebar-brand-tag">Performance Analysis</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("**Asset**")
    ticker_list     = sorted(returns_df["ticker"].unique())
    selected_ticker = st.selectbox("Asset", ticker_list, label_visibility="collapsed")

    st.divider()

    st.markdown("**Comparison Basket**")
    compare_tickers = st.multiselect(
        "Compare with",
        [t for t in ticker_list if t != selected_ticker],
        default=[],
        label_visibility="collapsed",
        max_selections=4,
        placeholder="Add assets to compare…"
    )

    st.divider()

    st.markdown("**Period**")
    min_date  = returns_df["date_id"].min().date()
    max_date  = returns_df["date_id"].max().date()
    date_range = st.date_input(
        "Period",
        value=(max_date - timedelta(days=365), max_date),
        min_value=min_date, max_value=max_date,
        label_visibility="collapsed"
    )

    st.divider()

    show_table  = st.toggle("Show Returns Table",  value=True)
    show_vol    = st.toggle("Show Volatility Gauge", value=True)

    st.divider()
    st.markdown("<span style='font-size:0.7rem;color:#2a3a4a;'>v1.0.0 — SmartInvest BI-AI</span>",
                unsafe_allow_html=True)

# ----------------------------------------------------------
# FILTER
# ----------------------------------------------------------

if len(date_range) == 2:
    s, e = pd.Timestamp(date_range[0]), pd.Timestamp(date_range[1])
    rdf  = returns_df[(returns_df["date_id"] >= s) & (returns_df["date_id"] <= e)]
else:
    rdf  = returns_df.copy()

fdf = rdf[rdf["ticker"] == selected_ticker].sort_values("date_id").reset_index(drop=True)

if fdf.empty:
    st.warning("No data available for the selected filters.")
    st.stop()

# ----------------------------------------------------------
# KPI CALCULATIONS
# ----------------------------------------------------------

def compute_metrics(sub):
    dr  = sub["daily_return"].dropna()
    ann = dr.mean() * 252 * 100
    vol = dr.std() * np.sqrt(252) * 100
    sr  = ann / vol if vol else 0
    mx  = dr.cumsum()
    mdd = (mx - mx.cummax()).min() * 100
    pos = (dr > 0).sum() / len(dr) * 100 if len(dr) else 0
    cum = (1 + dr).prod() - 1
    return dict(ann=ann, vol=vol, sr=sr, mdd=mdd, pos=pos, cum=cum)

m = compute_metrics(fdf)

sign    = lambda v: "pos" if v >= 0 else "neg"
arrow   = lambda v: "▲" if v >= 0 else "▼"
up_down = lambda v: "green" if v >= 0 else "red"

# ----------------------------------------------------------
# PAGE HEADER
# ----------------------------------------------------------

st.markdown(f"""
<div class="page-header">
    <div class="page-badge">Performance Analysis</div>
    <h1 class="page-title">{selected_ticker}</h1>
    <p class="page-subtitle">
        {fdf["date_id"].min().strftime("%d %b %Y")} → {fdf["date_id"].max().strftime("%d %b %Y")}
        &nbsp;·&nbsp; {len(fdf)} sessions
    </p>
</div>
""", unsafe_allow_html=True)

# ----------------------------------------------------------
# KPI ROW
# ----------------------------------------------------------

st.markdown(f"""
<div class="kpi-row">
  <div class="kpi-card {up_down(m['cum'])}">
    <div class="kpi-label">Cumulative Return</div>
    <div class="kpi-value">{m['cum']*100:+.1f}%</div>
    <div class="kpi-delta {sign(m['cum'])}">{arrow(m['cum'])} over the period</div>
  </div>
  <div class="kpi-card {up_down(m['ann'])}">
    <div class="kpi-label">Ann. Return</div>
    <div class="kpi-value">{m['ann']:+.1f}%</div>
    <div class="kpi-delta {sign(m['ann'])}">Annualised avg</div>
  </div>
  <div class="kpi-card amber">
    <div class="kpi-label">Volatility</div>
    <div class="kpi-value">{m['vol']:.1f}%</div>
    <div class="kpi-delta neu">Annualised σ</div>
  </div>
  <div class="kpi-card {up_down(m['sr'])}">
    <div class="kpi-label">Sharpe Ratio</div>
    <div class="kpi-value">{m['sr']:.2f}</div>
    <div class="kpi-delta {sign(m['sr'])}">Risk-adjusted return</div>
  </div>
  <div class="kpi-card red">
    <div class="kpi-label">Max Drawdown</div>
    <div class="kpi-value">{m['mdd']:.1f}%</div>
    <div class="kpi-delta neg">Peak-to-trough</div>
  </div>
  <div class="kpi-card purple">
    <div class="kpi-label">Win Rate</div>
    <div class="kpi-value">{m['pos']:.0f}%</div>
    <div class="kpi-delta neu">Positive days</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ----------------------------------------------------------
# CHART THEME
# ----------------------------------------------------------

CHART_BG   = "rgba(0,0,0,0)"
GRID_COLOR = "rgba(255,255,255,0.05)"
FONT_COLOR = "#5a6a80"
ACCENT     = "#00c878"
PURPLE     = "#a78bfa"
RED        = "#ff4d6d"
AMBER      = "#f59e0b"

PALETTE = [ACCENT, "#00aaff", PURPLE, AMBER, "#f97316"]

layout_base = dict(
    paper_bgcolor=CHART_BG, plot_bgcolor=CHART_BG,
    font=dict(family="DM Mono", color=FONT_COLOR, size=11),
    xaxis=dict(gridcolor=GRID_COLOR, zeroline=False,
               showspikes=True, spikecolor=ACCENT, spikemode="across",
               spikethickness=1, spikedash="dot"),
    yaxis=dict(gridcolor=GRID_COLOR, zeroline=False),
    legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=11)),
    margin=dict(l=0, r=0, t=40, b=0),
    hovermode="x unified",
    hoverlabel=dict(bgcolor="#0d0f1a", font_color="#eef2f7", font_size=12, bordercolor=PURPLE),
)

# ----------------------------------------------------------
# CUMULATIVE RETURNS (multi-asset)
# ----------------------------------------------------------

st.markdown('<div class="section-title">Cumulative Performance</div>', unsafe_allow_html=True)

all_tickers = [selected_ticker] + list(compare_tickers)
fig_cum_line = go.Figure()

for i, tkr in enumerate(all_tickers):
    sub = rdf[rdf["ticker"] == tkr].sort_values("date_id")
    if sub.empty:
        continue
    cum_series = (1 + sub["daily_return"].fillna(0)).cumprod() - 1
    is_main = (tkr == selected_ticker)
    fig_cum_line.add_trace(go.Scatter(
        x=sub["date_id"], y=cum_series * 100,
        name=tkr,
        line=dict(color=PALETTE[i % len(PALETTE)], width=2.5 if is_main else 1.5,
                  dash="solid" if is_main else "dot"),
        fill="tozeroy" if is_main else "none",
        fillcolor="rgba(0,200,120,0.05)" if is_main else "rgba(0,0,0,0)",
        hovertemplate=f"<b>{tkr}</b>: %{{y:+.2f}}%<extra></extra>"
    ))

fig_cum_line.add_hline(y=0, line_color="rgba(255,255,255,0.1)", line_width=1)
fig_cum_line.update_layout(**layout_base, height=340,
                            yaxis_title="Cumulative Return (%)",
                            yaxis_tickformat=".1f",
                            xaxis_rangeslider_visible=False)

st.markdown('<div class="chart-container">', unsafe_allow_html=True)
st.plotly_chart(fig_cum_line, use_container_width=True, config={"displayModeBar": False})
st.markdown('</div>', unsafe_allow_html=True)

# ----------------------------------------------------------
# DAILY RETURN + DRAWDOWN  (2 rows)
# ----------------------------------------------------------

col_l, col_r = st.columns(2)

with col_l:
    st.markdown('<div class="section-title">Daily Returns</div>', unsafe_allow_html=True)
    colors = [ACCENT if v >= 0 else RED for v in fdf["daily_return"].fillna(0)]
    fig_dr = go.Figure()
    fig_dr.add_trace(go.Bar(
        x=fdf["date_id"], y=fdf["daily_return"] * 100,
        marker_color=colors,
        name="Daily return",
        hovertemplate="<b>%{x|%d %b %Y}</b><br>Return: %{y:+.2f}%<extra></extra>"
    ))
    fig_dr.add_hline(y=0, line_color="rgba(255,255,255,0.1)")
    fig_dr.update_layout(**layout_base, height=260,
                         yaxis_title="Return (%)", bargap=0.1)
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    st.plotly_chart(fig_dr, use_container_width=True, config={"displayModeBar": False})
    st.markdown('</div>', unsafe_allow_html=True)

with col_r:
    st.markdown('<div class="section-title">Drawdown</div>', unsafe_allow_html=True)
    cum_ret  = (1 + fdf["daily_return"].fillna(0)).cumprod()
    drawdown = (cum_ret - cum_ret.cummax()) / cum_ret.cummax() * 100
    fig_dd = go.Figure()
    fig_dd.add_trace(go.Scatter(
        x=fdf["date_id"], y=drawdown,
        fill="tozeroy", fillcolor="rgba(255,77,109,0.12)",
        line=dict(color=RED, width=1.5),
        name="Drawdown",
        hovertemplate="<b>%{x|%d %b %Y}</b><br>DD: %{y:.2f}%<extra></extra>"
    ))
    fig_dd.update_layout(**layout_base, height=260,
                         yaxis_title="Drawdown (%)", yaxis_tickformat=".1f")
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    st.plotly_chart(fig_dd, use_container_width=True, config={"displayModeBar": False})
    st.markdown('</div>', unsafe_allow_html=True)

# ----------------------------------------------------------
# LEADERBOARD  (Top 5 / Worst 5)
# ----------------------------------------------------------

st.markdown('<div class="section-title">Asset Ranking</div>', unsafe_allow_html=True)

col_top, col_bot = st.columns(2)

with col_top:
    top5 = cum_df.sort_values("cum_return", ascending=False).head(5).reset_index(drop=True)
    fig_top = go.Figure()
    bar_colors_top = [ACCENT if v >= 0 else RED for v in top5["cum_return"]]
    fig_top.add_trace(go.Bar(
        y=top5["ticker"], x=top5["cum_return"] * 100,
        orientation="h",
        marker=dict(color=bar_colors_top, line=dict(width=0)),
        hovertemplate="%{y}: %{x:+.2f}%<extra></extra>"
    ))
    fig_top.update_layout(
        **layout_base, height=220,
        title=dict(text="🏆 Top 5", font=dict(family="Syne", size=13, color="#eef2f7")),
        xaxis_title="Cumulative Return (%)",
        xaxis_tickformat=".1f"
    )
    fig_top.update_yaxes(autorange="reversed")
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    st.plotly_chart(fig_top, use_container_width=True, config={"displayModeBar": False})
    st.markdown('</div>', unsafe_allow_html=True)

with col_bot:
    bot5 = cum_df.sort_values("cum_return").head(5).reset_index(drop=True)
    bar_colors_bot = [RED if v < 0 else ACCENT for v in bot5["cum_return"]]
    fig_bot = go.Figure()
    fig_bot.add_trace(go.Bar(
        y=bot5["ticker"], x=bot5["cum_return"] * 100,
        orientation="h",
        marker=dict(color=bar_colors_bot, line=dict(width=0)),
        hovertemplate="%{y}: %{x:+.2f}%<extra></extra>"
    ))
    fig_bot.update_layout(
        **layout_base, height=220,
        title=dict(text="📉 Worst 5", font=dict(family="Syne", size=13, color="#eef2f7")),
        xaxis_title="Cumulative Return (%)",
        xaxis_tickformat=".1f"
    )
    fig_bot.update_yaxes(autorange="reversed")
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    st.plotly_chart(fig_bot, use_container_width=True, config={"displayModeBar": False})
    st.markdown('</div>', unsafe_allow_html=True)

# ----------------------------------------------------------
# ROLLING VOLATILITY  (30j)
# ----------------------------------------------------------

if show_vol:
    st.markdown('<div class="section-title">Rolling 30-Day Volatility</div>', unsafe_allow_html=True)
    fdf["roll_vol"] = fdf["daily_return"].rolling(30).std() * np.sqrt(252) * 100
    fig_rvol = go.Figure()
    fig_rvol.add_trace(go.Scatter(
        x=fdf["date_id"], y=fdf["roll_vol"],
        fill="tozeroy", fillcolor="rgba(245,158,11,0.07)",
        line=dict(color=AMBER, width=1.8),
        name="Rolling Vol",
        hovertemplate="<b>%{x|%d %b %Y}</b><br>Vol: %{y:.1f}%<extra></extra>"
    ))
    fig_rvol.update_layout(**layout_base, height=220,
                           yaxis_title="Annualised Vol (%)", yaxis_tickformat=".1f")
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    st.plotly_chart(fig_rvol, use_container_width=True, config={"displayModeBar": False})
    st.markdown('</div>', unsafe_allow_html=True)

# ----------------------------------------------------------
# RETURNS TABLE
# ----------------------------------------------------------

if show_table:
    st.markdown('<div class="section-title">Daily Returns — Last 50 Sessions</div>',
                unsafe_allow_html=True)

    tbl = fdf[["date_id", "daily_return"]].tail(50).sort_values("date_id", ascending=False).copy()
    tbl["date_id"]     = tbl["date_id"].dt.strftime("%Y-%m-%d")
    tbl["daily_return"] = tbl["daily_return"] * 100

    st.dataframe(
        tbl,
        use_container_width=True,
        hide_index=True,
        column_config={
            "date_id":     st.column_config.TextColumn("Date"),
            "daily_return": st.column_config.NumberColumn(
                "Daily Return (%)", format="%.2f",
                help="Daily return in percent"
            ),
        }
    )