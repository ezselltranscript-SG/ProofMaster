import os
import re
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List
from supabase import create_client, Client
from dotenv import load_dotenv
import pathlib

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

# Inicializar el cliente de Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
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
    allow_origins=["https://proofmaster-frontend.onrender.com", "http://localhost:3000"],  # Permitir el frontend en producción y desarrollo
    allow_credentials=True,
    allow_methods=["*"],  # Permitir todos los métodos
    allow_headers=["*"],  # Permitir todos los headers
)

# Configurar directorio para archivos estáticos
@app.on_event("startup")
async def startup_event():
    # Crear directorio para archivos estáticos si no existe
    static_dir = pathlib.Path("static")
    static_dir.mkdir(exist_ok=True)
    
    # Crear un archivo index.html simple si no existe
    index_path = static_dir / "index.html"
    if not index_path.exists():
        with open(index_path, "w") as f:
            f.write("""
            <!DOCTYPE html>
            <html>
                <head>
                    <title>ProofMaster</title>
                    <meta charset="UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
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
                        .card {
                            background-color: #f5f5f5;
                            padding: 20px;
                            border-radius: 5px;
                            margin-bottom: 20px;
                            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                        }
                        .btn {
                            background-color: #2979ff;
                            color: white;
                            border: none;
                            padding: 10px 15px;
                            border-radius: 5px;
                            cursor: pointer;
                            text-decoration: none;
                            display: inline-block;
                            margin-top: 10px;
                        }
                        .btn:hover {
                            background-color: #1c54b2;
                        }
                    </style>
                </head>
                <body>
                    <h1>ProofMaster</h1>
                    <div class="card">
                        <h2>Bienvenido a ProofMaster</h2>
                        <p>Esta es una aplicación de corrección ortográfica que te ayuda a mejorar tus textos.</p>
                        <p>Actualmente estás viendo la versión de respaldo. Para acceder a la aplicación completa, necesitas desplegar el frontend.</p>
                        <a href="/docs" class="btn">Ver documentación de la API</a>
                    </div>
                    <div class="card">
                        <h2>API Endpoints</h2>
                        <p><strong>POST /spellcheck</strong>: Analiza un texto y devuelve sugerencias de corrección.</p>
                        <p>Ejemplo de uso:</p>
                        <pre>curl -X POST "https://proofmaster.onrender.com/spellcheck" \
-H "Content-Type: application/json" \
-d '{"text":"I will arrive at the office AM tomorrow"}'</pre>
                    </div>
                </body>
            </html>
            """)

# Montar archivos estáticos
app.mount("/static", StaticFiles(directory="static"), name="static")

# Ruta raíz para servir el frontend o una página de bienvenida
@app.get("/", response_class=HTMLResponse)
async def read_root():
    # Servir el archivo index.html del frontend
    index_path = pathlib.Path("static/index.html")
    if index_path.exists():
        return FileResponse(index_path)
    
    # Si no existe, mostrar una página de bienvenida HTML
    html_content = """
    <!DOCTYPE html>
    <html>
        <head>
            <title>ProofMaster</title>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
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
                .card {
                    background-color: #f5f5f5;
                    padding: 20px;
                    border-radius: 5px;
                    margin-bottom: 20px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }
                .btn {
                    background-color: #2979ff;
                    color: white;
                    border: none;
                    padding: 10px 15px;
                    border-radius: 5px;
                    cursor: pointer;
                    text-decoration: none;
                    display: inline-block;
                    margin-top: 10px;
                }
                .btn:hover {
                    background-color: #1c54b2;
                }
            </style>
        </head>
        <body>
            <h1>ProofMaster API</h1>
            <div class="card">
                <h2>Bienvenido a la API de ProofMaster para corrección ortográfica.</h2>
                <p>Esta es la API del backend. La aplicación frontend no se ha encontrado.</p>
                <a href="/docs" class="btn">Ver Documentación</a>
            </div>
            <div class="card">
                <h2>Endpoints disponibles:</h2>
                <p><strong>GET /</strong> - Esta página de bienvenida</p>
                <p><strong>GET /api</strong> - Documentación de la API</p>
                <p><strong>POST /spellcheck</strong> - Endpoint para revisar ortografía</p>
                <p>Ejemplo de uso:</p>
                <pre>curl -X POST "https://proofmaster.onrender.com/spellcheck" \
-H "Content-Type: application/json" \
-d '{"text": "Este es un texto con herrores ortograficos"}'</pre>
            </div>
        </body>
    </html>
    """
    return HTMLResponse(content=html_content)

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
