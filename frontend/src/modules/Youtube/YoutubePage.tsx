import React, { useState, useRef } from "react";
import { analyzeYouTube } from "../../services/api";
import EmotionCard from "../../components/EmotionCard";
import type { EmotionRow } from "../../components/EmotionCard";

const EMOTIONS = ["neutral", "happy", "surprise", "sad", "angry", "disgust", "fear"] as const;
type EmotionKey = typeof EMOTIONS[number];

const LABEL_ES: Record<EmotionKey, string> = {
  neutral: "Neutral",
  happy: "Feliz",
  surprise: "Sorpresa",
  sad: "Tristeza",
  angry: "Enojo",
  disgust: "Disgusto",
  fear: "Miedo",
};

const YouTubePage: React.FC = () => {
  const [url, setUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<null | Awaited<ReturnType<typeof analyzeYouTube>>>(null);
  const [error, setError] = useState<string | null>(null);
  const [videoDuration, setVideoDuration] = useState<number>(0);
  const hiddenVideoRef = useRef<HTMLVideoElement | null>(null);

  // === Extraer ID de video de YouTube ===
  const extractVideoId = (youtubeUrl: string): string | null => {
    try {
      const urlObj = new URL(youtubeUrl);
      if (urlObj.hostname.includes("youtu.be")) return urlObj.pathname.substring(1);
      return urlObj.searchParams.get("v");
    } catch {
      return null;
    }
  };

  // === Cargar duración del video (metadatos) ===
  const handleMetadataLoad = () => {
    if (hiddenVideoRef.current) {
      const dur = hiddenVideoRef.current.duration;
      if (!isNaN(dur) && dur > 0) {
        setVideoDuration(dur);
        console.log(`🎞️ Duración detectada: ${dur.toFixed(2)}s`);
      }
    }
  };

  // === Análisis del video ===
  const handleAnalyze = async (): Promise<void> => {
    if (!url.trim()) {
      alert("Por favor ingresa una URL válida de YouTube.");
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const data = await analyzeYouTube(url);
      setResult(data);
    } catch (err: any) {
      console.error(err);
      setError(err.response?.data?.detail || "Error analizando el video.");
    } finally {
      setLoading(false);
    }
  };

  // === Calcular resumen ===
  const rows: EmotionRow[] = React.useMemo(() => {
    if (!result?.summary) return [];
    const total = Object.values(result.summary).reduce((a, b) => a + b, 0) || 1;
    return EMOTIONS.map((e) => ({
      key: e,
      label: LABEL_ES[e],
      pct: ((result.summary[e] || 0) / total) * 100,
      avgConf: ((result.summary[e] || 0) / total) * 100,
    }));
  }, [result]);

  const main = React.useMemo<EmotionRow | null>(() => {
    if (!rows.length) return null;
    return rows.reduce((a, b) => (b.pct > a.pct ? b : a), rows[0]);
  }, [rows]);

  const videoId = extractVideoId(url);
  const embedUrl = videoId ? `https://www.youtube.com/embed/${videoId}` : null;
  const videoSrc = videoId ? `https://www.youtube.com/watch?v=${videoId}` : null;

  return (
    <div className="text-center mt-4">
      <h3 className="fw-bold mb-3">🎬 Análisis de Video de YouTube</h3>

      {/* === Campo de entrada === */}
      <div className="mb-4">
        <input
          type="text"
          value={url}
          onChange={(e) => {
            setUrl(e.target.value);
            setResult(null);
            setVideoDuration(0);
          }}
          placeholder="Pega el enlace de YouTube aquí"
          style={{ width: "60%", padding: 10 }}
        />
        <button
          onClick={handleAnalyze}
          disabled={loading}
          style={{
            background: "#0E1D36",
            color: "#fff",
            marginLeft: 8,
            border: "none",
            borderRadius: 6,
            padding: "10px 20px",
            fontWeight: 600,
          }}
        >
          {loading ? "Analizando..." : "Analizar"}
        </button>
      </div>

      {/* === Video visible === */}
      <div style={{ position: "relative", display: "inline-block" }}>
        {result ? (
          <video
            src={result.public_url}
            controls
            style={{
              width: "640px",
              height: "360px",
              borderRadius: 8,
              border: "2px solid #0E1D36",
            }}
          />
        ) : embedUrl ? (
          <iframe
            src={`${embedUrl}?enablejsapi=1&autoplay=0&mute=0&controls=1`}
            style={{
              width: "640px",
              height: "360px",
              border: "2px solid #0E1D36",
              borderRadius: 8,
            }}
            allow="autoplay; encrypted-media; picture-in-picture"
            allowFullScreen
          />
        ) : (
          <div
            style={{
              width: "640px",
              height: "360px",
              border: "2px dashed #aaa",
              borderRadius: 8,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              color: "#666",
            }}
          >
            <p>Pega un enlace de YouTube para comenzar</p>
          </div>
        )}
      </div>

      {/* === Video oculto para leer metadata === */}
      {videoSrc && (
        <video
          ref={hiddenVideoRef}
          src={`https://corsproxy.io/?${encodeURIComponent(videoSrc)}`}
          style={{ display: "none" }}
          preload="metadata"
          onLoadedMetadata={handleMetadataLoad}
        />
      )}

      {/* === Círculo elegante de carga === */}
      {loading && (
        <div style={{ marginTop: 40 }}>
          <div
            style={{
              width: 70,
              height: 70,
              margin: "0 auto",
              border: "6px solid rgba(14, 29, 54, 0.2)",
              borderTop: "6px solid #0E1D36",
              borderRadius: "50%",
              animation: "spin 1s linear infinite",
              boxShadow: "0 0 12px rgba(14,29,54,0.15)",
            }}
          />
          <p style={{ color: "#0E1D36", marginTop: 20, fontWeight: 600, fontSize: 16 }}>
            Analizando video... <br />
            <span style={{ color: "#555", fontWeight: 400 }}>
              Esto puede tardar algunos minutos, según la duración del video.
            </span>
          </p>

          <style>
            {`
              @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
              }
            `}
          </style>
        </div>
      )}

      {/* === Resultados === */}
      {result && (
        <div style={{ marginTop: 25 }}>
          <EmotionCard title="Resumen de emociones" rows={rows} main={main} />
          <p className="mt-3 text-secondary">
            ⏱️ {result.duration_sec.toFixed(1)}s analizados — {result.frames_analyzed} frames
          </p>
          <p className="text-success fw-bold">{result.message}</p>
        </div>
      )}

      {error && (
        <div className="alert alert-danger mt-3" style={{ width: 640, margin: "0 auto" }}>
          {error}
        </div>
      )}
    </div>
  );
};

export default YouTubePage;
