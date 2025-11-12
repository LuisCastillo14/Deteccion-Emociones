# Imagen base de Python
FROM python:3.10-slim

# Evita mensajes de instalación
ENV DEBIAN_FRONTEND=noninteractive

# Instalar librerías necesarias para OpenCV y TensorFlow
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxrender1 \
    libxext6 \
    ffmpeg \
 && rm -rf /var/lib/apt/lists/*


# Copiar los archivos del proyecto al contenedor
WORKDIR /app
COPY . /app

# Instalar dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8080
CMD gunicorn -k uvicorn.workers.UvicornWorker -w 1 -b 0.0.0.0:${PORT:-8080} app.main:app

