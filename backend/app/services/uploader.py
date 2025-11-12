# app/services/uploader.py
from datetime import timedelta
import os
from google.cloud import storage
import logging
import subprocess

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def get_gcs_client():
    credentials_path = os.getenv("GCS_CREDENTIALS_PATH")
    logger.info(f"Usando credenciales de GCS en: {credentials_path}")
    if not credentials_path or not os.path.exists(credentials_path):
        raise FileNotFoundError("No se encontró el archivo de credenciales de GCS.")
    return storage.Client.from_service_account_json(credentials_path)

def upload_to_gcs(local_path: str, destination_blob_name: str) -> str:
    """
    Sube un archivo al bucket de GCS y devuelve una URL firmada temporal (24h).
    Compatible con buckets con acceso uniforme (sin ACLs).
    """
    bucket_name = os.getenv("GCS_BUCKET_NAME")
    credentials_path = os.getenv("GCS_CREDENTIALS_PATH")
    logger.info(f"Usando credenciales de GCS en: {credentials_path}")

    client = storage.Client.from_service_account_json(credentials_path)
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)

    try:
        blob.chunk_size = 10 * 1024 * 1024  # 10 MB por chunk
        blob.upload_from_filename(local_path, timeout=600)

        
        url = blob.generate_signed_url(
            expiration=timedelta(hours=24),
            method="GET",
        )

        logger.info(f"Archivo subido correctamente: gs://{bucket_name}/{destination_blob_name}")
        logger.info(f"URL firmada (válida 24h): {url}")

        return url

    except Exception as e:
        logger.exception(f"Error al subir archivo a GCS: {e}")
        raise

def delete_from_gcs(destination_blob_name: str):
    bucket_name = os.getenv("GCS_BUCKET_NAME")
    client = get_gcs_client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)
    try:
        if blob.exists():
            blob.delete()
            logger.info(f"Archivo gs://{bucket_name}/{destination_blob_name} eliminado.")
        else:
            logger.warning(f"No existe gs://{bucket_name}/{destination_blob_name}.")
    except Exception as e:
        logger.error(f"Error al eliminar archivo de GCS: {e}")
        raise

def compress_video(input_path: str, output_path: str) -> str:
    import shutil
    ffmpeg_path = shutil.which("ffmpeg") or "C:\\ffmpeg\\bin\\ffmpeg.exe"
    compressed_path = output_path.replace(".mp4", "_compressed.mp4")

    if not os.path.exists(input_path):
        logger.warning(f"⚠️ Archivo no encontrado para comprimir: {input_path}")
        return output_path

    command = [
        ffmpeg_path, "-y",
        "-i", f'"{input_path}"',
        "-b:v", "1500k",
        "-bufsize", "1500k",
        f'"{compressed_path}"'
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
            logger.error(f" FFmpeg compresión falló:\n{result.stderr}")
            return input_path

        logger.info(f"✅ Video comprimido generado: {compressed_path}")
        return compressed_path

    except Exception as e:
        logger.error(f"⚠️ Error comprimiendo video: {e}")
        return input_path

