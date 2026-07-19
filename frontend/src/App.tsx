import { BrowserRouter, Routes, Route, Navigate, NavLink } from "react-router-dom";
import { UploadCloud, MessageSquareText, Clock, LogOut, Database, LayoutDashboard } from "lucide-react";
import { AuthProvider, useAuth } from "./context/AuthContext";
import { DatasetsProvider } from "./context/DatasetsContext";
import LoginPage from "./pages/LoginPage";
import DatasetsPage from "./pages/DatasetsPage";
import DashboardPage from "./pages/DashboardPage";
import AskAnalystPage from "./pages/AskAnalystPage";
import HistoryPage from "./pages/HistoryPage";

const NAV_ITEMS = [
  { to: "/data", label: "Data Intake", icon: UploadCloud },
  { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { to: "/ask", label: "Ask Analyst", icon: MessageSquareText },
  { to: "/history", label: "History", icon: Clock },
];

function AppShell() {
  const { user, logout } = useAuth();

  return (
    <div style={{ display: "flex", height: "100vh" }}>
      <div
        style={{
          width: 220,
          borderRight: "1px solid var(--color-hairline)",
          display: "flex",
          flexDirection: "column",
          padding: "20px 14px",
          boxSizing: "border-box",
          flexShrink: 0,
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 9, padding: "0 8px", marginBottom: 28 }}>
          <div
            style={{
              width: 26,
              height: 26,
              borderRadius: 5,
              background: "var(--color-panel-raised)",
              border: "1px solid var(--color-hairline)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            <Database size={13} color="var(--color-amber)" />
          </div>
          <span style={{ fontFamily: "var(--font-display)", fontSize: 15, fontWeight: 700 }}>DataPilot</span>
        </div>

        <div
          className="mono"
          style={{ fontSize: 10, letterSpacing: "0.1em", color: "var(--color-muted)", textTransform: "uppercase", padding: "0 8px", marginBottom: 8 }}
        >
          Workspace
        </div>

        {NAV_ITEMS.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            style={({ isActive }) => ({
              display: "flex",
              alignItems: "center",
              gap: 10,
              padding: "9px 10px",
              borderRadius: 5,
              textDecoration: "none",
              color: isActive ? "var(--color-text)" : "var(--color-muted)",
              background: isActive ? "var(--color-panel-raised)" : "transparent",
              borderLeft: isActive ? "2px solid var(--color-amber)" : "2px solid transparent",
              marginBottom: 2,
              fontSize: 13,
              fontWeight: isActive ? 500 : 400,
            })}
          >
            <Icon size={15} />
            {label}
          </NavLink>
        ))}

        <div style={{ flex: 1 }} />

        <div className="mono" style={{ fontSize: 10, color: "var(--color-muted)", padding: "0 8px", marginBottom: 8, overflow: "hidden", textOverflow: "ellipsis" }}>
          {user?.email}
        </div>
        <div onClick={logout} style={{ display: "flex", alignItems: "center", gap: 10, padding: "9px 10px", cursor: "pointer", color: "var(--color-muted)" }}>
          <LogOut size={15} />
          <span style={{ fontSize: 13 }}>Sign out</span>
        </div>
      </div>

      <div style={{ flex: 1, overflowY: "auto" }}>
        <Routes>
          <Route path="/data" element={<DatasetsPage />} />
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/ask" element={<AskAnalystPage />} />
          <Route path="/history" element={<HistoryPage />} />
          <Route path="*" element={<Navigate to="/data" replace />} />
        </Routes>
      </div>
    </div>
  );
}

function AppRoutes() {
  const { user, loading } = useAuth();

  if (loading) {
    return <div style={{ minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center", color: "var(--color-muted)" }}>Loading…</div>;
  }

  if (!user) {
    return <LoginPage />;
  }

  return (
    <DatasetsProvider>
      <AppShell />
    </DatasetsProvider>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </BrowserRouter>
  );
}
