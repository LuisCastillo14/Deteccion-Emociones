
import logging
from fastapi import APIRouter, HTTPException, BackgroundTasks


# Importaremos el analizador en el siguiente paso
from app.services.video_processor import process_video
from app.services.youtube_dowload import YouTubeRequest, download_youtube_video


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


router = APIRouter()


@router.post("/analyze-youtube")
async def analyze_youtube_video(request: YouTubeRequest, background_tasks: BackgroundTasks):
    """
    Endpoint que descarga, analiza y procesa un video de YouTube.
    """

    logger.info("======= POST /analyze-youtube =======")

    # Validar URL
    url = request.url.strip()
    if not url.startswith("http") or "youtube.com" not in url and "youtu.be" not in url:
        raise HTTPException(status_code=400, detail="URL de YouTube inválida")

    # Paso 1: Descargar video temporalmente
    try:
        video_path = download_youtube_video(url)
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.exception("Fallo inesperado en descarga")
        raise HTTPException(status_code=500, detail=str(e))

    # Paso 2: Procesar el video
    try:
        result = process_video(video_path)
    except Exception as e:
        logger.exception("Error en el procesamiento del video")
        raise HTTPException(status_code=500, detail=str(e))

    # Devuelve respuesta con ruta local (temporal) y resumen
    return {
        "status": "done",
        "public_url": result["public_url"], 
        "summary": result["summary"],
        "frames_analyzed": result["frames_analyzed"],
        "duration_sec": result["duration_sec"],
        "message": "Video procesado y subido correctamente a GCS."
    }
