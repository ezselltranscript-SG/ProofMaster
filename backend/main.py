import os
import re
import nltk
from fuzzywuzzy import fuzz
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Dict, Set
from supabase import create_client, Client
from dotenv import load_dotenv
import pathlib
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Descargar recursos de NLTK si no están disponibles
try:
    nltk.data.find('corpora/words')
except LookupError:
    logger.info("Descargando recursos de NLTK...")
    nltk.download('words')

# Cargar diccionario de palabras en inglés
try:
    from nltk.corpus import words
    ENGLISH_WORDS = set(words.words())
    logger.info(f"Diccionario de inglés cargado con {len(ENGLISH_WORDS)} palabras")
except Exception as e:
    logger.error(f"Error al cargar el diccionario de inglés: {str(e)}")
    ENGLISH_WORDS = set()
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

# Función mejorada de similitud usando FuzzyWuzzy
def get_similarity(s1, s2):
    """Calcula una ratio de similitud entre dos cadenas usando FuzzyWuzzy."""
    # Convertir a minúsculas para comparación insensible a mayúsculas/minúsculas
    s1, s2 = s1.lower(), s2.lower()
    
    # Si las cadenas son iguales, la similitud es 1.0
    if s1 == s2:
        return 1.0
    
    # Calcular diferentes tipos de ratios
    simple_ratio = fuzz.ratio(s1, s2) / 100.0
    partial_ratio = fuzz.partial_ratio(s1, s2) / 100.0
    token_sort_ratio = fuzz.token_sort_ratio(s1, s2) / 100.0
    token_set_ratio = fuzz.token_set_ratio(s1, s2) / 100.0
    
    # Para palabras cortas, dar más peso al ratio simple
    if len(s1) <= 4 or len(s2) <= 4:
        return max(simple_ratio * 1.1, partial_ratio, token_sort_ratio, token_set_ratio)
    
    # Para palabras más largas, usar el máximo de todos los ratios
    return max(simple_ratio, partial_ratio, token_sort_ratio, token_set_ratio)

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
    correction_type: str = "normal"  # Puede ser "normal" o "town"

