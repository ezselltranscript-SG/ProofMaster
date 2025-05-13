import os
import re
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
from supabase import create_client, Client
from dotenv import load_dotenv
import Levenshtein

# Cargar variables desde .env
load_dotenv()

# Configura tus claves
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise EnvironmentError("Faltan SUPABASE_URL o SUPABASE_KEY en .env")

# Conectar con Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Crear instancia de FastAPI
app = FastAPI()

# Modelos
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
            similarity = Levenshtein.ratio(word.lower(), original.lower())

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
