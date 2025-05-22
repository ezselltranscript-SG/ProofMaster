import requests
import json

# URL del endpoint
url = "http://127.0.0.1:8000/spellcheck"

# Texto de prueba
test_text = """Gooood morning! I woke up at 7 am and plan to work until 6 pm today.

My bro called me yesterday and kinna asked if I wanted to go to the movies. I told him I wasnt sure becuase I have alot of work to do. He said it's no problm, we can reschedule for next week.

Im trying to improve my speling and grammer with this amazng app. It's definately helping me idntify common misstakes in my writing.

Btw, I gotta finish this projct by Friday. The documntation is almost complete, but I still need to fix some erors in the code. Asap I finish this, I'll send you the final versiun.

Thnak you for creating such a usefull tool! It's kinna cool how it can detect both formal errors and slang like gonna and wanna."""

# Datos para enviar
payload = {"text": test_text}

# Realizar la solicitud POST
response = requests.post(url, json=payload)

# Verificar si la solicitud fue exitosa
if response.status_code == 200:
    # Imprimir la respuesta formateada
    result = response.json()
    print("\n=== SUGERENCIAS ===\n")
    for i, suggestion in enumerate(result["suggestions"], 1):
        print(f"{i}. '{suggestion['original']}' -> '{suggestion['suggestion']}' (similitud: {suggestion['similarity']})")
    
    print("\n=== TEXTO CORREGIDO ===\n")
    print(result["corrected_text"])
    
    print("\n=== CÓDIGO CORREGIDO ===\n")
    print(result["full_corrected_code"])
else:
    print(f"Error: {response.status_code}")
    print(response.text)
