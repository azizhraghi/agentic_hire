import { useState } from "react";
import { recruiterAPI } from "../api";

export default function RecruiterDashboard() {
  const [activeTab, setActiveTab] = useState("create");
  const [description, setDescription] = useState("");
  const [loading, setLoading] = useState(false);
  const [jobResult, setJobResult] = useState(null);
  const [offers, setOffers] = useState(null);
  const [offersLoading, setOffersLoading] = useState(false);

  async function handleGenerate() {
    if (!description.trim()) return;
    setLoading(true);
    try {
      const data = await recruiterAPI.generateJob(description);
      setJobResult(data);
    } catch (err) {
      alert("Erreur: " + err.message);
    } finally {
      setLoading(false);
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
        <button className={`tab ${activeTab === "offers" ? "active" : ""}`} onClick={() => { setActiveTab("offers"); loadOffers(); }}>📋 Mes Offres</button>
      </div>

      {activeTab === "create" && (
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
              <button className="btn btn-primary btn-lg" onClick={handleGenerate} disabled={loading || !description.trim()}>
                {loading ? <><span className="spinner"></span> Agents IA au travail...</> : "🚀 Générer avec l'IA"}
              </button>
            </div>
          </div>

          {jobResult && (
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 24 }}>
              <div className="glass-card" style={{ padding: 24 }}>
                <h3 style={{ marginBottom: 16 }}>📄 Fiche de Poste Générée</h3>
                {renderJobData(jobResult.job_data)}
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

      {activeTab === "offers" && (
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
                    <span style={{ color: "var(--text-muted)", fontSize: "0.8rem" }}>{o.date}</span>
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
