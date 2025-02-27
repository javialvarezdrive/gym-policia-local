import streamlit as st
import pandas as pd
from db_utils import get_supabase_client
from auth_utils import get_current_user

def show_agent_management():
    st.title("Gestión de Agentes")
    
    # Tabs para organizar la interfaz
    tabs = st.tabs(["Registro de Agentes", "Lista de Agentes", "Editar Agentes"])
    
    # Tab de Registro de Agentes
    with tabs[0]:
        show_agent_registration()
    
    # Tab de Lista de Agentes
    with tabs[1]:
        show_agent_list()
    
    # Tab de Edición de Agentes
    with tabs[2]:
        show_agent_edit()

def show_agent_registration():
    st.header("Registro de Nuevo Agente")
    
    # Verificar si debemos limpiar el formulario (después de un registro exitoso)
    if 'clear_form' in st.session_state and st.session_state.clear_form:
        # Limpiar las variables del formulario antes de renderizar los widgets
        if 'register_nombre' in st.session_state:
            del st.session_state.register_nombre
        if 'register_apellidos' in st.session_state:
            del st.session_state.register_apellidos
        if 'register_nip' in st.session_state:
            del st.session_state.register_nip
        if 'register_email' in st.session_state:
            del st.session_state.register_email
        if 'register_telefono' in st.session_state:
            del st.session_state.register_telefono
        if 'register_es_monitor' in st.session_state:
            del st.session_state.register_es_monitor
        
        # Resetear el flag
        st.session_state.clear_form = False
    
    with st.form("register_agent_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            nombre = st.text_input("Nombre", key="register_nombre")
            nip = st.text_input("NIP (6 cifras)", key="register_nip")
            seccion = st.selectbox("Sección", 
                                  options=["Motorista", "Patrullas", "GOA", "Atestados"],
                                  key="register_seccion")
            email = st.text_input("Email", key="register_email")
        
        with col2:
            apellidos = st.text_input("Apellidos", key="register_apellidos")
            grupo = st.selectbox("Grupo", 
                                options=["G-1", "G-2", "G-3"],
                                key="register_grupo")
            telefono = st.text_input("Teléfono", key="register_telefono")
            es_monitor = st.checkbox("Es Monitor", key="register_es_monitor")
        
        submit = st.form_submit_button("Registrar Agente")
        
        if submit:
            if not nombre or not apellidos or not nip:
                st.error("Nombre, Apellidos y NIP son campos obligatorios")
            elif len(nip) != 6 or not nip.isdigit():
                st.error("El NIP debe ser un número de 6 cifras")
            else:
                supabase = get_supabase_client()
                
                # Verificar si el NIP ya existe
                response = supabase.table('agentes').select('*').eq('nip', nip).execute()
                
                if response.data and len(response.data) > 0:
                    st.error(f"Ya existe un agente con el NIP {nip}")
                else:
                    # Insertar nuevo agente
                    data = {
                        'nombre': nombre,
                        'apellidos': apellidos,
                        'nip': nip,
                        'seccion': seccion,
                        'grupo': grupo,
                        'email': email if email else None,
                        'telefono': telefono if telefono else None,
                        'es_monitor': es_monitor
                    }
                    
                    response = supabase.table('agentes').insert(data).execute()
                    
                    if response.data:
                        st.success(f"Agente {nombre} {apellidos} registrado correctamente")
                        # En lugar de modificar directamente, establecemos un flag para limpiar en la próxima ejecución
                        st.session_state.clear_form = True
                        st.rerun()
                    else:
                        st.error("Error al registrar el agente")

def show_agent_list():
    st.header("Lista de Agentes")
    
    # Filtros
    col1, col2, col3 = st.columns(3)
    with col1:
        filter_seccion = st.multiselect(
            "Filtrar por Sección",
            options=["Motorista", "Patrullas", "GOA", "Atestados"],
            default=[]
        )
    with col2:
        filter_grupo = st.multiselect(
            "Filtrar por Grupo",
            options=["G-1", "G-2", "G-3"],
            default=[]
        )
    with col3:
        filter_monitor = st.selectbox(
            "Mostrar",
            options=["Todos", "Solo Monitores", "Solo Agentes"],
            index=0
        )
    
    # Obtener la lista de agentes
    supabase = get_supabase_client()
    query = supabase.table('agentes').select('*')
    
    # Aplicar filtros
    if filter_seccion:
        query = query.in_('seccion', filter_seccion)
    if filter_grupo:
        query = query.in_('grupo', filter_grupo)
    if filter_monitor == "Solo Monitores":
        query = query.eq('es_monitor', True)
    elif filter_monitor == "Solo Agentes":
        query = query.eq('es_monitor', False)
    
    response = query.execute()
    
    if response.data:
        # Convertir a DataFrame para mostrar
        df = pd.DataFrame(response.data)
        
        # Reorganizar y renombrar columnas para mejor visualización
        columns_to_display = ['nombre', 'apellidos', 'nip', 'seccion', 'grupo', 'email', 'telefono', 'es_monitor']
        df_display = df[columns_to_display].copy()
        
        # Renombrar columnas para mostrar
        df_display.columns = ['Nombre', 'Apellidos', 'NIP', 'Sección', 'Grupo', 'Email', 'Teléfono', 'Es Monitor']
        
        # Mostrar número total de agentes filtrados
        st.write(f"Total de agentes: {len(df_display)}")
        
        # Mostrar DataFrame
        st.dataframe(df_display, use_container_width=True)
        
        # Opción para descargar como CSV
        csv = df_display.to_csv(index=False).encode('utf-8')
        st.download_button(
            "Descargar como CSV",
            csv,
            "agentes.csv",
            "text/csv",
            key="download-csv"
        )
    else:
        st.info("No se encontraron agentes con los filtros seleccionados")

def show_agent_edit():
    st.header("Editar Agente")
    
    # Buscar agente por NIP
    nip = st.text_input("Introducir NIP del Agente a Editar")
    
    if nip:
        supabase = get_supabase_client()
        response = supabase.table('agentes').select('*').eq('nip', nip).execute()
        
        if response.data and len(response.data) > 0:
            agent = response.data[0]
            
            st.success(f"Agente encontrado: {agent['nombre']} {agent['apellidos']}")
            
            with st.form("edit_agent_form"):
                col1, col2 = st.columns(2)
                
                with col1:
                    nombre = st.text_input("Nombre", value=agent['nombre'], key="edit_nombre")
                    seccion = st.selectbox("Sección", 
                                          options=["Motorista", "Patrullas", "GOA", "Atestados"],
                                          index=["Motorista", "Patrullas", "GOA", "Atestados"].index(agent['seccion']),
                                          key="edit_seccion")
                    email = st.text_input("Email", value=agent['email'] if agent['email'] else "", key="edit_email")
                
                with col2:
                    apellidos = st.text_input("Apellidos", value=agent['apellidos'], key="edit_apellidos")
                    grupo = st.selectbox("Grupo", 
                                        options=["G-1", "G-2", "G-3"],
                                        index=["G-1", "G-2", "G-3"].index(agent['grupo']),
                                        key="edit_grupo")
                    telefono = st.text_input("Teléfono", value=agent['telefono'] if agent['telefono'] else "", key="edit_telefono")
                    es_monitor = st.checkbox("Es Monitor", value=agent['es_monitor'], key="edit_es_monitor")
                
                submit = st.form_submit_button("Actualizar Agente")
                
                if submit:
                    if not nombre or not apellidos:
                        st.error("Nombre y Apellidos son campos obligatorios")
                    else:
                        # Actualizar agente
                        data = {
                            'nombre': nombre,
                            'apellidos': apellidos,
                            'seccion': seccion,
                            'grupo': grupo,
                            'email': email if email else None,
                            'telefono': telefono if telefono else None,
                            'es_monitor': es_monitor
                        }
                        
                        response = supabase.table('agentes').update(data).eq('id', agent['id']).execute()
                        
                        if response.data:
                            st.success(f"Agente {nombre} {apellidos} actualizado correctamente")
                        else:
                            st.error("Error al actualizar el agente")
        else:
            st.error(f"No se encontró ningún agente con el NIP {nip}")
