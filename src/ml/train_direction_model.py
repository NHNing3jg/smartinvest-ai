from __future__ import annotations

import os
from pathlib import Path

import joblib
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    roc_auc_score,
)
from xgboost import XGBClassifier

MODEL_DIR = Path("models")
MODEL_DIR.mkdir(parents=True, exist_ok=True)

TARGET_TICKERS = ["AAPL", "MSFT", "NVDA", "TSLA", "AMZN"]


def get_engine():
    load_dotenv()
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "5432")
    db = os.getenv("DB_NAME", "smartinvest_dw")
    user = os.getenv("DB_USER", "postgres")
    pwd = os.getenv("DB_PASSWORD", "")

    if not pwd:
        raise ValueError("DB_PASSWORD manquant dans .env")

    url = f"postgresql+psycopg2://{user}:{pwd}@{host}:{port}/{db}?sslmode=disable"
    return create_engine(url)


def load_market_returns(engine):
    query = """
        SELECT date_id, ticker, daily_return
        FROM smartinvest.v_market_returns_daily
        ORDER BY date_id
    """
    df = pd.read_sql(query, engine)
    df["date_id"] = pd.to_datetime(df["date_id"])
    return df


def load_oil_returns(engine):
    query = """
        SELECT date_id, close, daily_return
        FROM smartinvest.v_oil_daily
        WHERE ticker = 'CL=F'
        ORDER BY date_id
    """
    df = pd.read_sql(query, engine)
    df["date_id"] = pd.to_datetime(df["date_id"])
    df = df.rename(columns={
        "close": "oil_close",
        "daily_return": "oil_return"
    })
    return df


def load_macro(engine):
    try:
        query = """
            SELECT date_id, series_id, value
            FROM smartinvest.v_macro_daily
            WHERE series_id IN ('FEDFUNDS', 'CPIAUCSL', 'UNRATE')
            ORDER BY date_id
        """
        df = pd.read_sql(query, engine)
        if df.empty:
            print("[WARN] No macro data available (FRED API key missing)")
            return pd.DataFrame({"date_id": []})
        df["date_id"] = pd.to_datetime(df["date_id"])
        pivot = df.pivot(index="date_id", columns="series_id", values="value").reset_index()
        pivot.columns.name = None
        return pivot
    except Exception as e:
        print(f"[WARN] Could not load macro data: {e}")
        return pd.DataFrame({"date_id": []})


def load_indices(engine):
    query = """
        SELECT date_id, ticker, daily_return
        FROM smartinvest.v_market_returns_daily
        WHERE ticker IN ('^GSPC', '^IXIC')
        ORDER BY date_id
    """
    df = pd.read_sql(query, engine)
    df["date_id"] = pd.to_datetime(df["date_id"])
    pivot = df.pivot(index="date_id", columns="ticker", values="daily_return").reset_index()
    pivot = pivot.rename(columns={
        "^GSPC": "sp500_return",
        "^IXIC": "nasdaq_return"
    })
    return pivot


def build_features_for_ticker(stock_df, oil_df, macro_df, index_df, ticker):
    df = stock_df[stock_df["ticker"] == ticker].copy()
    df = df.sort_values("date_id").reset_index(drop=True)

    df = df.merge(oil_df, on="date_id", how="left")
    df = df.merge(macro_df, on="date_id", how="left")
    df = df.merge(index_df, on="date_id", how="left")

    # Lags rendement actif
    df["return_lag_1"] = df["daily_return"].shift(1)
    df["return_lag_2"] = df["daily_return"].shift(2)
    df["return_lag_3"] = df["daily_return"].shift(3)
    df["return_lag_5"] = df["daily_return"].shift(5)

    # Rolling stats actif
    df["rolling_mean_5"] = df["daily_return"].rolling(5).mean()
    df["rolling_mean_10"] = df["daily_return"].rolling(10).mean()
    df["rolling_vol_5"] = df["daily_return"].rolling(5).std()
    df["rolling_vol_10"] = df["daily_return"].rolling(10).std()

    # Momentum
    df["momentum_5"] = df["daily_return"].rolling(5).sum()
    df["momentum_10"] = df["daily_return"].rolling(10).sum()

    # Oil features
    df["oil_return_lag_1"] = df["oil_return"].shift(1)
    df["oil_return_lag_2"] = df["oil_return"].shift(2)
    df["oil_mean_5"] = df["oil_return"].rolling(5).mean()
    df["oil_vol_5"] = df["oil_return"].rolling(5).std()

    # Index features
    df["sp500_lag_1"] = df["sp500_return"].shift(1)
    df["nasdaq_lag_1"] = df["nasdaq_return"].shift(1)

    # Macro variations
    for col in ["FEDFUNDS", "CPIAUCSL", "UNRATE"]:
        if col in df.columns:
            df[f"{col}_chg"] = df[col].pct_change()

    # Target : direction du jour suivant
    df["target"] = (df["daily_return"].shift(-1) > 0).astype(int)
    df["asset"] = ticker

    return df


