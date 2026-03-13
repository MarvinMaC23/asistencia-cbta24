import streamlit as st
import pandas as pd
from datetime import date
from streamlit_gsheets import GSheetsConnection

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
            # Crear el registro para la base de datos
            # Si no hay faltas, se guarda un registro de 'Asistencia Completa'
            if not faltas:
                faltas_final = ["ASISTENCIA COMPLETA"]
            else:
                faltas_final = faltas

            nuevos_datos = pd.DataFrame({
                "Fecha": [str(date.today())] * len(faltas_final),
                "Alumno": faltas_final,
                "Docente": [docente_sel] * len(faltas_final),
                "Grupo": [grupo_sel] * len(faltas_final),
                "Carrera": [carrera_sel] * len(faltas_final)
            })
            
            # Intentar subir a Google Sheets
            try:
                # Leemos lo que ya hay para no borrarlo (ttl=0 para datos frescos)
                data_actual = conn.read(ttl=0)
                data_final = pd.concat([data_actual, nuevos_datos], ignore_index=True)
                
                # Actualizamos la hoja de cálculo
                conn.update(data=data_final)
                st.success(f"🚀 ¡Datos guardados! Se registraron {len(faltas)} inasistencias en la base de datos central.")
            except Exception as e:
                st.error(f"Error al guardar: {e}")
                st.info("Asegúrate de haber configurado el link de Google Sheets en los Secrets de Streamlit.")
