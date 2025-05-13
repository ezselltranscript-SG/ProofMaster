# Usar una imagen de Python para la aplicación
FROM python:3.9-slim

WORKDIR /app

# Copiar los archivos de requisitos primero para aprovechar la caché de Docker
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto de los archivos del backend
COPY backend/ ./

# Crear directorio para archivos estáticos
RUN mkdir -p ./static
RUN echo '<!DOCTYPE html><html><head><title>ProofMaster API</title><style>body{font-family:Arial,sans-serif;margin:0;padding:20px;color:#333}h1{color:#2c3e50}h2{color:#3498db}pre{background:#f4f4f4;border:1px solid #ddd;padding:1em;overflow:auto}a.btn{display:inline-block;padding:10px 20px;background:#3498db;color:white;text-decoration:none;border-radius:5px}</style></head><body><h1>ProofMaster API</h1><p>Bienvenido a la API de ProofMaster para corrección ortográfica.</p><h2>Endpoints disponibles:</h2><ul><li><strong>GET /</strong> - Esta página de bienvenida</li><li><strong>GET /api</strong> - Documentación de la API</li><li><strong>POST /spellcheck</strong> - Endpoint para revisar ortografía</li></ul><h2>Ejemplo de uso:</h2><pre>curl -X POST "https://proofmaster-api.onrender.com/spellcheck" -H "Content-Type: application/json" -d {"text": "Este es un texto con herrores ortograficos"}</pre><p><a href="/api" class="btn">Ver Documentación</a></p></body></html>' > ./static/index.html

# Variables de entorno
ENV SUPABASE_URL=${SUPABASE_URL}
ENV SUPABASE_KEY=${SUPABASE_KEY}

# Exponer puerto
EXPOSE 8000

# Comando para ejecutar la aplicación
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
