import streamlit as st
from auth_utils import login, logout, reset_password, is_authenticated, get_current_user

# Configurar la página
st.set_page_config(
    page_title="Gimnasio Policía Local de Vigo",
    page_icon="💪",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Función para mostrar la página de login
def show_login_page():
    st.title("Acceso Gimnasio Policía Local de Vigo")
    
    with st.form("login_form"):
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Contraseña", type="password", key="login_password")
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            submitted = st.form_submit_button("Iniciar Sesión")
        
        with col2:
            st.write("")  # Espacio para alineación
            if st.button("Recuperar Contraseña"):
                if email:
                    success, message = reset_password(email)
                    if success:
                        st.success(message)
                    else:
                        st.error(message)
                else:
                    st.error("Por favor, introduce tu email para recuperar la contraseña")
        
        if submitted:
            if not email or not password:
                st.error("Por favor, introduce email y contraseña")
            else:
                success, user_data = login(email, password)
                
                if success:
                    st.session_state.user = user_data
                    st.experimental_rerun()
                else:
                    st.error(user_data.get("error", "Error de autenticación"))

# Función para mostrar la página principal después del login
def show_main_page():
    user = get_current_user()
    
    # Sidebar con navegación
    with st.sidebar:
        st.title("Gimnasio Policía Local")
        
        st.write(f"Usuario: {user['monitor_data']['nombre']} {user['monitor_data']['apellidos']}")
        
        st.divider()
        
        # Botón de logout
        if st.button("Cerrar Sesión"):
            logout()
            st.experimental_rerun()
    
    # Contenido principal
    st.title("Bienvenido al sistema de gestión del gimnasio")
    st.write("Esta es una versión inicial para comprobar la conexión a Supabase y el sistema de login.")
    
    # Mostrar información de la conexión
    st.subheader("Información de la conexión")
    st.json({
        "Usuario": f"{user['monitor_data']['nombre']} {user['monitor_data']['apellidos']}",
        "Email": user['email'],
        "NIP": user['monitor_data']['nip'],
        "Es monitor": user['monitor_data']['es_monitor']
    })

# Función principal
def main():
    if is_authenticated():
        show_main_page()
    else:
        show_login_page()

if __name__ == "__main__":
    main()

