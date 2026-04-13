from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

# ==========================================================
# Page — AI Investment Advisor
# SmartInvest BI-AI Dashboard
# ==========================================================

st.set_page_config(
    page_title="AI Investment Advisor — SmartInvest",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ----------------------------------------------------------
# CUSTOM CSS
# ----------------------------------------------------------

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Mono:wght@300;400;500&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Mono', monospace;
}

.stApp {
    background: #07080f;
    background-image:
        radial-gradient(ellipse 80% 50% at 50% -10%, rgba(0,200,120,0.08) 0%, transparent 70%),
        radial-gradient(ellipse 40% 30% at 90% 85%, rgba(0,170,255,0.06) 0%, transparent 60%);
}

[data-testid="stSidebar"] {
    background: #0d0f1a !important;
    border-right: 1px solid rgba(0,200,120,0.15);
}

.page-header { padding: 1.8rem 0 1rem 0; }

.page-badge {
    display: inline-block;
    font-size: 0.68rem;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: #00c878;
    border: 1px solid rgba(0,200,120,0.3);
    border-radius: 2px;
    padding: 3px 12px;
    background: rgba(0,200,120,0.06);
    margin-bottom: 0.8rem;
}

.page-title {
    font-family: 'Syne', sans-serif;
    font-size: 2.2rem;
    font-weight: 800;
    color: #eef2f7;
    letter-spacing: -0.02em;
    margin: 0;
}

.page-subtitle {
    font-size: 0.8rem;
    color: #3a4a5a;
    margin-top: 0.4rem;
}

.kpi-row {
    display: flex;
    gap: 0.85rem;
    margin: 1.5rem 0;
    flex-wrap: wrap;
}

.kpi-card {
    flex: 1;
    min-width: 150px;
    background: rgba(255,255,255,0.025);
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 6px;
    padding: 1rem 1.2rem;
    position: relative;
    overflow: hidden;
}

.kpi-card::after {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
}

