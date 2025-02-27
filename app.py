import streamlit as st
from auth_utils import login, logout, reset_password, is_authenticated, get_current_user, is_admin

# Configuración inicial de la aplicación
st.set_page_config(
    page_title="Sistema de Gestión - Gimnasio Policía Local de Vigo",
    page_icon="🏋️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Funciones para mostrar diferentes secciones de la aplicación
def show_dashboard():
    st.title("Dashboard")
    st.write("Bienvenido al panel de control del sistema de gestión del gimnasio.")
    # Aquí puedes añadir estadísticas, gráficos, etc.
    st.info("Esta sección mostrará información general y estadísticas del gimnasio.")

def show_agent_management():
    st.title("Gestión de Agentes")
    st.write("En esta sección puedes gestionar los agentes de policía registrados.")
    # Implementación básica
    st.info("Aquí podrás añadir, editar o eliminar agentes.")

def show_reservation_management():
    st.title("Gestión de Reservas")
    st.write("Administra las reservas del gimnasio.")
    # Implementación básica
    st.info("Aquí podrás ver, crear y gestionar reservas para diferentes actividades.")

def show_activity_management():
    st.title("Gestión de Actividades")
    st.write("Configura las actividades disponibles en el gimnasio.")
    # Implementación básica
    st.info("Aquí podrás crear y gestionar las diferentes actividades disponibles.")

def show_user_management():
    st.title("Gestión de Usuarios")
    st.write("Administra los usuarios del sistema.")
    # Implementación básica - solo para administradores
    st.info("Aquí podrás añadir, editar o eliminar usuarios del sistema.")

def show_analytics():
    st.title("Análisis de Datos")
    st.write("Visualiza estadísticas y análisis del uso del gimnasio.")
    # Implementación básica
    st.info("Aquí se mostrarán gráficos y estadísticas sobre el uso del gimnasio.")

def show_settings():
    st.title("Configuración")
    st.write("Configura los ajustes del sistema.")
    # Implementación básica
    st.info("Aquí podrás ajustar la configuración general del sistema.")

# Función para mostrar la página de login
def show_login_page():
    st.title("Acceso Gimnasio Policía Local de Vigo")
    
    with st.form("login_form"):
        email = st.text_input("Email")
        password = st.text_input("Contraseña", type="password")
        submit = st.form_submit_button("Iniciar Sesión")
    
    if submit:
        if email and password:
            success, user_data = login(email, password)
            if success:
                st.success(f"Bienvenido, {user_data['username']}!")
                st.rerun()
            else:
                st.error("Credenciales incorrectas")
        else:
            st.error("Por favor, complete todos los campos")
    
    # Opción para recuperar contraseña
    with st.expander("¿Olvidaste tu contraseña?"):
        with st.form("reset_password_form"):
            reset_email = st.text_input("Email", key="reset_email")
            new_password = st.text_input("Nueva Contraseña", type="password", key="new_password")
            confirm_password = st.text_input("Confirmar Nueva Contraseña", type="password", key="confirm_password")
            reset_submit = st.form_submit_button("Restablecer Contraseña")
        
        if reset_submit:
            if not reset_email:
                st.error("Por favor, ingresa tu email")
            elif not new_password or not confirm_password:
                st.error("Por favor, completa todos los campos de contraseña")
            elif new_password != confirm_password:
                st.error("Las contraseñas no coinciden")
            else:
                if reset_password(reset_email, new_password):
                    st.success("Contraseña restablecida correctamente. Puedes iniciar sesión ahora.")
                else:
                    st.error("No se pudo restablecer la contraseña. Verifica que el email sea correcto.")

# Función para mostrar el menú de navegación lateral
def show_navigation():
    user = get_current_user()
    
    with st.sidebar:
        st.title("Menú de Navegación")
        
        # Información del usuario
        if user:
            st.write(f"Bienvenido, **{user['username']}**")
            role_badge = "🛡️ Admin" if user.get('role') == 'admin' else "👤 Usuario"
            st.caption(role_badge)
            
            # Opciones de navegación
            st.header("Opciones")
            selected = st.radio(
                "Ir a:",
                options=[
                    "Dashboard", 
                    "Reservas", 
                    "Agentes",
                    "Actividades",
                    "Análisis",
                    "Usuarios", 
                    "Configuración"
                ],
                label_visibility="collapsed"
            )
            
            # Botón de logout
            if st.button("Cerrar Sesión"):
                logout()
        else:
            st.warning("No has iniciado sesión")
            selected = "Login"
    
    return selected

# Función principal de la aplicación
def main():
    # Verificar si el usuario está autenticado
    if not is_authenticated():
        show_login_page()
        return
    
    # Mostrar menú lateral y obtener la opción seleccionada
    selected_option = show_navigation()
    
    # Mostrar la sección correspondiente según la opción seleccionada
    if selected_option == "Dashboard":
        show_dashboard()
    
    elif selected_option == "Reservas":
        show_reservation_management()
    
    elif selected_option == "Agentes":
        show_agent_management()
    
    elif selected_option == "Actividades":
        show_activity_management()
    
    elif selected_option == "Análisis":
        show_analytics()
    
    elif selected_option == "Usuarios":
        # Solo los administradores pueden acceder a la gestión de usuarios
        if is_admin():
            show_user_management()
        else:
            st.error("No tienes permisos para acceder a esta sección")
    
    elif selected_option == "Configuración":
        show_settings()

# Ejecutar la aplicación
if __name__ == "__main__":
    main()
