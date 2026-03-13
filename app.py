import streamlit as st
import pandas as pd
from datetime import date

# Configuración de la página
st.set_page_config(page_title="Asistencia CBTA 24", layout="wide")

st.title("📊 Control de Asistencia - CBTA 24")

# 1. Cargar Datos (Sustituye 'alumnos.xlsx' por tu archivo)
@st.cache_data
def load_data():
    df = pd.read_excel("alumnos.xlsx")
    # Aseguramos que la columna ASISTENCIA exista
    if 'ASISTENCIA' not in df.columns:
        df['ASISTENCIA'] = "PRESENTE"
    return df

df = load_data()

# 2. Filtro de Docente
docentes = df['DOCENTE'].unique()
docente_sel = st.selectbox("Seleccione su Nombre:", ["-- Seleccione --"] + list(docentes))

if docente_sel != "-- Seleccione --":
    # Filtrar datos por docente
    df_filtrado = df[df['DOCENTE'] == docente_sel].copy()
    
    # 3. Filtros secundarios (Carrera y Grupo)
    carreras = df_filtrado['CARRERA'].unique()
    carrera_sel = st.selectbox("Carrera:", carreras)
    
    grupos = df_filtrado[df_filtrado['CARRERA'] == carrera_sel]['GRUPO'].unique()
    grupo_sel = st.radio("Grupo:", grupos, horizontal=True)
    
    # Lista final de alumnos
    lista_alumnos = df_filtrado[(df_filtrado['CARRERA'] == carrera_sel) & 
                                (df_filtrado['GRUPO'] == grupo_sel)]
    
    st.subheader(f"Lista de Alumnos - {grupo_sel}")
    st.info("Marque a los alumnos que NO asistieron:")

    # 4. Formulario de asistencia
    st.subheader(f"Lista de Alumnos - {grupo_sel}")
    st.info("Marque a los alumnos que NO asistieron:")

    with st.form("asistencia_form"):
        faltas = []
        for index, row in lista_alumnos.iterrows():
            # Buscamos el nombre y el número de control de forma segura
            nombre = row.get('Nombre Completo', 'Sin Nombre')
            # Intentamos buscar 'NO CONTROL' o 'NO. CONTROL'
            num_control = row.get('NO CONTROL', row.get('NO. CONTROL', 'S/N'))
            
            check = st.checkbox(f"{nombre} (ID: {num_control})", key=index)
            if check:
                faltas.append(nombre)
        
        btn_guardar = st.form_submit_button("Guardar Inasistencias")
        
        if btn_guardar:
            if faltas:
                # Crear un pequeño resumen para descargar
                reporte_df = pd.DataFrame({
                    "Fecha": [date.today()] * len(faltas),
                    "Alumno": faltas,
                    "Docente": [docente_sel] * len(faltas),
                    "Grupo": [grupo_sel] * len(faltas)
                })
                
                st.warning(f"Se registraron {len(faltas)} inasistencias.")
                
                # Botón para descargar el reporte en CSV (se abre en Excel)
                csv = reporte_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="⬇️ Descargar Reporte de Faltas",
                    data=csv,
                    file_name=f"Faltas_{grupo_sel}_{date.today()}.csv",
                    mime="text/csv",
                )
            else:
                st.success("¡Asistencia completa! Todos presentes.")
