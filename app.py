import streamlit as st
import pandas as pd
from datetime import date
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="Asistencia CBTA 24", layout="wide")
st.title("📊 Control de Asistencia - CBTA 24")

# Conexión a Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data
def load_data():
    return pd.read_excel("alumnos.xlsx")

df = load_data()

docentes = sorted(df['DOCENTE'].dropna().unique())
docente_sel = st.selectbox("Seleccione su Nombre:", ["-- Seleccione --"] + list(docentes))

if docente_sel != "-- Seleccione --":
    df_filtrado = df[df['DOCENTE'] == docente_sel].copy()
    
    carreras = sorted(df_filtrado['CARRERA'].unique())
    carrera_sel = st.selectbox("Carrera:", carreras)
    
    grupos = sorted(df_filtrado[df_filtrado['CARRERA'] == carrera_sel]['GRUPO'].unique())
    grupo_sel = st.radio("Grupo:", grupos, horizontal=True)
    
    # Lista de alumnos ordenada alfabéticamente
    lista_alumnos = df_filtrado[(df_filtrado['CARRERA'] == carrera_sel) & 
                                (df_filtrado['GRUPO'] == grupo_sel)].sort_values(by='NOMBRE COMPLETO')
    
    st.subheader(f"Lista de Alumnos - {grupo_sel}")
    
    with st.form("asistencia_form"):
        faltas = []
        for index, row in lista_alumnos.iterrows():
            nombre = row.get('NOMBRE COMPLETO', row.get('Nombre Completo', 'Sin Nombre'))
            num_control = row.get('NO CONTROL', row.get('NO. CONTROL', 'S/N'))
            
            if st.checkbox(f"{nombre} (ID: {num_control})", key=index):
                faltas.append(nombre)
        
        if st.form_submit_button("Guardar Asistencia en la Nube"):
            if faltas:
                # Crear DataFrame para la base de datos
                nuevos_datos = pd.DataFrame({
                    "Fecha": [str(date.today())] * len(faltas),
                    "Alumno": faltas,
                    "Docente": [docente_sel] * len(faltas),
                    "Grupo": [grupo_sel] * len(faltas),
                    "Carrera": [carrera_sel] * len(faltas)
                })
                
                # ENVIAR A GOOGLE SHEETS
                # Nota: ttl=0 asegura que no use caché y lea lo más nuevo
                data_actual = conn.read(ttl=0)
                data_final = pd.concat([data_actual, nuevos_datos], ignore_index=True)
                conn.update(data=data_final)
                
                st.success(f"✅ ¡Hecho! Se registraron {len(faltas)} faltas en la base de datos central.")
            else:
                st.success("✅ Asistencia guardada: Todos presentes.")
