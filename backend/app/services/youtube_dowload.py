import os
import uuid
import logging
import tempfile
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from yt_dlp import YoutubeDL

# Importaremos el analizador en el siguiente paso
from app.services.analyzer import analyze_bytes

# ============================================================
# Configuración de logging
# ============================================================
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# ============================================================
# Inicializar el router
# ============================================================
router = APIRouter()

# ============================================================
# Modelo de entrada del request
# ============================================================
class YouTubeRequest(BaseModel):
    url: str


# ============================================================
# Función auxiliar: descarga el video temporalmente
# ============================================================
def download_youtube_video(url: str) -> str:
    """
    Descarga un video de YouTube usando yt_dlp.
    Devuelve la ruta local del archivo descargado (en /tmp).
    """

    # Directorio temporal permitido en Cloud Run
    tmp_dir = tempfile.gettempdir()
    video_id = str(uuid.uuid4())[:8]
    output_path = os.path.join(tmp_dir, f"yt_{video_id}.mp4")

    # Opciones de yt_dlp (solo video, sin audio para acelerar)
    ydl_opts = {
        "format": "bestvideo[height<=480]+bestaudio/best[height<=480]",
        "merge_output_format": "mp4",
        "outtmpl": output_path,
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "ffmpeg_location": "C:/ffmpeg/bin",
        "max_filesize": 500 * 1024 * 1024,  # 500 MB límite
    }

    logger.info(f"Iniciando descarga de YouTube: {url}")
    logger.info(f"Ruta temporal: {output_path}")

    try:
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        if not os.path.exists(output_path):
            raise FileNotFoundError("La descarga no generó el archivo esperado.")
        size = os.path.getsize(output_path)
        logger.info(f"Descarga completada correctamente. Tamaño: {size / (1024 * 1024):.2f} MB")
        return output_path

    except Exception as e:
        logger.exception(f"Error al descargar video desde YouTube: {e}")
        raise HTTPException(status_code=500, detail=f"Error al descargar video: {str(e)}")