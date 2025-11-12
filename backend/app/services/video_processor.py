import os
import cv2
import numpy as np
import time
import logging
import uuid
import subprocess
from app.services.analyzer import analyze_bytes
from app.services.uploader import compress_video, upload_to_gcs  

# =========== CONFIGURAR LOGGING ========== #
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


# ==========================================================
# FUNCIÓN AUXILIAR: COMBINAR AUDIO ORIGINAL CON EL PROCESADO
# ==========================================================
def merge_audio(original_path: str, processed_path: str) -> str:
    """
    Combina el video procesado con el audio original usando FFmpeg.
    """
    import shutil
    ffmpeg_path = shutil.which("ffmpeg") or "C:\\ffmpeg\\bin\\ffmpeg.exe"
    final_path = processed_path.replace(".mp4", "_with_audio.mp4")

    if not os.path.exists(original_path):
        logger.warning("⚠️ Archivo original no encontrado para mezclar audio.")
        return processed_path
    if not os.path.exists(processed_path):
        logger.warning("⚠️ Archivo procesado no encontrado para mezclar audio.")
        return processed_path

    command = [
        ffmpeg_path, "-y",
        "-i", f'"{processed_path}"',
        "-i", f'"{original_path}"',
        "-c:v", "copy",
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-shortest",
        f'"{final_path}"'
    ]
    command_str = " ".join(command)

    try:
        result = subprocess.run(
            command_str,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        if result.returncode != 0:
            logger.error(f"FFmpeg mezcla falló:\n{result.stderr}")
            return processed_path

        logger.info(f"✅ Video final con audio generado: {final_path}")
        return final_path

    except Exception as e:
        logger.warning(f"⚠️ No se pudo combinar audio: {e}")
        return processed_path



# ==========================================================
# FUNCIÓN PRINCIPAL: PROCESAR VIDEO COMPLETO
# ==========================================================
def process_video(video_path: str) -> dict:
    """
    Procesa un video completo con detección de emociones.
    - Dibuja las detecciones sobre el video.
    - Mantiene persistencia entre frames.
    - Combina el audio original.
    - Sube el resultado final a Google Cloud Storage.
    """

    start_time = time.time()
    logger.info(f"Iniciando procesamiento de video: {video_path}")

    if not os.path.exists(video_path):
        raise FileNotFoundError("El archivo de video no existe.")

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise Exception("No se pudo abrir el video.")

    fps = cap.get(cv2.CAP_PROP_FPS) or 25
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    logger.info(f"Resolución: {frame_width}x{frame_height}, FPS: {fps:.2f}, Total frames: {total_frames}")

    # ==== Configuración de salida ====
    output_id = str(uuid.uuid4())[:8]
    temp_name = f"processed_{output_id}.mp4"
    output_path = os.path.join(os.path.dirname(video_path), temp_name)
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (frame_width, frame_height))

    frame_interval = int(fps * 2)  # Analizar 1 frame cada ~2 segundos
    processed_frames = 0
    analyzed_frames = 0

    # ==== Contadores de emociones ====
    emotion_counts = {e: 0 for e in ['angry', 'disgust', 'fear', 'happy', 'neutral', 'sad', 'surprise']}

    # ==== Colores por emoción ====
    COLORS = {
        "neutral": (189, 195, 199),
        "happy": (46, 204, 113),
        "surprise": (241, 196, 15),
        "sad": (52, 152, 219),
        "angry": (231, 76, 60),
        "disgust": (22, 160, 133),
        "fear": (142, 68, 173),
    }

    # ==== Persistencia de detecciones ====
    last_detections = []

    logger.info("Iniciando bucle de procesamiento de frames...")

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            if frame is None or len(frame.shape) != 3:
                logger.warning("Frame inválido o sin canales RGB, se omite.")
                continue

            frame_id = int(cap.get(cv2.CAP_PROP_POS_FRAMES))
            processed_frames += 1

            # === Usar detecciones previas en frames intermedios ===
            if processed_frames % frame_interval != 0:
                if last_detections:
                    for det in last_detections:
                        bbox = det.get("bbox") or det.get("box")
                        if not bbox or len(bbox) != 4:
                            continue
                        x, y, w, h = map(int, bbox)
                        emotion = det["emotion"]
                        confidence = det["confidence"]

                        color = COLORS.get(emotion, (0, 255, 0))
                        label = f"{emotion.upper()} {confidence*100:.1f}%"

                        cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
                        text_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
                        text_w, text_h = text_size
                        cv2.rectangle(frame, (x, y - 20), (x + text_w, y), color, -1)
                        cv2.putText(frame, label, (x, y - 5),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
                out.write(frame)
                continue

            # === Procesar frame actual ===
            analyzed_frames += 1
            ret, buffer = cv2.imencode('.jpg', frame)
            if not ret:
                continue

            try:
                result = analyze_bytes(buffer.tobytes())
            except Exception as e:
                logger.warning(f"Error analizando frame {frame_id}: {e}")
                out.write(frame)
                continue

            detections = result.get("results", [])
            if detections:
                last_detections = detections  # Guardar detecciones para persistencia
                for det in detections:
                    bbox = det.get("bbox") or det.get("box")
                    if not bbox or len(bbox) != 4:
                        continue

                    x, y, w, h = map(int, bbox)
                    emotion = det["emotion"]
                    confidence = det["confidence"]

                    color = COLORS.get(emotion, (0, 255, 0))
                    label = f"{emotion.upper()} {confidence*100:.1f}%"

                    cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
                    text_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
                    text_w, text_h = text_size
                    cv2.rectangle(frame, (x, y - 20), (x + text_w, y), color, -1)
                    cv2.putText(frame, label, (x, y - 5),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)

                    # Actualizar contador de emociones
                    if emotion in emotion_counts:
                        emotion_counts[emotion] += 1

            out.write(frame)

        logger.info(f"Procesamiento completado. Frames analizados: {analyzed_frames}/{processed_frames}")

    finally:
        cap.release()
        out.release()

    # === Estadísticas ===
    elapsed = time.time() - start_time
    total = sum(emotion_counts.values()) or 1
    summary = {k: round((v / total) * 100, 2) for k, v in emotion_counts.items()}

    # === Combinar audio ===
    output_with_audio = merge_audio(video_path, output_path)
    
    compressed_path = compress_video(output_with_audio, output_with_audio)


    # === Subir a Google Cloud Storage ===
    try:
        filename = os.path.basename(compressed_path)
        gcs_path = f"processed_videos/{filename}"
        public_url = upload_to_gcs(compressed_path, gcs_path)

        logger.info(f"✅ Video subido a GCS correctamente: {public_url}")

        # Eliminar archivo local
        os.remove(output_with_audio)
        logger.info("🗑️ Archivo local eliminado tras la subida.")
    except Exception as e:
        logger.exception("Error subiendo el video a GCS")
        public_url = None

    logger.info(f"Resumen de emociones: {summary}")
    logger.info(f"Tiempo total: {elapsed:.2f}s")

    return {
        "summary": summary,
        "frames_analyzed": analyzed_frames,
        "duration_sec": round(elapsed, 2),
        "public_url": public_url,
    }
