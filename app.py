import streamlit as st
from datetime import datetime, date
import boto3
from boto3.dynamodb.conditions import Key, Attr
import uuid
import os
from botocore.exceptions import ClientError

# ============================
#  CONFIGURACIÓN INICIAL
# ============================

st.set_page_config(
    page_title="Gestión de Tareas UAO",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS personalizados
st.markdown("""
<style>
    .stButton>button {
        width: 100%;
    }
    .task-completed {
        opacity: 0.6;
    }
    div[data-testid="stMetricValue"] {
        font-size: 28px;
    }
</style>
""", unsafe_allow_html=True)

st.title("📝 Sistema de Gestión de Tareas UAO")
st.subheader("Proyecto Final AWS + DynamoDB")

# ============================
#  CONEXIÓN A DYNAMODB
# ============================

@st.cache_resource
def inicializar_dynamodb():
    """Inicializa la conexión a DynamoDB con manejo de errores mejorado"""
    try:
        # En VocLabs, las credenciales temporales se obtienen automáticamente
        # desde las variables de entorno configuradas por AWS Academy
        dynamodb = boto3.resource(
            "dynamodb",
            region_name=os.environ.get("AWS_DEFAULT_REGION", "us-east-1")
        )
        tabla = dynamodb.Table("Tareas")
        
        # Verificar que la tabla existe
        tabla.load()
        return tabla, None
    except ClientError as e:
        error_msg = f"Error de AWS: {e.response['Error']['Message']}"
        return None, error_msg
    except Exception as e:
        error_msg = f"Error al conectar con DynamoDB: {str(e)}"
        return None, error_msg

tabla, error_conexion = inicializar_dynamodb()

def probar_conexion():
    """Prueba la conexión a DynamoDB"""
    if tabla is None:
        return False, error_conexion
    try:
        tabla.table_status
        return True, "Conectado correctamente"
    except Exception as e:
        return False, str(e)

# ============================
#  FUNCIONES CRUD
# ============================

def crear_tarea_db(titulo, descripcion, fecha, importancia):
    """Crea una nueva tarea en DynamoDB"""
    try:
        tarea_id = str(uuid.uuid4())
        tabla.put_item(Item={
            "id": tarea_id,
            "titulo": titulo,
            "descripcion": descripcion,
            "fecha": str(fecha),
            "importancia": importancia,
            "completada": False,
            "creada": datetime.now().isoformat(),
            "actualizada": datetime.now().isoformat()
        })
        return True, "Tarea creada exitosamente"
    except Exception as e:
        return False, f"Error al crear tarea: {str(e)}"

def obtener_tareas_db(filtro="todas"):
    """Obtiene tareas desde DynamoDB con filtros opcionales"""
    try:
        if filtro == "todas":
            resp = tabla.scan()
        elif filtro == "pendientes":
            resp = tabla.scan(FilterExpression=Attr("completada").eq(False))
        elif filtro == "completadas":
            resp = tabla.scan(FilterExpression=Attr("completada").eq(True))
        else:
            resp = tabla.scan()
        
        tareas = resp.get("Items", [])
        
        # Ordenar por fecha
        tareas_ordenadas = sorted(
            tareas,
            key=lambda x: (x.get("completada", False), x.get("fecha", ""))
        )
        
        return tareas_ordenadas
    except Exception as e:
        st.error(f"Error al obtener tareas: {str(e)}")
        return []

def cambiar_estado_db(id_tarea, nuevo_estado):
    """Actualiza el estado de completado de una tarea"""
    try:
        tabla.update_item(
            Key={"id": id_tarea},
            UpdateExpression="SET completada = :estado, actualizada = :fecha",
            ExpressionAttributeValues={
                ":estado": nuevo_estado,
                ":fecha": datetime.now().isoformat()
            }
        )
        return True
    except Exception as e:
        st.error(f"Error al actualizar tarea: {str(e)}")
        return False

def eliminar_tarea_db(id_tarea):
    """Elimina una tarea de DynamoDB"""
    try:
        tabla.delete_item(Key={"id": id_tarea})
        return True
    except Exception as e:
        st.error(f"Error al eliminar tarea: {str(e)}")
        return False

def editar_tarea_db(id_tarea, titulo, descripcion, fecha, importancia):
    """Edita una tarea existente"""
    try:
        tabla.update_item(
            Key={"id": id_tarea},
            UpdateExpression="SET titulo = :t, descripcion = :d, fecha = :f, importancia = :i, actualizada = :a",
            ExpressionAttributeValues={
                ":t": titulo,
                ":d": descripcion,
                ":f": str(fecha),
                ":i": importancia,
                ":a": datetime.now().isoformat()
            }
        )
        return True
    except Exception as e:
        st.error(f"Error al editar tarea: {str(e)}")
        return False

# ============================
#  VERIFICAR CONEXIÓN
# ============================

if tabla is None:
    st.error(f"⚠️ No se pudo conectar a DynamoDB: {error_conexion}")
    st.info("""
    **Posibles soluciones:**
    1. Verifica que la tabla 'Tareas' existe en DynamoDB
    2. Asegúrate de que la instancia EC2 tiene un rol IAM con permisos para DynamoDB
    3. Verifica la región configurada
    4. Comprueba las credenciales de AWS
    """)
    st.stop()

# ============================
#  PESTAÑAS DE LA INTERFAZ
# ============================

tab1, tab2, tab3 = st.tabs(["➕ Nueva Tarea", "📋 Todas las Tareas", "📊 Estadísticas"])

# ============================
#  TAB 1 - Crear Nueva Tarea
# ============================

with tab1:
    st.header("Crear Nueva Tarea")

    with st.form("nueva_tarea", clear_on_submit=True):
        titulo = st.text_input("Título *", max_chars=100)
        descripcion = st.text_area("Descripción", max_chars=500, height=100)
        
        col1, col2 = st.columns(2)
        with col1:
            fecha = st.date_input(
                "Fecha límite",
                min_value=date.today(),
                value=date.today()
            )
        with col2:
            importancia = st.selectbox(
                "Importancia",
                ["🟢 Baja", "🟡 Media", "🔴 Alta"],
                index=1
            )

        submit = st.form_submit_button("✨ Crear Tarea", use_container_width=True)

        if submit:
            if not titulo.strip():
                st.error("⚠️ El título es obligatorio")
            else:
                exito, mensaje = crear_tarea_db(titulo, descripcion, fecha, importancia)
                if exito:
                    st.success("✅ Tarea guardada en DynamoDB 🎉")
                    st.balloons()
                    st.rerun()
                else:
                    st.error(mensaje)

# ============================
#  TAB 2 - Listado de Tareas
# ============================

with tab2:
    col_header1, col_header2 = st.columns([3, 1])
    
    with col_header1:
        st.header("Lista de Tareas")
    
    with col_header2:
        filtro = st.selectbox(
            "Filtrar",
            ["todas", "pendientes", "completadas"],
            label_visibility="collapsed"
        )

    tareas = obtener_tareas_db(filtro)

    if not tareas:
        st.info("📭 No hay tareas para mostrar")
    else:
        for idx, tarea in enumerate(tareas):
            with st.container():
                col1, col2, col3 = st.columns([4, 2, 1])

                # Columna info principal
                with col1:
                    emoji = tarea["importancia"].split()[0]
                    if tarea["completada"]:
                        st.markdown(f"### ✅ ~~{tarea['titulo']}~~")
                    else:
                        st.markdown(f"### {emoji} {tarea['titulo']}")

                    if tarea.get("descripcion"):
                        st.write(tarea["descripcion"])

                    # Cálculo de días restantes
                    try:
                        fecha_lim = date.fromisoformat(tarea["fecha"])
                        dias = (fecha_lim - date.today()).days

                        if dias < 0:
                            st.error(f"⚠️ Vencida hace {abs(dias)} días")
                        elif dias == 0:
                            st.warning("⏰ Vence HOY")
                        elif dias <= 3:
                            st.warning(f"📅 Vence en {dias} días")
                        else:
                            st.info(f"📅 Fecha límite: {fecha_lim.strftime('%d/%m/%Y')}")
                    except:
                        st.caption(f"📅 {tarea['fecha']}")

                # Columna detalles
                with col2:
                    st.write(f"**Importancia:** {tarea['importancia']}")
                    estado_texto = "✅ Completada" if tarea['completada'] else "⏳ Pendiente"
                    st.write(f"**Estado:** {estado_texto}")

                # Columna acciones
                with col3:
                    if not tarea["completada"]:
                        if st.button("✔️ Completar", key=f"comp_{tarea['id']}", use_container_width=True):
                            if cambiar_estado_db(tarea["id"], True):
                                st.success("✅ Completada!")
                                st.rerun()
                    else:
                        if st.button("↩️ Reabrir", key=f"reab_{tarea['id']}", use_container_width=True):
                            if cambiar_estado_db(tarea["id"], False):
                                st.rerun()

                    if st.button("🗑️ Eliminar", key=f"elim_{tarea['id']}", use_container_width=True):
                        if eliminar_tarea_db(tarea["id"]):
                            st.success("🗑️ Eliminada!")
                            st.rerun()

                st.divider()

# ============================
#  TAB 3 - Estadísticas
# ============================

with tab3:
    st.header("📊 Estadísticas y Resumen")

    tareas = obtener_tareas_db()

    total = len(tareas)
    completadas = sum(1 for t in tareas if t["completada"])
    pendientes = total - completadas
    
    # Métricas principales
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("📝 Total", total)
    col2.metric("✅ Completadas", completadas)
    col3.metric("⏳ Pendientes", pendientes)
    
    avance = int((completadas/total)*100) if total > 0 else 0
    col4.metric("📈 Avance", f"{avance}%")

    # Barra de progreso
    st.progress(avance / 100)

    st.divider()

    # Estadísticas por importancia
    col_a, col_b = st.columns(2)
    
    with col_a:
        st.subheader("Por Importancia")
        alta = sum(1 for t in tareas if t['importancia']=='🔴 Alta')
        media = sum(1 for t in tareas if t['importancia']=='🟡 Media')
        baja = sum(1 for t in tareas if t['importancia']=='🟢 Baja')
        
        st.write(f"🔴 **Alta:** {alta} tareas")
        st.write(f"🟡 **Media:** {media} tareas")
        st.write(f"🟢 **Baja:** {baja} tareas")
    
    with col_b:
        st.subheader("Tareas Vencidas")
        vencidas = 0
        hoy = date.today()
        
        for t in tareas:
            if not t["completada"]:
                try:
                    fecha_tarea = date.fromisoformat(t["fecha"])
                    if fecha_tarea < hoy:
                        vencidas += 1
                except:
                    pass
        
        if vencidas > 0:
            st.error(f"⚠️ **{vencidas}** tareas vencidas")
        else:
            st.success("✅ No hay tareas vencidas")

    # Resumen de productividad
    if total > 0:
        st.divider()
        st.subheader("💡 Insights")
        
        if avance == 100:
            st.success("🎉 ¡Excelente! Has completado todas tus tareas")
        elif avance >= 70:
            st.info("👍 Buen progreso, sigue así")
        elif avance >= 40:
            st.warning("⚡ Aún hay trabajo por hacer")
        else:
            st.error("🚨 Necesitas ponerte al día con tus tareas")

# ============================
#  SIDEBAR
# ============================

with st.sidebar:
    st.header("🔌 Estado del Sistema")

    if st.button("🔄 Probar Conexión DynamoDB", use_container_width=True):
        resultado, mensaje = probar_conexion()
        if resultado:
            st.success(f"✅ {mensaje}")
            st.info(f"**Región:** {os.environ.get('AWS_REGION', 'us-east-1')}")
        else:
            st.error(f"❌ {mensaje}")

    st.divider()
    
    # Información del sistema
    st.subheader("ℹ️ Información")
    st.caption(f"""
    **Base de datos:** Amazon DynamoDB  
    **Tabla:** Tareas  
    **Región:** {os.environ.get('AWS_REGION', 'us-east-1')}  
    **Total tareas:** {len(obtener_tareas_db())}
    """)
    
    st.divider()
    
    # Acciones rápidas
    st.subheader("⚙️ Acciones")
    
    if st.button("🔄 Refrescar Datos", use_container_width=True):
        st.cache_resource.clear()
        st.rerun()
    
    st.divider()
    st.caption("🎓 Proyecto Final UAO - AWS Academy")
    st.caption("📅 " + datetime.now().strftime("%Y"))