# ProofMaster API

Esta es la API de backend para ProofMaster, una aplicación de corrección ortográfica que utiliza FastAPI y Supabase.

## Requisitos

- Python 3.8+
- Supabase (cuenta y proyecto configurado)

## Instalación

1. Crea un entorno virtual:
   ```
   python -m venv venv
   ```

2. Activa el entorno virtual:
   - Windows: `venv\Scripts\activate`
   - Linux/Mac: `source venv/bin/activate`

3. Instala las dependencias:
   ```
   pip install -r requirements.txt
   ```

4. Crea un archivo `.env` basado en `.env.example` y configura tus credenciales de Supabase.

## Ejecución

Para iniciar el servidor de desarrollo:

```
python start.py
```

O directamente con uvicorn:

```
uvicorn main:app --reload
```

El servidor estará disponible en `http://localhost:8000`.

## Documentación de la API

Una vez que el servidor esté en ejecución, puedes acceder a la documentación interactiva de la API en:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Endpoints

### POST /spellcheck

Realiza una corrección ortográfica del texto proporcionado.

**Request Body:**
```json
{
  "text": "Texto a corregir"
}
```

**Response:**
```json
{
  "suggestions": [
    {
      "original": "palabra_original",
      "suggestion": "palabra_sugerida",
      "similarity": 0.85
    }
  ],
  "corrected_text": "Texto corregido",
  "full_corrected_code": "Formato de código con correcciones"
}
```

## Estructura de la Base de Datos

La API espera una tabla en Supabase llamada `spellcheck` con la siguiente estructura:

- `original`: Palabra original o con error
- `suggestion`: Palabra sugerida o correcta

## Configuración de CORS

La API está configurada para permitir solicitudes desde `http://localhost:3000` (el frontend de React).
