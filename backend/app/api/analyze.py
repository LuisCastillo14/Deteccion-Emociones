from fastapi import APIRouter, UploadFile, File, HTTPException
from app.services.analyzer import analyze_image, analyze_bytes
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/analyze-image")
async def analyze_image_route(file: UploadFile = File(...)):
    logger.info("======= POST /analyze-image =======")
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="El archivo debe ser una imagen.")

    try:
        await file.seek(0)
        logger.info(f"Archivo recibido: {file.filename}, tipo: {file.content_type}")
        result = await analyze_image(file)
        logger.info(f"Análisis OK. Rostros detectados: {result.get('num_faces')}")
        return result
    except Exception as e:
        logger.exception("Error procesando imagen en /analyze-image")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze-frame")
async def analyze_frame_route(file: UploadFile = File(...)):
    logger.info("======= POST /analyze-frame =======")
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="El archivo debe ser una imagen (frame).")
    try:
        file_bytes = await file.read()
        logger.info(f"Tamaño frame: {len(file_bytes)} bytes")
        result = analyze_bytes(file_bytes)
        logger.info(f"Frame procesado con {result.get('num_faces')} rostro(s)")
        return result
    except Exception as e:
        logger.exception("Error procesando frame")
        raise HTTPException(status_code=500, detail=str(e))
