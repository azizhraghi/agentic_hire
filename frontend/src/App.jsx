import { useState, useEffect } from "react";
import LoginPage from "./pages/LoginPage";
import HomePage from "./pages/HomePage";
import RecruiterDashboard from "./pages/RecruiterDashboard";
import StudentDashboard from "./pages/StudentDashboard";
import { isAuthenticated, clearToken, authAPI } from "./api";

const SPACE_LABELS = {
  student: { icon: "🎓", label: "Espace Candidat" },
  recruiter: { icon: "🚀", label: "Espace Recruteur" },
};

export default function App() {
  const [user, setUser] = useState(null);
  const [page, setPage] = useState("home");
  const [checking, setChecking] = useState(true);

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
    return <LoginPage onLogin={handleLogin} />;
  }

  const isInSpace = page !== "home";
  const spaceInfo = SPACE_LABELS[page];

  return (
    <div className="app-layout">
      {/* Sidebar */}
      <aside className="sidebar">
        <div className="sidebar-logo" onClick={() => setPage("home")} style={{ cursor: "pointer" }}>
          <span>🤖 AgenticHire</span>
        </div>

        <nav className="sidebar-nav">
          {isInSpace ? (
            <>
              {/* Back to Home */}
              <button
                className="sidebar-link back-link"
                onClick={() => setPage("home")}
              >
                ← Accueil
              </button>

              {/* Current space indicator */}
              <div className="sidebar-space-indicator">
                <span className="space-icon">{spaceInfo?.icon}</span>
                <span className="space-label">{spaceInfo?.label}</span>
              </div>
            </>
          ) : (
            /* Home — no extra links, the home cards handle navigation */
            <button
              className="sidebar-link active"
              onClick={() => setPage("home")}
            >
              🏠 Accueil
            </button>
          )}
        </nav>

        <div style={{ borderTop: "1px solid var(--border-glass)", paddingTop: 16, marginTop: "auto" }}>
          <div style={{ fontSize: "0.85rem", color: "var(--text-muted)", marginBottom: 8 }}>
            👤 {user.username}
          </div>
          <button className="btn btn-secondary btn-sm btn-full" onClick={handleLogout}>
            Se déconnecter
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="main-content">
        {page === "home" && (
          <HomePage user={user} onNavigate={setPage} />
        )}
        {page === "recruiter" && <RecruiterDashboard />}
        {page === "student" && <StudentDashboard />}
      </main>
    </div>
  );
}
