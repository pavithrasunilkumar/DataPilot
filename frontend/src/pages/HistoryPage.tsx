import { useEffect, useState } from "react";
import { Clock } from "lucide-react";
import { Bezel, Label, SectionHeader } from "../components/ui";
import { useDatasets } from "../context/DatasetsContext";
import { api, Insight } from "../api/client";

export default function HistoryPage() {
  const { selectedDataset } = useDatasets();
  const [insights, setInsights] = useState<Insight[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!selectedDataset) return;
    setLoading(true);
    api
      .getInsightHistory(selectedDataset.id)
      .then(setInsights)
      .finally(() => setLoading(false));
  }, [selectedDataset]);

  if (!selectedDataset) {
    return (
      <div style={{ padding: 32 }}>
        <SectionHeader eyebrow="History" title="Insight history" description="Select a dataset to see its question history." />
      </div>
    );
  }

  return (
    <div style={{ padding: 32, maxWidth: 820 }}>
      <SectionHeader eyebrow={`History · ${selectedDataset.filename}`} title="Past questions & findings" description="Every AI Analyst answer on this dataset, most recent first." />

      {loading && <div className="mono" style={{ fontSize: 12, color: "var(--color-muted)" }}>LOADING…</div>}

      {!loading && insights.length === 0 && (
        <div style={{ color: "var(--color-muted)", fontSize: 13 }}>No questions asked on this dataset yet.</div>
      )}

      {insights.map((insight) => (
        <Bezel key={insight.id} style={{ padding: 16, marginBottom: 12 }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
              <Clock size={12} color="var(--color-muted)" />
              <span className="mono" style={{ fontSize: 10, color: "var(--color-muted)" }}>
                {new Date(insight.created_at).toLocaleString()}
              </span>
            </div>
            {insight.confidence_score != null && (
              <span className="mono" style={{ fontSize: 10, color: "var(--color-teal)" }}>
                {insight.confidence_score}% CONFIDENCE
              </span>
            )}
          </div>
          <div style={{ fontSize: 13, fontWeight: 500, marginBottom: 6 }}>{insight.question}</div>
          <div style={{ fontSize: 12.5, color: "var(--color-muted)", lineHeight: 1.5 }}>{insight.explanation}</div>
          {insight.diff_summary && (
            <div style={{ fontSize: 12, color: "var(--color-teal)", marginTop: 8, fontStyle: "italic" }}>
              {insight.diff_summary}
            </div>
          )}
        </Bezel>
      ))}
    </div>
  );
}
