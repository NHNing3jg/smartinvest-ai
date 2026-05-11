import { BarChart3, BrainCircuit, CheckCircle2, FileText, Gauge, GitCompareArrows, ImageOff, Target } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import ErrorMessage from "../components/ui/ErrorMessage";
import KpiCard from "../components/ui/KpiCard";
import Loader from "../components/ui/Loader";
import type { ModelClassificationMetrics, ModelComparisonRow, ModelMetricKey } from "../types/modelEvaluation";

const BASE_PATH = "/ml_metrics";

const ARTIFACTS = {
  validationMetrics: `${BASE_PATH}/direction_model_xgb_validation_classification_metrics.json`,
  testMetrics: `${BASE_PATH}/direction_model_xgb_test_classification_metrics.json`,
  validationSummary: `${BASE_PATH}/direction_model_xgb_validation_summary.txt`,
  testSummary: `${BASE_PATH}/direction_model_xgb_test_summary.txt`,
  modelComparison: `${BASE_PATH}/model_comparison.csv`,
  validationMatrix: `${BASE_PATH}/direction_model_xgb_validation_confusion_matrix.png`,
  testMatrix: `${BASE_PATH}/direction_model_xgb_test_confusion_matrix.png`,
  featureImportance: `${BASE_PATH}/direction_model_xgb_feature_importance.png`,
};

const METRIC_KEYS: ModelMetricKey[] = ["accuracy", "precision", "recall", "f1_score"];

type EvidenceState = {
  validationMetrics: ModelClassificationMetrics | null;
  testMetrics: ModelClassificationMetrics | null;
  validationSummary: string | null;
  testSummary: string | null;
  comparisonRows: ModelComparisonRow[];
};

const emptyEvidence: EvidenceState = {
  validationMetrics: null,
  testMetrics: null,
  validationSummary: null,
  testSummary: null,
  comparisonRows: [],
};

const isRecord = (value: unknown): value is Record<string, unknown> =>
  typeof value === "object" && value !== null && !Array.isArray(value);

const parseNumber = (value: unknown) => {
  if (typeof value === "number") {
    return Number.isFinite(value) ? value : null;
  }

  if (typeof value === "string" && value.trim() !== "") {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : null;
  }

  return null;
};

const normalizeMetrics = (payload: unknown): ModelClassificationMetrics | null => {
  if (!isRecord(payload)) {
    return null;
  }

  const accuracy = parseNumber(payload.accuracy);
  const precision = parseNumber(payload.precision);
  const recall = parseNumber(payload.recall);
  const f1Score = parseNumber(payload.f1_score);
  const observations = parseNumber(payload.observations);

  if (
    accuracy === null ||
    precision === null ||
    recall === null ||
    f1Score === null ||
    observations === null
  ) {
    return null;
  }

  return {
    model_name: String(payload.model_name ?? "direction_model_xgb"),
    metric_type: String(payload.metric_type ?? "classification"),
    timestamp: String(payload.timestamp ?? ""),
    observations,
    accuracy,
    precision,
    recall,
    f1_score: f1Score,
  };
};

const fetchJson = async (path: string) => {
  const response = await fetch(path, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`${path} returned ${response.status}`);
  }
  return response.json() as Promise<unknown>;
};

const fetchText = async (path: string) => {
  const response = await fetch(path, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`${path} returned ${response.status}`);
  }
  return response.text();
};

const parseCsvLine = (line: string) => {
  const cells: string[] = [];
  let current = "";
  let inQuotes = false;

  for (let index = 0; index < line.length; index += 1) {
    const char = line[index];
    const nextChar = line[index + 1];

    if (char === '"' && nextChar === '"') {
      current += '"';
      index += 1;
    } else if (char === '"') {
      inQuotes = !inQuotes;
    } else if (char === "," && !inQuotes) {
      cells.push(current);
      current = "";
    } else {
      current += char;
    }
  }

  cells.push(current);
  return cells;
};

const parseCsv = (csv: string): ModelComparisonRow[] => {
  const lines = csv.split(/\r?\n/).filter((line) => line.trim() !== "");

  if (lines.length < 2) {
    return [];
  }

  const headers = parseCsvLine(lines[0]);
  return lines.slice(1).map((line) => {
    const cells = parseCsvLine(line);
    return headers.reduce<ModelComparisonRow>((row, header, index) => {
      row[header] = cells[index] ?? "";
      return row;
    }, {});
  });
};

const formatMetricLabel = (key: ModelMetricKey) =>
  key === "f1_score" ? "F1 Score" : key.charAt(0).toUpperCase() + key.slice(1);

const formatPercentMetric = (value: number | null | undefined) => {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return "N/A";
  }

  return `${(value * 100).toFixed(2)}%`;
};

const formatCount = (value: number | null | undefined) => {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return "N/A";
  }

  return Math.round(value).toLocaleString();
};

