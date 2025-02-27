import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import uuid
from db_utils import get_supabase_client
from auth_utils import get_current_user

def show_reservation_management():
    st.title("Reservas del Gimnasio")
    
    # Tabs para organizar la interfaz
    tabs = st.tabs(["Calendario de Reservas", "Nueva Reserva", "Gestionar Participantes"])
    
    # Tab de Calendario de Reservas
    with tabs[0]:
        show_reservation_calendar()
    
    # Tab de Nueva Reserva
    with tabs[1]:
        show_new_reservation()
    
    # Tab de Gestionar Participantes
    with tabs[2]:
        show_manage_participants()

def show_reservation_calendar():
    st.header("Calendario de Reservas")
    
    # Filtros de fecha
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Fecha Inicio", value=datetime.now().date())
    with col2:
        end_date = st.date_input("Fecha Fin", value=(datetime.now() + timedelta(days=30)).date())
    
    if start_date > end_date:
        st.error("La fecha de inicio debe ser anterior a la fecha de fin")
        return
    
    # Obtener reservas en el rango de fechas
    supabase = get_supabase_client()
    
    # Consulta de reservas con join a turnos, actividades y monitores
    reservas_query = f'''
    SELECT r.id, r.fecha, t.nombre as turno, a.nombre as actividad, 
           ag.nombre as monitor_nombre, ag.apellidos as monitor_apellidos,
           (SELECT COUNT(*) FROM participaciones p WHERE p.reserva_id = r.id) as num_participantes
    FROM reservas r
    JOIN turnos t ON r.turno_id = t.id
    JOIN actividades a ON r.actividad_id = a.id
    JOIN agentes ag ON r.monitor_id = ag.id
    WHERE r.fecha BETWEEN '{start_date}' AND '{end_date}'
    ORDER BY r.fecha, t.nombre
    '''
    
    reservas_response = supabase.rpc('ejecutar_consulta', {'query': reservas_query}).execute()
    
    # Si no hay función RPC configurada, puedes usar esta alternativa (menos eficiente)
    if not reservas_response.data:
        # Obtener reservas
        reservas_response = supabase.table('reservas').select('*').gte('fecha', str(start_date)).lte('fecha', str(end_date)).execute()
        
        if reservas_response.data:
            # Obtener datos adicionales de forma manual
            reservas_data = []
            for reserva in reservas_response.data:
                # Obtener turno
                turno_response = supabase.table('turnos').select('*').eq('id', reserva['turno_id']).execute()
                turno = turno_response.data[0] if turno_response.data else {'nombre': 'Desconocido'}
                
                # Obtener actividad
                actividad_response = supabase.table('actividades').select('*').eq('id', reserva['actividad_id']).execute()
                actividad = actividad_response.data[0] if actividad_response.data else {'nombre': 'Desconocida'}
                
                # Obtener monitor
                monitor_response = supabase.table('agentes').select('*').eq('id', reserva['monitor_id']).execute()
                monitor = monitor_response.data[0] if monitor_response.data else {'nombre': 'Desconocido', 'apellidos': ''}
                
                # Contar participantes
                participantes_response = supabase.table('participaciones').select('*').eq('reserva_id', reserva['id']).execute()
                num_participantes = len(participantes_response.data) if participantes_response.data else 0
                
                reservas_data.append({
                    'id': reserva['id'],
                    'fecha': reserva['fecha'],
                    'turno': turno['nombre'],
                    'actividad': actividad['nombre'],
                    'monitor_nombre': monitor['nombre'],
                    'monitor_apellidos': monitor['apellidos'],
                    'num_participantes': num_participantes
                })
            
            reservas_response.data = reservas_data
    
    if reservas_response.data:
        # Agrupar por fecha para visualización por día
        df = pd.DataFrame(reservas_response.data)
        
        # Formatear fecha para agrupar por día
        if 'fecha' in df.columns:
            df['fecha'] = pd.to_datetime(df['fecha']).dt.date
        
        # Mostrar reservas agrupadas por fecha
        for fecha, grupo in df.groupby('fecha'):
            st.subheader(f"📅 {fecha.strftime('%d/%m/%Y')}")
            
            # Preparar datos para mostrar
            tabla_dia = grupo[['turno', 'actividad', 'monitor_nombre', 'monitor_apellidos', 'num_participantes']].copy()
            tabla_dia.columns = ['Turno', 'Actividad', 'Nombre Monitor', 'Apellidos Monitor', 'Participantes']
            tabla_dia['Monitor'] = tabla_dia['Nombre Monitor'] + ' ' + tabla_dia['Apellidos Monitor']
            tabla_dia = tabla_dia[['Turno', 'Actividad', 'Monitor', 'Participantes']]
            
            st.dataframe(tabla_dia, use_container_width=True)
            st.divider()
    else:
        st.info("No hay reservas en el rango de fechas seleccionado")

