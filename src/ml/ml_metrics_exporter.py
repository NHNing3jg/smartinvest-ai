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
    from PIL import Image, ImageDraw, ImageFont
except Exception:
    Image = None
    ImageDraw = None
    ImageFont = None

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


def _load_font(size: int = 18):
    if ImageFont is None:
        return None

    for font_name in ("arial.ttf", "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(font_name, size)
        except Exception:
            continue
    return ImageFont.load_default()


def _text_size(draw, text: str, font) -> tuple[int, int]:
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def _draw_centered_text(draw, box, text: str, font, fill=(20, 24, 33)) -> None:
    left, top, right, bottom = box
    width, height = _text_size(draw, text, font)
    draw.text(
        (
            left + (right - left - width) / 2,
            top + (bottom - top - height) / 2,
        ),
        text,
        fill=fill,
        font=font,
    )


def _save_confusion_matrix_png(matrix, labels, title: str, output_path: str) -> str | None:
    if Image is None or ImageDraw is None:
        print(f"[ML EXPORT] Confusion matrix PNG skipped for {title}: missing matplotlib and pillow")
        return None

    matrix_array = np.asarray(matrix, dtype=int)
    if matrix_array.size == 0:
        print(f"[ML EXPORT] Confusion matrix PNG skipped for {title}: empty matrix")
        return None

    labels = labels if labels is not None else list(range(matrix_array.shape[0]))
    labels = [str(label) for label in labels]

    image_width = 900
    image_height = 720
    margin_left = 170
    margin_top = 135
    cell_size = 170
    image = Image.new("RGB", (image_width, image_height), "white")
    draw = ImageDraw.Draw(image)

    title_font = _load_font(30)
    label_font = _load_font(20)
    value_font = _load_font(28)
    small_font = _load_font(16)

    draw.text((40, 36), title, fill=(17, 24, 39), font=title_font)
    draw.text((margin_left + 70, 92), "Predicted label", fill=(55, 65, 81), font=label_font)
    draw.text((34, margin_top + 150), "True label", fill=(55, 65, 81), font=label_font)

    max_value = max(int(matrix_array.max()), 1)
    for row_index, true_label in enumerate(labels):
        y0 = margin_top + row_index * cell_size
        _draw_centered_text(
            draw,
            (margin_left - 120, y0, margin_left - 20, y0 + cell_size),
            true_label,
            label_font,
        )

        for col_index, predicted_label in enumerate(labels):
            x0 = margin_left + col_index * cell_size
            if row_index == 0:
                _draw_centered_text(
                    draw,
                    (x0, margin_top - 60, x0 + cell_size, margin_top - 10),
                    predicted_label,
                    label_font,
                )

            value = int(matrix_array[row_index, col_index])
            intensity = int(235 - 155 * (value / max_value))
            color = (intensity, min(245, intensity + 18), 255)
            draw.rectangle(
                (x0, y0, x0 + cell_size, y0 + cell_size),
                fill=color,
                outline=(148, 163, 184),
                width=2,
            )
            value_fill = (15, 23, 42) if value / max_value < 0.65 else (255, 255, 255)
            _draw_centered_text(
                draw,
                (x0, y0, x0 + cell_size, y0 + cell_size),
                str(value),
                value_font,
                fill=value_fill,
            )

    total = int(matrix_array.sum())
    correct = int(np.trace(matrix_array))
    accuracy = correct / total if total else 0
    draw.text(
        (40, image_height - 64),
        f"Observations: {total}    Correct: {correct}    Accuracy: {accuracy:.4f}",
        fill=(55, 65, 81),
        font=small_font,
    )

    image.save(output_path)
    return output_path


def _save_feature_importance_png(importance_df: pd.DataFrame, model_name: str, output_path: str) -> str | None:
    if Image is None or ImageDraw is None:
        print(f"[ML EXPORT] Feature importance PNG skipped for {model_name}: missing matplotlib and pillow")
        return None

    if importance_df.empty:
        print(f"[ML EXPORT] Feature importance PNG skipped for {model_name}: empty importance data")
        return None

    plot_df = importance_df.head(25).copy()
    max_importance = max(float(plot_df["importance"].max()), 1e-12)

    image_width = 1200
    row_height = 34
    margin_top = 110
    margin_bottom = 60
    margin_left = 310
    margin_right = 60
    image_height = margin_top + margin_bottom + len(plot_df) * row_height

    image = Image.new("RGB", (image_width, image_height), "white")
    draw = ImageDraw.Draw(image)
    title_font = _load_font(30)
    label_font = _load_font(16)
    small_font = _load_font(14)

    draw.text((40, 36), f"{model_name} Feature Importance", fill=(17, 24, 39), font=title_font)
    draw.text((40, 74), "Top features from the trained model", fill=(75, 85, 99), font=small_font)

    bar_left = margin_left
    bar_max_width = image_width - margin_left - margin_right - 100

    for row_index, row in enumerate(plot_df.itertuples(index=False)):
        y = margin_top + row_index * row_height
        feature = str(row.feature)
        importance = float(row.importance)
        bar_width = int(bar_max_width * importance / max_importance)

        draw.text((40, y + 6), feature[:34], fill=(31, 41, 55), font=label_font)
        draw.rectangle(
            (bar_left, y + 5, bar_left + bar_max_width, y + row_height - 8),
            fill=(241, 245, 249),
        )
        draw.rectangle(
            (bar_left, y + 5, bar_left + bar_width, y + row_height - 8),
            fill=(37, 99, 235),
        )
        draw.text(
            (bar_left + bar_max_width + 16, y + 5),
            f"{importance:.4f}",
            fill=(55, 65, 81),
            font=small_font,
        )

    image.save(output_path)
    return output_path


def _require_classification_dependencies() -> bool:
    if (
        accuracy_score is None
        or precision_score is None
        or recall_score is None
        or f1_score is None
        or confusion_matrix is None
    ):
        print("[ML EXPORT] Classification export skipped: missing sklearn")
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
        if not _require_classification_dependencies():
            return {}

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

        export_model_summary(metrics, model_name)

        try:
            matrix = confusion_matrix(y_true, y_pred, labels=labels)
            matrix_path = os.path.join(
                EXPORT_DIR,
                f"{model_name}_confusion_matrix.png",
            )

            if plt is not None and ConfusionMatrixDisplay is not None:
                display = ConfusionMatrixDisplay(
                    confusion_matrix=matrix,
                    display_labels=labels,
                )
                display.plot(cmap="Blues", values_format="d")
                plt.title(f"{model_name} Confusion Matrix")
                plt.tight_layout()
                plt.savefig(matrix_path, dpi=300, bbox_inches="tight")
                plt.close()
                print(f"[ML EXPORT] Confusion matrix saved: {matrix_path}")
            else:
                saved_path = _save_confusion_matrix_png(
                    matrix,
                    labels,
                    f"{model_name} Confusion Matrix",
                    matrix_path,
                )
                if saved_path:
                    print(f"[ML EXPORT] Confusion matrix saved: {saved_path}")
        except Exception as exc:
            if plt is not None:
                plt.close()
            print(f"[ML EXPORT] Could not export confusion matrix for {model_name}: {exc}")

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

        importance_path = os.path.join(
            EXPORT_DIR,
            f"{model_name}_feature_importance.png",
        )

        if plt is not None:
            plt.figure(figsize=(11, max(6, len(importance_df) * 0.28)))
            plt.barh(importance_df["feature"], importance_df["importance"])
            plt.gca().invert_yaxis()
            plt.xlabel("Importance")
            plt.title(f"{model_name} Feature Importance")
            plt.tight_layout()
            plt.savefig(importance_path, dpi=300, bbox_inches="tight")
            plt.close()
            print(f"[ML EXPORT] Feature importance exported: {importance_path}")
            return importance_path

        saved_path = _save_feature_importance_png(
            importance_df,
            model_name,
            importance_path,
        )
        if saved_path:
            print(f"[ML EXPORT] Feature importance exported: {saved_path}")
        return saved_path
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
