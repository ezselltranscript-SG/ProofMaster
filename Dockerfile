FROM node:16-alpine as frontend-build

WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

FROM python:3.9-slim

WORKDIR /app

# Copiar los archivos de requisitos primero para aprovechar la caché de Docker
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto de los archivos del backend
COPY backend/ .

# Copiar los archivos construidos del frontend
COPY --from=frontend-build /app/frontend/build /app/static

# Exponer el puerto que utiliza la aplicación
EXPOSE 8000

# Variables de entorno
ENV SUPABASE_URL=${SUPABASE_URL}
ENV SUPABASE_KEY=${SUPABASE_KEY}

# Comando para ejecutar la aplicación
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
