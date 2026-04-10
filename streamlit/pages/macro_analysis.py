# ==========================================================
# Page 3 — Macro Analysis
# SmartInvest BI-AI Dashboard
# ==========================================================

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
from sqlalchemy import create_engine
from datetime import timedelta

# ----------------------------------------------------------
# PAGE CONFIG
# ----------------------------------------------------------

st.set_page_config(
    page_title="Macro Analysis — SmartInvest",
    page_icon="🌐",
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
        radial-gradient(ellipse 80% 50% at 50% -10%, rgba(0,170,255,0.09) 0%, transparent 70%),
        radial-gradient(ellipse 40% 30% at 85% 85%, rgba(245,158,11,0.06) 0%, transparent 60%);
}
[data-testid="stSidebar"] {
    background: #0d0f1a !important;
    border-right: 1px solid rgba(0,170,255,0.15);
}

/* ── Page header ── */
.page-header { padding: 1.8rem 0 1rem 0; }
.page-badge {
    display: inline-block; font-size: 0.68rem; letter-spacing: 0.18em;
    text-transform: uppercase; color: #00aaff;
    border: 1px solid rgba(0,170,255,0.3); border-radius: 2px;
    padding: 3px 12px; background: rgba(0,170,255,0.06); margin-bottom: 0.8rem;
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
.kpi-card.blue::after   { background: linear-gradient(90deg,#00aaff,transparent); }
.kpi-card.green::after  { background: linear-gradient(90deg,#00c878,transparent); }
.kpi-card.red::after    { background: linear-gradient(90deg,#ff4d6d,transparent); }
.kpi-card.amber::after  { background: linear-gradient(90deg,#f59e0b,transparent); }
.kpi-card.purple::after { background: linear-gradient(90deg,#a78bfa,transparent); }

.kpi-label { font-size: 0.65rem; letter-spacing: 0.12em; text-transform: uppercase; color: #3a4a5a; margin-bottom: 0.35rem; }
.kpi-value { font-family: 'Syne', sans-serif; font-size: 1.4rem; font-weight: 700; color: #eef2f7; }
.kpi-delta { font-size: 0.72rem; margin-top: 0.25rem; }
.kpi-delta.pos { color: #00c878; }
.kpi-delta.neg { color: #ff4d6d; }
.kpi-delta.neu { color: #00aaff; }

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
.sidebar-brand { padding: 1.2rem 0 1rem 0; text-align: center; border-bottom: 1px solid rgba(0,170,255,0.1); margin-bottom: 1rem; }
.sidebar-brand-name { font-family: 'Syne', sans-serif; font-size: 1.05rem; font-weight: 800; color: #eef2f7 !important; }
.sidebar-brand-tag  { font-size: 0.65rem; color: #00aaff !important; letter-spacing: 0.15em; text-transform: uppercase; }

/* ── Indicator pill ── */
.indicator-pill {
    display: inline-block; font-size: 0.68rem; letter-spacing: 0.1em;
    padding: 2px 10px; border-radius: 20px; margin-right: 6px; margin-bottom: 4px;
    font-weight: 500;
}
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
    return create_engine(DATABASE_URL, connect_args={"client_encoding": "utf8"})

@st.cache_data(ttl=300, show_spinner=False)
def load_macro():
    df = pd.read_sql(
        "SELECT * FROM smartinvest.v_macro_daily ORDER BY date_id",
        get_engine()
    )
    df["date_id"] = pd.to_datetime(df["date_id"])
    return df

# ----------------------------------------------------------
# LOAD DATA
# ----------------------------------------------------------

with st.spinner("Loading macro data…"):
    try:
        macro_df = load_macro()
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
        <div class="sidebar-brand-tag">Macro Analysis</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("**Indicator**")
    series_list     = sorted(macro_df["series_id"].unique())
    selected_series = st.selectbox("Indicator", series_list, label_visibility="collapsed")

    st.divider()

    st.markdown("**Compare Indicators**")
    compare_series = st.multiselect(
        "Add indicators",
        [s for s in series_list if s != selected_series],
        default=[],
        label_visibility="collapsed",
        max_selections=4,
        placeholder="Add indicators…"
    )

    st.divider()

    st.markdown("**Period**")
    min_date   = macro_df["date_id"].min().date()
    max_date   = macro_df["date_id"].max().date()
    date_range = st.date_input(
        "Period",
        value=(max_date - timedelta(days=365 * 3), max_date),
        min_value=min_date, max_value=max_date,
        label_visibility="collapsed"
    )

    st.divider()

    show_yoy   = st.toggle("Show YoY Change",      value=True)
    show_norm  = st.toggle("Show Normalised Chart", value=False)
    show_table = st.toggle("Show Data Table",       value=True)

    st.divider()
    st.markdown("<span style='font-size:0.7rem;color:#2a3a4a;'>v1.0.0 — SmartInvest BI-AI</span>",
                unsafe_allow_html=True)

# ----------------------------------------------------------
# FILTER
# ----------------------------------------------------------

if len(date_range) == 2:
    s, e = pd.Timestamp(date_range[0]), pd.Timestamp(date_range[1])
    mdf  = macro_df[(macro_df["date_id"] >= s) & (macro_df["date_id"] <= e)]
else:
    mdf  = macro_df.copy()

fdf = mdf[mdf["series_id"] == selected_series].sort_values("date_id").reset_index(drop=True)

if fdf.empty:
    st.warning("No data available for the selected filters.")
    st.stop()

# ----------------------------------------------------------
# KPI CALCULATIONS
# ----------------------------------------------------------

latest_val   = fdf["value"].iloc[-1]
prev_val     = fdf["value"].iloc[-2]  if len(fdf) > 1 else latest_val
first_val    = fdf["value"].iloc[0]
chg_abs      = latest_val - prev_val
chg_pct      = (chg_abs / abs(prev_val) * 100) if prev_val else 0
period_chg   = ((latest_val - first_val) / abs(first_val) * 100) if first_val else 0
mean_val     = fdf["value"].mean()
std_val      = fdf["value"].std()
min_val      = fdf["value"].min()
max_val      = fdf["value"].max()

# YoY
fdf_sorted   = fdf.sort_values("date_id")
fdf_yoy      = fdf_sorted.copy()
fdf_yoy["yoy"] = fdf_yoy["value"].pct_change(periods=252) * 100  # ~252 trading days

sign    = lambda v: "pos" if v >= 0 else "neg"
arrow   = lambda v: "▲" if v >= 0 else "▼"
up_down = lambda v: "green" if v >= 0 else "red"

# Try to detect unit from series name
unit = ""
sid_lower = selected_series.lower()
if "rate" in sid_lower or "yield" in sid_lower or "cpi" in sid_lower or "gdp" in sid_lower:
    unit = "%"
elif "index" in sid_lower or "idx" in sid_lower:
    unit = " pts"

def fmt(v):
    return f"{v:,.2f}{unit}"

# ----------------------------------------------------------
# CHART THEME
# ----------------------------------------------------------

CHART_BG   = "rgba(0,0,0,0)"
GRID_COLOR = "rgba(255,255,255,0.05)"
FONT_COLOR = "#5a6a80"
BLUE       = "#00aaff"
GREEN      = "#00c878"
RED        = "#ff4d6d"
AMBER      = "#f59e0b"
PURPLE     = "#a78bfa"
PALETTE    = [BLUE, GREEN, PURPLE, AMBER, "#f97316"]

layout_base = dict(
    paper_bgcolor=CHART_BG, plot_bgcolor=CHART_BG,
    font=dict(family="DM Mono", color=FONT_COLOR, size=11),
    xaxis=dict(gridcolor=GRID_COLOR, zeroline=False,
               showspikes=True, spikecolor=BLUE, spikemode="across",
               spikethickness=1, spikedash="dot"),
    yaxis=dict(gridcolor=GRID_COLOR, zeroline=False),
    legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=11)),
    margin=dict(l=0, r=0, t=40, b=0),
    hovermode="x unified",
    hoverlabel=dict(bgcolor="#0d0f1a", font_color="#eef2f7", font_size=12, bordercolor=BLUE),
)

# ----------------------------------------------------------
# PAGE HEADER
# ----------------------------------------------------------

st.markdown(f"""
<div class="page-header">
    <div class="page-badge">Macro Analysis</div>
    <h1 class="page-title">{selected_series}</h1>
    <p class="page-subtitle">
        {fdf["date_id"].min().strftime("%d %b %Y")} → {fdf["date_id"].max().strftime("%d %b %Y")}
        &nbsp;·&nbsp; {len(fdf)} observations
    </p>
</div>
""", unsafe_allow_html=True)

# ----------------------------------------------------------
# KPI ROW
# ----------------------------------------------------------

st.markdown(f"""
<div class="kpi-row">
  <div class="kpi-card {up_down(chg_abs)}">
    <div class="kpi-label">Latest Value</div>
    <div class="kpi-value">{fmt(latest_val)}</div>
    <div class="kpi-delta {sign(chg_abs)}">{arrow(chg_abs)} {abs(chg_pct):.2f}% vs prev. obs.</div>
  </div>
  <div class="kpi-card {up_down(period_chg)}">
    <div class="kpi-label">Period Change</div>
    <div class="kpi-value">{period_chg:+.1f}%</div>
    <div class="kpi-delta {sign(period_chg)}">{arrow(period_chg)} since {fdf['date_id'].iloc[0].strftime('%d %b %Y')}</div>
  </div>
  <div class="kpi-card blue">
    <div class="kpi-label">Period Mean</div>
    <div class="kpi-value">{fmt(mean_val)}</div>
    <div class="kpi-delta neu">σ = {std_val:.2f}{unit}</div>
  </div>
  <div class="kpi-card amber">
    <div class="kpi-label">Range</div>
    <div class="kpi-value">{fmt(min_val)} – {fmt(max_val)}</div>
    <div class="kpi-delta neu">Period low / high</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ----------------------------------------------------------
# MAIN INDICATOR CHART
# ----------------------------------------------------------

st.markdown('<div class="section-title">Indicator Evolution</div>', unsafe_allow_html=True)

fig_main = go.Figure()

# Mean band
fig_main.add_hrect(
    y0=mean_val - std_val, y1=mean_val + std_val,
    fillcolor="rgba(0,170,255,0.04)", line_width=0,
    annotation_text="±1σ", annotation_position="top right",
    annotation_font_color="#3a4a5a", annotation_font_size=10
)
fig_main.add_hline(
    y=mean_val, line_dash="dot", line_color="rgba(0,170,255,0.3)",
    annotation_text=f"μ {fmt(mean_val)}",
    annotation_font_color="#3a4a5a", annotation_font_size=10,
    annotation_position="bottom right"
)

# Main series
fig_main.add_trace(go.Scatter(
    x=fdf["date_id"], y=fdf["value"],
    fill="tozeroy", fillcolor="rgba(0,170,255,0.06)",
    line=dict(color=BLUE, width=2),
    name=selected_series,
    hovertemplate=f"<b>%{{x|%d %b %Y}}</b><br>{selected_series}: %{{y:,.2f}}{unit}<extra></extra>"
))

fig_main.update_layout(**layout_base, height=360,
                        yaxis_title=f"Value{' (' + unit.strip() + ')' if unit.strip() else ''}")

st.markdown('<div class="chart-container">', unsafe_allow_html=True)
st.plotly_chart(fig_main, use_container_width=True, config={"displayModeBar": False})
st.markdown('</div>', unsafe_allow_html=True)

# ----------------------------------------------------------
# YoY CHANGE
# ----------------------------------------------------------

if show_yoy:
    yoy_clean = fdf_yoy.dropna(subset=["yoy"])
    if not yoy_clean.empty:
        st.markdown('<div class="section-title">Year-over-Year Change</div>', unsafe_allow_html=True)

        bar_colors = [GREEN if v >= 0 else RED for v in yoy_clean["yoy"]]

        fig_yoy = go.Figure()
        fig_yoy.add_trace(go.Bar(
            x=yoy_clean["date_id"], y=yoy_clean["yoy"],
            marker_color=bar_colors,
            name="YoY %",
            hovertemplate="<b>%{x|%d %b %Y}</b><br>YoY: %{y:+.2f}%<extra></extra>"
        ))
        fig_yoy.add_hline(y=0, line_color="rgba(255,255,255,0.1)")
        fig_yoy.update_layout(**layout_base, height=240,
                               yaxis_title="YoY Change (%)", bargap=0.1)

        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.plotly_chart(fig_yoy, use_container_width=True, config={"displayModeBar": False})
        st.markdown('</div>', unsafe_allow_html=True)

# ----------------------------------------------------------
# MULTI-INDICATOR COMPARISON
# ----------------------------------------------------------

all_series = [selected_series] + list(compare_series)

if len(all_series) > 1 or compare_series:
    st.markdown('<div class="section-title">Indicators Comparison</div>', unsafe_allow_html=True)

    if show_norm:
        # Normalised 0–100
        fig_comp = go.Figure()
        for i, sid in enumerate(all_series):
            sub = mdf[mdf["series_id"] == sid].sort_values("date_id")
            if sub.empty:
                continue
            vmin, vmax = sub["value"].min(), sub["value"].max()
            norm = (sub["value"] - vmin) / (vmax - vmin) * 100 if vmax != vmin else sub["value"] * 0
            fig_comp.add_trace(go.Scatter(
                x=sub["date_id"], y=norm,
                name=sid,
                line=dict(color=PALETTE[i % len(PALETTE)], width=2 if i == 0 else 1.5,
                          dash="solid" if i == 0 else "dot"),
                hovertemplate=f"<b>{sid}</b> (norm): %{{y:.1f}}<extra></extra>"
            ))
        fig_comp.update_layout(**layout_base, height=320, yaxis_title="Normalised (0–100)")
        note = "📐 Values normalised to 0–100 for comparability"
    else:
        # Dual-axis if only 2 series, else same axis
        fig_comp = go.Figure()
        for i, sid in enumerate(all_series):
            sub = mdf[mdf["series_id"] == sid].sort_values("date_id")
            if sub.empty:
                continue
            fig_comp.add_trace(go.Scatter(
                x=sub["date_id"], y=sub["value"],
                name=sid,
                line=dict(color=PALETTE[i % len(PALETTE)], width=2 if i == 0 else 1.5,
                          dash="solid" if i == 0 else "dot"),
                yaxis="y2" if (i == 1 and len(all_series) == 2) else "y",
                hovertemplate=f"<b>{sid}</b>: %{{y:,.2f}}<extra></extra>"
            ))
        layout_extra = {}
        if len(all_series) == 2:
            layout_extra = dict(
                yaxis2=dict(overlaying="y", side="right",
                            gridcolor="rgba(0,0,0,0)", zeroline=False,
                            tickfont=dict(color=PALETTE[1]))
            )
        fig_comp.update_layout(**layout_base, height=320, **layout_extra)
        note = "💡 Enable 'Normalised Chart' in sidebar to compare different scales"

    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    st.plotly_chart(fig_comp, use_container_width=True, config={"displayModeBar": False})
    st.markdown('</div>', unsafe_allow_html=True)
    st.caption(note)

elif not compare_series:
    st.markdown('<div class="section-title">Indicators Comparison</div>', unsafe_allow_html=True)
    st.info("Select additional indicators in the sidebar to compare them.", icon="ℹ️")

# ----------------------------------------------------------
# ROLLING STATS  (30-day rolling mean + std)
# ----------------------------------------------------------

st.markdown('<div class="section-title">Rolling Statistics (30-day)</div>', unsafe_allow_html=True)

fdf["roll_mean"] = fdf["value"].rolling(30).mean()
fdf["roll_std"]  = fdf["value"].rolling(30).std()
fdf["upper"]     = fdf["roll_mean"] + fdf["roll_std"]
fdf["lower"]     = fdf["roll_mean"] - fdf["roll_std"]

fig_roll = go.Figure()

# Confidence band
fig_roll.add_trace(go.Scatter(
    x=pd.concat([fdf["date_id"], fdf["date_id"][::-1]]),
    y=pd.concat([fdf["upper"], fdf["lower"][::-1]]),
    fill="toself", fillcolor="rgba(0,170,255,0.07)",
    line=dict(color="rgba(0,0,0,0)"),
    showlegend=True, name="±1σ band",
    hoverinfo="skip"
))
# Rolling mean
fig_roll.add_trace(go.Scatter(
    x=fdf["date_id"], y=fdf["roll_mean"],
    line=dict(color=BLUE, width=2),
    name="30d Rolling Mean",
    hovertemplate="<b>%{x|%d %b %Y}</b><br>Mean: %{y:,.2f}<extra></extra>"
))
# Raw
fig_roll.add_trace(go.Scatter(
    x=fdf["date_id"], y=fdf["value"],
    line=dict(color="rgba(0,170,255,0.3)", width=1),
    name=selected_series,
    hovertemplate="%{y:,.2f}<extra></extra>"
))

fig_roll.update_layout(**layout_base, height=280,
                        yaxis_title=f"Value{' (' + unit.strip() + ')' if unit.strip() else ''}")

st.markdown('<div class="chart-container">', unsafe_allow_html=True)
st.plotly_chart(fig_roll, use_container_width=True, config={"displayModeBar": False})
st.markdown('</div>', unsafe_allow_html=True)

# ----------------------------------------------------------
# DATA TABLE
# ----------------------------------------------------------

if show_table:
    st.markdown('<div class="section-title">Macro Data — Last 50 Observations</div>',
                unsafe_allow_html=True)

    tbl = fdf[["date_id", "value"]].tail(50).sort_values("date_id", ascending=False).copy()
    tbl["date_id"] = tbl["date_id"].dt.strftime("%Y-%m-%d")

    st.dataframe(
        tbl,
        use_container_width=True,
        hide_index=True,
        column_config={
            "date_id": st.column_config.TextColumn("Date"),
            "value":   st.column_config.NumberColumn(
                f"{selected_series}", format="%.4f",
                help="Raw indicator value"
            ),
        }
    )