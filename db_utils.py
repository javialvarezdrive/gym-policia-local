import os
from supabase import create_client
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

def get_supabase_client():
    """Obtener el cliente de Supabase"""
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        raise ValueError("SUPABASE_URL y SUPABASE_KEY deben estar configurados en el archivo .env")
    
    return create_client(supabase_url, supabase_key)

