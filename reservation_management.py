import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from db_utils import get_supabase_client
from auth_utils import get_current_user

def show_reservation_management():
    st.title("Reservas del Gimnasio")
    
    # Tabs para organizar la interfaz
    tabs = st.tabs(["Calendario de Reservas", "Nueva Reserva", "Gestionar Reservas"])
    
    # Tab de Calendario de Reservas
    with tabs[0]:
        show_reservation_calendar()
    
    # Tab de Nueva Reserva
    with tabs[1]:
        show_new_reservation()
    
    # Tab de Gestión de Reservas
    with tabs[2]:
        show_reservation_management_tab()

def show_reservation_calendar():
    st.header("Calendario de Reservas")
    
    supabase = get_supabase_client()
    
    # Filtros de fecha para el calendario
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Fecha Inicio", value=datetime.now().date())
    with col2:
        end_date = st.date_input("Fecha Fin", value=(datetime.now() + timedelta(days=30)).date())
    
    if start_date > end_date:
        st.error("La fecha de inicio debe ser anterior a la fecha de fin")
        return
    
    # Obtener las reservas directamente, sin usar RPC
    reservas = []
    
    # Consultar todas las reservas en el rango de fechas
    reservas_response = supabase.table('reservas').select('*').gte('fecha', start_date.isoformat()).lte('fecha', end_date.isoformat()).execute()
    
    if reservas_response.data:
        # Para cada reserva, obtener información adicional
        for reserva in reservas_response.data:
            # Obtener datos del turno
            turno_response = supabase.table('turnos').select('*').eq('id', reserva['turno_id']).execute()
            turno = turno_response.data[0] if turno_response.data else None
            
            # Obtener datos de la actividad
            actividad_response = supabase.table('actividades').select('*').eq('id', reserva['actividad_id']).execute()
            actividad = actividad_response.data[0] if actividad_response.data else None
            
            # Obtener datos del monitor
            monitor_response = supabase.table('agentes').select('*').eq('id', reserva['monitor_id']).execute()
            monitor = monitor_response.data[0] if monitor_response.data else None
            
            # Obtener participantes
            participantes_response = supabase.table('participaciones').select('*').eq('reserva_id', reserva['id']).execute()
            num_participantes = len(participantes_response.data) if participantes_response.data else 0
            
            # Añadir información completa a la lista de reservas
            reservas.append({
                'id': reserva['id'],
                'fecha': reserva['fecha'],
                'turno': turno['nombre'] if turno else 'Desconocido',
                'hora_inicio': turno['hora_inicio'] if turno else 'Desconocido',
                'hora_fin': turno['hora_fin'] if turno else 'Desconocido',
                'actividad': actividad['nombre'] if actividad else 'Desconocida',
                'monitor': f"{monitor['nombre']} {monitor['apellidos']}" if monitor else 'Desconocido',
                'num_participantes': num_participantes
            })
    
    if not reservas:
        st.info(f"No hay reservas programadas entre {start_date} y {end_date}")
        return
    
    # Crear DataFrame para mostrar las reservas
    df = pd.DataFrame(reservas)
    
    # Convertir fecha para mejor visualización
    df['fecha'] = pd.to_datetime(df['fecha']).dt.strftime('%d/%m/%Y')
    
    # Organizar las columnas para mejor visualización
    df_display = df[['fecha', 'turno', 'hora_inicio', 'hora_fin', 'actividad', 'monitor', 'num_participantes']]
    df_display.columns = ['Fecha', 'Turno', 'Hora Inicio', 'Hora Fin', 'Actividad', 'Monitor', 'Participantes']
    
    # Mostrar la tabla de reservas
    st.dataframe(df_display, use_container_width=True)

