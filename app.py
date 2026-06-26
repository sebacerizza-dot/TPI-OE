import streamlit as st
import pandas as pd
# Importamos la lógica de negocio y configuraciones de tu script existente
import utils as fn

# Configuración inicial de la pestaña del navegador
st.set_page_config(page_title="Gestor de Vacaciones", page_icon="📅", layout="wide")

# ── 1. GESTIÓN DE SESIÓN E INTENTOS DE LOGIN ──────────────────────────────────
if 'usuario_autenticado' not in st.session_state:
    st.session_state['usuario_autenticado'] = None

if 'intentos_restantes' not in st.session_state:
    st.session_state['intentos_restantes'] = fn.MAX_INTENTOS

def login_screen():
    st.markdown("<h2 style='text-align: center;'>💼 GESTOR DE VACACIONES</h2>", unsafe_allow_html=True)
    st.markdown("---")
    
    # Centrar el formulario visualmente en la pantalla
    _, col2, _ = st.columns([1, 1.5, 1])
    with col2:
        # Bloquear la interfaz por completo si se agotaron los intentos
        if st.session_state['intentos_restantes'] <= 0:
            st.error("❌ Superó el límite de intentos. Acceso bloqueado.")
            return

        with st.form("form_login"):
            st.markdown("### Iniciar Sesión")
            user_input = st.text_input("Usuario").strip()
            pass_input = st.text_input("Contraseña", type="password").strip()
            boton_login = st.form_submit_button("Ingresar", use_container_width=True)
            
            if boton_login:
                usuario = fn.validar_login(user_input, pass_input)
                if usuario:
                    # Login exitoso: guardamos usuario y restauramos intentos
                    st.session_state['usuario_autenticado'] = usuario
                    st.session_state['intentos_restantes'] = fn.MAX_INTENTOS
                    st.rerun()
                else:
                    # Descontar intento fallido
                    st.session_state['intentos_restantes'] -= 1
                    restantes = st.session_state['intentos_restantes']
                    if restantes > 0:
                        st.error(f"⚠️ Credenciales incorrectas. Intentos restantes: {restantes}.")
                    st.rerun()

def logout():
    st.session_state['usuario_autenticado'] = None
    st.rerun()


# ── 2. VISTA EMPLEADO ─────────────────────────────────────────────────────────
def vista_empleado(usuario):
    # Recargar datos del usuario en cada ciclo para ver el saldo actualizado
    u = fn.obtener_usuario(usuario['id'])
    
    st.title(f"👋 Bienvenido, {u['nombre']}")
    
    # Métricas superiores organizadas de forma limpia
    col_info1, col_info2 = st.columns(2)
    with col_info1:
        st.metric(label="Días de vacaciones disponibles", value=f"{u['dias_disponibles']} días")
    with col_info2:
        st.metric(label="Tu identificador de Empleado (ID)", value=f"#{u['id']}")
    
    st.markdown("---")
    col_solicitar, col_historial = st.columns([1, 1.2])
    
    with col_solicitar:
        st.subheader("📝 Solicitar Vacaciones")
        with st.form("form_vacaciones", clear_on_submit=True):
            st.info("💡 **Condiciones de solicitud:**\n- La fecha de inicio debe ser un lunes.\n- Las vacaciones se toman en bloques de 7 días.")
            
            fecha_inicio = st.date_input("Fecha de inicio", value=None)
            fecha_fin = st.date_input("Fecha de fin", value=None)
            enviar = st.form_submit_button("Enviar Solicitud a Jefatura", use_container_width=True)
            
            if enviar:
                if not fecha_inicio or not fecha_fin:
                    st.error("Debes seleccionar ambas fechas en el calendario.")
                else:
                    # Parsear a cadenas ISO YYYY-MM-DD para respetar tu backend
                    f_ini_str = fecha_inicio.isoformat()
                    f_fin_str = fecha_fin.isoformat()
                    
                    # Validar con las reglas de negocio originales de utils.py
                    errores = fn.validar_solicitud(u['id'], f_ini_str, f_fin_str)
                    
                    if errores:
                        st.error("🚨 Solicitud rechazada por las siguientes razones:")
                        for err in errores:
                            st.markdown(f"- {err}")
                    else:
                        sol = fn.registrar_solicitud(u['id'], u['nombre'], f_ini_str, f_fin_str)
                        st.success(f"✅ Solicitud registrada con éxito (ID: {sol['id']}). Enviada a Jefatura.")
                        st.rerun()
                        
    with col_historial:
        st.subheader("📊 Tus Solicitudes y Estados")
        solicitudes = fn.obtener_solicitudes_por_empleado(u['id'])
        if solicitudes:
            # Crear DataFrame y mapear los estados técnicos a nombres legibles usando tu diccionario
            df = pd.DataFrame(solicitudes)
            df['estado'] = df['estado'].map(fn.ESTADOS)
            
            # Reorganizar columnas para la interfaz de usuario
            df_mostrar = df[['id', 'fecha_inicio', 'fecha_fin', 'dias', 'estado', 'comentario']]
            df_mostrar.columns = ['ID', 'Inicio', 'Fin', 'Días', 'Estado del Trámite', 'Motivo / Comentarios']
            
            st.dataframe(df_mostrar, use_container_width=True, hide_index=True)
        else:
            st.info("Aún no registraste ninguna solicitud de vacaciones.")


