import { useEffect, useState } from "react";
import { Download, FileText, Sparkles, Brain } from "lucide-react";
import {
  LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from "recharts";
import { Bezel, Label, ReadoutCard, SectionHeader } from "../components/ui";
import { useDatasets } from "../context/DatasetsContext";
import { api, DashboardSpec, AutonomousAnalysis, ModelResult, CleaningResult, ApiError } from "../api/client";

const CHART_COLORS = ["#f0a94e", "#45c6b8", "#e2617a", "#7c8794"];

function downloadBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

export default function DashboardPage() {
  const { selectedDataset } = useDatasets();
  const [dashboard, setDashboard] = useState<DashboardSpec | null>(null);
  const [analysis, setAnalysis] = useState<AutonomousAnalysis | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [cleaning, setCleaning] = useState(false);
  const [cleaningResult, setCleaningResult] = useState<CleaningResult | null>(null);

  const [targetColumn, setTargetColumn] = useState("");
  const [training, setTraining] = useState(false);
  const [modelResult, setModelResult] = useState<ModelResult | null>(null);
  const [trainError, setTrainError] = useState<string | null>(null);

  const [exporting, setExporting] = useState<"csv" | "pdf" | null>(null);

  const loadDashboard = async () => {
    if (!selectedDataset) return;
    setLoading(true);
    setError(null);
    try {
      const [dash, ana] = await Promise.all([
        api.getDashboard(selectedDataset.id),
        api.getAnalysis(selectedDataset.id),
      ]);
      setDashboard(dash);
      setAnalysis(ana);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to load dashboard");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDashboard();
    setCleaningResult(null);
    setModelResult(null);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedDataset]);

  const handleClean = async () => {
    if (!selectedDataset) return;
    setCleaning(true);
    try {
      const result = await api.cleanDataset(selectedDataset.id);
      setCleaningResult(result);
      await loadDashboard();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Cleaning failed");
    } finally {
      setCleaning(false);
    }
  };

  const handleTrain = async () => {
    if (!selectedDataset || !targetColumn.trim()) return;
    setTraining(true);
    setTrainError(null);
    try {
      const result = await api.trainModel(selectedDataset.id, targetColumn.trim());
      setModelResult(result);
      await loadDashboard();
    } catch (err) {
      setTrainError(err instanceof ApiError ? err.message : "Training failed");
    } finally {
      setTraining(false);
    }
  };

  const handleExport = async (type: "csv" | "pdf") => {
    if (!selectedDataset) return;
    setExporting(type);
    try {
      if (type === "csv") {
        const blob = await api.downloadCleanedCsv(selectedDataset.id);
        downloadBlob(blob, `cleaned_${selectedDataset.filename}`);
      } else {
        const blob = await api.downloadPdfReport(selectedDataset.id);
        downloadBlob(blob, `datapilot_report_${selectedDataset.filename}.pdf`);
      }
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Export failed");
    } finally {
      setExporting(null);
    }
  };

  if (!selectedDataset) {
    return (
      <div style={{ padding: 32 }}>
        <SectionHeader eyebrow="Dashboard" title="No dataset selected" description="Upload a dataset from Data Intake first." />
      </div>
    );
  }

  return (
    <div style={{ padding: 32, maxWidth: 1080 }}>
      <SectionHeader
        eyebrow={`Dashboard · ${selectedDataset.filename}${dashboard?.domain ? ` · ${dashboard.domain.toUpperCase()}` : ""}`}
        title="Auto-generated dashboard"
        description="Rebuilt from the current (cleaned, if available) version of this dataset."
      />

      <div style={{ display: "flex", gap: 10, marginBottom: 24, flexWrap: "wrap" }}>
        <button className="btn btn-primary" onClick={handleClean} disabled={cleaning}>
          <Sparkles size={14} /> {cleaning ? "Cleaning…" : "Auto Clean Dataset"}
        </button>
        <button className="btn" onClick={() => handleExport("csv")} disabled={exporting === "csv"}>
          <Download size={14} /> {exporting === "csv" ? "Downloading…" : "Download Cleaned CSV"}
        </button>
        <button className="btn" onClick={() => handleExport("pdf")} disabled={exporting === "pdf"}>
          <FileText size={14} /> {exporting === "pdf" ? "Generating…" : "Download PDF Report"}
        </button>
      </div>

      {cleaningResult && (
        <Bezel style={{ padding: 16, marginBottom: 20 }}>
          <Label>Cleaning Result</Label>
          <div style={{ fontSize: 13 }}>
            Quality score: <b>{cleaningResult.quality_score_before}</b> → <b style={{ color: "var(--color-teal)" }}>{cleaningResult.quality_score_after}</b>
            {" · "}Rows: {cleaningResult.cleaning_report.rows_before} → {cleaningResult.cleaning_report.rows_after}
            {" · "}Duplicates removed: {cleaningResult.cleaning_report.duplicate_rows_removed}
          </div>
          {cleaningResult.cleaning_report.columns_flagged_for_manual_review.length > 0 && (
            <div style={{ fontSize: 12, color: "var(--color-amber)", marginTop: 6 }}>
              Flagged for manual review (too much missing data to auto-impute): {cleaningResult.cleaning_report.columns_flagged_for_manual_review.join(", ")}
            </div>
          )}
        </Bezel>
      )}

      {error && <div style={{ color: "var(--color-rose)", fontSize: 13, marginBottom: 16 }}>{error}</div>}
      {loading && <div className="mono" style={{ fontSize: 12, color: "var(--color-muted)" }}>LOADING DASHBOARD…</div>}

      {dashboard && (
        <>
          <div style={{ display: "grid", gridTemplateColumns: `repeat(${Math.min(dashboard.kpi_cards.length, 4)}, 1fr)`, gap: 14, marginBottom: 24 }}>
            {dashboard.kpi_cards.map((kpi, i) => (
              <ReadoutCard key={i} label={kpi.label} value={kpi.value} unit={kpi.unit} />
            ))}
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "1.3fr 1fr", gap: 14, marginBottom: 14 }}>
            {dashboard.time_series && (
              <Bezel style={{ padding: 20 }}>
                <Label>{dashboard.time_series.value_column} over time</Label>
                <div style={{ height: 200 }}>
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={dashboard.time_series.data}>
                      <CartesianGrid stroke="var(--color-hairline)" vertical={false} />
                      <XAxis dataKey="period" stroke="var(--color-muted)" tick={{ fontSize: 10 }} axisLine={{ stroke: "var(--color-hairline)" }} tickLine={false} />
                      <YAxis stroke="var(--color-muted)" tick={{ fontSize: 10 }} axisLine={false} tickLine={false} />
                      <Tooltip contentStyle={{ background: "var(--color-panel-raised)", border: "1px solid var(--color-hairline)", fontSize: 12 }} />
                      <Line type="monotone" dataKey="value" stroke="var(--color-amber)" strokeWidth={2} dot={{ r: 2 }} />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </Bezel>
            )}

            {Object.entries(dashboard.bar_charts).slice(0, 1).map(([col, data]) => (
              <Bezel key={col} style={{ padding: 20 }}>
                <Label>Top {col} values</Label>
                <div style={{ height: 200 }}>
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={data}>
                      <CartesianGrid stroke="var(--color-hairline)" vertical={false} />
                      <XAxis dataKey="category" stroke="var(--color-muted)" tick={{ fontSize: 10 }} axisLine={{ stroke: "var(--color-hairline)" }} tickLine={false} />
                      <YAxis stroke="var(--color-muted)" tick={{ fontSize: 10 }} axisLine={false} tickLine={false} />
                      <Tooltip contentStyle={{ background: "var(--color-panel-raised)", border: "1px solid var(--color-hairline)", fontSize: 12 }} />
                      <Bar dataKey="count" fill="var(--color-teal)" radius={[3, 3, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </Bezel>
            ))}
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: 14, marginBottom: 14 }}>
            {Object.entries(dashboard.histograms).slice(0, 2).map(([col, data]) => (
              <Bezel key={col} style={{ padding: 20 }}>
                <Label>Distribution — {col}</Label>
                <div style={{ height: 160 }}>
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={data}>
                      <XAxis dataKey="bucket" stroke="var(--color-muted)" tick={{ fontSize: 9 }} axisLine={{ stroke: "var(--color-hairline)" }} tickLine={false} interval={1} />
                      <YAxis stroke="var(--color-muted)" tick={{ fontSize: 10 }} axisLine={false} tickLine={false} />
                      <Tooltip contentStyle={{ background: "var(--color-panel-raised)", border: "1px solid var(--color-hairline)", fontSize: 12 }} />
                      <Bar dataKey="count" fill="var(--color-amber)" radius={[2, 2, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </Bezel>
            ))}
          </div>

          {dashboard.feature_importance && (
            <Bezel style={{ padding: 20, marginBottom: 14 }}>
              <Label>Feature Importance (trained model)</Label>
              <div style={{ height: 220 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={dashboard.feature_importance} layout="vertical">
                    <XAxis type="number" stroke="var(--color-muted)" tick={{ fontSize: 10 }} axisLine={false} tickLine={false} />
                    <YAxis dataKey="feature" type="category" stroke="var(--color-muted)" tick={{ fontSize: 11 }} axisLine={false} tickLine={false} width={110} />
                    <Tooltip contentStyle={{ background: "var(--color-panel-raised)", border: "1px solid var(--color-hairline)", fontSize: 12 }} />
                    <Bar dataKey="importance" fill="var(--color-rose)" radius={[0, 3, 3, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </Bezel>
          )}
        </>
      )}

      {analysis && (
        <Bezel style={{ padding: 20, marginBottom: 14 }}>
          <Label>Autonomous Analysis</Label>
          <p style={{ fontSize: 13, lineHeight: 1.6, marginBottom: 12 }}>{analysis.summary}</p>
          {analysis.correlations.top_pairs.length > 0 && (
            <>
              <div className="mono" style={{ fontSize: 10, color: "var(--color-muted)", marginBottom: 6 }}>STRONGEST CORRELATIONS</div>
              {analysis.correlations.top_pairs.slice(0, 5).map((p, i) => (
                <div key={i} style={{ fontSize: 12, marginBottom: 4 }}>
                  {p.column_a} ↔ {p.column_b}: <b style={{ color: Math.abs(p.correlation) > 0.5 ? "var(--color-amber)" : "var(--color-text)" }}>{p.correlation.toFixed(2)}</b>
                </div>
              ))}
            </>
          )}
        </Bezel>
      )}

      <Bezel style={{ padding: 20 }}>
        <Label>Train a Predictive Model</Label>
        <div style={{ display: "flex", gap: 10, marginBottom: 12 }}>
          <input
            className="input"
            placeholder="Target column (e.g. churn)"
            value={targetColumn}
            onChange={(e) => setTargetColumn(e.target.value)}
            style={{ flex: 1 }}
          />
          <button className="btn btn-primary" onClick={handleTrain} disabled={training || !targetColumn.trim()}>
            <Brain size={14} /> {training ? "Training…" : "Train"}
          </button>
        </div>
        {trainError && <div style={{ color: "var(--color-rose)", fontSize: 12, marginBottom: 8 }}>{trainError}</div>}
        {modelResult && (
          <div style={{ fontSize: 13 }}>
            <div style={{ marginBottom: 6 }}>
              Best model: <b>{modelResult.chosen_model}</b> · Accuracy: <b>{(modelResult.boosted_model.metrics.accuracy * 100).toFixed(1)}%</b>
              {" · "}F1: <b>{modelResult.boosted_model.metrics.f1}</b>
            </div>
            <div className="mono" style={{ fontSize: 11, color: "var(--color-muted)" }}>
              Trained on {modelResult.n_train} rows, evaluated on {modelResult.n_test} held-out rows.
            </div>
          </div>
        )}
      </Bezel>
    </div>
  );
}
