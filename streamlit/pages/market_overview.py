# ==========================================================
# Page 1 — Market Overview
# SmartInvest BI-AI
# ==========================================================

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from sqlalchemy import create_engine
from datetime import datetime, timedelta
import numpy as np

# ----------------------------------------------------------
# PAGE CONFIG
# ----------------------------------------------------------

st.set_page_config(
    page_title="Market Overview — SmartInvest",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ----------------------------------------------------------
# CUSTOM CSS  (cohérent avec app.py)
# ----------------------------------------------------------

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Mono:wght@300;400;500&display=swap');

html, body, [class*="css"] { font-family: 'DM Mono', monospace; }

.stApp {
    background: #07080f;
    background-image:
        radial-gradient(ellipse 80% 50% at 50% -10%, rgba(0,200,120,0.10) 0%, transparent 70%),
        radial-gradient(ellipse 40% 30% at 90% 80%, rgba(0,150,255,0.06) 0%, transparent 60%);
}

[data-testid="stSidebar"] {
    background: #0d0f1a !important;
    border-right: 1px solid rgba(0,200,120,0.15);
}

/* ── Page header ── */
.page-header { padding: 1.8rem 0 1.2rem 0; }
.page-badge {
    display: inline-block;
    font-size: 0.68rem; letter-spacing: 0.18em; text-transform: uppercase;
    color: #00c878; border: 1px solid rgba(0,200,120,0.3);
    border-radius: 2px; padding: 3px 12px;
    background: rgba(0,200,120,0.06); margin-bottom: 0.8rem;
}
.page-title {
    font-family: 'Syne', sans-serif;
    font-size: 2.2rem; font-weight: 800;
    color: #eef2f7; letter-spacing: -0.02em; margin: 0;
}
.page-subtitle { font-size: 0.8rem; color: #3a4a5a; margin-top: 0.4rem; }

/* ── KPI cards ── */
.kpi-row { display: flex; gap: 0.85rem; margin: 1.5rem 0; flex-wrap: wrap; }
.kpi-card {
    flex: 1; min-width: 140px;
    background: rgba(255,255,255,0.025);
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 6px; padding: 1rem 1.2rem;
    position: relative; overflow: hidden;
}
.kpi-card::after {
    content: ''; position: absolute;
    top: 0; left: 0; right: 0; height: 2px;
}
.kpi-card.up::after   { background: linear-gradient(90deg,#00c878,transparent); }
.kpi-card.down::after { background: linear-gradient(90deg,#ff4d6d,transparent); }
.kpi-card.neut::after { background: linear-gradient(90deg,#00aaff,transparent); }

.kpi-label { font-size: 0.65rem; letter-spacing: 0.12em; text-transform: uppercase; color: #3a4a5a; margin-bottom: 0.35rem; }
.kpi-value { font-family: 'Syne', sans-serif; font-size: 1.45rem; font-weight: 700; color: #eef2f7; }
.kpi-delta { font-size: 0.72rem; margin-top: 0.25rem; }
.kpi-delta.pos { color: #00c878; }
.kpi-delta.neg { color: #ff4d6d; }
.kpi-delta.neu { color: #00aaff; }

/* ── Section titles ── */
.section-title {
    font-family: 'Syne', sans-serif;
    font-size: 0.85rem; font-weight: 700;
    color: #8898aa; letter-spacing: 0.1em;
    text-transform: uppercase; margin: 1.8rem 0 0.8rem 0;
    display: flex; align-items: center; gap: 0.5rem;
}
.section-title::after {
    content: ''; flex: 1; height: 1px;
    background: linear-gradient(90deg, rgba(255,255,255,0.07), transparent);
}

/* ── Sidebar brand ── */
.sidebar-brand { padding: 1.2rem 0 1rem 0; text-align: center; border-bottom: 1px solid rgba(0,200,120,0.1); margin-bottom: 1rem; }
.sidebar-brand-name { font-family: 'Syne', sans-serif; font-size: 1.05rem; font-weight: 800; color: #eef2f7 !important; letter-spacing: 0.04em; }
.sidebar-brand-tag  { font-size: 0.65rem; color: #00c878 !important; letter-spacing: 0.15em; text-transform: uppercase; margin-top: 2px; }

/* ── Plotly chart container ── */
.chart-container {
    background: rgba(255,255,255,0.02);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 6px; padding: 0.5rem 0.5rem 0 0.5rem;
    margin-bottom: 1rem;
}

/* ── Dataframe ── */
[data-testid="stDataFrame"] { border: 1px solid rgba(255,255,255,0.06) !important; border-radius: 6px !important; }
</style>
""", unsafe_allow_html=True)

# ----------------------------------------------------------
# DATABASE CONNECTION  (avec cache)
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
def load_market_data():
    query = """
        SELECT *
        FROM smartinvest.v_market_daily
        ORDER BY date_id
    """
    df = pd.read_sql(query, get_engine())
    df["date_id"] = pd.to_datetime(df["date_id"])
    return df

# ----------------------------------------------------------
# LOAD DATA
# ----------------------------------------------------------

with st.spinner("Loading market data…"):
    try:
        df = load_market_data()
        db_ok = True
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
        <div class="sidebar-brand-tag">Market Overview</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("**Asset**")
    ticker_list     = sorted(df["ticker"].unique())
    selected_ticker = st.selectbox("Select asset", ticker_list, label_visibility="collapsed")

    st.divider()

    st.markdown("**Date Range**")
    min_date = df["date_id"].min().date()
    max_date = df["date_id"].max().date()
    date_range = st.date_input(
        "Period",
        value=(max_date - timedelta(days=180), max_date),
        min_value=min_date,
        max_value=max_date,
        label_visibility="collapsed"
    )

    st.divider()

    st.markdown("**Chart Options**")
    show_ma     = st.toggle("Moving Averages (20 / 50)", value=True)
    show_volume = st.toggle("Show Volume", value=True)
    show_table  = st.toggle("Show Data Table", value=True)
    chart_type  = st.radio("Price chart type", ["Line", "Candlestick"], horizontal=True)

    st.divider()
    st.markdown("<span style='font-size:0.7rem;color:#2a3a4a;'>v1.0.0 — SmartInvest BI-AI</span>",
                unsafe_allow_html=True)

# ----------------------------------------------------------
# FILTER DATA
# ----------------------------------------------------------

fdf = df[df["ticker"] == selected_ticker].copy()

if len(date_range) == 2:
    start_d, end_d = pd.Timestamp(date_range[0]), pd.Timestamp(date_range[1])
    fdf = fdf[(fdf["date_id"] >= start_d) & (fdf["date_id"] <= end_d)]

fdf = fdf.sort_values("date_id").reset_index(drop=True)

if fdf.empty:
    st.warning("No data available for the selected filters.")
    st.stop()

# ----------------------------------------------------------
# KPI CALCULATIONS
# ----------------------------------------------------------

latest   = fdf.iloc[-1]
previous = fdf.iloc[-2] if len(fdf) > 1 else latest

price_chg      = latest["close"] - previous["close"]
price_chg_pct  = (price_chg / previous["close"] * 100) if previous["close"] else 0
period_return  = ((fdf["close"].iloc[-1] / fdf["close"].iloc[0]) - 1) * 100
avg_volume     = fdf["volume"].mean()
price_high     = fdf["close"].max()
price_low      = fdf["close"].min()
volatility     = fdf["close"].pct_change().std() * np.sqrt(252) * 100  # annualised

def fmt_vol(v):
    if v >= 1_000_000: return f"{v/1_000_000:.1f}M"
    if v >= 1_000:     return f"{v/1_000:.0f}K"
    return str(int(v))

# ----------------------------------------------------------
# PAGE HEADER
# ----------------------------------------------------------

st.markdown(f"""
<div class="page-header">
    <div class="page-badge">Market Overview</div>
    <h1 class="page-title">{selected_ticker}</h1>
    <p class="page-subtitle">
        {fdf["date_id"].min().strftime("%d %b %Y")} → {fdf["date_id"].max().strftime("%d %b %Y")}
        &nbsp;·&nbsp; {len(fdf)} trading sessions
    </p>
</div>
""", unsafe_allow_html=True)

# ----------------------------------------------------------
# KPI ROW
# ----------------------------------------------------------

pos_neg = lambda v: "pos" if v >= 0 else "neg"
up_down = lambda v: "up" if v >= 0 else "down"
arrow   = lambda v: "▲" if v >= 0 else "▼"

st.markdown(f"""
<div class="kpi-row">
  <div class="kpi-card {up_down(price_chg)}">
    <div class="kpi-label">Last Close</div>
    <div class="kpi-value">${latest["close"]:,.2f}</div>
    <div class="kpi-delta {pos_neg(price_chg)}">{arrow(price_chg)} {abs(price_chg_pct):.2f}% vs prev. close</div>
  </div>
  <div class="kpi-card {up_down(period_return)}">
    <div class="kpi-label">Period Return</div>
    <div class="kpi-value">{period_return:+.1f}%</div>
    <div class="kpi-delta {pos_neg(period_return)}">{arrow(period_return)} since {fdf["date_id"].iloc[0].strftime("%d %b %Y")}</div>
  </div>
  <div class="kpi-card neut">
    <div class="kpi-label">52-W Range</div>
    <div class="kpi-value">${price_low:,.2f} – ${price_high:,.2f}</div>
    <div class="kpi-delta neu">Period high / low</div>
  </div>
  <div class="kpi-card neut">
    <div class="kpi-label">Avg Volume</div>
    <div class="kpi-value">{fmt_vol(avg_volume)}</div>
    <div class="kpi-delta neu">Annualised vol. {volatility:.1f}%</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ----------------------------------------------------------
# MOVING AVERAGES
# ----------------------------------------------------------

if show_ma:
    fdf["MA20"] = fdf["close"].rolling(20).mean()
    fdf["MA50"] = fdf["close"].rolling(50).mean()

# ----------------------------------------------------------
# CHART THEME  (cohérent dark)
# ----------------------------------------------------------

CHART_BG    = "rgba(0,0,0,0)"
GRID_COLOR  = "rgba(255,255,255,0.05)"
FONT_COLOR  = "#5a6a80"
ACCENT      = "#00c878"

layout_base = dict(
    paper_bgcolor=CHART_BG,
    plot_bgcolor=CHART_BG,
    font=dict(family="DM Mono", color=FONT_COLOR, size=11),
    xaxis=dict(
        gridcolor=GRID_COLOR, zeroline=False,
        showspikes=True, spikecolor=ACCENT, spikemode="across",
        spikethickness=1, spikedash="dot"
    ),
    yaxis=dict(gridcolor=GRID_COLOR, zeroline=False),
    legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=11)),
    margin=dict(l=0, r=0, t=40, b=0),
    hovermode="x unified",
    hoverlabel=dict(bgcolor="#0d0f1a", font_color="#eef2f7", font_size=12, bordercolor=ACCENT),
)

# ----------------------------------------------------------
# PRICE CHART
# ----------------------------------------------------------

st.markdown('<div class="section-title">Price Evolution</div>', unsafe_allow_html=True)

st.markdown('<div class="chart-container">', unsafe_allow_html=True)

if chart_type == "Candlestick" and all(c in fdf.columns for c in ["open", "high", "low", "close"]):
    fig_price = go.Figure()
    fig_price.add_trace(go.Candlestick(
        x=fdf["date_id"],
        open=fdf["open"], high=fdf["high"],
        low=fdf["low"],  close=fdf["close"],
        name=selected_ticker,
        increasing_line_color=ACCENT,
        decreasing_line_color="#ff4d6d",
        increasing_fillcolor=ACCENT,
        decreasing_fillcolor="#ff4d6d",
    ))
else:
    fig_price = go.Figure()
    # Filled area
    fig_price.add_trace(go.Scatter(
        x=fdf["date_id"], y=fdf["close"],
        fill="tozeroy",
        fillcolor="rgba(0,200,120,0.06)",
        line=dict(color=ACCENT, width=2),
        name=selected_ticker,
        hovertemplate="<b>%{x|%d %b %Y}</b><br>Close: $%{y:,.2f}<extra></extra>"
    ))

if show_ma and "MA20" in fdf.columns:
    fig_price.add_trace(go.Scatter(
        x=fdf["date_id"], y=fdf["MA20"],
        line=dict(color="#00aaff", width=1.2, dash="dot"),
        name="MA 20", hovertemplate="MA20: $%{y:,.2f}<extra></extra>"
    ))
if show_ma and "MA50" in fdf.columns:
    fig_price.add_trace(go.Scatter(
        x=fdf["date_id"], y=fdf["MA50"],
        line=dict(color="#a78bfa", width=1.2, dash="dash"),
        name="MA 50", hovertemplate="MA50: $%{y:,.2f}<extra></extra>"
    ))

fig_price.update_layout(**layout_base, height=380,
    yaxis_title="Price (USD)",
    xaxis_rangeslider_visible=False)

st.plotly_chart(fig_price, use_container_width=True, config={"displayModeBar": False})
st.markdown('</div>', unsafe_allow_html=True)

# ----------------------------------------------------------
# VOLUME CHART
# ----------------------------------------------------------

if show_volume:
    st.markdown('<div class="section-title">Trading Volume</div>', unsafe_allow_html=True)

    avg_vol_line = fdf["volume"].mean()
    bar_colors   = [ACCENT if v >= avg_vol_line else "rgba(0,200,120,0.35)" for v in fdf["volume"]]

    fig_vol = go.Figure()
    fig_vol.add_trace(go.Bar(
        x=fdf["date_id"], y=fdf["volume"],
        marker_color=bar_colors,
        name="Volume",
        hovertemplate="<b>%{x|%d %b %Y}</b><br>Volume: %{y:,.0f}<extra></extra>"
    ))
    fig_vol.add_hline(
        y=avg_vol_line,
        line_dash="dot", line_color="#f59e0b",
        annotation_text=f"Avg {fmt_vol(avg_vol_line)}",
        annotation_font_color="#f59e0b",
        annotation_font_size=10
    )

    fig_vol.update_layout(**layout_base, height=220,
        yaxis_title="Volume", bargap=0.15)

    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    st.plotly_chart(fig_vol, use_container_width=True, config={"displayModeBar": False})
    st.markdown('</div>', unsafe_allow_html=True)

# ----------------------------------------------------------
# RETURN DISTRIBUTION  (bonus)
# ----------------------------------------------------------

fdf["daily_return"] = fdf["close"].pct_change() * 100
returns_clean = fdf["daily_return"].dropna()

st.markdown('<div class="section-title">Daily Return Distribution</div>', unsafe_allow_html=True)

fig_hist = go.Figure()
fig_hist.add_trace(go.Histogram(
    x=returns_clean,
    nbinsx=50,
    marker_color=ACCENT,
    marker_line_color="rgba(0,0,0,0.3)",
    marker_line_width=0.5,
    opacity=0.75,
    name="Daily returns",
    hovertemplate="Return: %{x:.2f}%<br>Count: %{y}<extra></extra>"
))
fig_hist.add_vline(x=0, line_dash="solid", line_color="rgba(255,255,255,0.15)")
fig_hist.add_vline(x=returns_clean.mean(), line_dash="dot", line_color="#f59e0b",
                   annotation_text=f"μ {returns_clean.mean():.2f}%",
                   annotation_font_color="#f59e0b", annotation_font_size=10)

fig_hist.update_layout(**layout_base, height=220,
    xaxis_title="Daily Return (%)", yaxis_title="Count")

st.markdown('<div class="chart-container">', unsafe_allow_html=True)
st.plotly_chart(fig_hist, use_container_width=True, config={"displayModeBar": False})
st.markdown('</div>', unsafe_allow_html=True)

# ----------------------------------------------------------
# DATA TABLE
# ----------------------------------------------------------

if show_table:
    st.markdown('<div class="section-title">Market Data — Last 50 Sessions</div>',
                unsafe_allow_html=True)

    display_cols = ["date_id", "open", "high", "low", "close", "volume"]
    available    = [c for c in display_cols if c in fdf.columns]
    tbl = fdf[available].tail(50).sort_values("date_id", ascending=False).copy()
    tbl["date_id"] = tbl["date_id"].dt.strftime("%Y-%m-%d")

    # Color close column
    st.dataframe(
        tbl,
        use_container_width=True,
        hide_index=True,
        column_config={
            "date_id": st.column_config.TextColumn("Date"),
            "open":    st.column_config.NumberColumn("Open",   format="$%.2f"),
            "high":    st.column_config.NumberColumn("High",   format="$%.2f"),
            "low":     st.column_config.NumberColumn("Low",    format="$%.2f"),
            "close":   st.column_config.NumberColumn("Close",  format="$%.2f"),
            "volume":  st.column_config.NumberColumn("Volume", format="%d"),
        }
    )