function EvidenceImage({ title, src }: { title: string; src: string }) {
  const [hasError, setHasError] = useState(false);

  return (
    <div className="model-evidence-card">
      <div className="panel-heading-row">
        <div>
          <span className="eyebrow">Evidence Image</span>
          <h2>{title}</h2>
        </div>
      </div>
      {hasError ? (
        <div className="model-artifact-missing">
          <ImageOff size={28} />
          <strong>Artifact not found</strong>
          <span>{src}</span>
        </div>
      ) : (
        <img src={src} alt={title} onError={() => setHasError(true)} />
      )}
    </div>
  );
}

function SummaryBlock({ title, text }: { title: string; text: string | null }) {
  return (
    <div className="content-panel model-summary-panel">
      <div className="panel-heading-row">
        <div>
          <span className="eyebrow">Summary TXT</span>
          <h2>{title}</h2>
        </div>
        <FileText size={22} />
      </div>
      {text ? (
        <pre>{text}</pre>
      ) : (
        <div className="model-artifact-missing compact">
          <strong>Summary not found</strong>
          <span>The TXT export is not available in /ml_metrics.</span>
        </div>
      )}
    </div>
  );
}

function ComparisonTable({
  validationMetrics,
  testMetrics,
}: {
  validationMetrics: ModelClassificationMetrics | null;
  testMetrics: ModelClassificationMetrics | null;
}) {
  return (
    <div className="recommendation-table-wrap">
      <table className="recommendation-table model-evaluation-table">
        <thead>
          <tr>
            <th scope="col">Split</th>
            <th scope="col">Accuracy</th>
            <th scope="col">Precision</th>
            <th scope="col">Recall</th>
            <th scope="col">F1 Score</th>
            <th scope="col">Observations</th>
          </tr>
        </thead>
        <tbody>
          {[
            ["Validation", validationMetrics] as const,
            ["Test", testMetrics] as const,
          ].map(([label, metrics]) => (
            <tr key={label}>
              <td data-label="Split">{label}</td>
              <td data-label="Accuracy">{formatPercentMetric(metrics?.accuracy)}</td>
              <td data-label="Precision">{formatPercentMetric(metrics?.precision)}</td>
              <td data-label="Recall">{formatPercentMetric(metrics?.recall)}</td>
              <td data-label="F1 Score">{formatPercentMetric(metrics?.f1_score)}</td>
              <td data-label="Observations">{formatCount(metrics?.observations)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function ModelComparisonCsvTable({ rows }: { rows: ModelComparisonRow[] }) {
  const columns = useMemo(() => {
    const preferred = ["model_name", "metric_type", "observations", "accuracy", "precision", "recall", "f1_score", "shap_ready"];
    const available = new Set(rows.flatMap((row) => Object.keys(row)));
    return preferred.filter((column) => available.has(column));
  }, [rows]);

  if (rows.length === 0 || columns.length === 0) {
    return (
      <div className="table-empty-state">
        <strong>No model comparison CSV available</strong>
        <span>Expected /ml_metrics/model_comparison.csv.</span>
      </div>
    );
  }

  return (
    <div className="recommendation-table-wrap">
      <table className="recommendation-table model-comparison-table">
        <thead>
          <tr>
            {columns.map((column) => (
              <th key={column} scope="col">
                {column.replace(/_/g, " ")}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, rowIndex) => (
            <tr key={`${row.model_name ?? "model"}-${rowIndex}`}>
              {columns.map((column) => (
                <td key={column} data-label={column.replace(/_/g, " ")}>
                  {column in row && row[column] !== "" ? row[column] : "N/A"}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default function ModelEvaluation() {
  const [evidence, setEvidence] = useState<EvidenceState>(emptyEvidence);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;

    const loadEvidence = async () => {
      setIsLoading(true);
      setErrorMessage(null);

      const [validationMetrics, testMetrics, validationSummary, testSummary, comparisonCsv] = await Promise.allSettled([
        fetchJson(ARTIFACTS.validationMetrics),
        fetchJson(ARTIFACTS.testMetrics),
        fetchText(ARTIFACTS.validationSummary),
        fetchText(ARTIFACTS.testSummary),
        fetchText(ARTIFACTS.modelComparison),
      ]);

      const normalizedValidation =
        validationMetrics.status === "fulfilled" ? normalizeMetrics(validationMetrics.value) : null;
      const normalizedTest = testMetrics.status === "fulfilled" ? normalizeMetrics(testMetrics.value) : null;

      if (!isMounted) {
        return;
      }

      setEvidence({
        validationMetrics: normalizedValidation,
        testMetrics: normalizedTest,
        validationSummary: validationSummary.status === "fulfilled" ? validationSummary.value : null,
        testSummary: testSummary.status === "fulfilled" ? testSummary.value : null,
        comparisonRows: comparisonCsv.status === "fulfilled" ? parseCsv(comparisonCsv.value) : [],
      });

      if (!normalizedValidation || !normalizedTest) {
        setErrorMessage("Classification metric JSON files could not be loaded from /ml_metrics.");
      }

      setIsLoading(false);
    };

    void loadEvidence();

    return () => {
      isMounted = false;
    };
  }, []);

  const validation = evidence.validationMetrics;
  const test = evidence.testMetrics;

  return (
    <section className="page-stack model-evaluation-page">
      <div className="page-hero hero-model-evaluation">
        <div className="hero-copy">
          <span className="eyebrow">Model Evaluation</span>
          <h1>XGBoost Direction Evidence</h1>
          <p>Review validation and test metrics, confusion matrices, feature importance, summaries, and comparison exports.</p>
        </div>
        <div className="hero-visual" aria-hidden="true">
          <div className="model-evaluation-orbit">
            <BrainCircuit size={38} />
            <span />
            <span />
            <span />
          </div>
        </div>
      </div>

      {isLoading && (
        <div className="content-panel split-panel">
          <BarChart3 className="panel-icon" size={32} />
          <Loader label="Loading ML evaluation evidence" />
        </div>
      )}

      {!isLoading && errorMessage && <ErrorMessage title="Model evidence unavailable" message={errorMessage} />}

      {!isLoading && (
        <>
          <div className="kpi-grid model-kpi-grid">
            <KpiCard
              title="Validation Accuracy"
              value={formatPercentMetric(validation?.accuracy)}
              detail="Held-out validation split"
              icon={Gauge}
              tone="neutral"
            />
            <KpiCard
              title="Validation Precision"
              value={formatPercentMetric(validation?.precision)}
              detail="Weighted precision"
              icon={Target}
              tone="neutral"
            />
            <KpiCard
              title="Validation Recall"
              value={formatPercentMetric(validation?.recall)}
              detail="Weighted recall"
              icon={CheckCircle2}
              tone="neutral"
            />
            <KpiCard
              title="Validation F1"
              value={formatPercentMetric(validation?.f1_score)}
              detail="Weighted F1 score"
              icon={GitCompareArrows}
              tone="neutral"
            />
            <KpiCard
              title="Test Accuracy"
              value={formatPercentMetric(test?.accuracy)}
              detail="Final test split"
              icon={Gauge}
              tone="positive"
            />
            <KpiCard
              title="Test Precision"
              value={formatPercentMetric(test?.precision)}
              detail="Weighted precision"
              icon={Target}
              tone="positive"
            />
            <KpiCard
              title="Test Recall"
              value={formatPercentMetric(test?.recall)}
              detail="Weighted recall"
              icon={CheckCircle2}
              tone="positive"
            />
            <KpiCard
              title="Test F1"
              value={formatPercentMetric(test?.f1_score)}
              detail="Weighted F1 score"
              icon={GitCompareArrows}
              tone="positive"
            />
          </div>

          <div className="content-panel recommendation-panel">
            <div className="panel-heading-row">
              <div>
                <span className="eyebrow">Validation vs Test</span>
                <h2>Classification Metrics</h2>
              </div>
            </div>
            <ComparisonTable validationMetrics={validation} testMetrics={test} />
          </div>

          <div className="model-metric-strip">
            {METRIC_KEYS.map((metricKey) => {
              const validationValue = validation?.[metricKey] ?? null;
              const testValue = test?.[metricKey] ?? null;
              const delta = validationValue !== null && testValue !== null ? testValue - validationValue : null;

              return (
                <div key={metricKey} className="model-delta-tile">
                  <span>{formatMetricLabel(metricKey)}</span>
                  <strong>{delta === null ? "N/A" : `${delta >= 0 ? "+" : ""}${(delta * 100).toFixed(2)} pts`}</strong>
                  <em>test minus validation</em>
                </div>
              );
            })}
          </div>

          <div className="model-evidence-grid">
            <EvidenceImage title="Validation Confusion Matrix" src={ARTIFACTS.validationMatrix} />
            <EvidenceImage title="Test Confusion Matrix" src={ARTIFACTS.testMatrix} />
            <EvidenceImage title="Feature Importance" src={ARTIFACTS.featureImportance} />
          </div>

          <div className="model-summary-grid">
            <SummaryBlock title="Validation Summary" text={evidence.validationSummary} />
            <SummaryBlock title="Test Summary" text={evidence.testSummary} />
          </div>

          <div className="content-panel recommendation-panel">
            <div className="panel-heading-row">
              <div>
                <span className="eyebrow">Model Comparison CSV</span>
                <h2>Comparison Export</h2>
              </div>
            </div>
            <ModelComparisonCsvTable rows={evidence.comparisonRows} />
          </div>
        </>
      )}
    </section>
  );
}
