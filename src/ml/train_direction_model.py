from __future__ import annotations

import os
import logging
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

try:
    from src.ml.ml_metrics_exporter import (
        export_classification_metrics,
        export_feature_importance,
        update_model_comparison,
    )
except ModuleNotFoundError:
    try:
        from ml_metrics_exporter import (
            export_classification_metrics,
            export_feature_importance,
            update_model_comparison,
        )
    except Exception:
        export_classification_metrics = None
        export_feature_importance = None
        update_model_comparison = None
except Exception:
    export_classification_metrics = None
    export_feature_importance = None
    update_model_comparison = None

MODEL_DIR = Path("models")
MODEL_DIR.mkdir(parents=True, exist_ok=True)

TARGET_TICKERS = ["AAPL", "MSFT", "NVDA", "TSLA", "AMZN"]
MACRO_SERIES = ["FEDFUNDS", "CPIAUCSL", "UNRATE"]

logging.basicConfig(
    level=os.getenv("ML_LOG_LEVEL", "INFO").upper(),
    format="[%(levelname)s] %(message)s",
)
LOGGER = logging.getLogger(__name__)


def log_rows(label: str, df: pd.DataFrame) -> None:
    LOGGER.info("%s rows: %s", label, len(df))


def require_non_empty(df: pd.DataFrame, step: str, detail: str = "") -> None:
    if not df.empty:
        return

    message = f"Training dataset is empty after {step}."
    if detail:
        message = f"{message} {detail}"
    raise ValueError(message)


def log_date_range(label: str, df: pd.DataFrame) -> None:
    if df.empty or "date_id" not in df.columns:
        LOGGER.info("%s date range: empty", label)
        return

    LOGGER.info(
        "%s date range: %s -> %s",
        label,
        df["date_id"].min().date(),
        df["date_id"].max().date(),
    )


def log_non_null_coverage(label: str, df: pd.DataFrame, columns: list[str]) -> None:
    existing = [column for column in columns if column in df.columns]
    if not existing:
        LOGGER.info("%s coverage: no matching columns", label)
        return

    coverage = {column: int(df[column].notna().sum()) for column in existing}
    LOGGER.info("%s non-null rows: %s", label, coverage)


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
    log_rows("Market rows loaded", df)
    log_date_range("Market rows loaded", df)
    return df


def load_oil_returns(engine):
    query = """
        SELECT date_id, close, daily_return
        FROM smartinvest.v_oil_daily
        WHERE ticker = 'CL=F'
        ORDER BY date_id
    """
    df = pd.read_sql(query, engine)
    if df.empty:
        log_rows("Oil rows loaded", df)
        return pd.DataFrame(columns=["date_id", "oil_close", "oil_return"])

    df["date_id"] = pd.to_datetime(df["date_id"])
    df = df.rename(columns={
        "close": "oil_close",
        "daily_return": "oil_return"
    })
    log_rows("Oil rows loaded", df)
    log_date_range("Oil rows loaded", df)
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
        log_rows("Macro rows loaded", df)
        if df.empty:
            print("[WARN] No macro data available (FRED API key missing)")
            return pd.DataFrame(columns=["date_id", *MACRO_SERIES])
        df["date_id"] = pd.to_datetime(df["date_id"])
        pivot = (
            df.pivot_table(
                index="date_id",
                columns="series_id",
                values="value",
                aggfunc="last",
            )
            .reset_index()
            .sort_values("date_id")
            .reset_index(drop=True)
        )
        pivot.columns.name = None
        log_rows("Macro pivot date rows loaded", pivot)
        log_date_range("Macro rows loaded", pivot)
        log_non_null_coverage("Macro pivot", pivot, MACRO_SERIES)
        return pivot
    except Exception as e:
        print(f"[WARN] Could not load macro data: {e}")
        return pd.DataFrame(columns=["date_id", *MACRO_SERIES])


