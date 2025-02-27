import streamlit as st
import pandas as pd
import plotly.express as px
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
    
    # Obtener datos para el dashboard
    query = f'''
    SELECT a.nombre, a.apellidos, a.nip, a.seccion, a.grupo, COUNT(p.id) as total_participaciones
    FROM agentes a
    LEFT JOIN participaciones p ON a.id = p.agente_id
    LEFT JOIN reservas r ON p.reserva_id = r.id
    WHERE r.fecha BETWEEN '{start_date}' AND '{end_date}' OR r.fecha IS NULL
    GROUP BY a.id, a.nombre, a.apellidos, a.nip, a.seccion, a.grupo
    ORDER BY total_participaciones DESC
    '''
    
    response = supabase.rpc('ejecutar_consulta', {'query': query}).execute()
    
    # Si no hay función RPC, alternativa manual (menos eficiente)
    if not response.data:
        # Obtener todos los agentes
        agentes_response = supabase.table('agentes').select('*').execute()
        agentes = agentes_response.data if agentes_response.data else []
        
        # Para cada agente, contar participaciones
        dashboard_data = []
        for agente in agentes:
            # Obtener participaciones del agente
            participaciones_query = f'''
            SELECT COUNT(p.id) as total
            FROM participaciones p
            JOIN reservas r ON p.reserva_id = r.id
            WHERE p.agente_id = '{agente['id']}'
            AND r.fecha BETWEEN '{start_date}' AND '{end_date}'
            '''
            
            participaciones_response = supabase.rpc('ejecutar_consulta', {'query': participaciones_query}).execute()
            
            # Si no funciona el RPC, hacerlo manualmente
            if not participaciones_response.data:
                # Obtener todas las participaciones del agente
                participaciones_response = supabase.table('participaciones').select('*').eq('agente_id', agente['id']).execute()
                
                # Filtrar por fecha si hay participaciones
                total_participaciones = 0
                if participaciones_response.data:
                    for p in participaciones_response.data:
                        reserva_response = supabase.table('reservas').select('*').eq('id', p['reserva_id']).execute()
                        if reserva_response.data:
                            reserva_fecha = datetime.strptime(reserva_response.data[0]['fecha'].split('T')[0], '%Y-%m-%d').date()
                            if start_date <= reserva_fecha <= end_date:
                                total_participaciones += 1
            else:
                total_participaciones = participaciones_response.data[0]['total'] if participaciones_response.data else 0
            
            dashboard_data.append({
                'nombre': agente['nombre'],
                'apellidos': agente['apellidos'],
                'nip': agente['nip'],
                'seccion': agente['seccion'],
                'grupo': agente['grupo'],
                'total_participaciones': total_participaciones
            })
        
        response.data = dashboard_data
    
    if response.data:
        df = pd.DataFrame(response.data)
        
        # Visualización 1: Tabla de participaciones por agente
        st.subheader("Participaciones por Agente")
        df_display = df.copy()
        df_display['Nombre Completo'] = df_display['nombre'] + ' ' + df_display['apellidos']
        df_display = df_display[['Nombre Completo', 'nip', 'seccion', 'grupo', 'total_participaciones']]
        df_display.columns = ['Nombre Completo', 'NIP', 'Sección', 'Grupo', 'Total Participaciones']
        
        st.dataframe(df_display.sort_values('Total Participaciones', ascending=False), use_container_width=True)
        
        # Visualización 2: Gráfico de participaciones por sección
        st.subheader("Participaciones por Sección")
        seccion_df = df.groupby('seccion')['total_participaciones'].sum().reset_index()
        fig_seccion = px.bar(
            seccion_df, 
            x='seccion', 
            y='total_participaciones',
            labels={'seccion': 'Sección', 'total_participaciones': 'Total Participaciones'},
            color='seccion',
            title="Participaciones por Sección"
        )
        st.plotly_chart(fig_seccion, use_container_width=True)
        
        # Visualización 3: Gráfico de participaciones por grupo
        st.subheader("Participaciones por Grupo")
        grupo_df = df.groupby('grupo')['total_participaciones'].sum().reset_index()
        fig_grupo = px.pie(
            grupo_df, 
            names='grupo', 
            values='total_participaciones',
            title="Participaciones por Grupo"
        )
        st.plotly_chart(fig_grupo, use_container_width=True)
        
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
