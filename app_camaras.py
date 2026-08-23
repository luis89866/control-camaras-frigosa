import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# Importamos nuestros módulos independientes
import asistencia
import pptt

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
    st.markdown("### 🏢 **ECAPRO Suite**")
    st.markdown(f"👤 **{nombre}**")
    st.markdown(f"🔑 Código: `{codigo_per}`")
    st.markdown(f"🛡️ Rol: `{rol}`")
    st.markdown("---")
    st.markdown("##### 🧭 Navegación ERP")
    
    # Menú lateral tipo botones corporativos para cambiar de módulo
    menu_opcion = st.radio(
        "Seleccione Módulo:",
        [
            "⏱️ Módulo 1: Asistencia",
            "📥 Módulo 2: Ingreso PPTT",
            "📤 Módulo 3: Despachos",
            "🗺️ Módulo 4: Layout Cámaras"
        ],
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    if st.button("🚪 Cerrar Sesión", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.user_info = None
        st.rerun()

# --- HEADER PRINCIPAL ESTILO ERP ---
st.markdown(
    """
    <div style="background-color: #1E3D59; padding: 15px; border-radius: 8px; color: white; margin-bottom: 20px;">
        <h2 style="margin: 0; font-size: 24px;">❄️ ECAPRO - Enterprise Resource Planning (Frigosa)</h2>
        <p style="margin: 5px 0 0 0; font-size: 14px; opacity: 0.8;">Sistema Integrado de Control Logístico y de Personal</p>
    </div>
    """,
    unsafe_allow_html=True
)

# --- CARGA DEL MÓDULO SELECCIONADO DESDE LA BARRA LATERAL ---
if "Módulo 1" in menu_opcion:
    asistencia.render_module(user, get_sheet, cargar_datos)
elif "Módulo 2" in menu_opcion:
    pptt.render_module(user, get_sheet, cargar_datos, registrar_log)
elif "Módulo 3" in menu_opcion:
    st.info("🚧 Módulo 3 (Despachos y Embarques) en proceso de integración modular.")
elif "Módulo 4" in menu_opcion:
    st.info("🚧 Módulo 4 (Layout de Cámaras) en proceso de integración modular.")
      
