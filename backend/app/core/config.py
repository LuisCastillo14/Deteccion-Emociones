import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    PROJECT_NAME: str = "EmotiScan"
    VERSION: str = "1.0.0"
    BACKEND_CORS_ORIGINS = ["http://localhost:5173"]  # Frontend Vite

settings = Settings()
