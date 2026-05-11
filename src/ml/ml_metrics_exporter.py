from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Any

import numpy as np
import pandas as pd

EXPORT_DIR = os.path.join("exports", "ml_metrics")
os.environ.setdefault("MPLCONFIGDIR", os.path.join(EXPORT_DIR, ".matplotlib"))

try:
    import matplotlib.pyplot as plt
except Exception:
    plt = None

try:
    from sklearn.metrics import (
        accuracy_score,
        precision_score,
        recall_score,
        f1_score,
        confusion_matrix,
        ConfusionMatrixDisplay,
        mean_squared_error,
        mean_absolute_error,
        r2_score,
    )
except Exception:
    accuracy_score = None
    precision_score = None
    recall_score = None
    f1_score = None
    confusion_matrix = None
    ConfusionMatrixDisplay = None
    mean_squared_error = None
    mean_absolute_error = None
    r2_score = None

def ensure_export_dir() -> str:
    """Create the ML metrics export folder if it does not already exist."""
    os.makedirs(EXPORT_DIR, exist_ok=True)
    return EXPORT_DIR


def _timestamp() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _clean_value(value: Any) -> Any:
    """Convert numpy/pandas/scikit-learn values into JSON-safe Python values."""
    if value is None:
        return None

    if isinstance(value, (np.integer,)):
        return int(value)

    if isinstance(value, (np.floating,)):
        value = float(value)

    if isinstance(value, float):
        if np.isnan(value) or np.isinf(value):
            return None
        return value

    if isinstance(value, (np.ndarray, list, tuple)):
        return [_clean_value(item) for item in value]

    return value


def _clean_metrics(metrics: dict[str, Any]) -> dict[str, Any]:
    return {key: _clean_value(value) for key, value in metrics.items()}


def _save_metrics(metrics: dict[str, Any], json_path: str, csv_path: str) -> None:
    clean_metrics = _clean_metrics(metrics)

    with open(json_path, "w", encoding="utf-8") as file:
        json.dump(clean_metrics, file, indent=2)

    pd.DataFrame([clean_metrics]).to_csv(csv_path, index=False)


def _require_classification_dependencies() -> bool:
    if (
        plt is None
        or accuracy_score is None
        or precision_score is None
        or recall_score is None
        or f1_score is None
        or confusion_matrix is None
        or ConfusionMatrixDisplay is None
    ):
        print("[ML EXPORT] Classification export skipped: missing matplotlib or sklearn")
        return False
    return True


def _require_regression_dependencies() -> bool:
    if (
        plt is None
        or mean_squared_error is None
        or mean_absolute_error is None
        or r2_score is None
    ):
        print("[ML EXPORT] Regression export skipped: missing matplotlib or sklearn")
        return False
    return True


def export_model_summary(metrics: dict, model_name: str) -> str | None:
    """
    Export a readable text summary for model evidence and auditability.

    Returns the written file path, or None if the summary could not be exported.
    """
    try:
        if not _require_classification_dependencies():
            return {}

        ensure_export_dir()
        summary_path = os.path.join(EXPORT_DIR, f"{model_name}_summary.txt")
        clean_metrics = _clean_metrics(metrics)

        with open(summary_path, "w", encoding="utf-8") as file:
            file.write(f"Model Summary: {model_name}\n")
            file.write(f"Generated at: {_timestamp()}\n")
            file.write("=" * 60 + "\n\n")
            for key, value in clean_metrics.items():
                file.write(f"{key}: {value}\n")

        print(f"[ML EXPORT] Model summary exported: {summary_path}")
        return summary_path
    except Exception as exc:
        print(f"[ML EXPORT] Could not export model summary for {model_name}: {exc}")
        return None


def export_classification_metrics(
    y_true,
    y_pred,
    labels=None,
    model_name="classification_model",
):
    """
    Export weighted classification metrics plus a confusion matrix image.

    Exporter failures are logged and do not raise, so ML pipelines keep running.
    """
    try:
        ensure_export_dir()

        metrics = {
            "model_name": model_name,
            "metric_type": "classification",
            "timestamp": _timestamp(),
            "observations": int(len(y_true)),
            "accuracy": accuracy_score(y_true, y_pred),
            "precision": precision_score(
                y_true,
                y_pred,
                average="weighted",
                zero_division=0,
            ),
            "recall": recall_score(
                y_true,
                y_pred,
                average="weighted",
                zero_division=0,
            ),
            "f1_score": f1_score(
                y_true,
                y_pred,
                average="weighted",
                zero_division=0,
            ),
        }
        metrics = _clean_metrics(metrics)

        json_path = os.path.join(
            EXPORT_DIR,
            f"{model_name}_classification_metrics.json",
        )
        csv_path = os.path.join(
            EXPORT_DIR,
            f"{model_name}_classification_metrics.csv",
        )
        _save_metrics(metrics, json_path, csv_path)
        print(f"[ML EXPORT] Classification metrics exported: {json_path}")
        print(f"[ML EXPORT] Classification metrics CSV exported: {csv_path}")

        matrix = confusion_matrix(y_true, y_pred, labels=labels)
        display = ConfusionMatrixDisplay(
            confusion_matrix=matrix,
            display_labels=labels,
        )
        display.plot(cmap="Blues", values_format="d")
        plt.title(f"{model_name} Confusion Matrix")
        plt.tight_layout()

        matrix_path = os.path.join(
            EXPORT_DIR,
            f"{model_name}_confusion_matrix.png",
        )
        plt.savefig(matrix_path, dpi=300, bbox_inches="tight")
        plt.close()
        print(f"[ML EXPORT] Confusion matrix saved: {matrix_path}")

        export_model_summary(metrics, model_name)
        return metrics
    except Exception as exc:
        if plt is not None:
            plt.close()
        print(f"[ML EXPORT] Could not export classification metrics for {model_name}: {exc}")
        return {}


