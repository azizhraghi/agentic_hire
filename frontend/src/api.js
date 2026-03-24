/**
 * API Client — Centralized fetch wrapper for all backend calls.
 */

const API_BASE = "http://localhost:8000/api";

function getToken() {
  return localStorage.getItem("agentichire_token");
}

export function setToken(token) {
  localStorage.setItem("agentichire_token", token);
}

export function clearToken() {
  localStorage.removeItem("agentichire_token");
}

export function isAuthenticated() {
  return !!getToken();
}

async function request(method, path, body = null) {
  const headers = { "Content-Type": "application/json" };
  const token = getToken();
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const opts = { method, headers };
  if (body) opts.body = JSON.stringify(body);

  const res = await fetch(`${API_BASE}${path}`, opts);
  const data = await res.json();

  if (!res.ok) {
    throw new Error(data.detail || "API Error");
  }
  return data;
}

// --- Auth ---
export const authAPI = {
  register: (username, password, email) =>
    request("POST", "/auth/register", { username, password, email }),
  login: (username, password) =>
    request("POST", "/auth/login", { username, password }),
  me: () => request("GET", "/auth/me"),
};

// --- Chat ---
export const chatAPI = {
  send: (message) => request("POST", "/chat", { message }),
};

// --- Recruiter ---
export const recruiterAPI = {
  generateJob: (description) =>
    request("POST", "/recruiter/generate-job", { description }),
  scoreCandidates: (candidates, job_data) =>
    request("POST", "/recruiter/score-candidates", { candidates, job_data }),
  getOffers: () => request("GET", "/recruiter/offers"),
  saveOffer: (job_data, linkedin_post, offer_id, form_url) =>
    request("POST", "/recruiter/offers", { job_data, linkedin_post, offer_id, form_url }),
};

// --- Student ---
export const studentAPI = {
  analyzeCV: (cv_text) =>
    request("POST", "/student/analyze-cv", { cv_text }),
  searchJobs: (cv_text, cv_analysis, opts = {}) =>
    request("POST", "/student/search-jobs", {
      cv_text,
      cv_analysis,
      jobs_per_site: opts.jobs_per_site || 5,
      demo_mode: opts.demo_mode || false,
      location: opts.location || "",
      include_remote: opts.include_remote !== false,
      selected_sources: opts.selected_sources || null,
    }),
  generateApplication: (cv_text, job) =>
    request("POST", "/student/generate-application", { cv_text, job }),
};

// --- Upload ---
export async function uploadPDF(file) {
  const formData = new FormData();
  formData.append("file", file);

  const headers = {};
  const token = getToken();
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`${API_BASE}/upload/pdf`, {
    method: "POST",
    headers,
    body: formData,
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || "Upload error");
  return data;
}