def load_indices(engine):
    query = """
        SELECT date_id, ticker, daily_return
        FROM smartinvest.v_market_returns_daily
        WHERE ticker IN ('^GSPC', '^IXIC')
        ORDER BY date_id
    """
    df = pd.read_sql(query, engine)
    if df.empty:
        log_rows("Index rows loaded", df)
        return pd.DataFrame(columns=["date_id", "sp500_return", "nasdaq_return"])

    df["date_id"] = pd.to_datetime(df["date_id"])
    log_rows("Index rows loaded", df)
    log_date_range("Index rows loaded", df)
    pivot = (
        df.pivot_table(
            index="date_id",
            columns="ticker",
            values="daily_return",
            aggfunc="last",
        )
        .reset_index()
        .sort_values("date_id")
        .reset_index(drop=True)
    )
    pivot = pivot.rename(columns={
        "^GSPC": "sp500_return",
        "^IXIC": "nasdaq_return"
    })
    log_rows("Index pivot date rows loaded", pivot)
    log_non_null_coverage("Index pivot", pivot, ["sp500_return", "nasdaq_return"])
    return pivot


def align_macro_to_market_dates(
    macro_df: pd.DataFrame,
    market_dates: pd.Series,
) -> pd.DataFrame:
    aligned = pd.DataFrame({"date_id": market_dates.drop_duplicates().sort_values()})
    macro_cols = [column for column in MACRO_SERIES if column in macro_df.columns]

    if macro_df.empty or not macro_cols:
        for column in MACRO_SERIES:
            aligned[column] = pd.NA
        log_rows("Macro rows after forward-fill alignment", aligned)
        log_non_null_coverage("Macro aligned", aligned, MACRO_SERIES)
        return aligned

    macro = (
        macro_df[["date_id", *macro_cols]]
        .drop_duplicates(subset=["date_id"], keep="last")
        .sort_values("date_id")
        .set_index("date_id")
    )
    market_index = pd.DatetimeIndex(aligned["date_id"])
    full_index = market_index.union(macro.index).sort_values()

    macro = macro.reindex(full_index).ffill()
    aligned = macro.loc[market_index].reset_index().rename(columns={"index": "date_id"})

    missing_cols = [column for column in MACRO_SERIES if column not in aligned.columns]
    for column in missing_cols:
        aligned[column] = pd.NA

    log_rows("Macro rows after forward-fill alignment", aligned)
    log_non_null_coverage("Macro aligned", aligned, MACRO_SERIES)
    return aligned


def align_oil_to_market_dates(
    oil_df: pd.DataFrame,
    market_dates: pd.Series,
) -> pd.DataFrame:
    aligned = pd.DataFrame({"date_id": market_dates.drop_duplicates().sort_values()})

    if oil_df.empty:
        aligned["oil_close"] = pd.NA
        aligned["oil_return"] = pd.NA
        log_rows("Oil rows after date alignment", aligned)
        log_non_null_coverage("Oil aligned", aligned, ["oil_close", "oil_return"])
        return aligned

    oil = (
        oil_df[["date_id", "oil_close", "oil_return"]]
        .drop_duplicates(subset=["date_id"], keep="last")
        .sort_values("date_id")
        .set_index("date_id")
    )
    market_index = pd.DatetimeIndex(aligned["date_id"])
    full_index = market_index.union(oil.index).sort_values()

    oil = oil.reindex(full_index)
    oil["oil_close"] = oil["oil_close"].ffill()
    aligned = oil.loc[market_index].reset_index().rename(columns={"index": "date_id"})

    log_rows("Oil rows after date alignment", aligned)
    log_non_null_coverage("Oil aligned", aligned, ["oil_close", "oil_return"])
    return aligned


def align_indices_to_market_dates(
    index_df: pd.DataFrame,
    market_dates: pd.Series,
) -> pd.DataFrame:
    aligned = pd.DataFrame({"date_id": market_dates.drop_duplicates().sort_values()})
    index_cols = [column for column in ["sp500_return", "nasdaq_return"] if column in index_df.columns]

    if index_df.empty or not index_cols:
        aligned["sp500_return"] = pd.NA
        aligned["nasdaq_return"] = pd.NA
        log_rows("Index rows after date alignment", aligned)
        log_non_null_coverage("Index aligned", aligned, ["sp500_return", "nasdaq_return"])
        return aligned

    aligned = aligned.merge(index_df[["date_id", *index_cols]], on="date_id", how="left")

    missing_cols = [column for column in ["sp500_return", "nasdaq_return"] if column not in aligned.columns]
    for column in missing_cols:
        aligned[column] = pd.NA

    log_rows("Index rows after date alignment", aligned)
    log_non_null_coverage("Index aligned", aligned, ["sp500_return", "nasdaq_return"])
    return aligned


