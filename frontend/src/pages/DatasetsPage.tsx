import { useState, useRef, useEffect } from "react";
import { UploadCloud, AlertTriangle, FileSpreadsheet } from "lucide-react";
import { Bezel, Label, ReadoutCard, SectionHeader } from "../components/ui";
import { useDatasets } from "../context/DatasetsContext";
import { api, QualityReport } from "../api/client";
import { ApiError } from "../api/client";

export default function DatasetsPage() {
  const { datasets, selectedDataset, setSelectedDataset, uploadDataset, projectLoading } = useDatasets();
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [report, setReport] = useState<QualityReport | null>(null);
  const [loadingReport, setLoadingReport] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (!selectedDataset) {
      setReport(null);
      return;
    }
    setLoadingReport(true);
    api
      .getQualityReport(selectedDataset.id)
      .then(setReport)
      .catch(() => setReport(null))
      .finally(() => setLoadingReport(false));
  }, [selectedDataset]);

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setError(null);
    setUploading(true);
    try {
      await uploadDataset(file);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Upload failed");
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  return (
    <div style={{ padding: 32, maxWidth: 980 }}>
      <SectionHeader
        eyebrow="Data Intake"
        title="Upload a dataset"
        description="CSV, Excel, or JSON. DataPilot profiles quality and detects domain automatically."
      />

      <input ref={fileInputRef} type="file" accept=".csv,.xlsx,.xls,.json" onChange={handleFileChange} style={{ display: "none" }} />

      <Bezel
        onClick={() => !projectLoading && !uploading && fileInputRef.current?.click()}
        style={{
          padding: "40px 24px",
          textAlign: "center",
          cursor: projectLoading || uploading ? "default" : "pointer",
          borderStyle: "dashed",
          marginBottom: 24,
        }}
      >
        <UploadCloud size={26} color="var(--color-muted)" style={{ marginBottom: 10 }} />
        <div style={{ fontSize: 14, fontWeight: 500 }}>
          {uploading ? "Uploading and profiling…" : projectLoading ? "Setting up your workspace…" : "Click to upload a file"}
        </div>
        <div className="mono" style={{ fontSize: 11, color: "var(--color-muted)", marginTop: 6 }}>
          .csv · .xlsx · .xls · .json
        </div>
      </Bezel>

      {error && <div style={{ color: "var(--color-rose)", fontSize: 13, marginBottom: 16 }}>{error}</div>}

      {datasets.length > 0 && (
        <div style={{ marginBottom: 24 }}>
          <Label>Your datasets</Label>
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            {datasets.map((d) => (
              <div
                key={d.id}
                onClick={() => setSelectedDataset(d)}
                className="mono"
                style={{
                  fontSize: 12,
                  padding: "8px 12px",
                  borderRadius: 5,
                  cursor: "pointer",
                  border: `1px solid ${selectedDataset?.id === d.id ? "var(--color-amber)" : "var(--color-hairline)"}`,
                  color: selectedDataset?.id === d.id ? "var(--color-amber)" : "var(--color-text)",
                  display: "flex",
                  alignItems: "center",
                  gap: 6,
                }}
              >
                <FileSpreadsheet size={13} />
                {d.filename}
              </div>
            ))}
          </div>
        </div>
      )}

      {loadingReport && <div className="mono" style={{ fontSize: 12, color: "var(--color-muted)" }}>LOADING QUALITY REPORT…</div>}

      {report && selectedDataset && (
        <>
          <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 16 }}>
            <span className="mono" style={{ fontSize: 12 }}>{selectedDataset.filename}</span>
            {selectedDataset.domain && (
              <span
                className="mono"
                style={{
                  fontSize: 10,
                  letterSpacing: "0.08em",
                  color: "var(--color-amber)",
                  border: "1px solid var(--color-amber)",
                  borderRadius: 3,
                  padding: "2px 8px",
                }}
              >
                DOMAIN: {selectedDataset.domain.toUpperCase()}
              </span>
            )}
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 14, marginBottom: 24 }}>
            <ReadoutCard label="Rows" value={report.row_count.toLocaleString()} />
            <ReadoutCard label="Columns" value={report.column_count} />
            <ReadoutCard label="Duplicate Rows" value={report.duplicate_row_pct} unit="%" accentColor="var(--color-rose)" />
            <ReadoutCard label="Quality Score" value={report.quality_score} unit="/ 100" accentColor="var(--color-amber)" />
          </div>

          {report.warnings.length > 0 && (
            <>
              <Label>Quality Warnings</Label>
              <Bezel style={{ padding: "6px 0" }}>
                {report.warnings.map((w, i) => (
                  <div
                    key={i}
                    style={{
                      display: "flex",
                      gap: 10,
                      alignItems: "flex-start",
                      padding: "12px 18px",
                      borderTop: i > 0 ? "1px solid var(--color-hairline)" : "none",
                    }}
                  >
                    <AlertTriangle size={14} color="var(--color-amber)" style={{ marginTop: 2, flexShrink: 0 }} />
                    <span style={{ fontSize: 13, lineHeight: 1.5 }}>{w}</span>
                  </div>
                ))}
              </Bezel>
            </>
          )}
        </>
      )}
    </div>
  );
}
