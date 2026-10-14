import axios from "axios";

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000",
  timeout: 30000,
});

export async function getHealth() {
  const response = await api.get("/health");
  return response.data;
}

export async function uploadDocument(file) {
  const formData = new FormData();
  formData.append("file", file);
  const response = await api.post("/api/documents", formData, {
    headers: { "Content-Type": "multipart/form-data" },
    timeout: 180000,
  });
  return response.data;
}
