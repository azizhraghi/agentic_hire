import { useState, useMemo } from "react";
import { studentAPI, uploadPDF } from "../api";

const ALL_SOURCES = [
  { id: "LinkedIn", color: "#0077B5", icon: "🔗" },
  { id: "Indeed", color: "#2164f3", icon: "💼" },
  { id: "RemoteOK", color: "#28a745", icon: "🌍" },
  { id: "Glassdoor", color: "#0caa41", icon: "🏢" },
  { id: "Remotive", color: "#4d3df7", icon: "🚀" },
  { id: "WeWorkRemotely", color: "#00c3a5", icon: "💻" },
  { id: "Wayup", color: "#f5a623", icon: "⬆️" },
  { id: "SimplyHired", color: "#1a8cff", icon: "🔎" },
  { id: "Google Jobs", color: "#ea4335", icon: "🔴" },
  { id: "Intern Insider", color: "#e91e63", icon: "🎓" },
  { id: "Adzuna", color: "#E67E22", icon: "📋" },
];

export default function StudentDashboard() {
  const [activeTab, setActiveTab] = useState("upload");
  const [cvText, setCvText] = useState("");
  const [cvAnalysis, setCvAnalysis] = useState(null);
  const [jobs, setJobs] = useState(null);
  const [loading, setLoading] = useState(false);
  const [loadingMsg, setLoadingMsg] = useState("");
  const [jobsPerSource, setJobsPerSource] = useState(5);
  const [selectedSources, setSelectedSources] = useState(ALL_SOURCES.map((s) => s.id));
  const [searchOpts, setSearchOpts] = useState({ demo_mode: false, location: "", include_remote: true });
  const [appResult, setAppResult] = useState(null);
  const [selectedJob, setSelectedJob] = useState(null);
  const [activeSource, setActiveSource] = useState("all");

  function toggleSource(id) {
    setSelectedSources((prev) =>
      prev.includes(id) ? prev.filter((s) => s !== id) : [...prev, id]
    );
  }

  function toggleAll() {
    if (selectedSources.length === ALL_SOURCES.length) {
      setSelectedSources([]);
    } else {
      setSelectedSources(ALL_SOURCES.map((s) => s.id));
    }
  }

  // Compute source breakdown and filtered jobs
  const sourceCounts = useMemo(() => {
    if (!jobs) return {};
    const counts = {};
    jobs.forEach((j) => {
      const src = j.source || "Unknown";
      counts[src] = (counts[src] || 0) + 1;
    });
    return counts;
  }, [jobs]);

  const filteredJobs = useMemo(() => {
    if (!jobs) return [];
    if (activeSource === "all") return jobs;
    return jobs.filter((j) => j.source === activeSource);
  }, [jobs, activeSource]);

  async function handleFileUpload(e) {
    const file = e.target.files[0];
    if (!file) return;

    if (file.name.toLowerCase().endsWith(".pdf")) {
      setLoading(true);
      setLoadingMsg("📄 Extraction du texte du PDF...");
      try {
        const data = await uploadPDF(file);
        setCvText(data.text);
      } catch (err) {
        alert("Erreur lors de l'extraction: " + err.message);
      } finally {
        setLoading(false);
        setLoadingMsg("");
      }
    } else {
      const text = await file.text();
      setCvText(text);
    }
  }

  async function handleAnalyze() {
    if (!cvText.trim()) return;
    setLoading(true);
    setLoadingMsg("🧠 Agent 1: Analyse du CV...");
    try {
      const data = await studentAPI.analyzeCV(cvText);
      setCvAnalysis(data.analysis);
      setActiveTab("search");
    } catch (err) {
      alert("Erreur: " + err.message);
    } finally {
      setLoading(false);
      setLoadingMsg("");
    }
  }

  async function handleSearch() {
    if (!cvText.trim() || selectedSources.length === 0) return;
    setLoading(true);
    const srcCount = selectedSources.length;
    setLoadingMsg(`🔍 Agents IA: Scraping ${srcCount} plateforme${srcCount > 1 ? "s" : ""} (${jobsPerSource} jobs/source)...`);
    try {
      const data = await studentAPI.searchJobs(cvText, cvAnalysis, {
        ...searchOpts,
        jobs_per_site: jobsPerSource,
        selected_sources: selectedSources,
      });
      setJobs(data.jobs || []);
      setActiveSource("all");
      setActiveTab("results");
    } catch (err) {
      alert("Erreur: " + err.message);
    } finally {
      setLoading(false);
      setLoadingMsg("");
    }
  }

  async function handleGenApp(job) {
    setSelectedJob(job);
    setLoading(true);
    setLoadingMsg("✍️ Agent 7: Génération du dossier de candidature...");
    try {
      const data = await studentAPI.generateApplication(cvText, job);
      setAppResult(data);
      setActiveTab("application");
    } catch (err) {
      alert("Erreur: " + err.message);
    } finally {
      setLoading(false);
      setLoadingMsg("");
    }
  }

  const totalJobs = jobs ? jobs.length : 0;
  const displayedJobs = filteredJobs;
  const highMatches = displayedJobs.filter((j) => j.ai_match_score >= 80).length;
  const avgScore = displayedJobs.length > 0 ? Math.round(displayedJobs.reduce((s, j) => s + (j.ai_match_score || 0), 0) / displayedJobs.length) : 0;
  const sourceCount = Object.keys(sourceCounts).length;
  const maxEstimate = selectedSources.length * jobsPerSource;

  return (
    <div>
      <div className="home-hero" style={{ padding: "32px 36px", marginBottom: 24 }}>
        <div>
          <h1 className="home-title" style={{ fontSize: "1.8rem" }}>🎓 Espace Candidat</h1>
          <p className="home-subtitle">
            7 Agents IA autonomes — Analyse CV, Scraping multi-source, Matching IA et Auto-candidature
          </p>
        </div>
      </div>

      {loading && (
        <div className="loading-overlay"><div className="spinner"></div><p>{loadingMsg}</p></div>
      )}

      {!loading && (
        <>
          <div className="tabs" style={{ background: "var(--bg-card)", padding: "0 16px", borderRadius: "var(--radius-md)", boxShadow: "var(--shadow-sm)", marginBottom: 24 }}>
            <button className={`tab ${activeTab === "upload" ? "active" : ""}`} onClick={() => setActiveTab("upload")}>📄 Upload CV</button>
            <button className={`tab ${activeTab === "search" ? "active" : ""}`} onClick={() => setActiveTab("search")} disabled={!cvAnalysis}>🔍 Recherche</button>
            <button className={`tab ${activeTab === "results" ? "active" : ""}`} onClick={() => setActiveTab("results")} disabled={!jobs}>🎯 Résultats</button>
            {appResult && <button className={`tab ${activeTab === "application" ? "active" : ""}`} onClick={() => setActiveTab("application")}>✍️ Candidature</button>}
          </div>

          {/* UPLOAD TAB */}
          {activeTab === "upload" && (
            <div className="glass-card" style={{ padding: 32 }}>
              <h3 style={{ marginBottom: 16, color: "var(--text-primary)" }}>📤 Chargez votre CV</h3>
              <p style={{ color: "var(--text-secondary)", marginBottom: 24, fontSize: "0.95rem" }}>
                Uploadez votre CV (texte) ou collez le contenu directement ci-dessous.
              </p>
              <div style={{ marginBottom: 16 }}>
                <input type="file" accept=".txt,.pdf,.doc" onChange={handleFileUpload} style={{ color: "var(--text-secondary)" }} />
              </div>
              <textarea
                className="textarea"
                placeholder="Ou collez le contenu de votre CV ici..."
                value={cvText}
                onChange={(e) => setCvText(e.target.value)}
                rows={10}
              />
              <div style={{ marginTop: 16 }}>
                <button className="btn btn-primary btn-lg" onClick={handleAnalyze} disabled={!cvText.trim()}>
                  🧠 Analyser avec l'IA
                </button>
              </div>

              {cvAnalysis && (
                <div style={{ marginTop: 24 }}>
                  <h4 style={{ marginBottom: 12 }}>✅ Analyse terminée</h4>
                  <div className="metrics-grid">
                    <div className="glass-card metric-card">
                      <div className="value">{(cvAnalysis.profile_type || "N/A").toUpperCase()}</div>
                      <div className="label">Niveau</div>
                    </div>
                    <div className="glass-card metric-card">
                      <div className="value">{cvAnalysis.experience_years || 0} ans</div>
                      <div className="label">Expérience</div>
                    </div>
                    <div className="glass-card metric-card">
                      <div className="value">{cvAnalysis.primary_role || "N/A"}</div>
                      <div className="label">Rôle</div>
                    </div>
                  </div>
                  {cvAnalysis.technical_skills && cvAnalysis.technical_skills.length > 0 && (
                    <div className="skills-grid" style={{ marginTop: 8 }}>
                      {cvAnalysis.technical_skills.map((s, i) => <span key={i} className="skill-tag">{s}</span>)}
                    </div>
                  )}
                </div>
              )}
            </div>
          )}

          {/* SEARCH TAB */}
          {activeTab === "search" && cvAnalysis && (
            <div className="glass-card" style={{ padding: 32 }}>
              <h3 style={{ marginBottom: 20 }}>🚀 Recherche Intelligente Multi-Source</h3>

              <div className="metrics-grid" style={{ marginBottom: 24 }}>
                <div className="glass-card metric-card">
                  <div className="value">{(cvAnalysis.profile_type || "").toUpperCase()}</div>
                  <div className="label">Profil</div>
                </div>
                <div className="glass-card metric-card">
                  <div className="value">{cvAnalysis.primary_role || "N/A"}</div>
                  <div className="label">Rôle</div>
                </div>
                <div className="glass-card metric-card">
                  <div className="value">{selectedSources.length}</div>
                  <div className="label">Sources actives</div>
                </div>
                <div className="glass-card metric-card">
                  <div className="value">~{maxEstimate}</div>
                  <div className="label">Jobs estimés</div>
                </div>
              </div>

              {/* Source Selector */}
              <div style={{ marginBottom: 24 }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
                  <h4 style={{ fontSize: "1rem" }}>🔍 Sources de recherche</h4>
                  <button className="btn btn-secondary btn-sm" onClick={toggleAll} style={{ fontSize: "0.8rem" }}>
                    {selectedSources.length === ALL_SOURCES.length ? "Tout décocher" : "Tout cocher"}
                  </button>
                </div>
                <div className="source-selector-grid">
                  {ALL_SOURCES.map((src) => {
                    const isActive = selectedSources.includes(src.id);
                    return (
                      <label
                        key={src.id}
                        className={`source-checkbox ${isActive ? "active" : ""}`}
                        style={{ "--source-color": src.color }}
                      >
                        <input
                          type="checkbox"
                          checked={isActive}
                          onChange={() => toggleSource(src.id)}
                          style={{ display: "none" }}
                        />
                        <span className="source-dot" style={{ background: src.color }}></span>
                        <span className="source-name">{src.id}</span>
                      </label>
                    );
                  })}
                </div>
              </div>

              {/* Jobs Per Source Slider */}
              <div style={{ marginBottom: 24 }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
                  <label style={{ fontWeight: 600, fontSize: "0.9rem" }}>Jobs par source</label>
                  <span style={{ color: "var(--accent-primary-hover)", fontWeight: 700, fontSize: "1.1rem" }}>{jobsPerSource}</span>
                </div>
                <input
                  type="range"
                  min={3}
                  max={15}
                  value={jobsPerSource}
                  onChange={(e) => setJobsPerSource(parseInt(e.target.value))}
                  className="slider"
                  style={{ width: "100%" }}
                />
                <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.75rem", color: "var(--text-muted)" }}>
                  <span>3 (rapide)</span>
                  <span>15 (complet)</span>
                </div>
              </div>

              {/* Location + Options */}
              <div style={{ marginBottom: 16 }}>
                <div className="form-group">
                  <label>📍 Localisation</label>
                  <input className="input" placeholder="Ex: Paris, France" value={searchOpts.location}
                    onChange={(e) => setSearchOpts({ ...searchOpts, location: e.target.value })} />
                </div>
              </div>

              <div style={{ display: "flex", gap: 16, marginBottom: 24 }}>
                <label style={{ display: "flex", alignItems: "center", gap: 6, color: "var(--text-secondary)", cursor: "pointer" }}>
                  <input type="checkbox" checked={searchOpts.include_remote}
                    onChange={(e) => setSearchOpts({ ...searchOpts, include_remote: e.target.checked })} />
                  🌐 Inclure Remote
                </label>
                <label style={{ display: "flex", alignItems: "center", gap: 6, color: "var(--text-secondary)", cursor: "pointer" }}>
                  <input type="checkbox" checked={searchOpts.demo_mode}
                    onChange={(e) => setSearchOpts({ ...searchOpts, demo_mode: e.target.checked })} />
                  🎬 Mode Démo
                </label>
              </div>

              <button
                className="btn btn-primary btn-lg btn-full"
                onClick={handleSearch}
                disabled={selectedSources.length === 0}
              >
                🚀 LANCER LA RECHERCHE ({selectedSources.length} sources · {jobsPerSource} jobs/source)
              </button>
            </div>
          )}

          {/* RESULTS TAB */}
          {activeTab === "results" && jobs && (
            <div>
              <div className="metrics-grid">
                <div className="glass-card metric-card">
                  <div className="value">{totalJobs}</div>
                  <div className="label">Total Jobs</div>
                </div>
                <div className="glass-card metric-card">
                  <div className="value">{sourceCount}</div>
                  <div className="label">🌐 Sources</div>
                </div>
                <div className="glass-card metric-card">
                  <div className="value">{highMatches}</div>
                  <div className="label">🎯 High Match</div>
                </div>
                <div className="glass-card metric-card">
                  <div className="value">{avgScore}%</div>
                  <div className="label">📈 Score Moyen</div>
                </div>
              </div>

              {/* Source Filter Pills */}
              <div className="source-filters">
                <button
                  className={`source-pill ${activeSource === "all" ? "active" : ""}`}
                  onClick={() => setActiveSource("all")}
                >
                  Toutes <span className="pill-count">{totalJobs}</span>
                </button>
                {Object.entries(sourceCounts)
                  .sort((a, b) => b[1] - a[1])
                  .map(([src, count]) => (
                    <button
                      key={src}
                      className={`source-pill ${activeSource === src ? "active" : ""}`}
                      onClick={() => setActiveSource(activeSource === src ? "all" : src)}
                    >
                      {src} <span className="pill-count">{count}</span>
                    </button>
                  ))}
              </div>

              <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                {[...displayedJobs].sort((a, b) => (b.ai_match_score || 0) - (a.ai_match_score || 0)).map((job, i) => {
                  const score = job.ai_match_score || 0;
                  const scoreClass = score >= 80 ? "score-high" : score >= 60 ? "score-medium" : "score-low";
                  const matchResult = job.ai_analysis?.match_result || {};
                  const source = job.source || "Unknown";
                  const sourceClass = source.toLowerCase().replace(/[\s()]+/g, "");

                  return (
                    <div key={i} className="glass-card job-card">
                      <div className="job-card-header">
                        <div>
                          <div className="job-title">
                            {job.title || "N/A"}
                            <span className={`source-badge source-${sourceClass}`}>{source}</span>
                          </div>
                          <div className="job-company">🏢 {job.company || "N/A"} — 📍 {job.location || "N/A"}</div>
                        </div>
                        <div className={`score-badge ${scoreClass}`}>{score}%</div>
                      </div>

                      <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 12 }}>
                        {(matchResult.matching_skills || []).slice(0, 5).map((s, j) => (
                          <span key={j} className="skill-tag">✅ {s}</span>
                        ))}
                        {(matchResult.missing_skills || []).slice(0, 3).map((s, j) => (
                          <span key={`m${j}`} className="skill-tag" style={{ background: "rgba(239,68,68,0.1)", borderColor: "rgba(239,68,68,0.2)", color: "var(--danger)" }}>❌ {s}</span>
                        ))}
                      </div>

                      <div style={{ display: "flex", gap: 12, alignItems: "center" }}>
                        <span style={{ fontSize: "0.85rem", color: "var(--text-muted)" }}>
                          {matchResult.recommendation || job.ai_priority || ""}
                        </span>
                        <button className="btn btn-primary btn-sm" onClick={() => handleGenApp(job)}>
                          ✍️ Générer Candidature
                        </button>
                        {job.url && job.url !== "#" && (
                          <a href={job.url} target="_blank" rel="noopener noreferrer" className="btn btn-secondary btn-sm">
                            🔗 Voir l'offre
                          </a>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* APPLICATION TAB */}
          {activeTab === "application" && appResult && selectedJob && (
            <div>
              <div className="glass-card" style={{ padding: 24, marginBottom: 24 }}>
                <h3>✍️ Dossier de candidature — {selectedJob.title} chez {selectedJob.company}</h3>
              </div>

              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 24 }}>
                <div className="glass-card" style={{ padding: 24 }}>
                  <h4 style={{ marginBottom: 12 }}>📄 CV Optimisé</h4>
                  <pre style={{ whiteSpace: "pre-wrap", color: "var(--text-secondary)", fontSize: "0.85rem", lineHeight: 1.7 }}>
                    {appResult.optimized_cv}
                  </pre>
                </div>
                <div className="glass-card" style={{ padding: 24 }}>
                  <h4 style={{ marginBottom: 12 }}>✉️ Lettre de Motivation</h4>
                  <pre style={{ whiteSpace: "pre-wrap", color: "var(--text-secondary)", fontSize: "0.85rem", lineHeight: 1.7 }}>
                    {appResult.cover_letter}
                  </pre>
                </div>
              </div>
              <div className="glass-card" style={{ padding: 24, marginTop: 24 }}>
                <h4 style={{ marginBottom: 12 }}>💼 Message LinkedIn</h4>
                <p style={{ color: "var(--text-secondary)" }}>{appResult.linkedin_message}</p>
                <button className="btn btn-secondary btn-sm" style={{ marginTop: 12 }}
                  onClick={() => navigator.clipboard.writeText(appResult.linkedin_message)}>
                  📋 Copier
                </button>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
