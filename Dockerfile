# Usar una imagen de Node.js para construir el frontend
FROM node:16-alpine as frontend-build

WORKDIR /app/frontend

# Copiar package.json y package-lock.json si existen
COPY frontend/package*.json ./

# Instalar dependencias si existe package.json
RUN if [ -f package.json ]; then npm install; fi

# Copiar el resto de los archivos del frontend
COPY frontend/ ./

# Construir el frontend si existe package.json
RUN if [ -f package.json ]; then npm run build || echo "Build failed, continuing..."; fi

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

# Copiar los archivos del frontend construido al directorio static
COPY --from=frontend-build /app/frontend/build ./static/ || true
COPY --from=frontend-build /app/frontend/public ./static/ || true
COPY --from=frontend-build /app/frontend/dist ./static/ || true
COPY --from=frontend-build /app/frontend/src ./static/src/ || true
COPY frontend/src/components ./static/components/ || true
COPY frontend/src/pages ./static/pages/ || true
COPY frontend/public ./static/public/ || true

# Exponer el puerto que utiliza la aplicación
EXPOSE 8000

# Variables de entorno
ENV SUPABASE_URL=${SUPABASE_URL}
ENV SUPABASE_KEY=${SUPABASE_KEY}

# Comando para ejecutar la aplicación
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
