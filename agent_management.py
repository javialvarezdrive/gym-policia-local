import streamlit as st
import pandas as pd
from db_utils import get_supabase_client
from auth_utils import get_current_user

def show_agent_management():
    st.title("Gestión de Agentes")
    
    tabs = st.tabs(["Lista de Agentes", "Registrar Nuevo Agente"])
    
    with tabs[0]:
        show_agents_list()
    
    with tabs[1]:
        show_agent_registration_form()

def show_agents_list():
    st.header("Lista de Agentes")
    
    supabase = get_supabase_client()
    
    # Obtener todos los agentes
    response = supabase.table('agentes').select('*').execute()
    agents = response.data if response.data else []
    
    if not agents:
        st.info("No hay agentes registrados en el sistema")
        return
    
    # Convertir a DataFrame
    df = pd.DataFrame(agents)
    
    # Guardar una copia del DataFrame original
    if 'original_agents_df' not in st.session_state:
        st.session_state.original_agents_df = df.copy()
    
    # Crear un filtro de búsqueda
    search_query = st.text_input("Buscar agente (NIP, Nombre o Apellidos)", key="agents_search")
    
    filtered_df = df
    if search_query:
        search_query = search_query.lower()
        filtered_df = df[
            df['nip'].astype(str).str.lower().str.contains(search_query) |
            df['nombre'].astype(str).str.lower().str.contains(search_query) |
            df['apellidos'].astype(str).str.lower().str.contains(search_query)
        ]
    
    # Seleccionar columnas para edición
    editable_df = filtered_df[['id', 'nombre', 'apellidos', 'nip', 'seccion', 'grupo', 'es_monitor']].copy()
    
    # Crear editor de datos interactivo
    edited_df = st.data_editor(
        editable_df,
        column_config={
            "id": st.column_config.Column(
                "ID",
                disabled=True,
                width="small",
            ),
            "nombre": st.column_config.TextColumn(
                "Nombre",
                width="medium",
                required=True,
            ),
            "apellidos": st.column_config.TextColumn(
                "Apellidos",
                width="medium",
                required=True,
            ),
            "nip": st.column_config.TextColumn(
                "NIP",
                width="small",
                required=True,
            ),
            "seccion": st.column_config.TextColumn(
                "Sección",
                width="small",
                required=True,
            ),
            "grupo": st.column_config.TextColumn(
                "Grupo",
                width="small",
                required=True,
            ),
            "es_monitor": st.column_config.CheckboxColumn(
                "Es Monitor",
                width="small",
                default=False,
            ),
        },
        disabled=False,
        hide_index=True,
        key="agent_editor",
        use_container_width=True,
    )
    
    # Botón para guardar cambios
    if st.button("Guardar Cambios"):
        changes_made = False
        error_occurred = False
        
        # Validar que no haya campos requeridos vacíos
        for index, row in edited_df.iterrows():
            for col in ['nombre', 'apellidos', 'nip', 'seccion', 'grupo']:
                if pd.isna(row[col]) or str(row[col]).strip() == '':
                    st.error(f"Error: El campo '{col}' no puede estar vacío en la fila {index + 1}")
                    error_occurred = True
        
        if error_occurred:
            return
        
        # Iterar sobre cada fila editada
        for index, row in edited_df.iterrows():
            agent_id = row['id']
            
            # Encontrar la fila original correspondiente
            original_row = st.session_state.original_agents_df[st.session_state.original_agents_df['id'] == agent_id]
            
            if not original_row.empty:
                # Verificar cambios en cada columna
                changes = {}
                original_row = original_row.iloc[0]
                
                # Lista de columnas a verificar (excluyendo 'id')
                columns_to_check = ['nombre', 'apellidos', 'nip', 'seccion', 'grupo', 'es_monitor']
                
                for col in columns_to_check:
                    # Asegurarse de que los valores sean comparables
                    edited_val = row[col]
                    original_val = original_row[col]
                    
                    # Para valores booleanos, asegurarse de que estén en el mismo formato
                    if col == 'es_monitor':
                        edited_val = bool(edited_val)
                        original_val = bool(original_val)
                    
                    # Comparar y agregar a cambios si son diferentes
                    if edited_val != original_val:
                        changes[col] = edited_val
                
                # Verificar unicidad de NIP si cambió
                if 'nip' in changes:
                    nip_check = supabase.table('agentes').select('id').eq('nip', changes['nip']).neq('id', agent_id).execute()
                    if nip_check.data and len(nip_check.data) > 0:
                        st.error(f"Error: El NIP '{changes['nip']}' ya está siendo utilizado por otro agente")
                        error_occurred = True
                        continue
                
                # Aplicar cambios si los hay
                if changes and not error_occurred:
                    try:
                        update_response = supabase.table('agentes').update(changes).eq('id', agent_id).execute()
                        
                        if update_response.data:
                            changes_made = True
                        else:
                            st.error(f"Error al actualizar el agente con ID {agent_id}")
                            error_occurred = True
                    except Exception as e:
                        st.error(f"Error al actualizar el agente: {str(e)}")
                        error_occurred = True
        
        if changes_made and not error_occurred:
            st.success("Cambios guardados correctamente")
            # Actualizar el DataFrame original
            response = supabase.table('agentes').select('*').execute()
            if response.data:
                st.session_state.original_agents_df = pd.DataFrame(response.data)
            st.rerun()
        elif not error_occurred and not changes_made:
            st.info("No se detectaron cambios")

def show_agent_registration_form():
    # Mantén la función original de registro de agentes
    st.header("Registrar Nuevo Agente")
    
    # Resto del código de registro de nuevos agentes...