def export_regression_metrics(
    y_true,
    y_pred,
    model_name="regression_model",
):
    """
    Export regression metrics plus prediction and residual evidence plots.

    Exporter failures are logged and do not raise, so ML pipelines keep running.
    """
    try:
        if not _require_regression_dependencies():
            return {}

        ensure_export_dir()
        y_true_array = np.asarray(y_true, dtype=float)
        y_pred_array = np.asarray(y_pred, dtype=float)
        residuals = y_true_array - y_pred_array

        metrics = {
            "model_name": model_name,
            "metric_type": "regression",
            "timestamp": _timestamp(),
            "observations": int(len(y_true_array)),
            "rmse": float(np.sqrt(mean_squared_error(y_true_array, y_pred_array))),
            "mae": mean_absolute_error(y_true_array, y_pred_array),
            "r2": r2_score(y_true_array, y_pred_array),
        }
        metrics = _clean_metrics(metrics)

        json_path = os.path.join(
            EXPORT_DIR,
            f"{model_name}_regression_metrics.json",
        )
        csv_path = os.path.join(
            EXPORT_DIR,
            f"{model_name}_regression_metrics.csv",
        )
        _save_metrics(metrics, json_path, csv_path)
        print(f"[ML EXPORT] Regression metrics exported: {json_path}")
        print(f"[ML EXPORT] Regression metrics CSV exported: {csv_path}")

        plt.figure(figsize=(11, 6))
        plt.plot(y_true_array, label="Real values")
        plt.plot(y_pred_array, label="Predicted values")
        plt.legend()
        plt.title(f"{model_name} Prediction vs Real")
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        prediction_path = os.path.join(
            EXPORT_DIR,
            f"{model_name}_prediction_vs_real.png",
        )
        plt.savefig(prediction_path, dpi=300, bbox_inches="tight")
        plt.close()
        print(f"[ML EXPORT] Prediction vs real plot saved: {prediction_path}")

        plt.figure(figsize=(11, 6))
        plt.scatter(y_pred_array, residuals, alpha=0.7)
        plt.axhline(y=0, color="red", linestyle="--", linewidth=1)
        plt.xlabel("Predicted values")
        plt.ylabel("Residuals")
        plt.title(f"{model_name} Residual Plot")
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        residual_path = os.path.join(
            EXPORT_DIR,
            f"{model_name}_residual_plot.png",
        )
        plt.savefig(residual_path, dpi=300, bbox_inches="tight")
        plt.close()
        print(f"[ML EXPORT] Residual plot saved: {residual_path}")

        export_model_summary(metrics, model_name)
        return metrics
    except Exception as exc:
        if plt is not None:
            plt.close()
        print(f"[ML EXPORT] Could not export regression metrics for {model_name}: {exc}")
        return {}


def export_feature_importance(
    model,
    feature_names,
    model_name="model",
):
    """Export a feature importance chart when the model exposes feature_importances_."""
    try:
        if plt is None:
            print(f"[ML EXPORT] Feature importance skipped for {model_name}: missing matplotlib")
            return None

        if not hasattr(model, "feature_importances_"):
            print(f"[ML EXPORT] Feature importance skipped for {model_name}: unavailable")
            return None

        ensure_export_dir()
        importances = np.asarray(model.feature_importances_, dtype=float)
        feature_names = list(feature_names)

        if len(importances) != len(feature_names):
            print(
                f"[ML EXPORT] Feature importance skipped for {model_name}: "
                "feature count mismatch"
            )
            return None

        importance_df = pd.DataFrame(
            {
                "feature": feature_names,
                "importance": importances,
            }
        ).sort_values("importance", ascending=False)

        plt.figure(figsize=(11, max(6, len(importance_df) * 0.28)))
        plt.barh(importance_df["feature"], importance_df["importance"])
        plt.gca().invert_yaxis()
        plt.xlabel("Importance")
        plt.title(f"{model_name} Feature Importance")
        plt.tight_layout()

        importance_path = os.path.join(
            EXPORT_DIR,
            f"{model_name}_feature_importance.png",
        )
        plt.savefig(importance_path, dpi=300, bbox_inches="tight")
        plt.close()

        print(f"[ML EXPORT] Feature importance exported: {importance_path}")
        return importance_path
    except Exception as exc:
        if plt is not None:
            plt.close()
        print(f"[ML EXPORT] Could not export feature importance for {model_name}: {exc}")
        return None


def update_model_comparison(metrics: dict, model_name: str) -> str | None:
    """
    Optional SHAP-ready/model-comparison structure.

    Appends one metrics row to a CSV that can later be enriched with explainability
    artifacts such as SHAP summaries.
    """
    try:
        ensure_export_dir()
        comparison_path = os.path.join(EXPORT_DIR, "model_comparison.csv")
        row = _clean_metrics({"model_name": model_name, **metrics})
        row["shap_ready"] = True

        if os.path.exists(comparison_path):
            comparison_df = pd.read_csv(comparison_path)
            comparison_df = pd.concat([comparison_df, pd.DataFrame([row])], ignore_index=True)
        else:
            comparison_df = pd.DataFrame([row])

        comparison_df.to_csv(comparison_path, index=False)
        print(f"[ML EXPORT] Model comparison updated: {comparison_path}")
        return comparison_path
    except Exception as exc:
        print(f"[ML EXPORT] Could not update model comparison for {model_name}: {exc}")
        return None
