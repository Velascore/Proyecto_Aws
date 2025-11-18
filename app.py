import streamlit as st
from datetime import datetime, date

# Configuración de la página
st.set_page_config(page_title="Gestión de Tareas", page_icon="📝", layout="wide")

# Título
st.title("📝 Sistema de Gestión de Tareas UAO")
# Subtítulo 
st.subheader("Proyecto Final AWS")

# Inicializar lista de tareas en session_state
if 'tareas' not in st.session_state:
    st.session_state.tareas = []

# Pestañas
tab1, tab2, tab3 = st.tabs(["➕ Nueva Tarea", "📋 Todas las Tareas", "📊 Estadísticas"])

# ========================================
# TAB 1: NUEVA TAREA
# ========================================
with tab1:
    st.header("Crear Nueva Tarea")
    
    with st.form("nueva_tarea"):
        titulo = st.text_input("Título de la tarea *", max_chars=100)
        descripcion = st.text_area("Descripción", height=100)
        
        col1, col2 = st.columns(2)
        with col1:
            fecha = st.date_input("Fecha límite", min_value=date.today())
        with col2:
            importancia = st.selectbox("Importancia", ["🟢 Baja", "🟡 Media", "🔴 Alta"])
        
        submit = st.form_submit_button("✅ Crear Tarea", use_container_width=True)
        
        if submit:
            if titulo:
                st.session_state.tareas.append({
                    'titulo': titulo,
                    'descripcion': descripcion,
                    'fecha': fecha,
                    'importancia': importancia,
                    'completada': False,
                    'creada': datetime.now()
                })
                st.success("¡Tarea creada exitosamente!")
                st.rerun()
            else:
                st.error("⚠️ El título es obligatorio")

# ========================================
# TAB 2: TODAS LAS TAREAS
# ========================================
with tab2:
    st.header("Lista de Tareas")
    
    # Filtros
    col1, col2, col3 = st.columns(3)
    
    with col1:
        filtro_estado = st.multiselect(
            "Filtrar por estado",
            ["Pendiente", "Completada"],
            default=["Pendiente", "Completada"]
        )
    
    with col2:
        filtro_importancia = st.multiselect(
            "Filtrar por importancia",
            ["🟢 Baja", "🟡 Media", "🔴 Alta"],
            default=["🟢 Baja", "🟡 Media", "🔴 Alta"]
        )
    
    with col3:
        ordenar = st.selectbox(
            "Ordenar por",
            ["Más reciente", "Más antigua", "Fecha límite", "Importancia"]
        )
    
    st.divider()
    
    # Filtrar tareas
    tareas_filtradas = []
    for tarea in st.session_state.tareas:
        estado = "Completada" if tarea['completada'] else "Pendiente"
        if estado in filtro_estado and tarea['importancia'] in filtro_importancia:
            tareas_filtradas.append(tarea)
    
    # Ordenar tareas
    if ordenar == "Más reciente":
        tareas_filtradas.sort(key=lambda x: x['creada'], reverse=True)
    elif ordenar == "Más antigua":
        tareas_filtradas.sort(key=lambda x: x['creada'])
    elif ordenar == "Fecha límite":
        tareas_filtradas.sort(key=lambda x: x['fecha'])
    elif ordenar == "Importancia":
        orden_imp = {"🔴 Alta": 0, "🟡 Media": 1, "🟢 Baja": 2}
        tareas_filtradas.sort(key=lambda x: orden_imp[x['importancia']])
    
    # Mostrar tareas
    if tareas_filtradas:
        for i, tarea in enumerate(st.session_state.tareas):
            if tarea not in tareas_filtradas:
                continue
                
            with st.container():
                col1, col2, col3, col4 = st.columns([3, 2, 1, 1])
                
                with col1:
                    # Emoji según importancia
                    if tarea['completada']:
                        st.subheader(f"✅ ~~{tarea['titulo']}~~")
                    else:
                        st.subheader(f"{tarea['importancia'][0]} {tarea['titulo']}")
                    
                    if tarea['descripcion']:
                        st.write(tarea['descripcion'])
                    
                    # Calcular días restantes
                    dias_restantes = (tarea['fecha'] - date.today()).days
                    if dias_restantes < 0:
                        st.error(f"⚠️ Vencida hace {abs(dias_restantes)} días")
                    elif dias_restantes == 0:
                        st.warning("⏰ Vence hoy")
                    elif dias_restantes <= 3:
                        st.warning(f"📅 Vence en {dias_restantes} días")
                    else:
                        st.info(f"📅 Vence el {tarea['fecha'].strftime('%d/%m/%Y')}")
                
                with col2:
                    st.write(f"**Importancia:** {tarea['importancia']}")
                    st.write(f"**Estado:** {'✅ Completada' if tarea['completada'] else '⏳ Pendiente'}")
                
                with col3:
                    if not tarea['completada']:
                        if st.button("✓ Completar", key=f"completar_{i}", use_container_width=True):
                            st.session_state.tareas[i]['completada'] = True
                            st.rerun()
                    else:
                        if st.button("↩️ Reabrir", key=f"reabrir_{i}", use_container_width=True):
                            st.session_state.tareas[i]['completada'] = False
                            st.rerun()
                
                with col4:
                    if st.button("🗑️ Eliminar", key=f"eliminar_{i}", use_container_width=True):
                        st.session_state.tareas.pop(i)
                        st.rerun()
                
                st.divider()
    else:
        st.info("No hay tareas que coincidan con los filtros seleccionados")

