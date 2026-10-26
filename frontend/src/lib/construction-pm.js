import { api } from "./api";

// ── Electrical Project Management & Labor Engine API client ──────────────────
// All endpoints live under /api/construction and are staff-authenticated
// (instructor+). No tier gates within the staff boundary.

const CP = "/api/construction";

export const constructionApi = {
  // ── Projects ────────────────────────────────────────────────────────────
  listProjects: (params = {}) => api.get(`${CP}/projects`, { params }),
  getProject: (id) => api.get(`${CP}/projects/${id}`),
  createProject: (payload) => api.post(`${CP}/projects`, payload),

  // ── Estimates / Takeoff ─────────────────────────────────────────────────
  calculateEstimate: (projectId, payload) =>
    api.post(`${CP}/projects/${projectId}/estimates/calculate`, payload),
  getTakeoff: (projectId) => api.get(`${CP}/projects/${projectId}/takeoff`),

  // ── Field logs + EVM ────────────────────────────────────────────────────
  submitFieldLog: (projectId, payload) =>
    api.post(`${CP}/projects/${projectId}/field-logs`, payload),
  getEvmMetrics: (projectId) => api.get(`${CP}/projects/${projectId}/evm-metrics`),

  // ── Blueprints ──────────────────────────────────────────────────────────
  uploadBlueprint: (projectId, payload) =>
    api.post(`${CP}/projects/${projectId}/blueprints/upload`, payload),
};