# ── 3. VISTA JEFATURA (CON COMENTARIO OBLIGATORIO) ─────────────────────────────
def vista_jefatura(usuario):
    st.title(f"💼 Panel de Jefatura")
    st.markdown(f"Evaluador activo: **{usuario['nombre']}**")
    st.markdown("---")
    
    st.subheader("📥 Solicitudes Pendientes de Preaprobación")
    pendientes = fn.obtener_solicitudes_por_estado('PENDIENTE_PREAPROBACION')
    
    if not pendientes:
        st.success("🎉 ¡No hay solicitudes pendientes de preaprobación!")
        return

    for s in pendientes:
        with st.expander(f"📋 Solicitud #{s['id']} — {s['empleado_nombre']} ({s['dias']} días)"):
            st.markdown(f"**Período solicitado:** Desde el `{s['fecha_inicio']}` hasta el `{s['fecha_fin']}`")
            st.markdown(f"**Fecha de presentación:** {s['fecha_solicitud']}")
            
            with st.form(key=f"form_jefe_{s['id']}"):
                comentario = st.text_input("Motivo de rechazo (⚠️ OBLIGATORIO para rechazar)", key=f"txt_jefe_{s['id']}").strip()
                
                c1, c2, _ = st.columns(3)  #  Corregido: genera 3 columnas

                with c1:
                    if st.form_submit_button("Preaprobar ✔️", type="primary"):
                        fn.preaprobar_solicitud(s['id'])
                        st.success("Aprobada. Derivada a RRHH.")
                        st.rerun()
                with c2:
                    if st.form_submit_button("Rechazar ❌"):
                        if not comentario:
                            st.error("🚫 Debes ingresar un motivo para poder rechazar la solicitud.")
                        else:
                            fn.rechazar_solicitud(s['id'], comentario)
                            st.warning("Solicitud rechazada.")
                            st.rerun()



# ── 4. VISTA RRHH (CON COMENTARIO OBLIGATORIO) ─────────────────────────────────
def vista_rrhh(usuario):
    st.title(f"🏢 Panel de Recursos Humanos")
    st.markdown(f"Auditor activo: **{usuario['nombre']}**")
    st.markdown("---")
    
    st.subheader("⚖️ Solicitudes Pendientes de Aprobación Final")
    pendientes = fn.obtener_solicitudes_por_estado('PENDIENTE_APROBACION')
    
    if not pendientes:
        st.success("🎉 ¡No hay solicitudes pendientes de aprobación final por RRHH!")
        return

    for s in pendientes:
        emp = fn.obtener_usuario(s['empleado_id'])
        saldo_actual = emp['dias_disponibles'] if emp else "N/C"
        
        with st.expander(f"📋 Solicitud #{s['id']} — {s['empleado_nombre']} (Saldo actual del empleado: {saldo_actual} días)"):
            st.markdown(f"**Período solicitado:** Desde el `{s['fecha_inicio']}` hasta el `{s['fecha_fin']}` ({s['dias']} días)")
            
            with st.form(key=f"form_rrhh_{s['id']}"):
                comentario = st.text_input("Motivo de rechazo (⚠️ OBLIGATORIO para rechazar)", key=f"txt_rrhh_{s['id']}").strip()
                
                c1, c2, _ = st.columns(3)  #  Corregido: genera 3 columnas

                with c1:
                    if st.form_submit_button("Aprobar Definitivo 🏆", type="primary"):
                        fn.aprobar_solicitud(s['id'])
                        st.success("¡Aprobada! Días descontados del saldo.")
                        st.rerun()
                with c2:
                    if st.form_submit_button("Rechazar ❌"):
                        if not comentario:
                            st.error("🚫 Debes ingresar un motivo para poder rechazar la solicitud.")
                        else:
                            fn.rechazar_solicitud(s['id'], comentario)
                            st.warning("Solicitud rechazada de forma definitiva.")
                            st.rerun()



# ── 5. RUTEO PRINCIPAL (EQUIVALENTE A TU DEF MAIN) ───────────────────────────
user = st.session_state['usuario_autenticado']

if user is None:
    login_screen()
else:
    # Construcción de la barra lateral de navegación y logout
    with st.sidebar:
        st.markdown(f"### 👤 Cuenta activa")
        st.markdown(f"**Usuario:** `{user['usuario']}`")
        st.markdown(f"**Rol:** `{user['rol'].upper()}`")
        st.markdown("---")
        st.button("Cerrar Sesión", on_click=logout, use_container_width=True)

    # Enrutador basado exactamente en las strings de tus roles de usuarios.csv
    rol = user['rol'].strip().lower()
    if rol == 'empleado':
        vista_empleado(user)
    elif rol == 'jefatura':
        vista_jefatura(user)
    elif rol == 'rrhh':
        vista_rrhh(user)
    else:
        st.error(f"Rol '{user['rol']}' no reconocido por el sistema. Por favor, contacta al administrador.")