# ========================================
# TAB 3: ESTADÍSTICAS
# ========================================
with tab3:
    st.header("Estadísticas Generales")
    
    # Calcular estadísticas
    total = len(st.session_state.tareas)
    completadas = sum(1 for t in st.session_state.tareas if t['completada'])
    pendientes = total - completadas
    
    # Métricas principales
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total de Tareas", total)
    with col2:
        st.metric("Completadas", completadas)
    with col3:
        st.metric("Pendientes", pendientes)
    with col4:
        if total > 0:
            porcentaje = round((completadas / total) * 100)
            st.metric("% Completado", f"{porcentaje}%")
        else:
            st.metric("% Completado", "0%")
    
    st.divider()
    
    # Estadísticas por importancia
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Por Importancia")
        alta = sum(1 for t in st.session_state.tareas if t['importancia'] == "🔴 Alta")
        media = sum(1 for t in st.session_state.tareas if t['importancia'] == "🟡 Media")
        baja = sum(1 for t in st.session_state.tareas if t['importancia'] == "🟢 Baja")
        
        st.write(f"🔴 Alta: {alta}")
        st.write(f"🟡 Media: {media}")
        st.write(f"🟢 Baja: {baja}")
    
    with col2:
        st.subheader("Tareas Vencidas")
        vencidas = sum(1 for t in st.session_state.tareas 
                      if t['fecha'] < date.today() and not t['completada'])
        vencen_hoy = sum(1 for t in st.session_state.tareas 
                        if t['fecha'] == date.today() and not t['completada'])
        
        if vencidas > 0:
            st.error(f"⚠️ {vencidas} tareas vencidas")
        else:
            st.success("✅ No hay tareas vencidas")
        
        if vencen_hoy > 0:
            st.warning(f"⏰ {vencen_hoy} tareas vencen hoy")

# ========================================
# SIDEBAR
# ========================================
with st.sidebar:
    st.header("📊 Resumen Rápido")
    
    # Resumen de tareas
    total = len(st.session_state.tareas)
    completadas = sum(1 for t in st.session_state.tareas if t['completada'])
    pendientes = total - completadas
    
    st.metric("Total", total)
    st.metric("Completadas", completadas)
    st.metric("Pendientes", pendientes)
    
    st.divider()
    
    # Botón para limpiar tareas completadas
    if st.button("🧹 Limpiar Completadas", use_container_width=True):
        st.session_state.tareas = [t for t in st.session_state.tareas if not t['completada']]
        st.rerun()
    
    # Botón para eliminar todas
    if st.button("🗑️ Eliminar Todas", use_container_width=True):
        st.session_state.tareas = []
        st.rerun()
    
    st.divider()
    st.info("💡 **App lista para AWS**\n\nPróximo paso: Agregar base de datos")