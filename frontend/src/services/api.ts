// src/services/api.ts
import axios from "axios";

const isLocal = window.location.hostname === "localhost";


const API_URL = isLocal
  ? "/api/v1" 
  : import.meta.env.VITE_API_BASE_URL1?.replace(/\/+$/, "") || "/api/v1";

console.log("🌐 API base URL:", API_URL);;

// ---------- Análisis de imagen ----------
export const analyzeImage = async (file: File) => {
  const fd = new FormData();
  fd.append("file", file);
  const { data } = await axios.post(`${API_URL}/analyze-image`, fd, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
};

// ---------- Análisis de frame ----------
export const analyzeFrame = async (blob: Blob) => {
  const fd = new FormData();
  fd.append("file", blob, "frame.jpg");
  const { data } = await axios.post(`${API_URL}/analyze-frame`, fd, {
    headers: { "Content-Type": "multipart/form-data" },
    timeout: 10000,
  });
  return data as {
    num_faces: number;
    results: { id: number; bbox: number[]; emotion: string; confidence: number }[];
  };
};

// ---------- NUEVO: Análisis de video de YouTube ----------
export const analyzeYouTube = async (youtubeUrl: string) => {
  const { data } = await axios.post(`${API_URL}/analyze-youtube`, {
    url: youtubeUrl, 
  });
  return data as {
    status: string;
    public_url: string;
    summary: Record<string, number>;
    frames_analyzed: number;
    duration_sec: number;
    message: string;
  };
};
