import streamlit as st
from auth_utils import login, logout, reset_password, is_authenticated, get_current_user
import agent_management
import activity_management
import reservation_management
import dashboard

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
    
    # Colocar el campo de email fuera del formulario para usarlo con ambos botones
    email = st.text_input("Email", key="login_email")
    
    # Formulario para el login
    with st.form("login_form"):
        password = st.text_input("Contraseña", type="password", key="login_password")
        submitted = st.form_submit_button("Iniciar Sesión")
        
        if submitted:
            if not email or not password:
                st.error("Por favor, introduce email y contraseña")
            else:
                success, user_data = login(email, password)
                
                if success:
                    st.session_state.user = user_data
                    st.rerun()
                else:
                    st.error(user_data.get("error", "Error de autenticación"))
    
    # Botón de recuperar contraseña fuera del formulario
    if st.button("Recuperar Contraseña"):
        if email:
            success, message = reset_password(email)
            if success:
                st.success(message)
            else:
                st.error(message)
        else:
            st.error("Por favor, introduce tu email para recuperar la contraseña")

# Función para mostrar la página principal después del login
def show_main_page():
    user = get_current_user()
    
    # Sidebar con navegación
    with st.sidebar:
        st.title("Gimnasio Policía Local")
        
        st.write(f"Usuario: {user['monitor_data']['nombre']} {user['monitor_data']['apellidos']}")
        
        st.divider()
        
        # Menú de navegación
        selected_page = st.radio(
            "Navegación",
            options=["Inicio", "Gestión de Agentes", "Gestión de Actividades", 
                    "Reservas del Gimnasio", "Dashboard"],
            index=0
        )
        
        st.divider()
        
        # Botón de logout
        if st.button("Cerrar Sesión"):
            logout()
            st.rerun()
    
    # Mostrar la página seleccionada
    if selected_page == "Inicio":
        st.title("Bienvenido al sistema de gestión del gimnasio")
        st.write("Selecciona una opción del menú lateral para comenzar.")
        
        # Tarjetas informativas
        col1, col2, col3 = st.columns(3)
        with col1:
            st.info("**Gestión de Agentes**: Registra y administra los agentes de la Policía Local.")
        with col2:
            st.info("**Gestión de Actividades**: Administra las actividades disponibles en el gimnasio.")
        with col3:
            st.info("**Reservas del Gimnasio**: Programa actividades en el calendario.")
            
        st.info("**Dashboard**: Visualiza estadísticas sobre la participación de los agentes en las actividades.")
            
    elif selected_page == "Gestión de Agentes":
        agent_management.show_agent_management()
        
    elif selected_page == "Gestión de Actividades":
        activity_management.show_activity_management()
        
    elif selected_page == "Reservas del Gimnasio":
        reservation_management.show_reservation_management()
        
    elif selected_page == "Dashboard":
        dashboard.show_dashboard()

# Función principal
def main():
    if is_authenticated():
        show_main_page()
    else:
        show_login_page()

if __name__ == "__main__":
    main()
