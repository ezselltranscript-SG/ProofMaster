# ProofMaster

ProofMaster es una aplicación de corrección ortográfica que utiliza FastAPI para el backend y React para el frontend.

## Estructura del Proyecto

```
ProofMaster/
├── backend/             # API de FastAPI
│   ├── main.py          # Punto de entrada de la API
│   ├── requirements.txt # Dependencias del backend
│   └── .env.example     # Ejemplo de variables de entorno
│
└── frontend/            # Aplicación React
    ├── public/          # Archivos estáticos
    └── src/             # Código fuente de React
        ├── components/  # Componentes reutilizables
        ├── pages/       # Páginas de la aplicación
        ├── services/    # Servicios para comunicación con API
        └── styles/      # Estilos globales
```

## Requisitos

- Python 3.8+
- Node.js 14+
- npm 6+
- Supabase (cuenta y proyecto configurado)

## Configuración

### Backend

1. Navega a la carpeta del backend:
   ```
   cd backend
   ```

2. Crea un entorno virtual:
   ```
   python -m venv venv
   ```

3. Activa el entorno virtual:
   - Windows: `venv\Scripts\activate`
   - Linux/Mac: `source venv/bin/activate`

4. Instala las dependencias:
   ```
   pip install -r requirements.txt
   ```

5. Crea un archivo `.env` basado en `.env.example` y configura tus credenciales de Supabase.

6. Inicia el servidor:
   ```
   uvicorn main:app --reload
   ```

### Frontend

1. Navega a la carpeta del frontend:
   ```
   cd frontend
   ```

2. Instala las dependencias:
   ```
   npm install
   ```

3. Inicia la aplicación:
   ```
   npm start
   ```

## Uso

1. Abre tu navegador y ve a `http://localhost:3000`
2. Escribe o pega el texto que deseas revisar en el editor
3. Haz clic en "Analizar Texto" para obtener sugerencias de corrección
4. Utiliza el botón "Fix All Issues" para aplicar todas las correcciones sugeridas

## Licencia

© 2025 ProofMaster. Todos los derechos reservados.