def show_new_reservation():
    st.header("Nueva Reserva")
    
    supabase = get_supabase_client()
    current_user = get_current_user()
    
    if not current_user:
        st.error("Debes iniciar sesión para crear reservas")
        return
    
    # Obtener datos necesarios para el formulario
    # Actividades
    actividades_response = supabase.table('actividades').select('*').execute()
    actividades = actividades_response.data if actividades_response.data else []
    
    if not actividades:
        st.error("No hay actividades registradas en el sistema")
        return
    
    # Turnos
    turnos_response = supabase.table('turnos').select('*').execute()
    turnos = turnos_response.data if turnos_response.data else []
    
    if not turnos:
        st.error("No hay turnos registrados en el sistema")
        return
    
    # Monitores (agentes que son monitores)
    monitores_response = supabase.table('agentes').select('*').eq('es_monitor', True).execute()
    monitores = monitores_response.data if monitores_response.data else []
    
    if not monitores:
        st.error("No hay monitores registrados en el sistema")
        return
    
    # Crear el formulario
    with st.form("new_reservation_form"):
        # Fecha
        fecha = st.date_input("Fecha", min_value=datetime.now().date())
        
        # Turno
        turno_options = {turno['id']: f"{turno['nombre']} ({turno['hora_inicio']} - {turno['hora_fin']})" for turno in turnos}
        turno_id = st.selectbox("Turno", options=list(turno_options.keys()), format_func=lambda x: turno_options[x])
        
        # Actividad
        actividad_options = {actividad['id']: actividad['nombre'] for actividad in actividades}
        actividad_id = st.selectbox("Actividad", options=list(actividad_options.keys()), format_func=lambda x: actividad_options[x])
        
        # Monitor
        monitor_options = {monitor['id']: f"{monitor['nombre']} {monitor['apellidos']} ({monitor['nip']})" for monitor in monitores}
        monitor_id = st.selectbox("Monitor", options=list(monitor_options.keys()), format_func=lambda x: monitor_options[x])
        
        # Botón para enviar el formulario
        submit = st.form_submit_button("Crear Reserva")
        
        if submit:
            # Verificar si ya existe una reserva para esa fecha y turno
            check_response = supabase.table('reservas').select('*').eq('fecha', fecha.isoformat()).eq('turno_id', turno_id).execute()
            
            if check_response.data and len(check_response.data) > 0:
                st.error(f"Ya existe una reserva para el {fecha} en ese turno")
            else:
                # Crear la reserva
                data = {
                    'fecha': fecha.isoformat(),
                    'turno_id': turno_id,
                    'actividad_id': actividad_id,
                    'monitor_id': monitor_id
                }
                
                response = supabase.table('reservas').insert(data).execute()
                
                if response.data:
                    st.success(f"Reserva creada correctamente para el {fecha}")
                    # Mostrar botón para gestionar participantes
                    reserva_id = response.data[0]['id']
                    st.session_state.created_reservation_id = reserva_id
                    st.info("Puedes añadir participantes en la pestaña 'Gestionar Reservas'")
                else:
                    st.error("Error al crear la reserva")

def show_reservation_management_tab():
    st.header("Gestionar Reservas")
    
    supabase = get_supabase_client()
    
    # Permitir buscar una reserva existente
    fecha_busqueda = st.date_input("Buscar reservas por fecha", value=datetime.now().date())
    
    # Obtener reservas para la fecha seleccionada
    reservas_response = supabase.table('reservas').select('*').eq('fecha', fecha_busqueda.isoformat()).execute()
    reservas = reservas_response.data if reservas_response.data else []
    
    if not reservas:
        st.info(f"No hay reservas para el {fecha_busqueda}")
        return
    
    # Preparar opciones para el selectbox
    reservas_info = []
    for reserva in reservas:
        # Obtener datos del turno
        turno_response = supabase.table('turnos').select('*').eq('id', reserva['turno_id']).execute()
        turno = turno_response.data[0] if turno_response.data else None
        
        # Obtener datos de la actividad
        actividad_response = supabase.table('actividades').select('*').eq('id', reserva['actividad_id']).execute()
        actividad = actividad_response.data[0] if actividad_response.data else None
        
        # Crear información resumida
        turno_info = f"{turno['nombre']} ({turno['hora_inicio']} - {turno['hora_fin']})" if turno else "Turno desconocido"
        actividad_info = actividad['nombre'] if actividad else "Actividad desconocida"
        
        reservas_info.append({
            'id': reserva['id'],
            'info': f"{fecha_busqueda} - {turno_info} - {actividad_info}"
        })
    
    # Permitir seleccionar una reserva
    reserva_options = {r['id']: r['info'] for r in reservas_info}
    selected_reserva_id = st.selectbox("Seleccionar reserva", options=list(reserva_options.keys()), format_func=lambda x: reserva_options[x])
    
    if selected_reserva_id:
        manage_reservation_participants(selected_reserva_id)