class SpellCheckResponse(BaseModel):
    suggestions: List[Suggestion]
    corrected_text: str
    full_corrected_code: str  # Campo añadido para devolver el código corregido
    town_matches: List[Suggestion] = []  # Campo para sugerencias de pueblos/ciudades

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
        # Conectar y obtener datos de la tabla spellcheck (correcciones personalizadas)
        response = supabase.table("spellcheck").select("original, suggestion").execute()
        custom_replacements = {item["original"].lower(): item["suggestion"] for item in response.data}
        logger.info(f"Cargadas {len(custom_replacements)} correcciones personalizadas de Supabase")
        
        # Cargar nombres de pueblos/ciudades desde la tabla towns
        towns_response = supabase.table("towns").select("name").execute()
        town_names = [item["name"] for item in towns_response.data]
        logger.info(f"Cargados {len(town_names)} nombres de pueblos/ciudades desde Supabase")
    except Exception as e:
        logger.error(f"Error al conectar con Supabase: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al conectar con Supabase: {str(e)}")
    
    # Lista de palabras de jerga o abreviaturas que no deben corregirse
    slang_words = ["btw", "asap", "lol", "omg", "idk", "gonna", "wanna", "gotta"]
    
    # Diccionario de correcciones comunes para errores frecuentes
    # Solo lo usaremos como respaldo si FuzzyWuzzy no encuentra una buena corrección
    common_errors = {
        "wasnt": "wasn't",
        "becuase": "because",
        "alot": "a lot",
        "problm": "problem",
        "im": "I'm",
        "speling": "spelling",
        "grammer": "grammar",
        "amazng": "amazing",
        "definately": "definitely",
        "idntify": "identify",
        "misstakes": "mistakes",
        "projct": "project",
        "documntation": "documentation",
        "erors": "errors",
        "versiun": "version",
        "thnak": "thank",
        "usefull": "useful",
    }

    # Extraer palabras y signos de puntuación del texto
    words = re.findall(r"\b[A-Za-z]+(?:'[A-Za-z]+)?\b|[^\s\w]", text)
    logger.info(f"Texto a analizar tiene {len(words)} palabras/tokens")
    corrected_words = []
    full_corrected_code = []  # Lista para almacenar las palabras corregidas y el código

    for word in words:
        original_word = word  # Guardar la palabra original para mostrarla en las sugerencias
        
        # Si no es una palabra alfabética (signos de puntuación, números, etc.)
        if not word.isalpha():
            corrected_words.append(word)
            full_corrected_code.append(word)
            continue
        
        # Convertir a minúsculas para las comparaciones
        word_lower = word.lower()
            
        # Verificar si la palabra está exactamente en la lista de towns (no necesita corrección)
        if word in town_names:
            corrected_words.append(word)
            full_corrected_code.append(word + " (town/city, exact match)")
            continue
            
        # Verificar correcciones personalizadas de Supabase (prioridad máxima)
        if word_lower in custom_replacements:
            suggestion_text = custom_replacements[word_lower]
            
            corrected_words.append(suggestion_text)
            suggestions.append({
                "original": original_word,
                "suggestion": suggestion_text,
                "similarity": 1.0
            })
            full_corrected_code.append(f"{original_word} -> {suggestion_text} (custom)")
            continue
            
        # Verificar si la palabra está en el diccionario (correcta)
        if word_lower in ENGLISH_WORDS and len(word) > 1:
            corrected_words.append(word)
            full_corrected_code.append(word)
            continue
        
        # No corregir palabras de jerga o abreviaturas comunes
        if word_lower in slang_words:
            corrected_words.append(word)
            full_corrected_code.append(word)
            continue
        
        # Verificar si es un error común conocido
        if word_lower in common_errors:
            suggestion_text = common_errors[word_lower]
            
            # Preservar capitalización original
            if word.istitle() and not suggestion_text.startswith("I"):
                suggestion_text = suggestion_text.title()
            elif word.isupper():
                suggestion_text = suggestion_text.upper()
                
            corrected_words.append(suggestion_text)
            suggestions.append({
                "original": original_word,
                "suggestion": suggestion_text,
                "similarity": 0.95  # Alta confianza para errores comunes conocidos
            })
            full_corrected_code.append(f"{original_word} -> {suggestion_text}")
            continue
            
        # Verificar si puede ser un nombre de pueblo/ciudad (solo si no es una coincidencia exacta)
        if len(word) >= 3 and word[0].isupper():  # Los nombres de lugares suelen empezar con mayúscula
            best_town_match = None
            best_town_score = 0
            
            # Buscar entre los nombres de pueblos/ciudades
            for town in town_names:
                # Evitar comparar con la misma palabra (ya manejado arriba)
                if word == town:
                    continue
                    
                # Usar la función get_similarity mejorada
                score = get_similarity(word, town) * 100  # Convertir a escala 0-100
                
                # Usar un umbral más bajo para nombres de lugares (pueden ser menos comunes)
                if score > 75 and score > best_town_score:
                    best_town_score = score
                    best_town_match = town
            
            # Si encontramos una buena coincidencia con un nombre de pueblo/ciudad
            if best_town_match:
                similarity = round(best_town_score / 100.0, 2)
                corrected_words.append(best_town_match)
                suggestions.append({
                    "original": original_word,
                    "suggestion": best_town_match,
                    "similarity": similarity,
                    "correction_type": "town"
                })
                full_corrected_code.append(f"{original_word} -> {best_town_match} (town/city, {similarity})")
                continue
            
        # Usar FuzzyWuzzy para palabras que no son muy cortas
        if len(word) >= 3:
            # Usar FuzzyWuzzy para encontrar la mejor corrección
            best_match = None
            best_score = 0
            
            # Ampliar la búsqueda para incluir más candidatos potenciales
            first_letter = word[0].lower()
            potential_matches = []
            
            # Incluir palabras que empiezan con la misma letra
            for w in ENGLISH_WORDS:
                if w[0].lower() == first_letter and abs(len(w) - len(word)) <= 3:
                    potential_matches.append(w)
                # Para palabras cortas, ser más flexible
                elif len(word) <= 4 and abs(len(w) - len(word)) <= 1:
                    potential_matches.append(w)
            
            # Limitar a 300 candidatos para mejorar la cobertura sin sacrificar rendimiento
            potential_matches = potential_matches[:300]
            
            for dict_word in potential_matches:
                # Usar la función get_similarity mejorada
                score = get_similarity(word_lower, dict_word.lower()) * 100  # Convertir a escala 0-100
                
                # Umbral adaptativo basado en la longitud de la palabra
                threshold = 80 if len(word) <= 4 else 85
                
                if score > threshold and score > best_score:
                    best_score = score
                    best_match = dict_word
            
            # Si encontramos una buena corrección con similitud > 85%
            similarity = round(best_score / 100.0, 2)
            if best_match and best_match.lower() != word_lower and similarity >= 0.85:
                # Preservar capitalización original
                if word.istitle():
                    best_match = best_match.title()
                elif word.isupper():
                    best_match = best_match.upper()
                    
                corrected_words.append(best_match)
                suggestions.append({
                    "original": original_word,
                    "suggestion": best_match,
                    "similarity": similarity
                })
                full_corrected_code.append(f"{original_word} -> {best_match}")
                continue
            # Si encontramos una sugerencia pero con similitud < 85%, solo sugerirla pero no aplicarla
            elif best_match and best_match.lower() != word_lower:
                suggestions.append({
                    "original": original_word,
                    "suggestion": best_match,
                    "similarity": similarity
                })
                corrected_words.append(word)  # Mantener la palabra original
                full_corrected_code.append(f"{original_word} -> {best_match} (no aplicado, similitud {similarity})")
                continue
        
        # Si llegamos aquí, mantener la palabra original
        corrected_words.append(word)
        full_corrected_code.append(word)

    corrected_text = " ".join(corrected_words)
    full_corrected_code = "\n".join(full_corrected_code)  # Formato de código corregido con las sugerencias

    # Filtrar sugerencias de pueblos/ciudades para la respuesta
    town_matches = [s for s in suggestions if "town/city" in full_corrected_code.split("\n")[suggestions.index(s)]]
    
    return {
        "suggestions": suggestions,
        "corrected_text": corrected_text,
        "full_corrected_code": full_corrected_code,
        "town_matches": town_matches
    }
