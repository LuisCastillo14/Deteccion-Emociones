import io
import os
import cv2
import numpy as np
from PIL import Image
from typing import Dict
import tensorflow as tf
from tensorflow.keras.models import load_model
from mtcnn import MTCNN
import threading
import logging
import time

# ========== CONFIGURAR LOGGING ==========
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

# ========== CONFIGURACIÓN ==========
logger.info("Inicializando detector y modelo de emociones")

start_time = time.time() 
detector = MTCNN()

MODEL_PATH = os.getenv(
    "MODEL_PATH",
    os.path.join(os.path.dirname(__file__), "..", "model", "modelo_v2b.h5")
)
logger.info(f"Ruta del modelo: {MODEL_PATH}")

# Cargar modelo ResNet50
model = load_model(MODEL_PATH, compile=False)
model.compile(optimizer="adam", loss="sparse_categorical_crossentropy", metrics=["accuracy"])
load_time = time.time() - start_time
logger.info(f"Modelo cargado correctamente en {load_time:.2f}s")

# Parámetros globales
TARGET_SIZE = 224
USE_GRAYSCALE = True
USE_CLAHE = True
DEBUG_SAVE_FRAMES = True   # 👈 Activa/desactiva guardado de rostros procesados
DEBUG_DIR = os.path.join(os.path.dirname(__file__), "..", "debug_faces")

CLASS_NAMES = ['angry','disgust','fear','happy','neutral','sad','surprise']
model_lock = threading.Lock()


# ========== UTILIDADES ==========
def ensure_dir(path: str):
    """Crea el directorio si no existe."""
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)


def read_image_to_rgb(file_bytes: bytes) -> np.ndarray:
    """Convierte bytes de imagen a RGB (mantiene compatibilidad con PIL)."""
    try:
        img = Image.open(io.BytesIO(file_bytes))
        img = img.convert("RGB")
        return np.array(img)
    except Exception as e:
        logger.exception("Error al leer imagen con PIL")
        raise ValueError(f"No se pudo leer la imagen: {e}")

def detect_faces(img_rgb: np.ndarray):
    """
    Detecta rostros en una imagen RGB usando MTCNN.
    Devuelve una lista de bounding boxes [(x, y, w, h)].
    """
    try:
        detections = detector.detect_faces(img_rgb)
    except Exception as e:
        logger.warning(f"Error interno de MTCNN: {e}")
        return []

    bboxes = []
    for det in detections:
        # Validar formato correcto
        if not isinstance(det, dict):
            logger.debug(f"Detección no válida (tipo {type(det)}): {det}")
            continue
        if "box" not in det:
            logger.debug(f"Detección sin clave 'box': {det.keys()}")
            continue
        if "confidence" in det and det["confidence"] < 0.85:
            logger.debug("Rostro ignorado por baja confianza (<0.85)")
            continue

        x, y, w, h = det["box"]
        x, y = max(0, x), max(0, y)
        w, h = max(1, w), max(1, h)

        # Evitar rostros diminutos (ruido)
        if w < 30 or h < 30:
            logger.debug(f"Rostro ignorado por tamaño pequeño: {w}x{h}")
            continue

        bboxes.append((x, y, w, h))

    logger.info(f"Detectadas {len(bboxes)} caras válidas.")
    return bboxes



# ========== PROCESAMIENTO DEL ROSTRO ==========
def preprocess_face(face_rgb: np.ndarray, frame_id: int, face_id: int) -> np.ndarray:
    """
    Recorta y prepara el rostro para la red neuronal.
    Aplica escala de grises + CLAHE y guarda la imagen final usada por el modelo.
    """
    # 1️⃣ Escala de grises
    face_gray = cv2.cvtColor(face_rgb, cv2.COLOR_RGB2GRAY)

    # 2️⃣ Realce de contraste (CLAHE)
    if USE_CLAHE:
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        face_gray = clahe.apply(face_gray)

    # 3️⃣ Convertir a RGB (3 canales duplicados)
    face_rgb_ready = cv2.cvtColor(face_gray, cv2.COLOR_GRAY2RGB)

    # 4️⃣ Redimensionar
    resized = cv2.resize(face_rgb_ready, (TARGET_SIZE, TARGET_SIZE))


    # 6️⃣ Convertir a batch y preprocesar para ResNet
    img_array = np.expand_dims(resized.astype(np.float32), axis=0)
    img_pre = tf.keras.applications.resnet.preprocess_input(img_array)
    return img_pre


# ========== FUNCIÓN PRINCIPAL ==========
def analyze_bytes(file_bytes: bytes) -> Dict:
    img_rgb = read_image_to_rgb(file_bytes)
    bboxes = detect_faces(img_rgb)

    if not bboxes:
        return {"num_faces": 0, "results": []}

    results = []
    with model_lock:
        for i, (x, y, w, h) in enumerate(bboxes):
            roi = img_rgb[y:y+h, x:x+w]
            if roi.size == 0:
                continue

            # 🔹 Preprocesar y guardar rostro
            x_input = preprocess_face(roi, frame_id=0, face_id=i + 1)

            # 🔹 Inferencia
            preds = model.predict(x_input, verbose=0)[0]
            probs = tf.nn.softmax(preds).numpy()
            idx = int(np.argmax(probs))
            emotion = CLASS_NAMES[idx]
            confidence = float(probs[idx])

            results.append({
                "id": i + 1,
                "bbox": [int(x), int(y), int(w), int(h)],
                "emotion": emotion,
                "confidence": confidence,
                "all_probs": {CLASS_NAMES[j]: float(probs[j]) for j in range(len(CLASS_NAMES))},
            })

    return {"num_faces": len(results), "results": results}


# ========== ENDPOINT COMPATIBLE ==========
async def analyze_image(file) -> Dict:
    try:
        await file.seek(0)
        file_bytes = await file.read()
        if not file_bytes:
            raise ValueError("Archivo vacío o no válido")
        return analyze_bytes(file_bytes)
    except Exception as e:
        logger.exception("Error en analyze_image")
        raise
