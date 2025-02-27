import streamlit as st
import pandas as pd
from db_utils import get_supabase_client

def show_activity_management():
    st.title("Gestión de Actividades")
    
    # Tabs para organizar la interfaz
    tabs = st.tabs(["Lista de Actividades", "Nueva Actividad", "Editar Actividad"])
    
    # Tab de Lista de Actividades
    with tabs[0]:
        show_activity_list()
    
    # Tab de Nueva Actividad
    with tabs[1]:
        show_new_activity()
    
    # Tab de Editar Actividad
    with tabs[2]:
        show_edit_activity()

def show_activity_list():
    st.header("Lista de Actividades")
    
    # Obtener las actividades
    supabase = get_supabase_client()
    response = supabase.table('actividades').select('*').execute()
    
    if response.data:
        # Convertir a DataFrame para mostrar
        df = pd.DataFrame(response.data)
        
        # Reorganizar y renombrar columnas para mejor visualización
        columns_to_display = ['nombre', 'descripcion']
        df_display = df[columns_to_display].copy()
        
        # Renombrar columnas para mostrar
        df_display.columns = ['Nombre', 'Descripción']
        
        # Mostrar DataFrame
        st.dataframe(df_display, use_container_width=True)
    else:
        st.info("No hay actividades registradas")

def show_new_activity():
    st.header("Registrar Nueva Actividad")
    
    with st.form("new_activity_form"):
        nombre = st.text_input("Nombre de la Actividad")
        descripcion = st.text_area("Descripción")
        
        submit = st.form_submit_button("Registrar Actividad")
        
        if submit:
            if not nombre:
                st.error("El nombre de la actividad es obligatorio")
            else:
                supabase = get_supabase_client()
                
                # Verificar si ya existe una actividad con ese nombre
                response = supabase.table('actividades').select('*').eq('nombre', nombre).execute()
                
                if response.data and len(response.data) > 0:
                    st.error(f"Ya existe una actividad con el nombre {nombre}")
                else:
                    # Insertar nueva actividad
                    data = {
                        'nombre': nombre,
                        'descripcion': descripcion if descripcion else None
                    }
                    
                    response = supabase.table('actividades').insert(data).execute()
                    
                    if response.data:
                        st.success(f"Actividad {nombre} registrada correctamente")
                        # Limpiar el formulario
                        st.session_state['nombre'] = ""
                        st.session_state['descripcion'] = ""
                    else:
                        st.error("Error al registrar la actividad")

def show_edit_activity():
    st.header("Editar Actividad")
    
    # Obtener lista de actividades
    supabase = get_supabase_client()
    response = supabase.table('actividades').select('*').execute()
    
    if not response.data:
        st.info("No hay actividades disponibles para editar")
        return
    
    # Crear lista de opciones para el selector
    activity_options = [f"{a['nombre']}" for a in response.data]
    selected_activity = st.selectbox("Seleccionar Actividad a Editar", options=activity_options)
    
    # Encontrar la actividad seleccionada
    activity = next((a for a in response.data if a['nombre'] == selected_activity), None)
    
    if activity:
        with st.form("edit_activity_form"):
            nombre = st.text_input("Nombre de la Actividad", value=activity['nombre'])
            descripcion = st.text_area("Descripción", value=activity['descripcion'] if activity['descripcion'] else "")
            
            submit = st.form_submit_button("Actualizar Actividad")
            
            if submit:
                if not nombre:
                    st.error("El nombre de la actividad es obligatorio")
                else:
                    # Verificar si el nuevo nombre ya existe (si se cambió)
                    if nombre != activity['nombre']:
                        check_response = supabase.table('actividades').select('*').eq('nombre', nombre).execute()
                        if check_response.data and len(check_response.data) > 0:
                            st.error(f"Ya existe una actividad con el nombre {nombre}")
                            return
                    
                    # Actualizar actividad
                    data = {
                        'nombre': nombre,
                        'descripcion': descripcion if descripcion else None
                    }
                    
                    response = supabase.table('actividades').update(data).eq('id', activity['id']).execute()
                    
                    if response.data:
                        st.success(f"Actividad actualizada correctamente")
                    else:
                        st.error("Error al actualizar la actividad")