.kpi-card.green::after  { background: linear-gradient(90deg,#00c878,transparent); }
.kpi-card.blue::after   { background: linear-gradient(90deg,#00aaff,transparent); }
.kpi-card.red::after    { background: linear-gradient(90deg,#ff4d6d,transparent); }
.kpi-card.amber::after  { background: linear-gradient(90deg,#f59e0b,transparent); }
.kpi-card.purple::after { background: linear-gradient(90deg,#a78bfa,transparent); }

.kpi-label {
    font-size: 0.65rem;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #3a4a5a;
    margin-bottom: 0.35rem;
}

.kpi-value {
    font-family: 'Syne', sans-serif;
    font-size: 1.4rem;
    font-weight: 700;
    color: #eef2f7;
}

.kpi-delta {
    font-size: 0.72rem;
    margin-top: 0.25rem;
    color: #8898aa;
}

.section-title {
    font-family: 'Syne', sans-serif;
    font-size: 0.85rem;
    font-weight: 700;
    color: #8898aa;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    margin: 1.8rem 0 0.8rem 0;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

.section-title::after {
    content: '';
    flex: 1;
    height: 1px;
    background: linear-gradient(90deg, rgba(255,255,255,0.07), transparent);
}

.chart-container {
    background: rgba(255,255,255,0.02);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 6px;
    padding: 0.5rem 0.5rem 0 0.5rem;
    margin-bottom: 1rem;
}

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
}

.sidebar-brand-tag {
    font-size: 0.65rem;
    color: #00c878 !important;
    letter-spacing: 0.15em;
    text-transform: uppercase;
}

.explanation-card {
    background: rgba(255,255,255,0.025);
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 8px;
    padding: 0.9rem 1rem;
    margin-bottom: 0.8rem;
}

.explanation-title {
    font-family: 'Syne', sans-serif;
    font-size: 0.95rem;
    font-weight: 700;
    color: #eef2f7;
    margin-bottom: 0.35rem;
}

.explanation-text {
    font-size: 0.78rem;
    color: #a8b3c2;
    line-height: 1.6;
}

.buy-text  { color: #00c878; }
.hold-text { color: #f59e0b; }
.sell-text { color: #ff4d6d; }
</style>
""", unsafe_allow_html=True)

# ----------------------------------------------------------
# PATHS
# ----------------------------------------------------------

RECO_PATH = Path("outputs/latest_recommendations.csv")
BACKTEST_SUMMARY_PATH = Path("outputs/backtest_summary.csv")
BACKTEST_METRICS_PATH = Path("outputs/backtest_metrics.csv")

# ----------------------------------------------------------
# LOAD DATA
# ----------------------------------------------------------

@st.cache_data(ttl=300, show_spinner=False)
def load_recommendations() -> pd.DataFrame:
    if not RECO_PATH.exists():
        raise FileNotFoundError(
            f"Recommendation file not found: {RECO_PATH}. "
            "Run `python -m src.ml.generate_recommendations` first."
        )

    df = pd.read_csv(RECO_PATH)
    df["date_id"] = pd.to_datetime(df["date_id"])
    return df


@st.cache_data(ttl=300, show_spinner=False)
def load_backtest_summary() -> pd.DataFrame:
    if not BACKTEST_SUMMARY_PATH.exists():
        return pd.DataFrame()
    return pd.read_csv(BACKTEST_SUMMARY_PATH)


@st.cache_data(ttl=300, show_spinner=False)
def load_backtest_metrics() -> pd.DataFrame:
    if not BACKTEST_METRICS_PATH.exists():
        return pd.DataFrame()
    return pd.read_csv(BACKTEST_METRICS_PATH)


try:
    reco_df = load_recommendations()
except Exception as e:
    st.error(f"Unable to load recommendations: {e}")
    st.stop()

backtest_summary_df = load_backtest_summary()
backtest_metrics_df = load_backtest_metrics()

# ----------------------------------------------------------
# SIDEBAR
# ----------------------------------------------------------

with st.sidebar:
    st.markdown("""
    <div class="sidebar-brand">
        <div class="sidebar-brand-name">SmartInvest</div>
        <div class="sidebar-brand-tag">AI Advisor</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("**Signal Filter**")
    selected_signal = st.multiselect(
        "Signal",
        options=sorted(reco_df["signal"].dropna().unique()),
        default=sorted(reco_df["signal"].dropna().unique()),
        label_visibility="collapsed"
    )

    st.divider()

    st.markdown("**Confidence Filter**")
    selected_confidence = st.multiselect(
        "Confidence",
        options=sorted(reco_df["confidence"].dropna().unique()),
        default=sorted(reco_df["confidence"].dropna().unique()),
        label_visibility="collapsed"
    )

    st.divider()

    st.markdown("**Minimum Probability Up**")
    min_prob = st.slider(
        "Minimum Probability",
        min_value=0.0,
        max_value=1.0,
        value=0.0,
        step=0.01,
        label_visibility="collapsed"
    )

    st.divider()
    st.markdown(
        "<span style='font-size:0.7rem;color:#2a3a4a;'>v1.1.0 — SmartInvest BI-AI</span>",
        unsafe_allow_html=True
    )

# ----------------------------------------------------------
# FILTER DATA
# ----------------------------------------------------------

filtered_df = reco_df[
    reco_df["signal"].isin(selected_signal) &
    reco_df["confidence"].isin(selected_confidence) &
    (reco_df["proba_up"] >= min_prob)
].copy()

if filtered_df.empty:
    st.warning("No recommendations available for the selected filters.")
    st.stop()

# ----------------------------------------------------------
# HEADER
# ----------------------------------------------------------

latest_date = filtered_df["date_id"].max().strftime("%d %b %Y")

st.markdown(f"""
<div class="page-header">
    <div class="page-badge">AI Investment Advisor</div>
    <h1 class="page-title">Smart Recommendations</h1>
    <p class="page-subtitle">
        Latest model-driven recommendations generated on {latest_date}
    </p>
</div>
""", unsafe_allow_html=True)

# ----------------------------------------------------------
# TOP KPIS
# ----------------------------------------------------------

buy_count = int((filtered_df["signal"] == "BUY").sum())
hold_count = int((filtered_df["signal"] == "HOLD").sum())
sell_count = int((filtered_df["signal"] == "SELL").sum())
avg_prob = filtered_df["proba_up"].mean() * 100
top_score = filtered_df["advisor_score"].max()

st.markdown(f"""
<div class="kpi-row">
  <div class="kpi-card green">
    <div class="kpi-label">Buy Signals</div>
    <div class="kpi-value">{buy_count}</div>
    <div class="kpi-delta">Assets with strongest positive profile</div>
  </div>
  <div class="kpi-card amber">
    <div class="kpi-label">Hold Signals</div>
    <div class="kpi-value">{hold_count}</div>
    <div class="kpi-delta">Neutral / uncertain opportunities</div>
  </div>
  <div class="kpi-card red">
    <div class="kpi-label">Sell Signals</div>
    <div class="kpi-value">{sell_count}</div>
    <div class="kpi-delta">Lowest-ranked assets</div>
  </div>
  <div class="kpi-card blue">
    <div class="kpi-label">Avg Probability Up</div>
    <div class="kpi-value">{avg_prob:.1f}%</div>
    <div class="kpi-delta">Mean model probability</div>
  </div>
  <div class="kpi-card purple">
    <div class="kpi-label">Top Advisor Score</div>
    <div class="kpi-value">{top_score:.4f}</div>
    <div class="kpi-delta">Best ranked recommendation</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ----------------------------------------------------------
# RECOMMENDATION TABLE
# ----------------------------------------------------------

st.markdown('<div class="section-title">Recommendation Table</div>', unsafe_allow_html=True)

display_df = filtered_df.copy()
display_df["proba_up_pct"] = (display_df["proba_up"] * 100).round(2)

st.dataframe(
    display_df[
        [
            "date_id",
            "ticker",
            "proba_up_pct",
            "predicted_direction",
            "signal",
            "confidence",
            "advisor_score",
            "momentum_5",
            "momentum_10",
            "rolling_vol_10",
            "oil_return",
            "sp500_return",
            "nasdaq_return",
            "explanation",
        ]
    ].rename(columns={"proba_up_pct": "proba_up (%)"}),
    use_container_width=True,
    hide_index=True,
    column_config={
        "date_id": st.column_config.DateColumn("Date"),
        "ticker": st.column_config.TextColumn("Ticker"),
        "proba_up (%)": st.column_config.NumberColumn("Proba Up (%)", format="%.2f"),
        "predicted_direction": st.column_config.TextColumn("Direction"),
        "signal": st.column_config.TextColumn("Signal"),
        "confidence": st.column_config.TextColumn("Confidence"),
        "advisor_score": st.column_config.NumberColumn("Advisor Score", format="%.4f"),
        "momentum_5": st.column_config.NumberColumn("Momentum 5", format="%.4f"),
        "momentum_10": st.column_config.NumberColumn("Momentum 10", format="%.4f"),
        "rolling_vol_10": st.column_config.NumberColumn("Rolling Vol 10", format="%.4f"),
        "oil_return": st.column_config.NumberColumn("Oil Return", format="%.4f"),
        "sp500_return": st.column_config.NumberColumn("S&P500 Return", format="%.4f"),
        "nasdaq_return": st.column_config.NumberColumn("NASDAQ Return", format="%.4f"),
        "explanation": st.column_config.TextColumn("Explanation", width="large"),
    }
)

# ----------------------------------------------------------
# AI EXPLANATIONS
# ----------------------------------------------------------

st.markdown('<div class="section-title">AI Explanations</div>', unsafe_allow_html=True)

for _, row in filtered_df.iterrows():
    signal_class = {
        "BUY": "buy-text",
        "HOLD": "hold-text",
        "SELL": "sell-text"
    }.get(row["signal"], "")

    st.markdown(f"""
    <div class="explanation-card">
        <div class="explanation-title">
            {row['ticker']} — <span class="{signal_class}">{row['signal']}</span>
        </div>
        <div class="explanation-text">
            {row['explanation']}
        </div>
    </div>
    """, unsafe_allow_html=True)

# ----------------------------------------------------------
# CHARTS
# ----------------------------------------------------------

st.markdown('<div class="section-title">Probability of Upward Movement</div>', unsafe_allow_html=True)

fig_prob = px.bar(
    filtered_df.sort_values("advisor_score", ascending=False),
    x="ticker",
    y="proba_up",
    color="signal",
    text="signal",
    color_discrete_map={
        "BUY": "#00c853",
        "HOLD": "#ffb300",
        "SELL": "#ff5252"
    },
    title="Predicted Probability of Price Increase"
)
fig_prob.update_traces(textposition="outside")
fig_prob.update_layout(
    yaxis_title="Probability Up",
    xaxis_title="Asset",
    template="plotly_dark"
)

st.markdown('<div class="chart-container">', unsafe_allow_html=True)
st.plotly_chart(fig_prob, use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    st.markdown('<div class="section-title">Advisor Score Ranking</div>', unsafe_allow_html=True)

    fig_score = px.bar(
        filtered_df.sort_values("advisor_score", ascending=False),
        x="ticker",
        y="advisor_score",
        color="signal",
        text="advisor_score",
        color_discrete_map={
            "BUY": "#00c853",
            "HOLD": "#ffb300",
            "SELL": "#ff5252"
        },
        title="Final Advisor Ranking"
    )
    fig_score.update_traces(textposition="outside")
    fig_score.update_layout(
        xaxis_title="Asset",
        yaxis_title="Advisor Score",
        template="plotly_dark"
    )

    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    st.plotly_chart(fig_score, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="section-title">Signal Distribution</div>', unsafe_allow_html=True)

    signal_counts = filtered_df["signal"].value_counts().reset_index()
    signal_counts.columns = ["signal", "count"]

    fig_signal = px.pie(
        signal_counts,
        names="signal",
        values="count",
        color="signal",
        color_discrete_map={
            "BUY": "#00c853",
            "HOLD": "#ffb300",
            "SELL": "#ff5252"
        },
        title="Distribution of AI Signals"
    )
    fig_signal.update_layout(template="plotly_dark")

    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    st.plotly_chart(fig_signal, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ----------------------------------------------------------
# TOP RECOMMENDATIONS
# ----------------------------------------------------------

col_buy, col_sell = st.columns(2)

with col_buy:
    st.markdown('<div class="section-title">Top Buy Opportunities</div>', unsafe_allow_html=True)

    top_buy = filtered_df[filtered_df["signal"] == "BUY"].sort_values(
        "advisor_score", ascending=False
    ).head(5)

    if not top_buy.empty:
        st.success("Top BUY opportunities identified by the AI advisor:")
        st.dataframe(
            top_buy[
                ["ticker", "proba_up", "confidence", "advisor_score", "momentum_5", "rolling_vol_10", "explanation"]
            ],
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No BUY signals available at the moment.")

with col_sell:
    st.markdown('<div class="section-title">Top Sell Alerts</div>', unsafe_allow_html=True)

    top_sell = filtered_df[filtered_df["signal"] == "SELL"].sort_values(
        "advisor_score", ascending=True
    ).head(5)

    if not top_sell.empty:
        st.warning("Lowest-ranked assets identified by the AI advisor:")
        st.dataframe(
            top_sell[
                ["ticker", "proba_up", "confidence", "advisor_score", "momentum_5", "rolling_vol_10", "explanation"]
            ],
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No SELL signals available at the moment.")

# ----------------------------------------------------------
# BACKTEST SUMMARY
# ----------------------------------------------------------

st.markdown('<div class="section-title">Backtest Summary</div>', unsafe_allow_html=True)

if backtest_summary_df.empty or backtest_metrics_df.empty:
    st.warning("Backtest files not found. Run `python -m src.ml.backtest_recommendations` first.")
else:
    metrics_map = dict(zip(backtest_metrics_df["metric"], backtest_metrics_df["value"]))

    buy_win = metrics_map.get("BUY win rate", 0)
    sell_win = metrics_map.get("SELL win rate", 0)
    hold_win = metrics_map.get("HOLD win rate", 0)
    buy_ret = metrics_map.get("BUY mean next-day return", 0)
    sell_ret = metrics_map.get("SELL mean next-day return", 0)
    hold_ret = metrics_map.get("HOLD mean next-day return", 0)

    st.markdown("### Validation KPIs")

    k1, k2, k3 = st.columns(3)
    k1.metric("BUY Win Rate", f"{buy_win:.2f}%")
    k2.metric("SELL Win Rate", f"{sell_win:.2f}%")
    k3.metric("HOLD Win Rate", f"{hold_win:.2f}%")

    k4, k5, k6 = st.columns(3)
    k4.metric("BUY Avg Next Return", f"{buy_ret:.4f}")
    k5.metric("SELL Avg Next Return", f"{sell_ret:.4f}")
    k6.metric("HOLD Avg Next Return", f"{hold_ret:.4f}")

    summary_display = backtest_summary_df.copy()
    st.dataframe(
        summary_display,
        use_container_width=True,
        hide_index=True,
        column_config={
            "signal": st.column_config.TextColumn("Signal"),
            "nb_obs": st.column_config.NumberColumn("Observations"),
            "avg_next_return": st.column_config.NumberColumn("Avg Next Return", format="%.4f"),
            "median_next_return": st.column_config.NumberColumn("Median Next Return", format="%.4f"),
            "win_rate": st.column_config.NumberColumn("Win Rate (%)", format="%.2f"),
            "avg_proba_up": st.column_config.NumberColumn("Avg Proba Up", format="%.4f"),
            "avg_advisor_score": st.column_config.NumberColumn("Avg Advisor Score", format="%.4f"),
        }
    )

    c1, c2 = st.columns(2)

    with c1:
        fig_win = px.bar(
            backtest_summary_df,
            x="signal",
            y="win_rate",
            color="signal",
            text="win_rate",
            color_discrete_map={
                "BUY": "#00c853",
                "HOLD": "#ffb300",
                "SELL": "#ff5252"
            },
            title="Win Rate by Signal"
        )
        fig_win.update_traces(textposition="outside")
        fig_win.update_layout(template="plotly_dark", yaxis_title="Win Rate (%)", xaxis_title="Signal")
        st.plotly_chart(fig_win, use_container_width=True)

    with c2:
        fig_ret = px.bar(
            backtest_summary_df,
            x="signal",
            y="avg_next_return",
            color="signal",
            text="avg_next_return",
            color_discrete_map={
                "BUY": "#00c853",
                "HOLD": "#ffb300",
                "SELL": "#ff5252"
            },
            title="Average Next-Day Return by Signal"
        )
        fig_ret.update_traces(textposition="outside")
        fig_ret.update_layout(template="plotly_dark", yaxis_title="Avg Next Return", xaxis_title="Signal")
        st.plotly_chart(fig_ret, use_container_width=True)

    st.markdown("### Model Insights")
    st.info(
        """
- BUY signals show the strongest historical validation and positive next-day average return.
- SELL signals are less reliable, which is common in equity markets with bullish long-term bias.
- HOLD captures assets with more neutral or mixed profiles.
- This backtest strengthens the credibility of the advisor by validating signals on historical data.
        """
    )