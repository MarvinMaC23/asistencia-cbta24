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
    with st.form("asistencia_form"):
        # Creamos una lista de checkboxes
        faltas = []
        for index, row in lista_alumnos.iterrows():
            check = st.checkbox(f"{row['NOMBRE COMPLETO']} ({row['NO CONTROL']})", key=index)
            if check:
                faltas.append(index)
        
        btn_guardar = st.form_submit_button("Guardar Inasistencias")
        
        if btn_guardar:
            # Aquí actualizarías tu Excel o Base de Datos
            st.success(f"Se registraron {len(faltas)} faltas para el día {date.today()}")
            # Lógica para guardar en Excel (opcionalmente usando st.connection)