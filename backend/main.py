import os
import re
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel
from typing import List
from supabase import create_client, Client
from dotenv import load_dotenv

# Función simple de similitud para reemplazar Levenshtein
def similarity_ratio(s1, s2):
    """Calcula una ratio de similitud simple entre dos cadenas."""
    s1, s2 = s1.lower(), s2.lower()
    
    # Si las cadenas son iguales, la similitud es 1.0
    if s1 == s2:
        return 1.0
    
    # Si una cadena está contenida en la otra, hay alta similitud
    if s1 in s2 or s2 in s1:
        return 0.9
    
    # Contar caracteres comunes
    common = sum(min(s1.count(c), s2.count(c)) for c in set(s1 + s2))
    total = len(s1) + len(s2)
    
    # Devolver ratio de similitud
    return 2 * common / total if total > 0 else 0.0

# Cargar variables desde .env
load_dotenv()

# Configura tus claves
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
class SpellCheckRequest(BaseModel):
    text: str

class Suggestion(BaseModel):
    original: str
    suggestion: str
    similarity: float

class SpellCheckResponse(BaseModel):
    suggestions: List[Suggestion]
    corrected_text: str
    full_corrected_code: str  # Campo añadido para devolver el código corregido

# Inicializar FastAPI
app = FastAPI(
    title="ProofMaster API",
    description="API para la aplicación de corrección ortográfica ProofMaster",
    version="1.0.0"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permitir todos los orígenes en desarrollo
    allow_credentials=True,
    allow_methods=["*"],  # Permitir todos los métodos
    allow_headers=["*"],  # Permitir todos los headers
)

# Ruta raíz para mostrar una página de bienvenida
@app.get("/", response_class=HTMLResponse)
def read_root():
    html_content = """
    <!DOCTYPE html>
    <html>
        <head>
            <title>ProofMaster API</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    max-width: 800px;
                    margin: 0 auto;
                    padding: 20px;
                    line-height: 1.6;
                }
                h1 {
                    color: #2979ff;
                }
                .endpoint {
                    background-color: #f5f5f5;
                    padding: 10px;
                    border-radius: 5px;
                    margin-bottom: 10px;
                }
                a {
                    color: #2979ff;
                    text-decoration: none;
                }
                a:hover {
                    text-decoration: underline;
                }
            </style>
        </head>
        <body>
            <h1>ProofMaster API</h1>
            <p>Bienvenido a la API de ProofMaster, una aplicación de corrección ortográfica.</p>
            
            <h2>Endpoints disponibles:</h2>
            <div class="endpoint">
                <strong>POST /spellcheck</strong>: Analiza un texto y devuelve sugerencias de corrección.
            </div>
            
            <p>Para ver la documentación completa de la API, visita <a href="/docs">/docs</a>.</p>
            
            <p>Para acceder a la interfaz de usuario de ProofMaster, necesitas desplegar el frontend por separado.</p>
        </body>
    </html>
    """
    return html_content

# Redireccionar a la documentación
@app.get("/api")
def redirect_to_docs():
    return RedirectResponse(url="/docs")

# Endpoint principal
@app.post("/spellcheck", response_model=SpellCheckResponse)
def spellcheck(request: SpellCheckRequest):
    text = request.text
    suggestions = []

    try:
        # Conectar y obtener datos de la tabla spellcheck
        response = supabase.table("spellcheck").select("original, suggestion").execute()
        replacements = response.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al conectar con Supabase: {str(e)}")

    words = re.findall(r"\b\w+\b|[^\s\w]", text)  # Incluye signos de puntuación
    corrected_words = []
    full_corrected_code = []  # Lista para almacenar las palabras corregidas y el código

    for word in words:
        found_match = False
        for item in replacements:
            original = item["original"]
            suggestion_text = item["suggestion"]
            similarity = similarity_ratio(word, original)

            # Si la similitud es 1.0 o si es mayor a 0.8 y la palabra coincide, sugerir la corrección
            if similarity == 1.0 or (similarity > 0.8 and word.lower() == original.lower()):
                corrected_words.append(suggestion_text)
                suggestions.append({
                    "original": word,
                    "suggestion": suggestion_text,
                    "similarity": round(similarity, 2)
                })
                full_corrected_code.append(f"{original} -> {suggestion_text}")
                found_match = True
                break

        if not found_match:
            corrected_words.append(word)
            full_corrected_code.append(word)

    corrected_text = " ".join(corrected_words)
    full_corrected_code = "\n".join(full_corrected_code)  # Formato de código corregido con las sugerencias

    return {
        "suggestions": suggestions,
        "corrected_text": corrected_text,
        "full_corrected_code": full_corrected_code
    }