def build_dataset(engine):
    market_df = load_market_returns(engine)
    oil_df = load_oil_returns(engine)
    macro_df = load_macro(engine)
    index_df = load_indices(engine)

    frames = []
    for ticker in TARGET_TICKERS:
        frames.append(
            build_features_for_ticker(
                stock_df=market_df,
                oil_df=oil_df,
                macro_df=macro_df,
                index_df=index_df,
                ticker=ticker
            )
        )

    df = pd.concat(frames, ignore_index=True)
    df = pd.get_dummies(df, columns=["asset"], drop_first=False)

    # Build feature_cols dynamically based on what exists
    feature_cols = [
        "return_lag_1", "return_lag_2", "return_lag_3", "return_lag_5",
        "rolling_mean_5", "rolling_mean_10",
        "rolling_vol_5", "rolling_vol_10",
        "momentum_5", "momentum_10",
        "oil_return", "oil_return_lag_1", "oil_return_lag_2",
        "oil_mean_5", "oil_vol_5", "oil_close",
        "sp500_return", "nasdaq_return", "sp500_lag_1", "nasdaq_lag_1",
    ]
    
    # Add macro features only if they exist
    macro_features = ["FEDFUNDS", "CPIAUCSL", "UNRATE", "FEDFUNDS_chg", "CPIAUCSL_chg", "UNRATE_chg"]
    for feat in macro_features:
        if feat in df.columns:
            feature_cols.append(feat)
    
    # Add asset dummies
    feature_cols += [c for c in df.columns if c.startswith("asset_")]

    df = df.dropna().reset_index(drop=True)

    # Filter to only features that exist
    feature_cols = [c for c in feature_cols if c in df.columns]

    X = df[feature_cols]
    y = df["target"]

    return df, X, y, feature_cols


def temporal_split(X, y, train_ratio=0.7, valid_ratio=0.15):
    n = len(X)
    train_end = int(n * train_ratio)
    valid_end = int(n * (train_ratio + valid_ratio))

    X_train = X.iloc[:train_end]
    y_train = y.iloc[:train_end]

    X_valid = X.iloc[train_end:valid_end]
    y_valid = y.iloc[train_end:valid_end]

    X_test = X.iloc[valid_end:]
    y_test = y.iloc[valid_end:]

    return X_train, X_valid, X_test, y_train, y_valid, y_test


def evaluate_model(name, y_true, y_pred, y_proba):
    print(f"\n=== {name} ===")
    print("Accuracy:", round(accuracy_score(y_true, y_pred), 4))
    print("Balanced Accuracy:", round(balanced_accuracy_score(y_true, y_pred), 4))
    print("F1-score:", round(f1_score(y_true, y_pred), 4))
    print("ROC-AUC:", round(roc_auc_score(y_true, y_proba), 4))
    print("\nClassification report:")
    print(classification_report(y_true, y_pred))
    print("\nConfusion matrix:")
    print(confusion_matrix(y_true, y_pred))


def train_model(X_train, y_train, X_valid, y_valid):
    model = XGBClassifier(
        n_estimators=400,
        max_depth=4,
        learning_rate=0.03,
        subsample=0.8,
        colsample_bytree=0.8,
        reg_alpha=0.5,
        reg_lambda=1.0,
        random_state=42,
        eval_metric="logloss"
    )

    model.fit(X_train, y_train)

    valid_proba = model.predict_proba(X_valid)[:, 1]

    # on choisit un seuil plus intelligent que 0.5
    best_threshold = 0.50
    best_f1 = -1

    for threshold in [0.45, 0.48, 0.50, 0.52, 0.55]:
        pred = (valid_proba >= threshold).astype(int)
        score = f1_score(y_valid, pred)
        if score > best_f1:
            best_f1 = score
            best_threshold = threshold

    print(f"\n[INFO] Best validation threshold: {best_threshold:.2f}")
    return model, best_threshold


def main():
    engine = get_engine()

    df, X, y, feature_cols = build_dataset(engine)

    X_train, X_valid, X_test, y_train, y_valid, y_test = temporal_split(X, y)

    model, threshold = train_model(X_train, y_train, X_valid, y_valid)

    valid_proba = model.predict_proba(X_valid)[:, 1]
    valid_pred = (valid_proba >= threshold).astype(int)
    evaluate_model("VALIDATION RESULTS", y_valid, valid_pred, valid_proba)

    test_proba = model.predict_proba(X_test)[:, 1]
    test_pred = (test_proba >= threshold).astype(int)
    evaluate_model("TEST RESULTS", y_test, test_pred, test_proba)

    importances = pd.Series(model.feature_importances_, index=feature_cols).sort_values(ascending=False)
    print("\nTop 15 features:")
    print(importances.head(15))

    joblib.dump(model, MODEL_DIR / "direction_model_xgb.pkl")
    joblib.dump(feature_cols, MODEL_DIR / "direction_model_features.pkl")
    joblib.dump(threshold, MODEL_DIR / "direction_model_threshold.pkl")

    print("\n[OK] Model saved:")
    print(" - models/direction_model_xgb.pkl")
    print(" - models/direction_model_features.pkl")
    print(" - models/direction_model_threshold.pkl")


if __name__ == "__main__":
    main()