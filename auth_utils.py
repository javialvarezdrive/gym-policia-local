import streamlit as st
import jwt
from datetime import datetime, timedelta
from db_utils import get_supabase_client

# Clave secreta para firmar el token JWT
SECRET_KEY = "tu_clave_secreta_aqui_cambiala_en_produccion"
TOKEN_EXPIRY_DAYS = 7  # El token durará 7 días

def login(username, password):
    """Maneja el proceso de login y configura la sesión"""
    supabase = get_supabase_client()
    
    # Buscar el usuario en la base de datos
    response = supabase.table('usuarios').select('*').eq('username', username).execute()
    
    if response.data and len(response.data) > 0:
        user = response.data[0]
        
        # Verificar contraseña (en una aplicación real deberías usar hash)
        if user['password'] == password:
            # Crear token JWT
            expiry = datetime.utcnow() + timedelta(days=TOKEN_EXPIRY_DAYS)
            token = jwt.encode({
                'user_id': user['id'],
                'username': user['username'],
                'role': user['role'],
                'exp': expiry
            }, SECRET_KEY, algorithm="HS256")
            
            # Guardar token en cookie y en session_state
            st.session_state.user = {
                'id': user['id'],
                'username': user['username'],
                'role': user['role']
            }
            
            # Establecer cookie con el token
            st.experimental_set_query_params(token=token)
            
            return True
    
    return False

def reset_password(username, new_password):
    """Restablece la contraseña de un usuario"""
    supabase = get_supabase_client()
    
    # Verificar que el usuario existe
    response = supabase.table('usuarios').select('*').eq('username', username).execute()
    
    if response.data and len(response.data) > 0:
        user = response.data[0]
        
        # Actualizar la contraseña
        update_response = supabase.table('usuarios').update(
            {'password': new_password}
        ).eq('id', user['id']).execute()
        
        if update_response.data:
            return True
    
    return False

def logout():
    """Maneja el proceso de logout"""
    if 'user' in st.session_state:
        del st.session_state.user
    
    # Limpiar parámetros de consulta para eliminar el token
    st.experimental_set_query_params()
    st.rerun()

def get_current_user():
    """Obtiene el usuario actual desde la sesión o token"""
    # Primero intentar desde session_state
    if 'user' in st.session_state:
        return st.session_state.user
    
    # Si no está en session_state, intentar desde los query params
    query_params = st.experimental_get_query_params()
    if 'token' in query_params:
        token = query_params['token'][0]
        try:
            # Verificar y decodificar el token
            payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            
            # Si el token es válido, restaurar la sesión
            st.session_state.user = {
                'id': payload['user_id'],
                'username': payload['username'],
                'role': payload['role']
            }
            return st.session_state.user
        except jwt.ExpiredSignatureError:
            # Token expirado
            st.warning("Tu sesión ha expirado. Por favor inicia sesión nuevamente.")
            st.experimental_set_query_params()
        except jwt.InvalidTokenError:
            # Token inválido
            st.experimental_set_query_params()
    
    return None

def is_authenticated():
    """Verifica si el usuario ha iniciado sesión"""
    return get_current_user() is not None

def is_admin():
    """Verifica si el usuario actual es administrador"""
    user = get_current_user()
    return user and user.get('role') == 'admin'

def show_login_required():
    """Muestra un mensaje de inicio de sesión requerido"""
    st.error("Debes iniciar sesión para acceder a esta sección")
    st.stop()
