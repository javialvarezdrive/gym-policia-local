import streamlit as st
from db_utils import get_supabase_client

def login(email, password):
    """
    Intenta iniciar sesión con las credenciales proporcionadas.
    
    Args:
        email: Email del usuario
        password: Contraseña del usuario
        
    Returns:
        Tupla (éxito, datos del usuario o mensaje de error)
    """
    supabase = get_supabase_client()
    
    try:
        # Intentar iniciar sesión
        response = supabase.auth.sign_in_with_password({"email": email, "password": password})
        user = response.user
        
        if user:
            # Verificar si el usuario es un monitor
            monitor_data = supabase.table('agentes').select('*').eq('email', email).eq('es_monitor', True).execute()
            
            if monitor_data.data and len(monitor_data.data) > 0:
                return True, {
                    "id": user.id, 
                    "email": user.email,
                    "monitor_data": monitor_data.data[0]
                }
            else:
                return False, {"error": "El usuario no tiene permisos de monitor"}
        else:
            return False, {"error": "Error de autenticación"}
    except Exception as e:
        return False, {"error": str(e)}

def reset_password(email):
    """
    Envía un correo para restablecer la contraseña.
    
    Args:
        email: Email del usuario
        
    Returns:
        Tupla (éxito, mensaje)
    """
    supabase = get_supabase_client()
    
    try:
        supabase.auth.reset_password_email(email)
        return True, "Se ha enviado un correo para restablecer la contraseña"
    except Exception as e:
        return False, f"Error al enviar el correo: {str(e)}"

def logout():
    """Cierra la sesión del usuario actual"""
    supabase = get_supabase_client()
    supabase.auth.sign_out()
    
    # Limpiar el estado de sesión en Streamlit
    for key in list(st.session_state.keys()):
        del st.session_state[key]

def is_authenticated():
    """Verifica si el usuario está autenticado"""
    return 'user' in st.session_state and st.session_state.user is not None

def get_current_user():
    """Obtiene los datos del usuario actual"""
    if is_authenticated():
        return st.session_state.user
    return None

