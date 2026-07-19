import { useState, FormEvent } from "react";
import { Database, ChevronRight } from "lucide-react";
import { useAuth } from "../context/AuthContext";
import { Bezel, Label } from "../components/ui";
import { ApiError } from "../api/client";

export default function LoginPage() {
  const { login, register } = useAuth();
  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      if (mode === "login") {
        await login(email, password);
      } else {
        await register(email, password, fullName || undefined);
      }
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong. Please try again.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div
      style={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: 24,
      }}
    >
      <div style={{ width: 380 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 28, justifyContent: "center" }}>
          <div
            style={{
              width: 34,
              height: 34,
              borderRadius: 6,
              background: "var(--color-panel-raised)",
              border: "1px solid var(--color-hairline)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            <Database size={17} color="var(--color-amber)" />
          </div>
          <span style={{ fontFamily: "var(--font-display)", fontSize: 20, fontWeight: 700 }}>DataPilot</span>
        </div>

        <Bezel style={{ padding: 28 }}>
          <div className="mono" style={{ fontSize: 10, letterSpacing: "0.14em", color: "var(--color-muted)", textTransform: "uppercase", marginBottom: 4 }}>
            Console access
          </div>
          <h1 style={{ fontFamily: "var(--font-display)", fontSize: 20, margin: "0 0 22px 0", fontWeight: 600 }}>
            {mode === "login" ? "Sign in to your workspace" : "Create your workspace"}
          </h1>

          <form onSubmit={handleSubmit}>
            {mode === "register" && (
              <>
                <Label>Full name</Label>
                <input className="input" value={fullName} onChange={(e) => setFullName(e.target.value)} placeholder="Jane Doe" />
                <div style={{ height: 16 }} />
              </>
            )}

            <Label>Email</Label>
            <input
              className="input"
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@company.com"
            />
            <div style={{ height: 16 }} />

            <Label>Password</Label>
            <input
              className="input"
              type="password"
              required
              minLength={8}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
            />

            {error && (
              <div style={{ color: "var(--color-rose)", fontSize: 12, marginTop: 12 }}>{error}</div>
            )}

            <button type="submit" className="btn btn-primary" disabled={submitting} style={{ width: "100%", justifyContent: "center", marginTop: 24 }}>
              {submitting ? "Please wait…" : mode === "login" ? "Sign in" : "Create account"}
              <ChevronRight size={15} />
            </button>
          </form>

          <div
            onClick={() => setMode(mode === "login" ? "register" : "login")}
            style={{ fontSize: 12, color: "var(--color-muted)", textAlign: "center", marginTop: 16, cursor: "pointer" }}
          >
            {mode === "login" ? "No account yet? Create one" : "Already have an account? Sign in"}
          </div>
        </Bezel>
      </div>
    </div>
  );
}
