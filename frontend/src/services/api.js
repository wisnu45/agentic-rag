import axios from "axios";

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000",
  timeout: 30000,
});

// Keep the access token in memory rather than localStorage to reduce persistence
// of credentials in the browser. A page refresh requires signing in again.
let accessToken = "";

export function setAccessToken(token) {
  accessToken = token || "";
}

api.interceptors.request.use((config) => {
  if (accessToken) config.headers.Authorization = `Bearer ${accessToken}`;
  return config;
});

function apiPath(path) {
  return (import.meta.env.VITE_API_BASE_URL || "") === "/api" ? path : `/api${path}`;
}

export async function login(username, password) {
  const body = new URLSearchParams({ username, password });
  const response = await api.post(apiPath("/auth/token"), body, {
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
  });
  setAccessToken(response.data.access_token);
  try {
    const identity = await api.get(apiPath("/auth/me"));
    return identity.data;
  } catch (error) {
    setAccessToken("");
    throw error;
  }
}

export function logout() {
  setAccessToken("");
}

export async function getHealth() {
  const response = (import.meta.env.VITE_API_BASE_URL || "") === "/api"
    ? await axios.get("/health")
    : await api.get("/health");
  return response.data;
}

export async function uploadDocument(file) {
  const formData = new FormData();
  formData.append("file", file);
  const response = await api.post(apiPath("/documents"), formData, {
    headers: { "Content-Type": "multipart/form-data" },
    timeout: 180000,
  });
  return response.data;
}

export async function searchDocuments(query, topK = 5) {
  const response = await api.post(apiPath("/search"), { query, top_k: topK }, { timeout: 180000 });
  return response.data;
}

export async function askQuestion(message, sessionId = "web-session") {
  const response = await api.post(apiPath("/chat"), { session_id: sessionId, message }, { timeout: 240000 });
  return response.data;
}
