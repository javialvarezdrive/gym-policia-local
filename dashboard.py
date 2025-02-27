import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from db_utils import get_supabase_client

def show_dashboard():
    st.title("Dashboard de Participación")
    
    supabase = get_supabase_client()
    
    # Filtros de fecha para el dashboard
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Fecha Inicio", value=(datetime.now() - timedelta(days=30)).date())
    with col2:
        end_date = st.date_input("Fecha Fin", value=datetime.now().date())
    
    if start_date > end_date:
        st.error("La fecha de inicio debe ser anterior a la fecha de fin")
        return
    
    # Cargar datos sin usar la función RPC
    
    # 1. Obtener todos los agentes
    agentes_response = supabase.table('agentes').select('*').execute()
    agentes = agentes_response.data if agentes_response.data else []
    
    if not agentes:
        st.info("No hay agentes registrados en el sistema")
        return
    
    # 2. Para cada agente, contar participaciones
    dashboard_data = []
    
    for agente in agentes:
        # Obtener participaciones del agente
        participaciones_response = supabase.table('participaciones').select('*').eq('agente_id', agente['id']).execute()
        participaciones = participaciones_response.data if participaciones_response.data else []
        
        # Contar participaciones en el rango de fechas
        total_participaciones = 0
        for p in participaciones:
            # Obtener la reserva correspondiente
            reserva_response = supabase.table('reservas').select('*').eq('id', p['reserva_id']).execute()
            if reserva_response.data:
                # Convertir fecha a objeto date para comparar
                reserva_fecha_str = reserva_response.data[0]['fecha'].split('T')[0] if 'T' in reserva_response.data[0]['fecha'] else reserva_response.data[0]['fecha']
                reserva_fecha = datetime.strptime(reserva_fecha_str, "%Y-%m-%d").date()
                
                # Verificar si está en el rango
                if start_date <= reserva_fecha <= end_date:
                    total_participaciones += 1
        
        # Añadir al conjunto de datos
        dashboard_data.append({
            'nombre': agente['nombre'],
            'apellidos': agente['apellidos'],
            'nip': agente['nip'],
            'seccion': agente['seccion'],
            'grupo': agente['grupo'],
            'total_participaciones': total_participaciones
        })
    
    # Procesar y mostrar los datos
    if dashboard_data:
        df = pd.DataFrame(dashboard_data)
        
        # Visualización 1: Tabla de participaciones por agente
        st.subheader("Participaciones por Agente")
        df_display = df.copy()
        df_display['Nombre Completo'] = df_display['nombre'] + ' ' + df_display['apellidos']
        df_display = df_display[['Nombre Completo', 'nip', 'seccion', 'grupo', 'total_participaciones']]
        df_display.columns = ['Nombre Completo', 'NIP', 'Sección', 'Grupo', 'Total Participaciones']
        
        st.dataframe(df_display.sort_values('Total Participaciones', ascending=False), use_container_width=True)
        
        # Visualización 2: Estadísticas por sección
        st.subheader("Participaciones por Sección")
        seccion_df = df.groupby('seccion')['total_participaciones'].sum().reset_index()
        seccion_df.columns = ['Sección', 'Total Participaciones']
        st.dataframe(seccion_df, use_container_width=True)
        
        # Visualización 3: Estadísticas por grupo
        st.subheader("Participaciones por Grupo")
        grupo_df = df.groupby('grupo')['total_participaciones'].sum().reset_index()
        grupo_df.columns = ['Grupo', 'Total Participaciones']
        st.dataframe(grupo_df, use_container_width=True)
        
        # Visualización 4: Agentes con menor participación
        st.subheader("Agentes con Menor Participación")
        menor_participacion = df.sort_values('total_participaciones')[['nombre', 'apellidos', 'nip', 'seccion', 'grupo', 'total_participaciones']].head(10)
        menor_participacion['Nombre Completo'] = menor_participacion['nombre'] + ' ' + menor_participacion['apellidos']
        menor_participacion = menor_participacion[['Nombre Completo', 'nip', 'seccion', 'grupo', 'total_participaciones']]
        menor_participacion.columns = ['Nombre Completo', 'NIP', 'Sección', 'Grupo', 'Total Participaciones']
        
        st.dataframe(menor_participacion, use_container_width=True)
        
        # Opción para descargar todo el reporte
        csv = df_display.to_csv(index=False).encode('utf-8')
        st.download_button(
            "Descargar Reporte Completo (CSV)",
            csv,
            "reporte_participaciones.csv",
            "text/csv",
            key="download-csv-report"
        )
    else:
        st.info("No hay datos de participación en el rango de fechas seleccionado")
