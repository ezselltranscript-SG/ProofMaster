import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Cargar variables desde .env
load_dotenv()

# Configurar claves de Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Inicializar el cliente de Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Correcciones personalizadas para añadir
custom_corrections = [
    # Palabras específicas solicitadas
    {"original": "am", "suggestion": "AM"},
    {"original": "pm", "suggestion": "PM"},
    {"original": "kinna", "suggestion": "kind of"},
    {"original": "bro", "suggestion": "brother"},
    
    # Algunas abreviaturas comunes
    {"original": "btw", "suggestion": "by the way"},
    {"original": "lol", "suggestion": "laugh out loud"},
    {"original": "idk", "suggestion": "I don't know"},
    {"original": "asap", "suggestion": "as soon as possible"},
    
    # Jerga de internet
    {"original": "gonna", "suggestion": "going to"},
    {"original": "wanna", "suggestion": "want to"},
    {"original": "gotta", "suggestion": "got to"},
    {"original": "lemme", "suggestion": "let me"},
]

# Función para insertar o actualizar correcciones
def upsert_corrections():
    try:
        print("Conectando a Supabase...")
        
        # Verificar si la tabla existe
        try:
            # Intentar hacer una consulta simple
            supabase.table("spellcheck").select("*").limit(1).execute()
            print("Tabla 'spellcheck' encontrada.")
        except Exception as e:
            print(f"Error al verificar la tabla: {str(e)}")
            print("Creando tabla 'spellcheck'...")
            # Aquí podrías añadir código para crear la tabla si no existe
            # Pero esto depende de cómo esté configurado Supabase
        
        # Insertar o actualizar correcciones
        for correction in custom_corrections:
            print(f"Procesando: {correction['original']} -> {correction['suggestion']}")
            
            # Verificar si la corrección ya existe
            response = supabase.table("spellcheck") \
                .select("*") \
                .eq("original", correction["original"]) \
                .execute()
                
            if len(response.data) > 0:
                print(f"  Actualizando corrección existente...")
                supabase.table("spellcheck") \
                    .update({"suggestion": correction["suggestion"]}) \
                    .eq("original", correction["original"]) \
                    .execute()
            else:
                print(f"  Insertando nueva corrección...")
                supabase.table("spellcheck") \
                    .insert(correction) \
                    .execute()
                    
        print("\nProceso completado con éxito!")
        
    except Exception as e:
        print(f"Error: {str(e)}")

# Ejecutar el script
if __name__ == "__main__":
    upsert_corrections()
