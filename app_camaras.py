import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# Importamos nuestros módulos independientes
import asistencia
import pptt
import envasado

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="WMS Frigosa - ERP Industrial",
    page_icon="❄️",
    layout="wide"
)

SPREADSHEET_ID = "1Yi5OwKDnidykEFG7d2xSEjBCwl2nYFKOU7ZX86nlroU"

# --- CONEXIÓN GLOBAL A GOOGLE SHEETS ---
@st.cache_resource
def get_gspread_client():
    creds_dict = dict(st.secrets["gcp_service_account"])
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    return gspread.authorize(creds)

def get_sheet(sheet_name):
    client = get_gspread_client()
    sh = client.open_by_key(SPREADSHEET_ID)
    return sh.worksheet(sheet_name)

@st.cache_data(ttl=30)
def cargar_datos(sheet_name):
    ws = get_sheet(sheet_name)
    rows = ws.get_all_values()
    if len(rows) > 1:
        headers = [str(h).strip() for h in rows[0]]
        data = rows[1:]
        return pd.DataFrame(data, columns=headers)
    elif len(rows) == 1:
        return pd.DataFrame(columns=[str(h).strip() for h in rows[0]])
    return pd.DataFrame()

def registrar_log(tipo_mov, camara, posicion, codigo_palet, producto, cajas, usuario):
    try:
        ws_log = get_sheet("Movimientos_Log")
        fecha_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        nuevo_id = f"LOG-{datetime.now().strftime('%y%m%d%H%M%S')}"
        ws_log.append_row([nuevo_id, fecha_hora, tipo_mov, camara, posicion, str(codigo_palet), str(producto), str(cajas), str(usuario)])
    except Exception as e:
        st.warning(f"No se pudo registrar log: {e}")

# --- LOGIN ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_info = None

if "modulo_activo" not in st.session_state:
    st.session_state.modulo_activo = "Home"

