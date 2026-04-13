from __future__ import annotations

from pathlib import Path
import pandas as pd
import streamlit as st
import plotly.express as px

st.set_page_config(
    page_title="AI Investment Advisor — SmartInvest",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("AI Investment Advisor")
st.write("Recommandations d’investissement générées à partir du modèle de prédiction.")

RECO_PATH = Path("outputs/latest_recommendations.csv")


@st.cache_data(ttl=300)
def load_recommendations():
    if not RECO_PATH.exists():
        raise FileNotFoundError(
            f"Recommendation file not found: {RECO_PATH}. "
            f"Run `python src/ml/generate_recommendations.py` first."
        )

    df = pd.read_csv(RECO_PATH)
    df["date_id"] = pd.to_datetime(df["date_id"])
    return df


try:
    reco_df = load_recommendations()
except Exception as e:
    st.error(f"Unable to load recommendations: {e}")
    st.stop()

with st.sidebar:
    st.header("Filters")

    selected_signal = st.multiselect(
        "Signal",
        options=sorted(reco_df["signal"].dropna().unique()),
        default=sorted(reco_df["signal"].dropna().unique())
    )

    selected_confidence = st.multiselect(
        "Confidence",
        options=sorted(reco_df["confidence"].dropna().unique()),
        default=sorted(reco_df["confidence"].dropna().unique())
    )

filtered_df = reco_df[
    reco_df["signal"].isin(selected_signal) &
    reco_df["confidence"].isin(selected_confidence)
].copy()

if filtered_df.empty:
    st.warning("No recommendations available for the selected filters.")
    st.stop()

# KPIs
col1, col2, col3, col4 = st.columns(4)

col1.metric("Total Assets", len(filtered_df))
col2.metric("BUY Signals", int((filtered_df["signal"] == "BUY").sum()))
col3.metric("HOLD Signals", int((filtered_df["signal"] == "HOLD").sum()))
col4.metric("SELL Signals", int((filtered_df["signal"] == "SELL").sum()))

st.subheader("Recommendation Table")

display_df = filtered_df.copy()
display_df["proba_up"] = (display_df["proba_up"] * 100).round(2)

st.dataframe(
    display_df[
        [
            "date_id",
            "ticker",
            "proba_up",
            "predicted_direction",
            "signal",
            "confidence",
            "momentum_5",
            "momentum_10",
            "rolling_vol_10",
            "oil_return",
            "sp500_return",
            "nasdaq_return",
        ]
    ].rename(columns={"proba_up": "proba_up (%)"}),
    use_container_width=True,
    hide_index=True
)

st.subheader("Probability of Upward Movement")

fig_prob = px.bar(
    filtered_df.sort_values("proba_up", ascending=False),
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

st.plotly_chart(fig_prob, use_container_width=True)

st.subheader("Signal Distribution")

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
st.plotly_chart(fig_signal, use_container_width=True)

st.subheader("Top Recommendations")

top_buy = filtered_df[filtered_df["signal"] == "BUY"].sort_values(
    "proba_up", ascending=False
).head(5)

if not top_buy.empty:
    st.success("Top BUY opportunities identified by the AI model:")
    st.dataframe(
        top_buy[["ticker", "proba_up", "confidence", "momentum_5", "rolling_vol_10"]],
        use_container_width=True,
        hide_index=True
    )
else:
    st.info("No BUY signals available at the moment.")