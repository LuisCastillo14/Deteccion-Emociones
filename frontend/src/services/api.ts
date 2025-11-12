// src/services/api.ts
import axios from "axios";

const API_URL =
  import.meta.env.VITE_API_BASE_URL1?.toString().replace(/\/+$/, "") ||
  "/api/v1";

console.log("API URL:", API_URL);

// ---------- Análisis de imagen ----------
export const analyzeImage = async (file: File) => {
  const fd = new FormData();
  console.log("Conectando a API para analizar", API_URL);
  fd.append("file", file);
  const { data } = await axios.post(`${API_URL}/analyze-image`, fd, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
};

// ---------- Análisis de frame ----------
export const analyzeFrame = async (blob: Blob) => {
  const fd = new FormData();
  console.log("Conectando a API para analizar", API_URL);
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
  console.log("Conectando a API para analizar video de YouTube:", API_URL);
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