def login_form():
    st.markdown("<h2 style='text-align: center; color: #1E3D59;'>❄️ ECAPRO / WMS Frigosa - ERP Acceso</h2>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        with st.form("login_form"):
            usuario = st.text_input("Usuario").strip().lower()
            codigo_ingresado = st.text_input("Código de Personal", type="password").strip()
            submit = st.form_submit_button("Ingresar al Sistema", use_container_width=True)
            
            if submit:
                try:
                    df_users = cargar_datos("Usuarios")
                    df_users["usuario"] = df_users["usuario"].astype(str).str.strip().str.lower()
                    df_users["codigo_personal"] = df_users["codigo_personal"].astype(str).str.strip()
                    df_users["estado"] = df_users["estado"].astype(str).str.strip().str.capitalize()

                    match = df_users[(df_users["usuario"] == usuario) & (df_users["codigo_personal"] == codigo_ingresado) & (df_users["estado"] == "Activo")]
                    
                    if not match.empty:
                        st.session_state.logged_in = True
                        st.session_state.user_info = match.iloc[0].to_dict()
                        st.session_state.modulo_activo = "Home"
                        st.rerun()
                    else:
                        st.error("Usuario o Código incorrecto.")
                except Exception as e:
                    st.error(f"Error: {e}")

if not st.session_state.logged_in:
    login_form()
    st.stop()

# Usuario activo
user = st.session_state.user_info
rol = user.get("rol", "Visualizador")
nombre = user.get("nombre_completo", user.get("usuario"))
codigo_per = user.get("codigo_personal", "P000")

# --- BARRA LATERAL ---
with st.sidebar:
    st.markdown(f"### 🏢 **ECAPRO Suite**")
    st.markdown(f"👤 **{nombre}**")
    st.markdown(f"🔑 Código: `{codigo_per}`")
    st.markdown(f"🛡️ Rol: `{rol}`")
    st.markdown("---")
    
    if st.session_state.modulo_activo != "Home":
        if st.button("🏠 Ir al Menú Principal", use_container_width=True):
            st.session_state.modulo_activo = "Home"
            st.rerun()
            
    if st.button("🚪 Cerrar Sesión", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.user_info = None
        st.session_state.modulo_activo = "Home"
        st.rerun()

# --- HEADER PRINCIPAL ESTILO ERP ---
st.markdown(
    """
    <div style="background: linear-gradient(135deg, #1E3D59 0%, #172B3A 100%); padding: 20px; border-radius: 10px; color: white; margin-bottom: 25px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
        <h1 style="margin: 0; font-size: 26px;">❄️ ECAPRO - Enterprise Resource Planning (Frigosa)</h1>
        <p style="margin: 5px 0 0 0; font-size: 15px; opacity: 0.85;">Sistema Integrado de Control Logístico, Producción y Personal</p>
    </div>
    """,
    unsafe_allow_html=True
)

# --- VISTA 1: DASHBOARD PRINCIPAL CON CUADROS / TARJETAS GRANDES ---
if st.session_state.modulo_activo == "Home":
    st.markdown("### 🎛️ Panel de Módulos del Sistema")
    st.caption("Seleccione un módulo haciendo clic en el cuadro correspondiente para gestionar las operaciones.")
    
    col_card1, col_card2 = st.columns(2)
    
    with col_card1:
        st.markdown(
            """
            <div style="background-color: #f8f9fa; border: 2px solid #1E3D59; border-radius: 10px; padding: 20px; text-align: center; margin-bottom: 15px;">
                <h3 style="color: #1E3D59; margin-top: 0;">⏱️ Módulo 1</h3>
                <h4 style="color: #333;">Control de Asistencia y Bolsa de Horas</h4>
                <p style="font-size: 13px; color: #666;">Gestión de ingresos, salidas, cálculo de horas extras y panel de compensaciones RR.HH.</p>
            </div>
            """,
            unsafe_allow_html=True
        )
        if st.button("🚀 Ingresar a Asistencia", use_container_width=True, key="btn_m1"):
            st.session_state.modulo_activo = "Asistencia"
            st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)

        st.markdown(
            """
            <div style="background-color: #f8f9fa; border: 2px solid #ff8800; border-radius: 10px; padding: 20px; text-align: center; margin-bottom: 15px;">
                <h3 style="color: #e67e22; margin-top: 0;">📦 Módulo 3</h3>
                <h4 style="color: #333;">Envasado y Control de Plaqueros</h4>
                <p style="font-size: 13px; color: #666;">Registro de túneles, plaqueros P1-P18, tiempos de congelación, rendimientos e histograma.</p>
            </div>
            """,
            unsafe_allow_html=True
        )
        if st.button("🚀 Ingresar a Envasado", use_container_width=True, key="btn_m_env"):
            st.session_state.modulo_activo = "Envasado"
            st.rerun()

    with col_card2:
        st.markdown(
            """
            <div style="background-color: #f8f9fa; border: 2px solid #007bff; border-radius: 10px; padding: 20px; text-align: center; margin-bottom: 15px;">
                <h3 style="color: #007bff; margin-top: 0;">📥 Módulo 2</h3>
                <h4 style="color: #333;">Ingreso de PPTT (Productos Terminados)</h4>
                <p style="font-size: 13px; color: #666;">Registro de palets, asignación automática de posiciones en cámaras, calibres y pesos.</p>
            </div>
            """,
            unsafe_allow_html=True
        )
        if st.button("🚀 Ingresar a PPTT", use_container_width=True, key="btn_m2"):
            st.session_state.modulo_activo = "PPTT"
            st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)

        st.markdown(
            """
            <div style="background-color: #f8f9fa; border: 2px solid #28a745; border-radius: 10px; padding: 20px; text-align: center; margin-bottom: 15px;">
                <h3 style="color: #28a745; margin-top: 0;">📤 Módulo 4</h3>
                <h4 style="color: #333;">Despachos y Embarques</h4>
                <p style="font-size: 13px; color: #666;">Salidas de palets, control de embarques y trazabilidad de productos terminados hacia clientes.</p>
            </div>
            """,
            unsafe_allow_html=True
        )
        if st.button("🚀 Ingresar a Despachos", use_container_width=True, key="btn_m3"):
            st.session_state.modulo_activo = "Despachos"
            st.rerun()

# --- VISTA 2: CARGA DEL MÓDULO SELECCIONADO ---
else:
    if st.button("⬅️ Volver al Panel de Módulos (Home)", type="secondary"):
        st.session_state.modulo_activo = "Home"
        st.rerun()
    
    st.markdown("---")

    if st.session_state.modulo_activo == "Asistencia":
        asistencia.render_module(user, get_sheet, cargar_datos)
    elif st.session_state.modulo_activo == "PPTT":
        pptt.render_module(user, get_sheet, cargar_datos, registrar_log)
    elif st.session_state.modulo_activo == "Envasado":
        envasado.render_module(user, get_sheet, cargar_datos)
    elif st.session_state.modulo_activo == "Despachos":
        st.info("🚧 Módulo de Despachos y Embarques en proceso de integración modular.")
       