def show_new_reservation():
    st.header("Nueva Reserva del Gimnasio")
    
    supabase = get_supabase_client()
    user = get_current_user()
    
    with st.form("new_reservation_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            fecha = st.date_input("Fecha", value=datetime.now().date())
            
            # Obtener turnos
            turnos_response = supabase.table('turnos').select('*').execute()
            turnos = turnos_response.data if turnos_response.data else []
            turnos_opciones = {t['id']: t['nombre'] for t in turnos}
            turno_id = st.selectbox("Turno", options=list(turnos_opciones.keys()), format_func=lambda x: turnos_opciones[x])
        
        with col2:
            # Obtener actividades
            actividades_response = supabase.table('actividades').select('*').execute()
            actividades = actividades_response.data if actividades_response.data else []
            actividades_opciones = {a['id']: a['nombre'] for a in actividades}
            actividad_id = st.selectbox("Actividad", options=list(actividades_opciones.keys()), format_func=lambda x: actividades_opciones[x])
            
            # Obtener monitores (todos los agentes que son monitores)
            monitores_response = supabase.table('agentes').select('*').eq('es_monitor', True).execute()
            monitores = monitores_response.data if monitores_response.data else []
            monitores_opciones = {m['id']: f"{m['nombre']} {m['apellidos']}" for m in monitores}
            
            # Por defecto, seleccionar al monitor actual
            monitor_id_default = next((m['id'] for m in monitores if m['email'] == user['email']), None)
            monitor_id = st.selectbox("Monitor", options=list(monitores_opciones.keys()), format_func=lambda x: monitores_opciones[x], index=list(monitores_opciones.keys()).index(monitor_id_default) if monitor_id_default in list(monitores_opciones.keys()) else 0)
        
        submit = st.form_submit_button("Realizar Reserva")
        
        if submit:
            # Comprobar disponibilidad
            disponibilidad_response = supabase.table('reservas').select('*').eq('fecha', str(fecha)).eq('turno_id', turno_id).execute()
            
            if disponibilidad_response.data and len(disponibilidad_response.data) > 0:
                st.error(f"Ya existe una reserva para la fecha {fecha} en ese turno")
            else:
                # Registrar la reserva
                data = {
                    'fecha': str(fecha),
                    'turno_id': turno_id,
                    'actividad_id': actividad_id,
                    'monitor_id': monitor_id
                }
                
                response = supabase.table('reservas').insert(data).execute()
                
                if response.data:
                    st.success(f"Reserva registrada correctamente para el {fecha}")
                else:
                    st.error("Error al registrar la reserva")

def show_manage_participants():
    st.header("Gestionar Participantes")
    
    supabase = get_supabase_client()
    
    # Step 1: Select a reservation
    # Obtener reservas futuras (desde hoy)
    reservas_query = f'''
    SELECT r.id, r.fecha, t.nombre as turno, a.nombre as actividad, 
           ag.nombre as monitor_nombre, ag.apellidos as monitor_apellidos
    FROM reservas r
    JOIN turnos t ON r.turno_id = t.id
    JOIN actividades a ON r.actividad_id = a.id
    JOIN agentes ag ON r.monitor_id = ag.id
    WHERE r.fecha >= '{datetime.now().date()}'
    ORDER BY r.fecha, t.nombre
    '''
    
    reservas_response = supabase.rpc('ejecutar_consulta', {'query': reservas_query}).execute()
    
    # Si no hay función RPC, alternativa manual
    if not reservas_response.data:
        reservas_response = supabase.table('reservas').select('*').gte('fecha', str(datetime.now().date())).execute()
        
        if reservas_response.data:
            reservas_data = []
            for reserva in reservas_response.data:
                # Obtener turno
                turno_response = supabase.table('turnos').select('*').eq('id', reserva['turno_id']).execute()
                turno = turno_response.data[0] if turno_response.data else {'nombre': 'Desconocido'}
                
                # Obtener actividad
                actividad_response = supabase.table('actividades').select('*').eq('id', reserva['actividad_id']).execute()
                actividad = actividad_response.data[0] if actividad_response.data else {'nombre': 'Desconocida'}
                
                # Obtener monitor
                monitor_response = supabase.table('agentes').select('*').eq('id', reserva['monitor_id']).execute()
                monitor = monitor_response.data[0] if monitor_response.data else {'nombre': 'Desconocido', 'apellidos': ''}
                
                reservas_data.append({
                    'id': reserva['id'],
                    'fecha': reserva['fecha'],
                    'turno': turno['nombre'],
                    'actividad': actividad['nombre'],
                    'monitor_nombre': monitor['nombre'],
                    'monitor_apellidos': monitor['apellidos'],
                })
            
            reservas_response.data = reservas_data
    
    if not reservas_response.data:
        st.info("No hay reservas disponibles para gestionar participantes")
        return
    
    # Crear opciones para el selector de reservas
    reservas_opciones = {r['id']: f"{r['fecha']} - {r['turno']} - {r['actividad']}" for r in reservas_response.data}
    reserva_id = st.selectbox("Seleccionar Reserva", options=list(reservas_opciones.keys()), format_func=lambda x: reservas_opciones[x])
    
    # Step 2: Mostrar participantes actuales
    st.subheader("Participantes Actuales")
    
    participantes_response = supabase.table('participaciones').select('*').eq('reserva_id', reserva_id).execute()
    
    if participantes_response.data:
        participantes_ids = [p['agente_id'] for p in participantes_response.data]
        participantes_data = []
        
        for p_id in participantes_ids:
            agente_response = supabase.table('agentes').select('*').eq('id', p_id).execute()
            if agente_response.data:
                agente = agente_response.data[0]
                participantes_data.append({
                    'id': p_id,
                    'nombre': agente['nombre'],
                    'apellidos': agente['apellidos'],
                    'nip': agente['nip'],
                    'seccion': agente['seccion'],
                    'grupo': agente['grupo']
                })
        
        if participantes_data:
            df_participantes = pd.DataFrame(participantes_data)
            df_participantes = df_participantes[['nombre', 'apellidos', 'nip', 'seccion', 'grupo']]
            df_participantes.columns = ['Nombre', 'Apellidos', 'NIP', 'Sección', 'Grupo']
            
            st.dataframe(df_participantes, use_container_width=True)
            
            # Botón para eliminar participantes
            if st.button("Eliminar todos los participantes"):
                response = supabase.table('participaciones').delete().eq('reserva_id', reserva_id).execute()
                if response.data:
                    st.success("Todos los participantes han sido eliminados")
                    st.rerun()
                else:
                    st.error("Error al eliminar participantes")
        else:
            st.info("No hay participantes en esta reserva")
    else:
        st.info("No hay participantes en esta reserva")
    
    # Step 3: Agregar nuevos participantes
    st.subheader("Añadir Participantes")
    
    # Obtener agentes que no son participantes
    agentes_response = supabase.table('agentes').select('*').execute()
    agentes = agentes_response.data if agentes_response.data else []
    
    # Filtrar agentes que ya son participantes
    participantes_ids_set = set(participantes_ids) if 'participantes_ids' in locals() else set()
    agentes_disponibles = [a for a in agentes if a['id'] not in participantes_ids_set]
    
    if not agentes_disponibles:
        st.info("No hay agentes disponibles para añadir")
        return
    
    # Crear filtros para encontrar agentes
    st.write("Filtrar agentes:")
    col1, col2 = st.columns(2)
    
    with col1:
        filter_seccion = st.multiselect(
            "Sección",
            options=list(set(a['seccion'] for a in agentes_disponibles)),
            default=[]
        )
    
    with col2:
        filter_grupo = st.multiselect(
            "Grupo",
            options=list(set(a['grupo'] for a in agentes_disponibles)),
            default=[]
        )
    
    # Aplicar filtros
    agentes_filtrados = agentes_disponibles
    if filter_seccion:
        agentes_filtrados = [a for a in agentes_filtrados if a['seccion'] in filter_seccion]
    if filter_grupo:
        agentes_filtrados = [a for a in agentes_filtrados if a['grupo'] in filter_grupo]
    
    # Mostrar agentes filtrados
    if agentes_filtrados:
        df_agentes = pd.DataFrame(agentes_filtrados)
        df_agentes = df_agentes[['id', 'nombre', 'apellidos', 'nip', 'seccion', 'grupo']]
        df_agentes.columns = ['ID', 'Nombre', 'Apellidos', 'NIP', 'Sección', 'Grupo']
        
        # Permitir selección múltiple
        selected_indices = st.multiselect(
            "Seleccionar Agentes a Añadir",
            options=list(range(len(df_agentes))),
            format_func=lambda i: f"{df_agentes.iloc[i]['Nombre']} {df_agentes.iloc[i]['Apellidos']} ({df_agentes.iloc[i]['NIP']})"
        )
        
        if st.button("Añadir Participantes Seleccionados"):
            if not selected_indices:
                st.warning("No has seleccionado ningún agente")
            else:
                # Insertar participaciones
                participaciones_data = []
                for i in selected_indices:
                    participaciones_data.append({
                        'reserva_id': reserva_id,
                        'agente_id': df_agentes.iloc[i]['ID']
                    })
                
                if participaciones_data:
                    response = supabase.table('participaciones').insert(participaciones_data).execute()
                    if response.data:
                        st.success(f"Se han añadido {len(participaciones_data)} participantes")
                        st.rerun()
                    else:
                        st.error("Error al añadir participantes")
    else:
        st.info("No hay agentes disponibles con los filtros seleccionados")
