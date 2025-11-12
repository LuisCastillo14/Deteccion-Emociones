import React, { useRef, useEffect } from "react";

interface PersonResult {
  id: number;
  bbox: number[]; // [x, y, w, h]
  emotion: string;
  confidence: number;
}

interface Props {
  imageUrl: string;
  results: PersonResult[];
}

const COLORS: Record<string, string> = {
  neutral: "#7f8c8d",
  happy: "#2ecc71",
  surprise: "#f1c40f",
  sad: "#3498db",
  angry: "#e74c3c",
  disgust: "#6ab04c",
  fear: "#8e44ad",
};

const ImageWithBoxes: React.FC<Props> = ({ imageUrl, results }) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    const ctx = canvas?.getContext("2d");
    if (!canvas || !ctx) return;

    const image = new Image();
    image.src = imageUrl;
    image.onload = () => {
      // Ajusta el canvas al tamaño nativo de la imagen (el contenedor limita el render)
      canvas.width = image.width;
      canvas.height = image.height;
      ctx.drawImage(image, 0, 0);

      results.forEach((r, index) => {
        const [x, y, w, h] = r.bbox;
        const color = COLORS[r.emotion] || "#2ecc71";

        // Caja
        ctx.strokeStyle = color;
        ctx.lineWidth = 2;
        ctx.strokeRect(x, y, w, h);

        // Etiqueta
        const text = `Persona ${index + 1}: ${r.emotion.toUpperCase()} ${(r.confidence * 100).toFixed(1)}%`;
        ctx.font = "bold 14px 'Segoe UI'";
        const tw = ctx.measureText(text).width;

        ctx.fillStyle = "rgba(0,0,0,0.65)";
        ctx.fillRect(x, y - 22, tw + 10, 20);

        ctx.fillStyle = color;
        ctx.fillText(text, x + 5, y - 7);
      });
    };
  }, [imageUrl, results]);

  return <canvas ref={canvasRef} style={{ maxWidth: "100%", borderRadius: 8 }} />;
};

export default ImageWithBoxes;