def build_features_for_ticker(stock_df, oil_df, macro_df, index_df, ticker):
    df = stock_df[stock_df["ticker"] == ticker].copy()
    df = df.sort_values("date_id").reset_index(drop=True)
    LOGGER.info("[%s] Base market rows: %s", ticker, len(df))

    df = df.merge(oil_df, on="date_id", how="left")
    LOGGER.info("[%s] Rows after oil merge: %s", ticker, len(df))
    log_non_null_coverage(f"[{ticker}] Oil after merge", df, ["oil_close", "oil_return"])

    df = df.merge(macro_df, on="date_id", how="left")
    LOGGER.info("[%s] Rows after macro merge: %s", ticker, len(df))
    log_non_null_coverage(f"[{ticker}] Macro after merge", df, MACRO_SERIES)

    df = df.merge(index_df, on="date_id", how="left")
    LOGGER.info("[%s] Rows after index merge: %s", ticker, len(df))
    log_non_null_coverage(f"[{ticker}] Index after merge", df, ["sp500_return", "nasdaq_return"])

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
    df["oil_mean_5"] = df["oil_return"].rolling(5, min_periods=3).mean()
    df["oil_vol_5"] = df["oil_return"].rolling(5, min_periods=3).std()

    # Index features
    df["sp500_lag_1"] = df["sp500_return"].shift(1)
    df["nasdaq_lag_1"] = df["nasdaq_return"].shift(1)

    # Macro variations
    for col in MACRO_SERIES:
        if col in df.columns:
            df[f"{col}_chg"] = df[col].pct_change(fill_method=None)

    # Target : direction du jour suivant
    next_return = df["daily_return"].shift(-1)
    df["target"] = (next_return > 0).astype("float")
    df.loc[next_return.isna(), "target"] = pd.NA
    df["asset"] = ticker

    LOGGER.info("[%s] Rows after feature engineering: %s", ticker, len(df))

    return df


