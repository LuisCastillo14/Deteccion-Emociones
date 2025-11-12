import React, { useState } from "react";
import { analyzeImage } from "../../services/api";
import "../../styles/UploadPage.css";
import ImageWithBoxes from "../../components/ImageWithBoxes";

interface PersonResult {
  id: number;
  bbox: number[];
  emotion: string;
  confidence: number;
  all_probs: Record<string, number>;
}

interface ApiResponse {
  num_faces: number;
  results: PersonResult[];
}

const emotionMap: Record<string, string> = {
  neutral: "Neutral",
  happy: "Felicidad",
  surprise: "Sorpresa",
  sad: "Tristeza",
  angry: "Enojo",
  disgust: "Disgusto",
  fear: "Miedo",
};

const MAX_SIZE_BYTES = 10 * 1024 * 1024; // 10MB

const UploadPage: React.FC = () => {
  const [preview, setPreview] = useState<string | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ApiResponse | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  const resetFeedback = () => {
    setErrorMsg(null);
    setSuccessMsg(null);
  };

  const handleFile = (f: File) => {
    resetFeedback();

    if (!f.type.startsWith("image/")) {
      setErrorMsg("El archivo debe ser una imagen (JPG/PNG/WebP).");
      return;
    }
    if (f.size > MAX_SIZE_BYTES) {
      setErrorMsg("La imagen supera el tamaño permitido (10 MB).");
      return;
    }

    const reader = new FileReader();
    reader.onloadend = () => setPreview(reader.result as string);
    reader.readAsDataURL(f);
    setFile(f);
    setResult(null);
  };

  const handleInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) handleFile(e.target.files[0]);
  };

  const handleAnalyze = async () => {
    if (!file) return;
    setLoading(true);
    setErrorMsg(null);
    setSuccessMsg(null);

    try {
      const response = (await analyzeImage(file)) as ApiResponse;
      setResult(response);

      if (response.num_faces === 0) {
        setSuccessMsg("Análisis completado. No se detectaron rostros.");
      } else {
        setSuccessMsg(`Análisis completado. Se detectaron ${response.num_faces} rostro(s).`);
      }
    } catch (err: any) {
      setErrorMsg(err?.message || "Ocurrió un error analizando la imagen.");
      setResult(null);
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setPreview(null);
    setFile(null);
    setResult(null);
    resetFeedback();
  };

  return (
    <div className="text-center mt-4">
      {/* Feedback */}
      {errorMsg && (
        <div
          style={{
            maxWidth: 640,
            margin: "0 auto 12px",
            padding: "10px 12px",
            borderRadius: 8,
            background: "#ffe5e7",
            color: "#b00020",
            textAlign: "left",
          }}
        >
          <strong>❌ Error:</strong> {errorMsg}
        </div>
      )}
      {successMsg && (
        <div
          style={{
            maxWidth: 640,
            margin: "0 auto 12px",
            padding: "10px 12px",
            borderRadius: 8,
            background: "#e9f9ef",
            color: "#0f7b3b",
            textAlign: "left",
          }}
        >
          {successMsg}
        </div>
      )}

      {/* Cuadro de Upload siempre visible */}
      <div
        className="upload-box"
        onClick={() => document.getElementById("fileInput")?.click()}
        style={{ cursor: loading ? "not-allowed" : "pointer", opacity: loading ? 0.7 : 1 }}
      >
        {preview ? (
          result ? (
            <ImageWithBoxes imageUrl={preview} results={result.results} />
          ) : (
            <img
              src={preview}
              alt="preview"
              style={{ maxHeight: "200px", maxWidth: "100%", borderRadius: 8 }}
            />
          )
        ) : (
          <>
            <i className="fas fa-upload fa-2x" style={{ color: "#666" }} />
            <p className="upload-text">Subir imagen</p>
            <p style={{ color: "#888", marginTop: 4, fontSize: 12 }}>
              JPG / PNG / WebP &nbsp;•&nbsp; Máx 10 MB
            </p>
          </>
        )}

        <input
          type="file"
          id="fileInput"
          style={{ display: "none" }}
          accept="image/*"
          onChange={handleInput}
          disabled={loading}
        />
      </div>

      {/* Acciones */}
      {!result ? (
        <button className="btn-analysis mt-3" onClick={handleAnalyze} disabled={!file || loading}>
          {loading ? "Analizando imagen..." : "Empezar análisis"}
        </button>
      ) : (
        <button className="btn-analysis mt-3" onClick={handleReset} disabled={loading}>
          Analizar otra imagen
        </button>
      )}

      {loading && (
        <div className="elegant-spinner mt-3">
          <div className="lds-ring">
            <div></div><div></div><div></div><div></div>
          </div>
        </div>
      )}

      {/* Dashboard múltiple */}
      {result &&
        result.results
          .slice()
          .sort((a, b) => a.bbox[0] - b.bbox[0])
          .map((person, index) => {
            return (
              <div
                key={`${index}-${person.bbox.join(",")}`}
                className="card mt-4 p-3 text-start mx-auto"
                style={{ maxWidth: 600 }}
              >
                <h5 className="mb-3">Persona {index + 1}</h5>

                <div className="d-flex align-items-center">
                  {/* Emoción principal */}
                  <div className="me-4 text-center">
                    <p className="mt-2 mb-1">Emoción principal</p>
                    <span style={{ fontSize: "2rem" }}>
                      {person.emotion === "happy" && "😊"}
                      {person.emotion === "sad" && "😢"}
                      {person.emotion === "angry" && "😡"}
                      {person.emotion === "neutral" && "😐"}
                      {person.emotion === "surprise" && "😲"}
                      {person.emotion === "disgust" && "🤢"}
                      {person.emotion === "fear" && "😨"}
                    </span>
                    <p className="fw-bold">{emotionMap[person.emotion] || person.emotion}</p>
                    <p className="text-muted">
                      Confianza: {Math.min(100, Math.max(0, person.confidence * 100)).toFixed(1)}%
                    </p>
                  </div>

                  {/* Barras */}
                  <div className="flex-grow-1">
                    {Object.entries(person.all_probs).map(([emo, prob]) => {
                      const pct = Math.min(100, Math.max(0, prob * 100));
                      let color = "#6c757d";
                      if (emo === "happy") color = "#28a745";
                      if (emo === "sad") color = "#007bff";
                      if (emo === "angry") color = "#dc3545";
                      if (emo === "neutral") color = "#6c757d";
                      if (emo === "surprise") color = "#ffc107";
                      if (emo === "disgust") color = "#8e44ad";
                      if (emo === "fear") color = "#17a2b8";

                      return (
                        <div key={`${emo}-${index}`} className="mb-2">
                          <div className="d-flex justify-content-between">
                            <span>{emotionMap[emo] || emo}</span>
                            <span>{Math.round(pct)}%</span>
                          </div>
                          <div className="progress" style={{ height: 20 }}>
                            <div
                              className="progress-bar"
                              role="progressbar"
                              style={{ width: `${pct}%`, backgroundColor: color }}
                              aria-valuenow={pct}
                              aria-valuemin={0}
                              aria-valuemax={100}
                            />
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              </div>
            );
          })}
    </div>
  );
};

export default UploadPage;
