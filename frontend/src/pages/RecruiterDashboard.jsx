import { useState } from "react";
import { recruiterAPI, uploadPDF } from "../api";

export default function RecruiterDashboard() {
  const [activeTab, setActiveTab] = useState("create");
  const [description, setDescription] = useState("");
  const [loading, setLoading] = useState(false);
  const [loadingMsg, setLoadingMsg] = useState("");
  const [jobResult, setJobResult] = useState(null);
  const [offers, setOffers] = useState(null);
  const [offersLoading, setOffersLoading] = useState(false);

  // --- Scorer state ---
  const [scorerJobData, setScorerJobData] = useState(null);
  const [candidates, setCandidates] = useState([]); // [{nom, cv_text, fileName}]
  const [scoredResults, setScoredResults] = useState(null);

  // ---- Create tab handlers ----
  async function handleGenerate() {
    if (!description.trim()) return;
    setLoading(true);
    setLoadingMsg("📝 Agents IA: Génération de la fiche de poste...");
    try {
      const data = await recruiterAPI.generateJob(description);
      setJobResult(data);
    } catch (err) {
      alert("Erreur: " + err.message);
    } finally {
      setLoading(false);
      setLoadingMsg("");
    }
  }

  async function handleSave() {
    if (!jobResult) return;
    try {
      await recruiterAPI.saveOffer(jobResult.job_data, jobResult.linkedin_post, jobResult.offer_id, jobResult.form_url);
      alert("✅ Offre sauvegardée !");
    } catch (err) {
      alert("Erreur: " + err.message);
    }
  }

  async function loadOffers() {
    setOffersLoading(true);
    try {
      const data = await recruiterAPI.getOffers();
      setOffers(data.offers || []);
    } catch (err) {
      alert("Erreur: " + err.message);
    } finally {
      setOffersLoading(false);
    }
  }

  // ---- Scorer tab handlers ----
  async function handleCandidateUpload(e) {
    const files = Array.from(e.target.files);
    if (!files.length) return;

    setLoading(true);
    setLoadingMsg(`📄 Extraction du texte de ${files.length} CV...`);

    const newCandidates = [];
    for (const file of files) {
      try {
        if (file.name.toLowerCase().endsWith(".pdf")) {
          const data = await uploadPDF(file);
          newCandidates.push({
            nom: file.name.replace(/\.pdf$/i, "").replace(/[_-]/g, " "),
            cv_text: data.text,
            fileName: file.name,
            pages: data.pages,
          });
        } else {
          const text = await file.text();
          newCandidates.push({
            nom: file.name.replace(/\.[^.]+$/, "").replace(/[_-]/g, " "),
            cv_text: text,
            fileName: file.name,
            pages: 1,
          });
        }
      } catch (err) {
        alert(`Erreur pour ${file.name}: ${err.message}`);
      }
    }

    setCandidates((prev) => [...prev, ...newCandidates]);
    setLoading(false);
    setLoadingMsg("");
    e.target.value = "";
  }

  function removeCandidate(index) {
    setCandidates((prev) => prev.filter((_, i) => i !== index));
  }

  async function handleScore() {
    if (!scorerJobData || candidates.length === 0) return;
    setLoading(true);
    setLoadingMsg(`🧠 Agent IA: Scoring de ${candidates.length} candidat(s)...`);
    try {
      const payload = candidates.map((c) => ({
        nom: c.nom,
        prenom: "",
        email: "",
        cv_text: c.cv_text,
      }));
      const data = await recruiterAPI.scoreCandidates(payload, scorerJobData);
      setScoredResults(data.scored_candidates || []);
    } catch (err) {
      alert("Erreur: " + err.message);
    } finally {
      setLoading(false);
      setLoadingMsg("");
    }
  }

  function useJobFromResult() {
    if (jobResult?.job_data) {
      setScorerJobData(jobResult.job_data);
      setActiveTab("scorer");
    }
  }

  function useJobFromOffer(offer) {
    if (offer?.data) {
      setScorerJobData(offer.data);
      setActiveTab("scorer");
    }
  }

  return (
    <div>
      <div className="home-hero" style={{ padding: "32px 36px", marginBottom: 24, background: "var(--bg-card)" }}>
        <div>
          <h1 className="home-title" style={{ fontSize: "1.8rem" }}>🚀 Espace Recruteur</h1>
          <p className="home-subtitle">
            5 Agents IA autonomes à votre service — Scénarisez, Sourcez, Scorer et Recrutez
          </p>
        </div>
      </div>

      <div className="tabs" style={{ background: "var(--bg-card)", padding: "0 16px", borderRadius: "var(--radius-md)", boxShadow: "var(--shadow-sm)", marginBottom: 24 }}>
        <button className={`tab ${activeTab === "create" ? "active" : ""}`} onClick={() => setActiveTab("create")}>📝 Créer une Offre</button>
        <button className={`tab ${activeTab === "scorer" ? "active" : ""}`} onClick={() => setActiveTab("scorer")}>📊 Scorer</button>
        <button className={`tab ${activeTab === "offers" ? "active" : ""}`} onClick={() => { setActiveTab("offers"); loadOffers(); }}>📋 Mes Offres</button>
      </div>

      {loading && (
        <div className="loading-overlay"><div className="spinner"></div><p>{loadingMsg}</p></div>
      )}

      {/* ============== CREATE TAB ============== */}
      {!loading && activeTab === "create" && (
        <div>
          <div className="glass-card" style={{ padding: 32, marginBottom: 24 }}>
            <h3 style={{ marginBottom: 16, color: "var(--text-primary)" }}>🎯 Décrivez votre besoin</h3>
            <p style={{ color: "var(--text-secondary)", fontSize: "0.95rem", marginBottom: 24 }}>
              L'IA génère automatiquement la fiche de poste technique optimisée + le post LinkedIn engageant.
            </p>
            <textarea
              className="textarea"
              placeholder="Ex: Je recrute un AI Engineer senior pour ma startup à Tunis, salaire 10k/mois, il faut Python, ML, et NLP..."
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={5}
            />
            <div style={{ marginTop: 16 }}>
              <button className="btn btn-primary btn-lg" onClick={handleGenerate} disabled={!description.trim()}>
                🚀 Générer avec l'IA
              </button>
            </div>
          </div>

          {jobResult && (
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 24 }}>
              <div className="glass-card" style={{ padding: 24 }}>
                <h3 style={{ marginBottom: 16 }}>📄 Fiche de Poste Générée</h3>
                {renderJobData(jobResult.job_data)}
                <div style={{ marginTop: 16 }}>
                  <button className="btn btn-secondary btn-sm" onClick={useJobFromResult}>
                    📊 Scorer des candidats pour ce poste →
                  </button>
                </div>
              </div>
              <div className="glass-card" style={{ padding: 24 }}>
                <h3 style={{ marginBottom: 16 }}>📢 Post LinkedIn</h3>
                <pre style={{ whiteSpace: "pre-wrap", color: "var(--text-secondary)", fontSize: "0.9rem", lineHeight: 1.8 }}>
                  {jobResult.linkedin_post}
                </pre>
                <div style={{ marginTop: 16, display: "flex", gap: 12 }}>
                  <button className="btn btn-primary" onClick={handleSave}>💾 Sauvegarder</button>
                  <button className="btn btn-secondary" onClick={() => navigator.clipboard.writeText(jobResult.linkedin_post)}>
                    📋 Copier le post
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* ============== SCORER TAB ============== */}
      {!loading && activeTab === "scorer" && (
        <div>
          {/* Step 1: Select Job */}
          <div className="glass-card" style={{ padding: 32, marginBottom: 24 }}>
            <h3 style={{ marginBottom: 16, color: "var(--text-primary)" }}>📋 1. Sélectionnez le poste à évaluer</h3>

            {scorerJobData ? (
              <div style={{ display: "flex", alignItems: "center", gap: 16, padding: 16, background: "var(--bg-secondary)", borderRadius: "var(--radius-md)" }}>
                <span style={{ fontSize: "1.5rem" }}>✅</span>
                <div style={{ flex: 1 }}>
                  <div style={{ fontWeight: 700, fontSize: "1.05rem" }}>{scorerJobData.job_title || "Poste sélectionné"}</div>
                  <div style={{ color: "var(--text-muted)", fontSize: "0.85rem" }}>
                    {scorerJobData.company_name || ""} — {scorerJobData.location || ""} — {(scorerJobData.skills_required || []).join(", ")}
                  </div>
                </div>
                <button className="btn btn-secondary btn-sm" onClick={() => setScorerJobData(null)}>Changer</button>
              </div>
            ) : (
              <div>
                <p style={{ color: "var(--text-secondary)", fontSize: "0.9rem", marginBottom: 16 }}>
                  Choisissez un poste depuis vos offres sauvegardées ou créez-en un d'abord.
                </p>
                {offers && offers.length > 0 ? (
                  <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                    {offers.map((o, i) => (
                      <button
                        key={i}
                        className="glass-card"
                        onClick={() => useJobFromOffer(o)}
                        style={{
                          padding: "12px 16px", textAlign: "left", cursor: "pointer", border: "1px solid var(--border-glass)",
                          display: "flex", justifyContent: "space-between", alignItems: "center",
                        }}
                      >
                        <span style={{ fontWeight: 600 }}>{o.data?.job_title || "Sans titre"}</span>
                        <span style={{ color: "var(--text-muted)", fontSize: "0.8rem" }}>{o.date}</span>
                      </button>
                    ))}
                  </div>
                ) : (
                  <div style={{ display: "flex", gap: 12 }}>
                    <button className="btn btn-secondary" onClick={() => { loadOffers(); }}>🔄 Charger mes offres</button>
                    <button className="btn btn-secondary" onClick={() => setActiveTab("create")}>📝 Créer une offre d'abord</button>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Step 2: Upload CVs */}
          <div className="glass-card" style={{ padding: 32, marginBottom: 24 }}>
            <h3 style={{ marginBottom: 16, color: "var(--text-primary)" }}>📄 2. Uploadez les CVs des candidats (PDF)</h3>
            <p style={{ color: "var(--text-secondary)", fontSize: "0.9rem", marginBottom: 16 }}>
              Uploadez un ou plusieurs CVs. L'IA extraira automatiquement le texte de chaque PDF pour le scoring.
            </p>

            <div style={{
              border: "2px dashed var(--border-glass-hover)", borderRadius: "var(--radius-md)",
              padding: 32, textAlign: "center", marginBottom: 16, background: "var(--bg-secondary)",
            }}>
              <input
                type="file"
                accept=".pdf,.txt"
                multiple
                onChange={handleCandidateUpload}
                style={{ display: "none" }}
                id="cv-upload"
              />
              <label htmlFor="cv-upload" style={{ cursor: "pointer", color: "var(--accent-primary)", fontWeight: 600, fontSize: "1rem" }}>
                📎 Cliquez ici ou glissez vos fichiers PDF
              </label>
              <p style={{ color: "var(--text-muted)", fontSize: "0.8rem", marginTop: 8 }}>Formats acceptés : PDF, TXT — Plusieurs fichiers autorisés</p>
            </div>

            {candidates.length > 0 && (
              <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 4 }}>
                  <span style={{ fontWeight: 700, fontSize: "0.95rem" }}>{candidates.length} candidat(s) chargé(s)</span>
                  <button className="btn btn-secondary btn-sm" onClick={() => setCandidates([])}>🗑️ Tout supprimer</button>
                </div>
                {candidates.map((c, i) => (
                  <div
                    key={i}
                    style={{
                      display: "flex", justifyContent: "space-between", alignItems: "center",
                      padding: "10px 14px", background: "var(--bg-secondary)", borderRadius: "var(--radius-sm)",
                      border: "1px solid var(--border-glass)",
                    }}
                  >
                    <div>
                      <span style={{ fontWeight: 600, fontSize: "0.9rem" }}>{c.nom}</span>
                      <span style={{ color: "var(--text-muted)", fontSize: "0.8rem", marginLeft: 8 }}>
                        ({c.pages} page{c.pages > 1 ? "s" : ""} · {c.cv_text.length} caractères)
                      </span>
                    </div>
                    <button
                      onClick={() => removeCandidate(i)}
                      style={{ background: "none", border: "none", color: "var(--danger)", cursor: "pointer", fontSize: "1rem" }}
                    >
                      ✕
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Step 3: Score Button */}
          <div style={{ marginBottom: 24 }}>
            <button
              className="btn btn-primary btn-lg btn-full"
              onClick={handleScore}
              disabled={!scorerJobData || candidates.length === 0}
            >
              🧠 SCORER {candidates.length} CANDIDAT{candidates.length > 1 ? "S" : ""} AVEC L'IA
            </button>
          </div>

          {/* Step 4: Results */}
          {scoredResults && scoredResults.length > 0 && (
            <div>
              <h3 style={{ marginBottom: 16, color: "var(--text-primary)" }}>🏆 Résultats du Scoring</h3>
              <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
                {scoredResults.map((c, i) => {
                  const score = c.score || 0;
                  const scoreClass = score >= 80 ? "score-high" : score >= 60 ? "score-medium" : "score-low";
                  return (
                    <div key={i} className="glass-card" style={{ padding: 24 }}>
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 12 }}>
                        <div>
                          <div style={{ fontWeight: 700, fontSize: "1.1rem" }}>
                            #{i + 1} — {c.nom} {c.prenom}
                          </div>
                          <div style={{ color: "var(--text-muted)", fontSize: "0.85rem", marginTop: 4 }}>
                            Priorité entretien : <strong>{c.interview_priority || "N/A"}</strong>
                          </div>
                        </div>
                        <div className={`score-badge ${scoreClass}`} style={{ fontSize: "1.2rem" }}>{score}%</div>
                      </div>

                      <div style={{ marginBottom: 12 }}>
                        <span style={{
                          padding: "4px 12px", borderRadius: 20, fontSize: "0.82rem", fontWeight: 600,
                          background: score >= 80 ? "var(--success-bg)" : score >= 60 ? "rgba(217,119,6,0.1)" : "rgba(220,38,38,0.1)",
                          color: score >= 80 ? "var(--success)" : score >= 60 ? "var(--warning)" : "var(--danger)",
                        }}>
                          {c.recommendation || "N/A"}
                        </span>
                      </div>

                      <p style={{ color: "var(--text-secondary)", fontSize: "0.9rem", marginBottom: 12, fontStyle: "italic" }}>
                        {c.reasoning || ""}
                      </p>

                      <div style={{ display: "flex", gap: 24 }}>
                        {c.strengths && c.strengths.length > 0 && (
                          <div style={{ flex: 1 }}>
                            <div style={{ fontWeight: 600, fontSize: "0.85rem", marginBottom: 6, color: "var(--success)" }}>✅ Points forts</div>
                            <div className="skills-grid">
                              {c.strengths.map((s, j) => <span key={j} className="skill-tag">{s}</span>)}
                            </div>
                          </div>
                        )}
                        {c.gaps && c.gaps.length > 0 && (
                          <div style={{ flex: 1 }}>
                            <div style={{ fontWeight: 600, fontSize: "0.85rem", marginBottom: 6, color: "var(--danger)" }}>⚠️ Lacunes</div>
                            <div className="skills-grid">
                              {c.gaps.map((g, j) => (
                                <span key={j} className="skill-tag" style={{ background: "rgba(220,38,38,0.08)", borderColor: "rgba(220,38,38,0.2)", color: "var(--danger)" }}>
                                  {g}
                                </span>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>

                      {c.interview_plan && (
                        <details style={{ marginTop: 16 }}>
                          <summary style={{ cursor: "pointer", fontWeight: 600, fontSize: "0.9rem", color: "var(--accent-primary)" }}>
                            📋 Plan d'entretien ({c.interview_plan.recommended_duration || "45min"})
                          </summary>
                          <div style={{ marginTop: 12, padding: 16, background: "var(--bg-secondary)", borderRadius: "var(--radius-sm)" }}>
                            {c.interview_plan.technical_questions && (
                              <div style={{ marginBottom: 12 }}>
                                <strong style={{ fontSize: "0.85rem" }}>🔧 Questions techniques</strong>
                                <ul style={{ color: "var(--text-secondary)", fontSize: "0.85rem", paddingLeft: 20, marginTop: 4 }}>
                                  {c.interview_plan.technical_questions.map((q, j) => <li key={j}>{q}</li>)}
                                </ul>
                              </div>
                            )}
                            {c.interview_plan.behavioral_questions && (
                              <div style={{ marginBottom: 12 }}>
                                <strong style={{ fontSize: "0.85rem" }}>💡 Questions comportementales</strong>
                                <ul style={{ color: "var(--text-secondary)", fontSize: "0.85rem", paddingLeft: 20, marginTop: 4 }}>
                                  {c.interview_plan.behavioral_questions.map((q, j) => <li key={j}>{q}</li>)}
                                </ul>
                              </div>
                            )}
                            {c.interview_plan.interview_tips && (
                              <p style={{ color: "var(--text-muted)", fontSize: "0.8rem", fontStyle: "italic", marginTop: 8 }}>
                                💬 {c.interview_plan.interview_tips}
                              </p>
                            )}
                          </div>
                        </details>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      )}

      {/* ============== OFFERS TAB ============== */}
      {!loading && activeTab === "offers" && (
        <div>
          {offersLoading ? (
            <div className="loading-overlay"><div className="spinner"></div><p>Chargement...</p></div>
          ) : offers && offers.length === 0 ? (
            <div className="glass-card" style={{ padding: 32, textAlign: "center" }}>
              <p style={{ color: "var(--text-secondary)" }}>📝 Aucune offre sauvegardée. Créez votre première offre !</p>
            </div>
          ) : offers ? (
            <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
              {offers.map((o, i) => (
                <div key={i} className="glass-card" style={{ padding: 20 }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                    <div>
                      <span style={{ fontWeight: 700 }}>{o.data?.job_title || "Sans titre"}</span>
                      <span style={{ color: "var(--text-muted)", marginLeft: 12, fontSize: "0.85rem" }}>
                        {o.data?.company_name || ""} — {o.data?.location || ""}
                      </span>
                    </div>
                    <div style={{ display: "flex", gap: 12, alignItems: "center" }}>
                      <button className="btn btn-secondary btn-sm" onClick={() => useJobFromOffer(o)}>
                        📊 Scorer
                      </button>
                      <span style={{ color: "var(--text-muted)", fontSize: "0.8rem" }}>{o.date}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : null}
        </div>
      )}
    </div>
  );
}

function renderJobData(jd) {
  if (!jd) return <p style={{ color: "var(--text-muted)" }}>Aucune donnée</p>;
  return (
    <div>
      <p><strong>Poste :</strong> {jd.job_title || "N/A"}</p>
      <p><strong>Entreprise :</strong> {jd.company_name || "N/A"}</p>
      <p><strong>Lieu :</strong> {jd.location || "N/A"}</p>
      <p><strong>Contrat :</strong> {jd.contract_type || "N/A"}</p>
      <p><strong>Expérience :</strong> {jd.experience_level || "N/A"}</p>
      <p><strong>Salaire :</strong> {jd.salary || "N/A"}</p>
      {jd.skills_required && jd.skills_required.length > 0 && (
        <div style={{ marginTop: 12 }}>
          <strong>Compétences :</strong>
          <div className="skills-grid">
            {jd.skills_required.map((s, i) => <span key={i} className="skill-tag">✔️ {s}</span>)}
          </div>
        </div>
      )}
      {jd.description && (
        <div style={{ marginTop: 12 }}>
          <strong>Description :</strong>
          <p style={{ color: "var(--text-secondary)", fontSize: "0.9rem", marginTop: 4 }}>{jd.description}</p>
        </div>
      )}
    </div>
  );
}
