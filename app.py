import streamlit as st
import pandas as pd
import requests
from datetime import date

# 1. Configuración de la página
st.set_page_config(page_title="Asistencia CBTA 24", layout="wide")
st.title("📊 Control de Asistencia - CBTA 24")

# 2. Conexión a Google Sheets (Base de datos central)
# Recuerda configurar la URL en los 'Secrets' de Streamlit Cloud
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception as e:
    st.error("Error de conexión a la base de datos. Verifica los Secrets.")

# 3. Cargar lista de alumnos desde el Excel de GitHub
@st.cache_data
def load_data():
    return pd.read_excel("alumnos.xlsx")

df = load_data()

# Limpieza de nombres de columnas para evitar errores de mayúsculas/minúsculas
df.columns = [c.strip() for c in df.columns]

# 4. Interfaz de selección
docentes = sorted(df['DOCENTE'].dropna().unique())
docente_sel = st.selectbox("👤 Seleccione su Nombre (Docente):", ["-- Seleccione --"] + list(docentes))

if docente_sel != "-- Seleccione --":
    df_filtrado = df[df['DOCENTE'] == docente_sel].copy()
    
    carreras = sorted(df_filtrado['CARRERA'].unique())
    carrera_sel = st.selectbox("🏫 Carrera:", carreras)
    
    grupos = sorted(df_filtrado[df_filtrado['CARRERA'] == carrera_sel]['GRUPO'].unique())
    grupo_sel = st.radio("👥 Grupo:", grupos, horizontal=True)
    
    # 5. Filtrar y ordenar alumnos de forma robusta
    lista_alumnos = df_filtrado[(df_filtrado['CARRERA'] == carrera_sel) & 
                                (df_filtrado['GRUPO'] == grupo_sel)].copy()
    
    # Detectar dinámicamente la columna de nombre (ignorando mayúsculas)
    col_nombre = next((c for c in lista_alumnos.columns if c.upper() == "NOMBRE COMPLETO"), None)
    col_control = next((c for c in lista_alumnos.columns if "CONTROL" in c.upper()), None)

    if col_nombre:
        lista_alumnos = lista_alumnos.sort_values(by=col_nombre)
    
    st.divider()
    st.subheader(f"Lista de Asistencia: {grupo_sel}")
    st.info("💡 Marque únicamente a los alumnos que **NO** asistieron.")

    # 6. Formulario de Pase de Lista
    with st.form("asistencia_form"):
        faltas = []
        for index, row in lista_alumnos.iterrows():
            nombre_display = row[col_nombre] if col_nombre else "Sin Nombre"
            id_display = row[col_control] if col_control else "S/N"
            
            # El checkbox devuelve True si se marca (Inasistencia)
            if st.checkbox(f"{nombre_display} (ID: {id_display})", key=index):
                faltas.append(nombre_display)
        
        submit = st.form_submit_button("✅ Guardar Reporte en la Nube")
        
        if submit:
            # URL de respuesta del formulario (IMPORTANTE: termina en formResponse)
            url_form = "https://docs.google.com/forms/d/e/1FAIpQLSehlNQl_dt7RQ15RucWI0J5LUPwX8YnhHh-JDcCZ8J90aOaXA/formResponse"
            
            # Si no seleccionaste a nadie, registramos que el grupo estuvo completo
            if not faltas:
                faltas_final = ["ASISTENCIA COMPLETA"]
            else:
                faltas_final = faltas

            exito = True
            
            # Mostramos una barra de progreso mientras envía los datos
            with st.spinner('Guardando registros en Google...'):
                for alumno in faltas_final:
                    # Estos IDs deben ser EXACTAMENTE los de tu enlace previo
                    datos = {
                        "entry.1302517964": str(date.today()), 
                        "entry.848090664": alumno,             
                        "entry.1257791887": docente_sel,        
                        "entry.1101725855": grupo_sel,          
                        "entry.1842755561": carrera_sel         
                    }
                    
                    try:
                        # Enviamos con un tiempo de espera (timeout) para evitar que se quede colgado
                        r = requests.post(url_form, data=datos, timeout=10)
                        if r.status_code != 200:
                            exito = False
                    except Exception as e:
                        st.error(f"Error técnico: {e}")
                        exito = False
            
            if exito:
                st.success(f"✅ ¡Registros guardados con éxito en el sistema del CBTA 24!")
                st.balloons() # Un pequeño festejo visual porque ya funcionó
            else:
                st.error("❌ Google rechazó la conexión. Revisa que el formulario acepte respuestas.")
