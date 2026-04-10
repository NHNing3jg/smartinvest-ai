# ==========================================================
# Page 4 — Energy Market Analysis
# SmartInvest BI-AI Dashboard
# ==========================================================

from __future__ import annotations
import os
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
from dotenv import load_dotenv
from sqlalchemy import create_engine
from datetime import timedelta

# ----------------------------------------------------------
# PAGE CONFIG
# ----------------------------------------------------------

st.set_page_config(
    page_title="Energy Market — SmartInvest",
    page_icon="🛢️",
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
        radial-gradient(ellipse 80% 50% at 50% -10%, rgba(245,158,11,0.10) 0%, transparent 70%),
        radial-gradient(ellipse 40% 30% at 90% 80%,  rgba(255,77,109,0.06) 0%, transparent 60%);
}
[data-testid="stSidebar"] {
    background: #0d0f1a !important;
    border-right: 1px solid rgba(245,158,11,0.18);
}

/* ── Page header ── */
.page-header { padding: 1.8rem 0 1rem 0; }
.page-badge {
    display: inline-block; font-size: 0.68rem; letter-spacing: 0.18em;
    text-transform: uppercase; color: #f59e0b;
    border: 1px solid rgba(245,158,11,0.3); border-radius: 2px;
    padding: 3px 12px; background: rgba(245,158,11,0.06); margin-bottom: 0.8rem;
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
.kpi-card.amber::after  { background: linear-gradient(90deg,#f59e0b,transparent); }
.kpi-card.green::after  { background: linear-gradient(90deg,#00c878,transparent); }
.kpi-card.red::after    { background: linear-gradient(90deg,#ff4d6d,transparent); }
.kpi-card.blue::after   { background: linear-gradient(90deg,#00aaff,transparent); }
.kpi-card.purple::after { background: linear-gradient(90deg,#a78bfa,transparent); }

.kpi-label { font-size: 0.65rem; letter-spacing: 0.12em; text-transform: uppercase; color: #3a4a5a; margin-bottom: 0.35rem; }
.kpi-value { font-family: 'Syne', sans-serif; font-size: 1.4rem; font-weight: 700; color: #eef2f7; }
.kpi-delta { font-size: 0.72rem; margin-top: 0.25rem; }
.kpi-delta.pos  { color: #00c878; }
.kpi-delta.neg  { color: #ff4d6d; }
.kpi-delta.neu  { color: #f59e0b; }
.kpi-delta.blue { color: #00aaff; }

/* ── Correlation badge ── */
.corr-badge {
    display: inline-flex; align-items: center; gap: 0.5rem;
    font-family: 'Syne', sans-serif; font-size: 2rem; font-weight: 800;
}
.corr-label { font-size: 0.65rem; color: #3a4a5a; text-transform: uppercase; letter-spacing: 0.1em; }

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

/* ── Correlation meter ── */
.corr-meter-wrap {
    background: rgba(255,255,255,0.02);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 6px; padding: 1.2rem 1.5rem;
    display: flex; align-items: center; gap: 2rem; flex-wrap: wrap;
}
.corr-bar-track {
    flex: 1; min-width: 200px; height: 6px;
    background: rgba(255,255,255,0.07); border-radius: 3px; position: relative;
}
.corr-bar-fill { height: 100%; border-radius: 3px; transition: width .4s; }
.corr-bar-zero {
    position: absolute; top: -4px; left: 50%;
    width: 1px; height: 14px; background: rgba(255,255,255,0.2);
}

/* ── Sidebar brand ── */
.sidebar-brand { padding: 1.2rem 0 1rem 0; text-align: center; border-bottom: 1px solid rgba(245,158,11,0.12); margin-bottom: 1rem; }
.sidebar-brand-name { font-family: 'Syne', sans-serif; font-size: 1.05rem; font-weight: 800; color: #eef2f7 !important; }
.sidebar-brand-tag  { font-size: 0.65rem; color: #f59e0b !important; letter-spacing: 0.15em; text-transform: uppercase; }
</style>
""", unsafe_allow_html=True)

# ----------------------------------------------------------
# DATABASE
# ----------------------------------------------------------

@st.cache_resource(show_spinner=False)
def get_engine():
    load_dotenv()
    url = (
        f"postgresql+psycopg2://"
        f"{os.getenv('DB_USER','postgres')}:{os.getenv('DB_PASSWORD','')}@"
        f"{os.getenv('DB_HOST','localhost')}:{os.getenv('DB_PORT','5432')}/"
        f"{os.getenv('DB_NAME','smartinvest_dw')}"
    )
    return create_engine(url)

@st.cache_data(ttl=300, show_spinner=False)
def load_oil_data():
    df = pd.read_sql(
        "SELECT date_id, ticker, close, daily_return FROM smartinvest.v_oil_daily ORDER BY date_id",
        get_engine()
    )
    df["date_id"] = pd.to_datetime(df["date_id"])
    return df

@st.cache_data(ttl=300, show_spinner=False)
def load_market_returns():
    df = pd.read_sql(
        "SELECT date_id, ticker, daily_return FROM smartinvest.v_market_returns_daily ORDER BY date_id",
        get_engine()
    )
    df["date_id"] = pd.to_datetime(df["date_id"])
    return df

# ----------------------------------------------------------
# LOAD DATA
# ----------------------------------------------------------

with st.spinner("Loading energy data…"):
    try:
        oil_df    = load_oil_data()
        market_df = load_market_returns()
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
        <div class="sidebar-brand-tag">Energy Market</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("**Oil Series**")
    oil_ticker = st.selectbox("Oil series", sorted(oil_df["ticker"].dropna().unique()),
                               label_visibility="collapsed")

    st.markdown("**Asset**")
    asset_ticker = st.selectbox("Asset", sorted(market_df["ticker"].dropna().unique()),
                                 label_visibility="collapsed")

    st.divider()

    st.markdown("**Period**")
    min_date   = oil_df["date_id"].min().date()
    max_date   = oil_df["date_id"].max().date()
    date_range = st.date_input(
        "Period",
        value=(max_date - timedelta(days=365 * 2), max_date),
        min_value=min_date, max_value=max_date,
        label_visibility="collapsed"
    )

    st.divider()

    corr_window  = st.slider("Rolling correlation window (days)", 10, 90, 30, step=5)
    show_scatter = st.toggle("Show Scatter Plot",      value=True)
    show_table   = st.toggle("Show Data Table",        value=False)

    st.divider()
    st.markdown("<span style='font-size:0.7rem;color:#2a3a4a;'>v1.0.0 — SmartInvest BI-AI</span>",
                unsafe_allow_html=True)

# ----------------------------------------------------------
# FILTER & MERGE
# ----------------------------------------------------------

if len(date_range) == 2:
    s, e = pd.Timestamp(date_range[0]), pd.Timestamp(date_range[1])
    oil_sel    = oil_df[(oil_df["ticker"] == oil_ticker)    & (oil_df["date_id"] >= s)    & (oil_df["date_id"] <= e)].copy()
    market_sel = market_df[(market_df["ticker"] == asset_ticker) & (market_df["date_id"] >= s) & (market_df["date_id"] <= e)].copy()
else:
    oil_sel    = oil_df[oil_df["ticker"] == oil_ticker].copy()
    market_sel = market_df[market_df["ticker"] == asset_ticker].copy()

merged = pd.merge(
    oil_sel[["date_id", "close", "daily_return"]],
    market_sel[["date_id", "daily_return"]],
    on="date_id", how="inner", suffixes=("_oil", "_asset")
).sort_values("date_id").reset_index(drop=True)

if merged.empty:
    st.warning("No common data between the selected oil series and asset.")
    st.stop()

merged["rolling_corr"] = (
    merged["daily_return_oil"].rolling(corr_window).corr(merged["daily_return_asset"])
)

# ----------------------------------------------------------
# KPI CALCULATIONS
# ----------------------------------------------------------

global_corr    = merged["daily_return_oil"].corr(merged["daily_return_asset"])
latest_corr    = merged["rolling_corr"].dropna().iloc[-1] if not merged["rolling_corr"].dropna().empty else np.nan
oil_last       = oil_sel["close"].iloc[-1]
oil_prev       = oil_sel["close"].iloc[-2] if len(oil_sel) > 1 else oil_last
oil_chg_pct    = (oil_last - oil_prev) / abs(oil_prev) * 100 if oil_prev else 0
oil_period_ret = ((oil_last / oil_sel["close"].iloc[0]) - 1) * 100 if oil_sel["close"].iloc[0] else 0
oil_vol        = merged["daily_return_oil"].std() * np.sqrt(252) * 100

# Correlation colour
def corr_color(c):
    if pd.isna(c): return "#8898aa"
    if c >  0.5: return "#00c878"
    if c >  0.2: return "#f59e0b"
    if c < -0.5: return "#ff4d6d"
    if c < -0.2: return "#a78bfa"
    return "#8898aa"

def corr_label(c):
    if pd.isna(c): return "N/A"
    if c >  0.7: return "Strong Positive"
    if c >  0.3: return "Moderate Positive"
    if c < -0.7: return "Strong Negative"
    if c < -0.3: return "Moderate Negative"
    return "Weak / Uncorrelated"

sign    = lambda v: "pos" if v >= 0 else "neg"
arrow   = lambda v: "▲" if v >= 0 else "▼"
up_down = lambda v: "green" if v >= 0 else "red"

# ----------------------------------------------------------
# CHART THEME
# ----------------------------------------------------------

CHART_BG   = "rgba(0,0,0,0)"
GRID_COLOR = "rgba(255,255,255,0.05)"
FONT_COLOR = "#5a6a80"
AMBER      = "#f59e0b"
GREEN      = "#00c878"
RED        = "#ff4d6d"
BLUE       = "#00aaff"
PURPLE     = "#a78bfa"

layout_base = dict(
    paper_bgcolor=CHART_BG, plot_bgcolor=CHART_BG,
    font=dict(family="DM Mono", color=FONT_COLOR, size=11),
    xaxis=dict(gridcolor=GRID_COLOR, zeroline=False,
               showspikes=True, spikecolor=AMBER, spikemode="across",
               spikethickness=1, spikedash="dot"),
    yaxis=dict(gridcolor=GRID_COLOR, zeroline=False),
    legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=11)),
    margin=dict(l=0, r=0, t=40, b=0),
    hovermode="x unified",
    hoverlabel=dict(bgcolor="#0d0f1a", font_color="#eef2f7", font_size=12, bordercolor=AMBER),
)

# ----------------------------------------------------------
# PAGE HEADER
# ----------------------------------------------------------

st.markdown(f"""
<div class="page-header">
    <div class="page-badge">🛢️ Energy Market</div>
    <h1 class="page-title">{oil_ticker} <span style="color:#3a4a5a;font-size:1.4rem;">×</span> {asset_ticker}</h1>
    <p class="page-subtitle">
        {merged["date_id"].min().strftime("%d %b %Y")} → {merged["date_id"].max().strftime("%d %b %Y")}
        &nbsp;·&nbsp; {len(merged)} common sessions
    </p>
</div>
""", unsafe_allow_html=True)

# ----------------------------------------------------------
# KPI ROW
# ----------------------------------------------------------

cc = corr_color(global_corr)
cl = corr_label(global_corr)

st.markdown(f"""
<div class="kpi-row">
  <div class="kpi-card {up_down(oil_chg_pct)}">
    <div class="kpi-label">Oil Last Close</div>
    <div class="kpi-value">${oil_last:,.2f}</div>
    <div class="kpi-delta {sign(oil_chg_pct)}">{arrow(oil_chg_pct)} {abs(oil_chg_pct):.2f}% vs prev.</div>
  </div>
  <div class="kpi-card {up_down(oil_period_ret)}">
    <div class="kpi-label">Oil Period Return</div>
    <div class="kpi-value">{oil_period_ret:+.1f}%</div>
    <div class="kpi-delta {sign(oil_period_ret)}">{arrow(oil_period_ret)} since {oil_sel['date_id'].iloc[0].strftime('%d %b %Y')}</div>
  </div>
  <div class="kpi-card amber">
    <div class="kpi-label">Oil Volatility</div>
    <div class="kpi-value">{oil_vol:.1f}%</div>
    <div class="kpi-delta neu">Annualised σ</div>
  </div>
  <div class="kpi-card blue">
    <div class="kpi-label">Global Correlation</div>
    <div class="kpi-value" style="color:{cc};">{global_corr:.3f}</div>
    <div class="kpi-delta blue">{cl}</div>
  </div>
  <div class="kpi-card blue">
    <div class="kpi-label">Latest {corr_window}d Corr.</div>
    <div class="kpi-value" style="color:{corr_color(latest_corr)};">{f"{latest_corr:.3f}" if pd.notna(latest_corr) else "N/A"}</div>
    <div class="kpi-delta blue">{corr_label(latest_corr)}</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ----------------------------------------------------------
# OIL PRICE EVOLUTION
# ----------------------------------------------------------

st.markdown('<div class="section-title">Oil Price Evolution</div>', unsafe_allow_html=True)

oil_sorted = oil_sel.sort_values("date_id")
fig_oil = go.Figure()
fig_oil.add_trace(go.Scatter(
    x=oil_sorted["date_id"], y=oil_sorted["close"],
    fill="tozeroy", fillcolor="rgba(245,158,11,0.07)",
    line=dict(color=AMBER, width=2),
    name=oil_ticker,
    hovertemplate="<b>%{x|%d %b %Y}</b><br>Price: $%{y:,.2f}<extra></extra>"
))

# 30d moving average
ma30 = oil_sorted["close"].rolling(30).mean()
fig_oil.add_trace(go.Scatter(
    x=oil_sorted["date_id"], y=ma30,
    line=dict(color="rgba(245,158,11,0.4)", width=1.2, dash="dot"),
    name="MA 30", hovertemplate="MA30: $%{y:,.2f}<extra></extra>"
))

fig_oil.update_layout(**layout_base, height=320, yaxis_title="Price (USD)",
                       xaxis_rangeslider_visible=False)

st.markdown('<div class="chart-container">', unsafe_allow_html=True)
st.plotly_chart(fig_oil, use_container_width=True, config={"displayModeBar": False})
st.markdown('</div>', unsafe_allow_html=True)

# ----------------------------------------------------------
# DAILY RETURNS COMPARISON
# ----------------------------------------------------------

st.markdown('<div class="section-title">Daily Returns Comparison</div>', unsafe_allow_html=True)

fig_ret = go.Figure()
fig_ret.add_trace(go.Scatter(
    x=merged["date_id"], y=merged["daily_return_oil"] * 100,
    line=dict(color=AMBER, width=1.5),
    name=f"{oil_ticker}",
    hovertemplate=f"<b>{oil_ticker}</b>: %{{y:+.2f}}%<extra></extra>"
))
fig_ret.add_trace(go.Scatter(
    x=merged["date_id"], y=merged["daily_return_asset"] * 100,
    line=dict(color=BLUE, width=1.5, dash="dot"),
    name=f"{asset_ticker}",
    hovertemplate=f"<b>{asset_ticker}</b>: %{{y:+.2f}}%<extra></extra>"
))
fig_ret.add_hline(y=0, line_color="rgba(255,255,255,0.08)")
fig_ret.update_layout(**layout_base, height=280, yaxis_title="Daily Return (%)")

st.markdown('<div class="chart-container">', unsafe_allow_html=True)
st.plotly_chart(fig_ret, use_container_width=True, config={"displayModeBar": False})
st.markdown('</div>', unsafe_allow_html=True)

# ----------------------------------------------------------
# ROLLING CORRELATION
# ----------------------------------------------------------

st.markdown(f'<div class="section-title">Rolling {corr_window}-Day Correlation</div>',
            unsafe_allow_html=True)

corr_clean = merged.dropna(subset=["rolling_corr"])
corr_colors_fill = [
    "rgba(0,200,120,0.12)" if v >= 0 else "rgba(255,77,109,0.10)"
    for v in corr_clean["rolling_corr"]
]

fig_corr = go.Figure()

# Positive zone
fig_corr.add_hrect(y0=0, y1=1,   fillcolor="rgba(0,200,120,0.03)", line_width=0)
fig_corr.add_hrect(y0=-1, y1=0,  fillcolor="rgba(255,77,109,0.03)", line_width=0)

# Strong correlation bands
fig_corr.add_hrect(y0=0.5,  y1=1,  fillcolor="rgba(0,200,120,0.04)", line_width=0,
                   annotation_text="Strong +", annotation_position="top right",
                   annotation_font_color="#2a4a3a", annotation_font_size=9)
fig_corr.add_hrect(y0=-1,  y1=-0.5, fillcolor="rgba(255,77,109,0.04)", line_width=0,
                   annotation_text="Strong −", annotation_position="bottom right",
                   annotation_font_color="#4a2a3a", annotation_font_size=9)

fig_corr.add_trace(go.Scatter(
    x=corr_clean["date_id"], y=corr_clean["rolling_corr"],
    fill="tozeroy",
    fillcolor="rgba(245,158,11,0.06)",
    line=dict(color=AMBER, width=2),
    name=f"Corr {corr_window}d",
    hovertemplate="<b>%{x|%d %b %Y}</b><br>Correlation: %{y:.3f}<extra></extra>"
))
fig_corr.add_hline(y=0, line_color="rgba(255,255,255,0.15)", line_width=1)
fig_corr.add_hline(y=global_corr, line_dash="dot", line_color="rgba(245,158,11,0.4)",
                   annotation_text=f"Global avg {global_corr:.3f}",
                   annotation_font_color="#6a5a2a", annotation_font_size=10,
                   annotation_position="top left")

fig_corr.update_layout(**layout_base, height=300, yaxis_title="Correlation")
fig_corr.update_yaxes(range=[-1.05, 1.05], tickvals=[-1, -0.5, 0, 0.5, 1])

st.markdown('<div class="chart-container">', unsafe_allow_html=True)
st.plotly_chart(fig_corr, use_container_width=True, config={"displayModeBar": False})
st.markdown('</div>', unsafe_allow_html=True)

# ----------------------------------------------------------
# SCATTER PLOT  (oil return vs asset return)
# ----------------------------------------------------------

if show_scatter:
    st.markdown(f'<div class="section-title">Return Scatter — {oil_ticker} vs {asset_ticker}</div>',
                unsafe_allow_html=True)

    x_vals = merged["daily_return_oil"].dropna() * 100
    y_vals = merged["daily_return_asset"].dropna() * 100
    common = merged.dropna(subset=["daily_return_oil", "daily_return_asset"])

    # Regression line
    if len(common) > 2:
        coef   = np.polyfit(common["daily_return_oil"], common["daily_return_asset"], 1)
        x_line = np.linspace(common["daily_return_oil"].min(), common["daily_return_oil"].max(), 100)
        y_line = np.polyval(coef, x_line)

    fig_sc = go.Figure()
    fig_sc.add_trace(go.Scatter(
        x=common["daily_return_oil"] * 100,
        y=common["daily_return_asset"] * 100,
        mode="markers",
        marker=dict(color=AMBER, size=4, opacity=0.5,
                    line=dict(color="rgba(0,0,0,0.2)", width=0.5)),
        name="Daily sessions",
        hovertemplate=(
            f"<b>%{{x:.2f}}%</b> {oil_ticker}<br>"
            f"<b>%{{y:.2f}}%</b> {asset_ticker}<extra></extra>"
        )
    ))

    if len(common) > 2:
        fig_sc.add_trace(go.Scatter(
            x=x_line * 100, y=y_line * 100,
            mode="lines",
            line=dict(color=RED, width=1.5, dash="dot"),
            name=f"Regression (β={coef[0]:.2f})",
            hoverinfo="skip"
        ))

    fig_sc.add_hline(y=0, line_color="rgba(255,255,255,0.08)")
    fig_sc.add_vline(x=0, line_color="rgba(255,255,255,0.08)")
    fig_sc.update_layout(
        **layout_base, height=380,
        xaxis_title=f"{oil_ticker} Daily Return (%)",
        yaxis_title=f"{asset_ticker} Daily Return (%)",
    )
    fig_sc.update_layout(hovermode="closest")
    fig_sc.update_xaxes(showspikes=False)

    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    st.plotly_chart(fig_sc, use_container_width=True, config={"displayModeBar": False})
    st.markdown('</div>', unsafe_allow_html=True)

    if len(common) > 2:
        st.caption(
            f"β = {coef[0]:.3f} — a 1% move in {oil_ticker} is associated with a "
            f"{coef[0]:.3f}% move in {asset_ticker} &nbsp;·&nbsp; "
            f"R² = {global_corr**2:.3f}"
        )

# ----------------------------------------------------------
# DATA TABLE
# ----------------------------------------------------------

if show_table:
    st.markdown('<div class="section-title">Merged Data — Last 30 Sessions</div>',
                unsafe_allow_html=True)

    tbl = merged[["date_id", "close", "daily_return_oil", "daily_return_asset", "rolling_corr"]]\
        .tail(30).sort_values("date_id", ascending=False).copy()
    tbl["date_id"]            = tbl["date_id"].dt.strftime("%Y-%m-%d")
    tbl["daily_return_oil"]   *= 100
    tbl["daily_return_asset"] *= 100

    st.dataframe(
        tbl,
        use_container_width=True,
        hide_index=True,
        column_config={
            "date_id":            st.column_config.TextColumn("Date"),
            "close":              st.column_config.NumberColumn("Oil Close",       format="$%.2f"),
            "daily_return_oil":   st.column_config.NumberColumn(f"{oil_ticker} Ret (%)",   format="%.2f"),
            "daily_return_asset": st.column_config.NumberColumn(f"{asset_ticker} Ret (%)", format="%.2f"),
            "rolling_corr":       st.column_config.NumberColumn(f"Corr {corr_window}d",   format="%.3f"),
        }
    )