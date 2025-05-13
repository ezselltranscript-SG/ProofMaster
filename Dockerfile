# Usar una imagen de Python para la aplicación
FROM python:3.9-slim

WORKDIR /app

# Copiar los archivos de requisitos primero para aprovechar la caché de Docker
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto de los archivos del backend
COPY backend/ ./

# Crear directorio para archivos estáticos y un archivo index.html básico
RUN mkdir -p ./static
RUN echo '<!DOCTYPE html><html><head><title>ProofMaster</title></head><body><h1>ProofMaster API</h1><p>Bienvenido a la API de ProofMaster</p></body></html>' > ./static/index.html

# Exponer el puerto que utiliza la aplicación
EXPOSE 8000

# Variables de entorno
ENV SUPABASE_URL=${SUPABASE_URL}
ENV SUPABASE_KEY=${SUPABASE_KEY}

# Comando para ejecutar la aplicación
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
