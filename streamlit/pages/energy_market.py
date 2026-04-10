from __future__ import annotations

import os
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from dotenv import load_dotenv
from sqlalchemy import create_engine

st.set_page_config(
    page_title="Energy Market Analysis — SmartInvest",
    page_icon="🛢️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("Energy Market Analysis")
st.write("Analyse de la relation entre le pétrole et les actifs financiers.")


@st.cache_resource
def get_engine():
    load_dotenv()
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "5432")
    db = os.getenv("DB_NAME", "smartinvest_dw")
    user = os.getenv("DB_USER", "postgres")
    pwd = os.getenv("DB_PASSWORD", "")

    url = f"postgresql+psycopg2://{user}:{pwd}@{host}:{port}/{db}"
    return create_engine(url)


@st.cache_data(ttl=300)
def load_oil_data():
    query = """
        SELECT date_id, ticker, close, daily_return
        FROM smartinvest.v_oil_daily
        ORDER BY date_id
    """
    df = pd.read_sql(query, get_engine())
    df["date_id"] = pd.to_datetime(df["date_id"])
    return df


@st.cache_data(ttl=300)
def load_market_returns():
    query = """
        SELECT date_id, ticker, daily_return
        FROM smartinvest.v_market_returns_daily
        ORDER BY date_id
    """
    df = pd.read_sql(query, get_engine())
    df["date_id"] = pd.to_datetime(df["date_id"])
    return df


oil_df = load_oil_data()
market_df = load_market_returns()

with st.sidebar:
    st.header("Filters")

    oil_ticker = st.selectbox(
        "Oil series",
        sorted(oil_df["ticker"].dropna().unique()),
        index=0
    )

    asset_ticker = st.selectbox(
        "Asset",
        sorted(market_df["ticker"].dropna().unique()),
        index=0
    )

oil_selected = oil_df[oil_df["ticker"] == oil_ticker].copy()
asset_selected = market_df[market_df["ticker"] == asset_ticker].copy()

merged = pd.merge(
    oil_selected[["date_id", "close", "daily_return"]],
    asset_selected[["date_id", "daily_return"]],
    on="date_id",
    how="inner",
    suffixes=("_oil", "_asset")
).sort_values("date_id")

if merged.empty:
    st.warning("Aucune donnée commune entre le pétrole et l’actif sélectionné.")
    st.stop()

merged["rolling_corr_30"] = merged["daily_return_oil"].rolling(30).corr(merged["daily_return_asset"])

global_corr = merged["daily_return_oil"].corr(merged["daily_return_asset"])

col1, col2, col3 = st.columns(3)

col1.metric("Oil Series", oil_ticker)
col2.metric("Selected Asset", asset_ticker)
col3.metric("Global Correlation", f"{global_corr:.3f}" if pd.notna(global_corr) else "N/A")

st.subheader("Oil Price Evolution")

fig_oil = go.Figure()
fig_oil.add_trace(go.Scatter(
    x=oil_selected["date_id"],
    y=oil_selected["close"],
    mode="lines",
    name=oil_ticker
))
fig_oil.update_layout(
    xaxis_title="Date",
    yaxis_title="Oil Price",
    template="plotly_dark"
)
st.plotly_chart(fig_oil, use_container_width=True)

st.subheader("Daily Returns Comparison")

fig_returns = go.Figure()
fig_returns.add_trace(go.Scatter(
    x=merged["date_id"],
    y=merged["daily_return_oil"] * 100,
    mode="lines",
    name=f"{oil_ticker} Return (%)"
))
fig_returns.add_trace(go.Scatter(
    x=merged["date_id"],
    y=merged["daily_return_asset"] * 100,
    mode="lines",
    name=f"{asset_ticker} Return (%)"
))
fig_returns.update_layout(
    xaxis_title="Date",
    yaxis_title="Daily Return (%)",
    template="plotly_dark"
)
st.plotly_chart(fig_returns, use_container_width=True)

st.subheader("30-Day Rolling Correlation")

fig_corr = go.Figure()
fig_corr.add_trace(go.Scatter(
    x=merged["date_id"],
    y=merged["rolling_corr_30"],
    mode="lines",
    name="Rolling Correlation (30d)"
))
fig_corr.add_hline(y=0, line_dash="dash")
fig_corr.update_layout(
    xaxis_title="Date",
    yaxis_title="Correlation",
    template="plotly_dark"
)
st.plotly_chart(fig_corr, use_container_width=True)

st.subheader("Merged Data Preview")
st.dataframe(merged.tail(30), use_container_width=True)