import streamlit as st
from datetime import datetime, date
import boto3
import json
import uuid

# ============================
#  CONFIGURACIÓN INICIAL
# ============================

st.set_page_config(page_title="Gestión de Tareas", page_icon="📝", layout="wide")

st.title("📝 Sistema de Gestión de Tareas UAO")
st.subheader("Proyecto Final AWS ")

# ============================
#  CONFIGURAR S3
# ============================

BUCKET = "proyecto-aws-camilo"     
ARCHIVO = "tareas.json"

s3 = boto3.client("s3", region_name="us-east-1")


# ----------------------------
# Funciones para S3
# ----------------------------

def cargar_tareas():
    """Lee las tareas desde el archivo JSON en S3."""
    try:
        obj = s3.get_object(Bucket=BUCKET, Key=ARCHIVO)
        data = obj["Body"].read().decode("utf-8")
        return json.loads(data)
    except s3.exceptions.NoSuchKey:
        return []  # Si no existe el archivo, no hay tareas
    except Exception as e:
        st.error(f"Error al cargar tareas desde S3: {e}")
        return []


def guardar_tareas(tareas):
    """Guarda la lista de tareas en S3 en formato JSON."""
    try:
        s3.put_object(
            Bucket=BUCKET,
            Key=ARCHIVO,
            Body=json.dumps(tareas),
            ContentType="application/json"
        )
    except Exception as e:
        st.error(f"Error al guardar tareas en S3: {e}")


def probar_conexion():
    """Prueba si el bucket es accesible."""
    try:
        s3.list_objects_v2(Bucket=BUCKET)
        return True
    except Exception as e:
        return str(e)


# ============================
#  INTERFAZ STREAMLIT
# ============================

tab1, tab2, tab3 = st.tabs(["➕ Nueva Tarea", "📋 Todas las Tareas", "📊 Estadísticas"])


# ===================================
# TAB 1 — Crear nueva tarea
# ===================================

with tab1:
    st.header("Crear Nueva Tarea")

    with st.form("nueva_tarea"):
        titulo = st.text_input("Título *")
        descripcion = st.text_area("Descripción")

        col1, col2 = st.columns(2)
        with col1:
            fecha = st.date_input("Fecha límite", min_value=date.today())
        with col2:
            importancia = st.selectbox("Importancia", ["🟢 Baja", "🟡 Media", "🔴 Alta"])

        submit = st.form_submit_button("Crear Tarea")

        if submit:
            if titulo.strip() == "":
                st.error("El título es obligatorio")
            else:
                tareas = cargar_tareas()
                nueva = {
                    "id": str(uuid.uuid4()),
                    "titulo": titulo,
                    "descripcion": descripcion,
                    "fecha": str(fecha),
                    "importancia": importancia,
                    "completada": False,
                    "creada": datetime.now().isoformat()
                }
                tareas.append(nueva)
                guardar_tareas(tareas)
                st.success("Tarea creada correctamente")
                st.rerun()


# ===================================
# TAB 2 — Listar tareas
# ===================================

with tab2:
    st.header("Tareas Registradas")

    tareas = cargar_tareas()

    if not tareas:
        st.info("No hay tareas registradas.")
    else:
        for tarea in tareas:
            with st.container():
                col1, col2, col3, col4 = st.columns([3, 2, 1, 1])

                # Información de la tarea
                with col1:
                    estado = "~~" + tarea["titulo"] + "~~" if tarea["completada"] else tarea["titulo"]
                    st.subheader(estado)
                    if tarea["descripcion"]:
                        st.write(tarea["descripcion"])

                # Info de estado
                with col2:
                    st.write(f"📅 Fecha límite: {tarea['fecha']}")
                    st.write(f"⭐ Importancia: {tarea['importancia']}")
                    st.write(f"Estado: {'Completada' if tarea['completada'] else 'Pendiente'}")

                # Completar / Reabrir
                with col3:
                    if st.button("✔", key=f"comp_{tarea['id']}"):
                        tarea["completada"] = not tarea["completada"]
                        guardar_tareas(tareas)
                        st.rerun()

                # Eliminar
                with col4:
                    if st.button("🗑", key=f"elim_{tarea['id']}"):
                        tareas = [t for t in tareas if t["id"] != tarea["id"]]
                        guardar_tareas(tareas)
                        st.rerun()

                st.divider()


# ===================================
# TAB 3 — Estadísticas
# ===================================

with tab3:
    st.header("Estadísticas")

    tareas = cargar_tareas()
    total = len(tareas)
    completadas = sum(1 for t in tareas if t["completada"])
    pendientes = total - completadas

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total", total)
    col2.metric("Completadas", completadas)
    col3.metric("Pendientes", pendientes)
    col4.metric("Avance", f"{int((completadas/total)*100) if total>0 else 0}%")

    st.divider()

# ===================================
# SIDEBAR
# ===================================

with st.sidebar:
    st.header("🔌 Conexión con AWS S3")

    if st.button("Probar conexión S3"):
        r = probar_conexion()
        if r is True:
            st.success("Conectado correctamente a S3 ✔")
        else:
            st.error(f"Error: {r}")

    st.info("Características:\n- S3 usado como base de datos\n- No necesita IAM Keys\n- Funciona en EC2 y local")

