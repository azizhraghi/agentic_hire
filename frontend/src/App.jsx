import { useState, useEffect, useCallback } from "react";
import LoginPage from "./pages/LoginPage";
import HomePage from "./pages/HomePage";
import RecruiterDashboard from "./pages/RecruiterDashboard";
import StudentDashboard from "./pages/StudentDashboard";
import { isAuthenticated, clearToken, authAPI } from "./api";

const SPACE_LABELS = {
  student: { icon: "🎓", label: "Espace Candidat" },
  recruiter: { icon: "🚀", label: "Espace Recruteur" },
};

/* ─── Toast Container (global error / success notifications) ─── */
function ToastContainer() {
  const [toasts, setToasts] = useState([]);

  const addToast = useCallback((e) => {
    const { type, message } = e.detail;
    const id = Date.now() + Math.random();
    setToasts((prev) => [...prev, { id, type, message }]);
    setTimeout(() => setToasts((prev) => prev.filter((t) => t.id !== id)), 5000);
  }, []);

  useEffect(() => {
    window.addEventListener("agentichire:toast", addToast);
    return () => window.removeEventListener("agentichire:toast", addToast);
  }, [addToast]);

  if (!toasts.length) return null;

  const icons = { error: "❌", warning: "⚠️", success: "✅" };

  return (
    <div className="toast-container">
      {toasts.map((t) => (
        <div key={t.id} className={`toast toast-${t.type}`}>
          <span className="toast-icon">{icons[t.type] || "ℹ️"}</span>
          <span className="toast-message">{t.message}</span>
          <button className="toast-close" onClick={() => setToasts((p) => p.filter((x) => x.id !== t.id))}>×</button>
        </div>
      ))}
    </div>
  );
}

export default function App() {
  const [user, setUser] = useState(null);
  const [page, setPage] = useState("home");
  const [checking, setChecking] = useState(true);
  const [theme, setTheme] = useState(localStorage.getItem('theme') || 'light');

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
  }, [theme]);

  useEffect(() => {
    if (isAuthenticated()) {
      authAPI
        .me()
        .then((u) => { setUser(u); setChecking(false); })
        .catch(() => { clearToken(); setChecking(false); });
    } else {
      setChecking(false);
    }
  }, []);

  function handleLogin(userData) {
    setUser(userData);
  }

  function handleLogout() {
    clearToken();
    setUser(null);
    setPage("home");
  }

  if (checking) {
    return (
      <div className="login-page">
        <div className="loading-overlay">
          <div className="spinner"></div>
          <p>Chargement...</p>
        </div>
      </div>
    );
  }

  if (!user) {
    return (
      <>
        <ToastContainer />
        <LoginPage onLogin={handleLogin} />
      </>
    );
  }

  const isInSpace = page !== "home";
  const spaceInfo = SPACE_LABELS[page];

  return (
    <div className="app-layout">
      <ToastContainer />

      {/* Sidebar */}
      <aside className="sidebar">
        <div className="sidebar-logo" onClick={() => setPage("home")} style={{ cursor: "pointer" }}>
          <span>🤖 AgenticHire</span>
        </div>

        <nav className="sidebar-nav">
          {isInSpace ? (
            <>
              <button className="sidebar-link back-link" onClick={() => setPage("home")}>
                ← Accueil
              </button>
              <div className="sidebar-space-indicator">
                <span className="space-icon">{spaceInfo?.icon}</span>
                <span className="space-label">{spaceInfo?.label}</span>
              </div>
            </>
          ) : (
            <button className="sidebar-link active" onClick={() => setPage("home")}>
              🏠 Accueil
            </button>
          )}
        </nav>

        <div style={{ borderTop: "1px solid var(--border-glass)", paddingTop: 16, marginTop: "auto" }}>
          <button className="btn btn-secondary btn-sm btn-full" onClick={() => setTheme(theme === 'light' ? 'dark' : 'light')} style={{ marginBottom: 12 }}>
            {theme === 'light' ? '🌙 Mode Sombre' : '☀️ Mode Clair'}
          </button>
          <div style={{ fontSize: "1.05rem", color: "var(--text-muted)", marginBottom: 12, textAlign: "center", fontWeight: "600" }}>
            👤 {user.username}
          </div>
          <button className="btn btn-secondary btn-sm btn-full" onClick={handleLogout}>
            Se déconnecter
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="main-content">
        {page === "home" && <HomePage user={user} onNavigate={setPage} />}
        {page === "recruiter" && <RecruiterDashboard />}
        {page === "student" && <StudentDashboard />}
      </main>
    </div>
  );
}
