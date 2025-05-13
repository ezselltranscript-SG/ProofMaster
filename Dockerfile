# Etapa 1: Construir el frontend
FROM node:16-alpine AS frontend-builder

# Establecer directorio de trabajo
WORKDIR /app

# Copiar archivos del frontend
COPY frontend/ ./frontend/

# Verificar si existe package.json y construir si es posible
RUN if [ -f frontend/package.json ]; then \
    cd frontend && \
    npm install && \
    npm run build || echo "Frontend build failed, continuing..."; \
    fi

# Etapa 2: Configurar el backend y copiar archivos del frontend
FROM python:3.9-slim

# Establecer directorio de trabajo
WORKDIR /app

# Instalar dependencias del backend
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copiar archivos del backend
COPY backend/ ./

# Crear directorio para archivos estáticos
RUN mkdir -p ./static

# Copiar archivos del frontend desde la etapa de construcción
# Intentar copiar desde diferentes ubicaciones posibles
COPY --from=frontend-builder /app/frontend/build ./static/ 2>/dev/null || true
COPY --from=frontend-builder /app/frontend/dist ./static/ 2>/dev/null || true

# Si no se pudo copiar desde build o dist, copiar los archivos fuente
RUN if [ ! -f ./static/index.html ]; then \
    mkdir -p ./static/src && \
    echo '<!DOCTYPE html><html><head><title>ProofMaster</title><style>body{font-family:Arial,sans-serif;line-height:1.6;margin:0;padding:20px;color:#333}h1{color:#2c3e50}h2{color:#3498db}pre{background:#f4f4f4;border:1px solid #ddd;border-left:3px solid #3498db;color:#333;page-break-inside:avoid;font-family:monospace;font-size:15px;line-height:1.6;margin-bottom:1.6em;max-width:100%;overflow:auto;padding:1em 1.5em;display:block;word-wrap:break-word}.container{max-width:1100px;margin:0 auto;overflow:auto;padding:0 40px}.card{border:1px solid #ddd;border-radius:10px;box-shadow:0 3px 10px rgba(0,0,0,0.1);padding:20px;margin:10px;background-color:white}.btn{display:inline-block;padding:10px 20px;cursor:pointer;background:#3498db;color:white;border:none;border-radius:5px;text-decoration:none}.btn:hover{background:#2980b9}</style></head><body><div class="container"><div class="card"><h1>ProofMaster API</h1><p>Bienvenido a la API de ProofMaster para corrección ortográfica.</p><h2>Endpoints disponibles:</h2><ul><li><strong>GET /</strong> - Esta página de bienvenida</li><li><strong>GET /api</strong> - Documentación de la API</li><li><strong>POST /spellcheck</strong> - Endpoint para revisar ortografía</li></ul><h2>Ejemplo de uso:</h2><pre>curl -X POST "https://proofmaster.onrender.com/spellcheck" \
-H "Content-Type: application/json" \
-d \'{"text": "Este es un texto con herrores ortograficos"}\'
</pre><p>Para más información, visite la <a href="/api" class="btn">Documentación</a></p></div></div></body></html>' > ./static/index.html; \
    fi

# Variables de entorno
ENV SUPABASE_URL=${SUPABASE_URL}
ENV SUPABASE_KEY=${SUPABASE_KEY}

# Exponer puerto
EXPOSE 8000

# Comando para ejecutar la aplicación
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
