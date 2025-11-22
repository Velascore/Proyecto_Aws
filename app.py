import streamlit as st
from datetime import datetime, date
import boto3
import json
import uuid
import altair as alt
import pandas as pd


# ============================
#  CONFIGURACIÓN INICIAL
# ============================

st.set_page_config(
    page_title="Gestión de Tareas UAO",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================
#  ESTILOS CSS PERSONALIZADOS
# ============================

st.markdown("""
<style>
    /* Tema oscuro global */
    .main {
        background: #001833;
    }
    
    /* Títulos principales */
    h1 {
        color: #ffffff !important;
        text-shadow: 0 0 20px rgba(0, 212, 255, 0.3);
        font-weight: 700 !important;
        margin-bottom: 0.5rem !important;
    }
    
    h2 {
        color: #ffffff !important;
        font-weight: 600 !important;
    }
    
    h3 {
        color: #26c6da !important;
    }
    
    /* Subtítulos */
    .subtitle {
        color: #b0bec5;
        font-size: 1.1rem;
        margin-bottom: 2rem;
    }
    
    /* Contenedor de tareas */
    .stContainer {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 15px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        border: 1px solid rgba(0, 212, 255, 0.2);
        backdrop-filter: blur(10px);
        transition: all 0.3s ease;
    }
    
    .stContainer:hover {
        border-color: rgba(0, 212, 255, 0.5);
        box-shadow: 0 8px 32px rgba(0, 212, 255, 0.1);
        transform: translateY(-2px);
    }
    
    /* Tabs personalizadas */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: rgba(255, 255, 255, 0.05);
        border-radius: 10px;
        padding: 5px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: transparent;
        border-radius: 8px;
        color: #b0bec5;
        font-weight: 600;
        padding: 10px 20px;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #00d4ff 0%, #00bcd4 100%);
        color: white !important;
    }
    
    /* Métricas mejoradas */
    [data-testid="stMetricValue"] {
        font-size: 2.5rem !important;
        font-weight: 700 !important;
        color: #00d4ff !important;
    }
    
    [data-testid="stMetricLabel"] {
        color: #b0bec5 !important;
        font-size: 1rem !important;
        font-weight: 600 !important;
    }
    
    /* Botones personalizados */
    .stButton button {
        border-radius: 10px;
        font-weight: 600;
        transition: all 0.3s ease;
        border: none;
    }
    
    .stButton button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 16px rgba(0, 0, 0, 0.2);
    }
    
    /* Inputs y formularios */
    .stTextInput input, .stTextArea textarea, .stSelectbox select {
        background: rgba(255, 255, 255, 0.08) !important;
        border: 1px solid rgba(0, 212, 255, 0.3) !important;
        border-radius: 10px !important;
        color: white !important;
        font-weight: 500 !important;
    }
    
    .stTextInput input:focus, .stTextArea textarea:focus, .stSelectbox select:focus {
        border-color: #00d4ff !important;
        box-shadow: 0 0 0 0.2rem rgba(0, 212, 255, 0.25) !important;
    }
    
    /* Divider personalizado */
    hr {
        border-color: rgba(0, 212, 255, 0.2) !important;
        margin: 1.5rem 0 !important;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background: #001833;
    }
    
    /* Info boxes */
    .stAlert {
        border-radius: 10px;
        border-left: 4px solid #00d4ff;
    }
    
    /* Badges de importancia */
    .badge-alta {
        background: linear-gradient(135deg, #ff1744 0%, #f50057 100%);
        color: white;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
        display: inline-block;
    }
    
    .badge-media {
        background: linear-gradient(135deg, #ffa726 0%, #fb8c00 100%);
        color: white;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
        display: inline-block;
    }
    
    .badge-baja {
        background: linear-gradient(135deg, #66bb6a 0%, #43a047 100%);
        color: white;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
        display: inline-block;
    }
    
    /* Estado completada */
    .task-completed {
        opacity: 0.6;
    }
    
    /* Logo UAO */
    .logo-container {
        position: fixed;
        top: 100cdpx;
        right: 40px;
        z-index: 999;
        background: rgba(0, 24, 51, 0.8);
        padding: 8px;
        border-radius: 10px;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(0, 212, 255, 0.2);
    }
    
    .logo-container img {
        width: 200px;
        height: auto;
        display: block;
    }
</style>
""", unsafe_allow_html=True)

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
        return []
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


# ----------------------------
# Funciones auxiliares
# ----------------------------

def get_badge_html(importancia):
    """Retorna HTML del badge según importancia"""
    badges = {
        "🔴 Alta": '<span class="badge-alta">🔴 ALTA</span>',
        "🟡 Media": '<span class="badge-media">🟡 MEDIA</span>',
        "🟢 Baja": '<span class="badge-baja">🟢 BAJA</span>'
    }
    return badges.get(importancia, importancia)


# ============================
#  HEADER PRINCIPAL
# ============================

# Logo UAO

URL_LOGO_UAO = "https://upload.wikimedia.org/wikipedia/commons/4/45/Logo-uao.png"
# --- Logo ---
# Código simplificado para mostrar el logo usando la URL directa
st.markdown(f"""
    <div class="logo-container">
        <img src="{URL_LOGO_UAO}" alt="Logo UAO">
    </div>
""", unsafe_allow_html=True)

st.markdown('<h1> Sistema de Gestión de Tareas UAO</h1>', unsafe_allow_html=True)
st.markdown('<h2 style="color: white;"> Proyecto Final AWS </h2>', unsafe_allow_html=True)
st.markdown('<p class="subtitle"> Camilo Velasco, Bradley Campo, Santiago Barriga, Manuel Luna</p>', unsafe_allow_html=True)
# ============================
#  TABS PRINCIPALES
# ============================

tab0,tab1, tab2, tab3,tab4 = st.tabs(["Descipcion proyecto","➕ Nueva Tarea", "📋 Todas las Tareas", "📊 Estadísticas"," 🖥️ Conexion instancia EC2 B"])


# ===================================
# TAB 0 – Crear nueva tarea
# ===================================

with tab0:
    st.header("Descripción General del Proyecto")
    st.markdown("""
**Sistema de Gestión de Tareas en AWS**

Este proyecto es una aplicación web desarrollada con **Python y Streamlit**, desplegada en una instancia **Amazon EC2 (t3.micro)**. Toda la información se almacena de manera persistente en un **archivo JSON alojado en un bucket de Amazon S3**.

La arquitectura utiliza un **Rol de IAM (LabRole)**, el cual permite que la instancia EC2 acceda a  al Bucket de S3 

### **Funciones principales de la aplicación:**
- Crear nuevas tareas.
- Listarlas y gestionarlas.
- Marcar tareas como completadas.
- Eliminar tareas con confirmación.
- Mostrar estadísticas y gráficas del uso.
- Persistencia de datos en S3 usando JSON.

### **Componentes del despliegue:**

• **Amazon EC2**
   - Ubuntu Server  
   - Tipo de instancia: *t3.micro*  
   - Ejecutando `app.py` (Streamlit) en el puerto **8501/TCP**  
   - Entorno virtual (venv) configurado

• **IAM Role: LabRole**
   - Permite acceso a S3 
   - Incluye permisos como: - `AmazonS3FullAccess`   - `AmazonEC2ReadOnlyAccess`  
     
    
• **Amazon S3**
   - Bucket: `proyecto-aws-camilo`  
   - Almacenamiento del archivo JSON: `tareas.json`  

• **Security Group**
   - SSH → 22/TCP  
   - Streamlit → **8501/TCP**  
   - HTTP/HTTPS 
   - **ICMP** habilitado para diagnóstico de red

""")
                


    st.info("Este proyecto es un sistema de gestión de tareas desarrollado en Streamlit, desplegado en una instancia EC2, y utilizando servicios como S3, DynamoDB, y Lambda.")# ===================================
# TAB 1 – Crear nueva tarea
# ===================================

with tab1:
    st.header("Crear Nueva Tarea")
    
    with st.form("nueva_tarea"):
        titulo = st.text_input("📝 Título *", placeholder="Ingrese el título de la tarea...")
        descripcion = st.text_area("📄 Descripción", placeholder="Añade detalles sobre la tarea...")

        col1, col2 = st.columns(2)
        with col1:
            fecha = st.date_input("📅 Fecha límite", min_value=date.today())
        with col2:
            importancia = st.selectbox("⭐ Importancia", ["🟢 Baja", "🟡 Media", "🔴 Alta"])

        submit = st.form_submit_button("✨ Crear Tarea", use_container_width=True)

        if submit:
            if titulo.strip() == "":
                st.error("❌ El título es obligatorio")
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
                st.success("✅ Tarea creada correctamente")
                st.rerun()


# ===================================
# TAB 2 – Listar tareas
# ===================================

with tab2:
    st.header("Tareas Registradas")

    tareas = cargar_tareas()
    
    # Filtros
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        filtro_estado = st.selectbox("🔍 Filtrar por estado", ["Todas", "Pendientes", "Completadas"])
    with col_f2:
        filtro_importancia = st.selectbox("🔍 Filtrar por importancia", ["Todas", "🔴 Alta", "🟡 Media", "🟢 Baja"])
    
    # Aplicar filtros
    tareas_filtradas = tareas.copy()
    
    if filtro_estado == "Pendientes":
        tareas_filtradas = [t for t in tareas_filtradas if not t["completada"]]
    elif filtro_estado == "Completadas":
        tareas_filtradas = [t for t in tareas_filtradas if t["completada"]]
    
    if filtro_importancia != "Todas":
        tareas_filtradas = [t for t in tareas_filtradas if t["importancia"] == filtro_importancia]

    st.divider()

    if not tareas_filtradas:
        st.info("📭 No hay tareas que coincidan con los filtros.")
    else:
        for tarea in tareas_filtradas:
            container_class = "task-completed" if tarea["completada"] else ""
            
            with st.container():
                col1, col2, col3, col4 = st.columns([3, 2, 1, 1])

                # Información de la tarea
                with col1:
                    estado = f"~~{tarea['titulo']}~~" if tarea["completada"] else tarea["titulo"]
                    st.subheader(estado)
                    if tarea["descripcion"]:
                        st.write(tarea["descripcion"])

                # Info de estado
                with col2:
                    st.write(f"📅 **Fecha límite:** {tarea['fecha']}")
                    st.markdown(f"⭐ **Importancia:** {get_badge_html(tarea['importancia'])}", unsafe_allow_html=True)
                    estado_emoji = "✅" if tarea['completada'] else "⏳"
                    estado_texto = "Completada" if tarea['completada'] else "Pendiente"
                    st.write(f"{estado_emoji} **Estado:** {estado_texto}")

                # Completar / Reabrir
                with col3:
                    boton_texto = "↩️" if tarea["completada"] else "✅"
                    if st.button(boton_texto, key=f"comp_{tarea['id']}", help="Cambiar estado"):
                        tarea["completada"] = not tarea["completada"]
                        guardar_tareas(tareas)
                        st.rerun()

                # Eliminar con confirmación
                with col4:
                    if f"confirm_delete_{tarea['id']}" not in st.session_state:
                        st.session_state[f"confirm_delete_{tarea['id']}"] = False
                    
                    if not st.session_state[f"confirm_delete_{tarea['id']}"]:
                        if st.button("🗑️", key=f"elim_{tarea['id']}", help="Eliminar tarea"):
                            st.session_state[f"confirm_delete_{tarea['id']}"] = True
                            st.rerun()
                    else:
                        col_si, col_no = st.columns(2)
                        with col_si:
                            if st.button("✓", key=f"conf_si_{tarea['id']}", help="Confirmar"):
                                tareas = [t for t in tareas if t["id"] != tarea["id"]]
                                guardar_tareas(tareas)
                                del st.session_state[f"confirm_delete_{tarea['id']}"]
                                st.rerun()
                        with col_no:
                            if st.button("✗", key=f"conf_no_{tarea['id']}", help="Cancelar"):
                                st.session_state[f"confirm_delete_{tarea['id']}"] = False
                                st.rerun()

                st.divider()


# ===================================
# TAB 3 – Estadísticas
# ===================================

with tab3:
    st.header("📊 Estadísticas y Análisis")

    tareas = cargar_tareas()
    total = len(tareas)
    completadas = sum(1 for t in tareas if t["completada"])
    pendientes = total - completadas

    # KPIs principales
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("📝 Total", total)
    col2.metric("✅ Completadas", completadas)
    col3.metric("⏳ Pendientes", pendientes)
    col4.metric("🎯 Avance", f"{int((completadas/total)*100) if total>0 else 0}%")

    st.divider()

    if total > 0:
        # Preparar datos para visualizaciones
        col_viz1, col_viz2 = st.columns(2)
        
        with col_viz1:
            st.subheader("📊 Estado de Tareas")
            
            # Gráfico de barras - Estado
            df_estado = pd.DataFrame({
                'Estado': ['Completadas', 'Pendientes'],
                'Cantidad': [completadas, pendientes]
            })
            
            chart_estado = alt.Chart(df_estado).mark_bar(cornerRadiusTopLeft=10, cornerRadiusTopRight=10).encode(
                x=alt.X('Estado:N', axis=alt.Axis(labelAngle=0, labelFontSize=12)),
                y=alt.Y('Cantidad:Q', title='Número de Tareas'),
                color=alt.Color('Estado:N', 
                    scale=alt.Scale(domain=['Completadas', 'Pendientes'], 
                                  range=['#43a047', '#ffa726']),
                    legend=None),
                tooltip=['Estado', 'Cantidad']
            ).properties(
                height=300
            ).configure_view(
                strokeWidth=0
            ).configure_axis(
                labelColor='#b0bec5',
                titleColor='#00d4ff',
                gridColor='rgba(255,255,255,0.1)'
            )
            
            st.altair_chart(chart_estado, use_container_width=True)
        
        with col_viz2:
            st.subheader("🎯 Distribución por Importancia")
            
            # Gráfico circular - Importancia
            importancia_count = {}
            for t in tareas:
                imp = t['importancia']
                importancia_count[imp] = importancia_count.get(imp, 0) + 1
            
            df_importancia = pd.DataFrame({
                'Importancia': list(importancia_count.keys()),
                'Cantidad': list(importancia_count.values())
            })
            
            chart_pie = alt.Chart(df_importancia).mark_arc(innerRadius=50).encode(
                theta=alt.Theta('Cantidad:Q'),
                color=alt.Color('Importancia:N', 
                    scale=alt.Scale(domain=['🟢 Baja', '🟡 Media', '🔴 Alta'],
                                  range=['#43a047', '#ffa726', '#ff1744'])),
                tooltip=['Importancia', 'Cantidad']
            ).properties(
                height=300
            )
            
            st.altair_chart(chart_pie, use_container_width=True)
        
        st.divider()
        
        # Gráfico de línea temporal
        st.subheader("📈 Tareas por Fecha Límite")
        
        df_fechas = pd.DataFrame(tareas)
        df_fechas['fecha'] = pd.to_datetime(df_fechas['fecha'])
        df_fechas_agrupadas = df_fechas.groupby('fecha').size().reset_index(name='cantidad')
        
        chart_timeline = alt.Chart(df_fechas_agrupadas).mark_line(
            point=alt.OverlayMarkDef(filled=True, size=100),
            strokeWidth=3
        ).encode(
            x=alt.X('fecha:T', title='Fecha', axis=alt.Axis(labelAngle=-45)),
            y=alt.Y('cantidad:Q', title='Número de Tareas'),
            color=alt.value('#00d4ff'),
            tooltip=[alt.Tooltip('fecha:T', title='Fecha'), alt.Tooltip('cantidad:Q', title='Tareas')]
        ).properties(
            height=300
        ).configure_view(
            strokeWidth=0
        ).configure_axis(
            labelColor='#b0bec5',
            titleColor='#00d4ff',
            gridColor='rgba(255,255,255,0.1)'
        )
        
        st.altair_chart(chart_timeline, use_container_width=True)
        
    else:
        st.info("📭 No hay datos suficientes para mostrar estadísticas. ¡Crea tu primera tarea!")

with tab4:  
    st.header("🖥️ Conexión desde Instancia EC2 - Prueba B")
    st.markdown("**Aquí podemos poner información sobre la conexión desde la instancia EC2.**")

# ===================================
# SIDEBAR
# ===================================

with st.sidebar:
    st.header("🔌 Conexión con AWS S3")

    if st.button("🔍 Probar conexión S3", use_container_width=True):
        r = probar_conexion()
        if r is True:
            st.success("✅ Conectado correctamente a S3")
        else:
            st.error(f"❌ Error: {r}")

    st.divider()
    
    st.info("**🚀 Características:**\n\n"
            "✅ S3 como base de datos\n"
            "✅ Sin IAM Keys necesarias\n"
            "✅ Compatible con EC2\n"
            "✅ Visualizaciones interactivas\n"
            "✅ Tema oscuro profesional")
    
    st.divider()
    
    tareas = cargar_tareas()
    if tareas:
        st.metric("📊 Total de tareas", len(tareas))
        st.metric("🔥 Tareas activas", sum(1 for t in tareas if not t["completada"]))
    
    st.divider()
    st.caption("🎓 Universidad Autónoma de Occidente")
    st.caption("💻 Proyecto AWS 2025")