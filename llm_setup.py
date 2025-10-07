from dotenv import load_dotenv
import os
import google.generativeai as genai
from langfuse import Langfuse

load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=api_key)

# --- INICIALIZACIÓN DE LANGFUSE ---
LANGFUSE_PUBLIC_KEY = os.getenv("LANGFUSE_PUBLIC_KEY")
LANGFUSE_SECRET_KEY = os.getenv("LANGFUSE_SECRET_KEY")
LANGFUSE_HOST = os.getenv("LANGFUSE_HOST")

# --- BLOQUE DE DEPURACIÓN TEMPORAL (CON FLUSH) ---
print("---[DEBUGGING ENVIRONMENT VARIABLES]---", flush=True)
print(f"LANGFUSE_PUBLIC_KEY_READ: {LANGFUSE_PUBLIC_KEY}", flush=True)
print(f"LANGFUSE_SECRET_KEY_READ: {'Value is present' if LANGFUSE_SECRET_KEY else 'Value is MISSING'}", flush=True)
print(f"LANGFUSE_HOST_READ: {LANGFUSE_HOST}", flush=True)
print("---------------------------------------", flush=True)
# ------------------------------------

# Inicializa el cliente solo si las claves están presentes
langfuse_client = None
if LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY and LANGFUSE_HOST:
    langfuse_client = Langfuse(
        public_key=LANGFUSE_PUBLIC_KEY,
        secret_key=LANGFUSE_SECRET_KEY,
        host=LANGFUSE_HOST
    )
    print("Langfuse client initialized.", flush=True)