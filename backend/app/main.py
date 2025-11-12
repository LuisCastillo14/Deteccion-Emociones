from fastapi import FastAPI
import os
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1 import analyze, youtube
from dotenv import load_dotenv

app = FastAPI(title="EmotiScan API", version="1.0.0")
load_dotenv()
credetials_path = os.getenv("GCS_CREDENTIALS_PATH")
print(f"Usando credenciales de GCS en: {credetials_path}")


origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://deteccion-emociones.vercel.app",
    "https://deteccion-emociones.vercel.app/",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ======================================================
# 🌐 Routers principales (análisis y YouTube)
# ======================================================
app.include_router(analyze.router, prefix="/api/v1", tags=["Análisis"])
app.include_router(youtube.router, prefix="/api/v1", tags=["YouTube"])


# ======================================================
# 🧩 Endpoint raíz simple
# ======================================================
@app.get("/")
def read_root():
    return {"message": "✅ Backend FastAPI listo con modelo de detección de emociones"}


