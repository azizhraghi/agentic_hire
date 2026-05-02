import { useState, useEffect } from "react";

export default function HomePage({ user, onNavigate }) {
  const [time, setTime] = useState(new Date());

  useEffect(() => {
    const t = setInterval(() => setTime(new Date()), 60000);
    return () => clearInterval(t);
  }, []);

  const hour = time.getHours();
  const greeting =
    hour < 12 ? "Bonjour" : hour < 18 ? "Bon après-midi" : "Bonsoir";

  return (
    <div>
      {/* Hero Welcome */}
      <div className="home-hero">
        <div className="home-hero-content">
          <h1 className="home-title">
            {greeting}, <span className="gradient-text">{user?.username || "Utilisateur"}</span> 👋
          </h1>
          <p className="home-subtitle">
            Bienvenue sur AgenticHire — votre plateforme de recrutement propulsée par 7 agents IA autonomes.
          </p>
          
          {/* Voice Assistant Widget */}
          <div style={{ marginTop: 32, display: "flex", gap: 16, alignItems: "center" }}>
            <button 
              className="btn btn-primary" 
              style={{ borderRadius: 50, width: 60, height: 60, padding: 0, fontSize: "1.5rem", boxShadow: "0 0 20px rgba(37, 99, 235, 0.4)" }}
              onClick={() => {
                const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
                if (!SpeechRecognition) {
                  alert("Votre navigateur ne supporte pas la reconnaissance vocale.");
                  return;
                }
                const recognition = new SpeechRecognition();
                recognition.lang = 'fr-FR';
                recognition.start();
                recognition.onresult = (event) => {
                  const transcript = event.results[0][0].transcript;
                  const isRecruiter = transcript.toLowerCase().includes("cherche") || transcript.toLowerCase().includes("recrut");
                  alert(`🗣️ Vous avez dit : "${transcript}"\n\n🤖 L'IA détecte l'intention : ${isRecruiter ? "Espace Recruteur" : "Espace Candidat"}`);
                  onNavigate(isRecruiter ? "recruiter" : "student");
                };
              }}
            >
              🎤
            </button>
            <div>
              <div style={{ fontWeight: 700, color: "var(--text-primary)" }}>Parlez à l'IA</div>
              <div style={{ fontSize: "0.85rem", color: "var(--text-muted)" }}>Ex: "Je cherche un développeur React..."</div>
            </div>
          </div>

        </div>
        <div className="home-hero-badge">
          <span className="pulse-dot"></span>
          <span>Agents IA actifs</span>
        </div>
      </div>

      {/* Role Cards */}
      <div className="home-cards-grid">
        <div
          className="home-role-card student-card"
          onClick={() => onNavigate("student")}
        >
          <div className="role-icon-title">
            <span className="role-icon">🎓</span>
            <h2>Espace Candidat</h2>
          </div>
          <p>
            Optimisez votre recherche d'emploi par IA. Laissez nos agents
            analyser votre CV, scanner le web et postuler automatiquement pour vous.
          </p>
          <div className="role-features">
            <span>Analyse CV</span>
            <span>11 sources</span>
            <span>IA Matching</span>
            <span>Auto-candidature</span>
          </div>
          <div className="role-cta">
            Accéder →
          </div>
        </div>

        <div
          className="home-role-card recruiter-card"
          onClick={() => onNavigate("recruiter")}
        >
          <div className="role-icon-title">
            <span className="role-icon">🚀</span>
            <h2>Espace Recruteur</h2>
          </div>
          <p>
            Automatisez votre sourcing et scoring. Génératrice de fiches de
            poste IA, scoring prédictif et diffusion multicanale.
          </p>
          <div className="role-features">
            <span>Fiches IA</span>
            <span>Scoring</span>
            <span>LinkedIn</span>
            <span>Gestion offres</span>
          </div>
          <div className="role-cta">
            Accéder →
          </div>
        </div>
      </div>

      {/* Platform Stats */}
      <div className="home-stats-bar">
        <div className="home-stat">
          <span className="home-stat-value">11</span>
          <span className="home-stat-label">Plateformes scrapées</span>
        </div>
        <div className="home-stat">
          <span className="home-stat-value">7</span>
          <span className="home-stat-label">Agents IA</span>
        </div>
        <div className="home-stat">
          <span className="home-stat-value">∞</span>
          <span className="home-stat-label">Candidatures générées</span>
        </div>
        <div className="home-stat">
          <span className="home-stat-value">⚡</span>
          <span className="home-stat-label">Temps réel</span>
        </div>
      </div>

      {/* Sources Grid */}
      <div className="glass-card" style={{ padding: 24 }}>
        <h3 style={{ marginBottom: 16, fontSize: "1rem" }}>🌐 Sources de données intégrées</h3>
        <div className="home-sources-grid">
          {[
            { name: "LinkedIn", color: "#0077B5", icon: "🔗" },
            { name: "Indeed", color: "#2164f3", icon: "💼" },
            { name: "Glassdoor", color: "#0caa41", icon: "🏢" },
            { name: "RemoteOK", color: "#28a745", icon: "🌍" },
            { name: "Remotive", color: "#4d3df7", icon: "🚀" },
            { name: "WeWorkRemotely", color: "#00c3a5", icon: "💻" },
            { name: "Wayup", color: "#f5a623", icon: "⬆️" },
            { name: "SimplyHired", color: "#1a8cff", icon: "🔎" },
            { name: "Google Jobs", color: "#ea4335", icon: "🔴" },
            { name: "Intern Insider", color: "#e91e63", icon: "🎓" },
            { name: "Adzuna", color: "#E67E22", icon: "📋" },
          ].map((s) => (
            <div 
              key={s.name} 
              className="home-source-chip"
              style={{ 
                '--source-color': s.color,
                '--source-shadow': `${s.color}40`
              }}
            >
              <span style={{ fontSize: "1.2rem" }}>{s.icon}</span>
              {s.name}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