def build_dataset(engine):
    market_df = load_market_returns(engine)
    require_non_empty(
        market_df,
        "loading market returns",
        "smartinvest.v_market_returns_daily returned no rows.",
    )

    target_market_df = market_df[market_df["ticker"].isin(TARGET_TICKERS)].copy()
    log_rows("Target ticker market rows loaded", target_market_df)
    require_non_empty(
        target_market_df,
        "filtering target tickers",
        f"No rows found for target tickers: {', '.join(TARGET_TICKERS)}.",
    )
    LOGGER.info(
        "Market rows per target ticker before features: %s",
        target_market_df.groupby("ticker").size().to_dict(),
    )

    market_dates = target_market_df["date_id"].drop_duplicates().sort_values()

    raw_oil_df = load_oil_returns(engine)
    raw_macro_df = load_macro(engine)
    raw_index_df = load_indices(engine)

    oil_df = align_oil_to_market_dates(raw_oil_df, market_dates)
    macro_df = align_macro_to_market_dates(raw_macro_df, market_dates)
    index_df = align_indices_to_market_dates(raw_index_df, market_dates)

    frames = []
    for ticker in TARGET_TICKERS:
        ticker_df = build_features_for_ticker(
            stock_df=target_market_df,
            oil_df=oil_df,
            macro_df=macro_df,
            index_df=index_df,
            ticker=ticker
        )
        if not ticker_df.empty:
            frames.append(ticker_df)

    if not frames:
        raise ValueError(
            "Training dataset is empty after feature engineering. "
            "No target ticker produced feature rows."
        )

    df = pd.concat(frames, ignore_index=True)
    log_rows("Rows after feature engineering", df)
    LOGGER.info("Rows per ticker after feature engineering: %s", df.groupby("ticker").size().to_dict())

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
    macro_features = [*MACRO_SERIES, "FEDFUNDS_chg", "CPIAUCSL_chg", "UNRATE_chg"]
    for feat in macro_features:
        if feat in df.columns:
            feature_cols.append(feat)
    
    # Add asset dummies
    feature_cols += [c for c in df.columns if c.startswith("asset_")]

    # Filter to only features that exist
    feature_cols = [c for c in feature_cols if c in df.columns]
    feature_cols = [
        c for c in feature_cols
        if df[c].notna().sum() > 0
    ]

    if not feature_cols:
        raise ValueError(
            "Training dataset is empty after feature selection. "
            "No candidate model features have non-null values."
        )

    missing_before_drop = df[feature_cols + ["target"]].isna().sum().sort_values(ascending=False)
    LOGGER.info(
        "Top missing model columns before dropna: %s",
        missing_before_drop[missing_before_drop > 0].head(12).to_dict(),
    )

    before_dropna = len(df)
    df = df.dropna(subset=feature_cols + ["target"]).reset_index(drop=True)
    log_rows("Rows after dropna on model features", df)
    LOGGER.info("Rows removed by model-feature dropna: %s", before_dropna - len(df))
    if df.empty:
        missing_detail = missing_before_drop[missing_before_drop > 0].head(12).to_dict()
        raise ValueError(
            "Training dataset is empty after dropna on model features. "
            f"Rows before dropna: {before_dropna}. "
            f"Most missing columns: {missing_detail}. "
            "Check macro/oil/index coverage and the merge diagnostics above."
        )

    df = df.sort_values(["date_id", "ticker"]).reset_index(drop=True)
    LOGGER.info("Rows per ticker after dropna: %s", df.groupby("ticker").size().to_dict())

    X = df[feature_cols]
    y = df["target"].astype(int)
    class_distribution = y.value_counts().sort_index().to_dict()
    LOGGER.info("Class distribution after dropna: %s", class_distribution)
    if y.nunique() < 2:
        raise ValueError(
            "Training dataset has only one target class after dropna. "
            f"Class distribution: {class_distribution}."
        )

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

    split_sizes = {
        "total": n,
        "train": len(X_train),
        "valid": len(X_valid),
        "test": len(X_test),
    }
    LOGGER.info("Temporal split sizes: %s", split_sizes)
    LOGGER.info("Train class distribution: %s", y_train.value_counts().sort_index().to_dict())
    LOGGER.info("Valid class distribution: %s", y_valid.value_counts().sort_index().to_dict())
    LOGGER.info("Test class distribution: %s", y_test.value_counts().sort_index().to_dict())

    if len(X_train) == 0 or len(X_valid) == 0 or len(X_test) == 0:
        raise ValueError(
            "Temporal train/valid/test split produced an empty split. "
            f"Split sizes: {split_sizes}."
        )

    if y_train.nunique() < 2:
        raise ValueError(
            "Training split has only one target class. "
            f"Train class distribution: {y_train.value_counts().sort_index().to_dict()}."
        )

    return X_train, X_valid, X_test, y_train, y_valid, y_test


def evaluate_model(name, y_true, y_pred, y_proba):
    print(f"\n=== {name} ===")
    print("Accuracy:", round(accuracy_score(y_true, y_pred), 4))
    print("Balanced Accuracy:", round(balanced_accuracy_score(y_true, y_pred), 4))
    print("F1-score:", round(f1_score(y_true, y_pred), 4))
    if pd.Series(y_true).nunique() >= 2:
        print("ROC-AUC:", round(roc_auc_score(y_true, y_proba), 4))
    else:
        print("ROC-AUC: unavailable (only one class present in y_true)")
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

    try:
        if (
            export_classification_metrics is None
            or export_feature_importance is None
            or update_model_comparison is None
        ):
            raise RuntimeError("ML metrics exporter is unavailable")

        validation_metrics = export_classification_metrics(
            y_valid,
            valid_pred,
            labels=[0, 1],
            model_name="direction_model_xgb_validation",
        )
        test_metrics = export_classification_metrics(
            y_test,
            test_pred,
            labels=[0, 1],
            model_name="direction_model_xgb_test",
        )
        export_feature_importance(
            model,
            feature_cols,
            model_name="direction_model_xgb",
        )
        if validation_metrics:
            update_model_comparison(
                validation_metrics,
                model_name="direction_model_xgb_validation",
            )
        if test_metrics:
            update_model_comparison(
                test_metrics,
                model_name="direction_model_xgb_test",
            )
    except Exception as e:
        print(f"[ML EXPORT] Metrics export skipped: {e}")

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
