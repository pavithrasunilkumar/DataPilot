import { useState, useRef, useEffect } from "react";
import { Send, Sparkles, AlertTriangle, GitCompare } from "lucide-react";
import { Bezel, Label, SectionHeader } from "../components/ui";
import { useDatasets } from "../context/DatasetsContext";
import { api, AskResponse } from "../api/client";
import { ApiError } from "../api/client";

interface Message {
  role: "user" | "assistant";
  text?: string;
  data?: AskResponse;
}

const SEVERITY_COLOR: Record<string, string> = {
  high: "var(--color-rose)",
  medium: "var(--color-amber)",
  low: "var(--color-muted)",
  info: "var(--color-teal)",
};

export default function AskAnalystPage() {
  const { selectedDataset } = useDatasets();
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [thinking, setThinking] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, thinking]);

  const ask = async (question: string) => {
    if (!question.trim() || !selectedDataset) return;
    setMessages((m) => [...m, { role: "user", text: question }]);
    setInput("");
    setThinking(true);
    setError(null);
    try {
      const response = await api.askAnalyst(selectedDataset.id, question);
      setMessages((m) => [...m, { role: "assistant", data: response }]);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong answering that question.");
    } finally {
      setThinking(false);
    }
  };

  if (!selectedDataset) {
    return (
      <div style={{ padding: 32 }}>
        <SectionHeader eyebrow="AI Analyst" title="Ask a question" description="Upload a dataset first — you'll pick it here once it's ready." />
        <div style={{ color: "var(--color-muted)", fontSize: 13 }}>No dataset selected yet.</div>
      </div>
    );
  }

  return (
    <div style={{ padding: 32, maxWidth: 820, display: "flex", flexDirection: "column", height: "100%", boxSizing: "border-box" }}>
      <SectionHeader
        eyebrow={`AI Analyst · ${selectedDataset.filename}`}
        title="Ask a question about your data"
        description="Answers are backed by real SQL execution and statistical tests — never model guesswork."
      />

      <div ref={scrollRef} className="scrollbar-thin" style={{ flex: 1, overflowY: "auto", marginBottom: 16 }}>
        {messages.length === 0 && (
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 8 }}>
            {["Why did revenue change recently?", "Forecast revenue for next month"].map((q) => (
              <div
                key={q}
                onClick={() => ask(q)}
                style={{
                  fontSize: 12,
                  color: "var(--color-muted)",
                  cursor: "pointer",
                  border: "1px solid var(--color-hairline)",
                  borderRadius: 5,
                  padding: "8px 12px",
                }}
              >
                {q}
              </div>
            ))}
          </div>
        )}

        {messages.map((m, i) =>
          m.role === "user" ? (
            <div key={i} style={{ display: "flex", justifyContent: "flex-end", marginBottom: 14 }}>
              <div
                style={{
                  fontSize: 13,
                  background: "var(--color-panel-raised)",
                  border: "1px solid var(--color-hairline)",
                  borderRadius: 5,
                  padding: "10px 14px",
                  maxWidth: "80%",
                }}
              >
                {m.text}
              </div>
            </div>
          ) : (
            <Bezel key={i} style={{ padding: 18, marginBottom: 14 }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
                <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                  <Sparkles size={13} color="var(--color-amber)" />
                  <span className="mono" style={{ fontSize: 10, letterSpacing: "0.1em", color: "var(--color-amber)" }}>ANALYSIS</span>
                </div>
                <span className="mono" style={{ fontSize: 10, color: "var(--color-teal)" }}>
                  CONFIDENCE {m.data!.confidence_score}%
                </span>
              </div>

              <Label>Generated SQL</Label>
              <pre
                className="mono"
                style={{
                  fontSize: 11.5,
                  background: "var(--color-void)",
                  border: "1px solid var(--color-hairline)",
                  borderRadius: 5,
                  padding: 12,
                  margin: "0 0 16px 0",
                  overflowX: "auto",
                  lineHeight: 1.6,
                  whiteSpace: "pre-wrap",
                }}
              >
                {m.data!.sql}
              </pre>

              {m.data!.result.length > 0 && (
                <>
                  <Label>Result ({m.data!.result.length} rows)</Label>
                  <div className="mono" style={{ fontSize: 11, marginBottom: 16, overflowX: "auto" }}>
                    <table style={{ borderCollapse: "collapse", width: "100%" }}>
                      <thead>
                        <tr>
                          {Object.keys(m.data!.result[0]).map((col) => (
                            <th key={col} style={{ textAlign: "left", padding: "4px 10px", borderBottom: "1px solid var(--color-hairline)", color: "var(--color-muted)" }}>
                              {col}
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {m.data!.result.slice(0, 12).map((row, ri) => (
                          <tr key={ri}>
                            {Object.values(row).map((val, ci) => (
                              <td key={ci} style={{ padding: "4px 10px", borderBottom: "1px solid var(--color-hairline)" }}>
                                {String(val)}
                              </td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </>
              )}

              <Label>Explanation</Label>
              <p style={{ fontSize: 13, lineHeight: 1.6, margin: "0 0 16px 0" }}>{m.data!.explanation}</p>

              {m.data!.diff_summary && (
                <div style={{ display: "flex", gap: 8, marginBottom: 16, padding: 10, background: "var(--color-panel-raised)", borderRadius: 5 }}>
                  <GitCompare size={14} color="var(--color-teal)" style={{ flexShrink: 0, marginTop: 2 }} />
                  <span style={{ fontSize: 12.5, lineHeight: 1.5 }}>{m.data!.diff_summary}</span>
                </div>
              )}

              <Label>Skeptic Agent — Trust Level: {m.data!.critique.trust_level.toUpperCase()}</Label>
              {m.data!.critique.flags.map((flag, fi) => (
                <div key={fi} style={{ display: "flex", gap: 8, marginBottom: 8, alignItems: "flex-start" }}>
                  <AlertTriangle size={13} color={SEVERITY_COLOR[flag.severity]} style={{ marginTop: 2, flexShrink: 0 }} />
                  <span style={{ fontSize: 12, color: "var(--color-muted)", lineHeight: 1.5 }}>{flag.message}</span>
                </div>
              ))}
            </Bezel>
          )
        )}

        {thinking && <div className="mono" style={{ fontSize: 11, color: "var(--color-muted)", letterSpacing: "0.08em" }}>RUNNING ANALYSIS…</div>}
        {error && <div style={{ color: "var(--color-rose)", fontSize: 13 }}>{error}</div>}
      </div>

      <div style={{ display: "flex", gap: 10 }}>
        <input
          className="input"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && ask(input)}
          placeholder="Ask about trends, forecasts, anomalies…"
          style={{ flex: 1 }}
        />
        <button className="btn btn-primary" onClick={() => ask(input)} disabled={thinking}>
          <Send size={14} />
        </button>
      </div>
    </div>
  );
}