def manage_reservation_participants(reserva_id):
    supabase = get_supabase_client()
    
    # Obtener información de la reserva
    reserva_response = supabase.table('reservas').select('*').eq('id', reserva_id).execute()
    
    if not reserva_response.data:
        st.error("No se pudo obtener la información de la reserva")
        return
    
    reserva = reserva_response.data[0]
    
    # Obtener información adicional
    # Turno
    turno_response = supabase.table('turnos').select('*').eq('id', reserva['turno_id']).execute()
    turno = turno_response.data[0] if turno_response.data else None
    
    # Actividad
    actividad_response = supabase.table('actividades').select('*').eq('id', reserva['actividad_id']).execute()
    actividad = actividad_response.data[0] if actividad_response.data else None
    
    # Monitor
    monitor_response = supabase.table('agentes').select('*').eq('id', reserva['monitor_id']).execute()
    monitor = monitor_response.data[0] if monitor_response.data else None
    
    # Mostrar información de la reserva
    st.subheader("Detalles de la Reserva")
    col1, col2 = st.columns(2)
    
    with col1:
        st.write(f"**Fecha:** {reserva['fecha']}")
        st.write(f"**Turno:** {turno['nombre'] if turno else 'Desconocido'}")
        st.write(f"**Horario:** {turno['hora_inicio'] if turno else '?'} - {turno['hora_fin'] if turno else '?'}")
    
    with col2:
        st.write(f"**Actividad:** {actividad['nombre'] if actividad else 'Desconocida'}")
        st.write(f"**Monitor:** {monitor['nombre']} {monitor['apellidos'] if monitor else 'Desconocido'}")
    
    # Gestión de participantes
    st.subheader("Participantes")
    
    # Obtener participantes actuales
    participaciones_response = supabase.table('participaciones').select('*').eq('reserva_id', reserva_id).execute()
    participaciones = participaciones_response.data if participaciones_response.data else []
    
    # Mostrar lista de participantes actuales
    if participaciones:
        participantes_info = []
        
        for p in participaciones:
            # Obtener información del agente
            agente_response = supabase.table('agentes').select('*').eq('id', p['agente_id']).execute()
            if agente_response.data:
                agente = agente_response.data[0]
                participantes_info.append({
                    'id': p['id'],
                    'agente_id': agente['id'],
                    'nombre': agente['nombre'],
                    'apellidos': agente['apellidos'],
                    'nip': agente['nip'],
                    'seccion': agente['seccion'],
                    'grupo': agente['grupo']
                })
        
        if participantes_info:
            df = pd.DataFrame(participantes_info)
            df['Nombre Completo'] = df['nombre'] + ' ' + df['apellidos']
            df_display = df[['Nombre Completo', 'nip', 'seccion', 'grupo']]
            df_display.columns = ['Nombre', 'NIP', 'Sección', 'Grupo']
            
            st.write(f"Total de participantes: {len(df_display)}")
            st.dataframe(df_display, use_container_width=True)
            
            # Opción para eliminar participantes
            with st.expander("Eliminar participantes"):
                agente_options = {row['agente_id']: f"{row['nombre']} {row['apellidos']} ({row['nip']})" for _, row in df.iterrows()}
                agente_to_remove = st.selectbox("Seleccionar agente a eliminar", options=list(agente_options.keys()), format_func=lambda x: agente_options[x])
                
                if st.button("Eliminar Participante"):
                    # Buscar la participación correspondiente
                    participacion_to_remove = next((p for p in participaciones if p['agente_id'] == agente_to_remove), None)
                    
                    if participacion_to_remove:
                        delete_response = supabase.table('participaciones').delete().eq('id', participacion_to_remove['id']).execute()
                        
                        if delete_response:
                            st.success("Participante eliminado correctamente")
                            st.rerun()
                        else:
                            st.error("Error al eliminar el participante")
    else:
        st.info("No hay participantes registrados en esta reserva")
    
    # Formulario para añadir participantes
    st.subheader("Añadir Participantes")
    
    # Obtener todos los agentes que no son participantes actuales
    agentes_participantes_ids = [p['agente_id'] for p in participaciones]
    
    # Consultar todos los agentes
    agentes_response = supabase.table('agentes').select('*').execute()
    agentes = agentes_response.data if agentes_response.data else []
    
    # Filtrar agentes que no son participantes actuales
    agentes_disponibles = [a for a in agentes if a['id'] not in agentes_participantes_ids]
    
    if not agentes_disponibles:
        st.info("No hay más agentes disponibles para añadir")
    else:
        # Opciones de filtrado
        col1, col2 = st.columns(2)
        
        with col1:
            filter_seccion = st.multiselect(
                "Filtrar por Sección",
                options=list(set(a['seccion'] for a in agentes_disponibles)),
                default=[]
            )
        
        with col2:
            filter_grupo = st.multiselect(
                "Filtrar por Grupo",
                options=list(set(a['grupo'] for a in agentes_disponibles)),
                default=[]
            )
        
        # Aplicar filtros
        if filter_seccion:
            agentes_disponibles = [a for a in agentes_disponibles if a['seccion'] in filter_seccion]
        
        if filter_grupo:
            agentes_disponibles = [a for a in agentes_disponibles if a['grupo'] in filter_grupo]
        
        # Buscar por NIP o nombre
        search_query = st.text_input("Buscar por NIP o Nombre")
        
        if search_query:
            search_query = search_query.lower()
            agentes_disponibles = [
                a for a in agentes_disponibles 
                if search_query in a['nip'].lower() or 
                   search_query in a['nombre'].lower() or 
                   search_query in a['apellidos'].lower()
            ]
        
        # Seleccionar agente a añadir
        if agentes_disponibles:
            agente_options = {a['id']: f"{a['nombre']} {a['apellidos']} ({a['nip']}) - {a['seccion']} - {a['grupo']}" for a in agentes_disponibles}
            selected_agente_id = st.selectbox("Seleccionar agente", options=list(agente_options.keys()), format_func=lambda x: agente_options[x])
            
            if st.button("Añadir Participante"):
                # Crear nueva participación
                data = {
                    'reserva_id': reserva_id,
                    'agente_id': selected_agente_id
                }
                
                insert_response = supabase.table('participaciones').insert(data).execute()
                
                if insert_response.data:
                    st.success("Participante añadido correctamente")
                    st.rerun()
                else:
                    st.error("Error al añadir el participante")
        else:
            st.info("No hay agentes disponibles con los filtros seleccionados")
