from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import streamlit as st

# ==========================================================
# IMPORTACIÓN DE MÓDULOS ACTIVOS
# ==========================================================
import asistencia
import embarque  # <-- MÓDULO 4: DESPACHOS Y EMBARQUES
import envasado
import mp  # <-- MÓDULO 6: MATERIA PRIMA (TOLVA)
import stock_produccion

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="WMS Frigosa - ERP Industrial", page_icon="❄️", layout="wide"
)

SPREADSHEET_ID = "1Yi5OwKDnidykEFG7d2xSEjBCwl2nYFKOU7ZX86nlroU"


# --- CONEXIÓN GLOBAL A GOOGLE SHEETS ---
@st.cache_resource
def get_gspread_client():
  creds_dict = dict(st.secrets["gcp_service_account"])
  scopes = [
      "https://www.googleapis.com/auth/spreadsheets",
      "https://www.googleapis.com/auth/drive",
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


def registrar_log(
    tipo_mov, camara, posicion, codigo_palet, producto, cajas, usuario
):
  try:
    ws_log = get_sheet("Movimientos_Log")
    fecha_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    nuevo_id = f"LOG-{datetime.now().strftime('%y%m%d%H%M%S')}"
    ws_log.append_row([
        nuevo_id,
        fecha_hora,
        tipo_mov,
        camara,
        posicion,
        str(codigo_palet),
        str(producto),
        str(cajas),
        str(usuario),
    ])
  except Exception as e:
    st.warning(f"No se pudo registrar log: {e}")


# --- INICIALIZACIÓN DE VARIABLES DE SESIÓN ---
if "logged_in" not in st.session_state:
  st.session_state.logged_in = False
  st.session_state.user_info = None

if "modulo_activo" not in st.session_state:
  st.session_state.modulo_activo = "Home"


# --- CONTROL DE ACCESO BASADO EN ROLES (RBAC) ---
def obtener_modulos_permitidos(rol_usuario):
  rol_clean = str(rol_usuario).strip().upper()

  # Matriz de permisos
  permisos = {
      "ADMINISTRADOR": [
          "Asistencia",
          "Envasado",
          "Despachos",
          "StockProduccion",
          "MateriaPrima",
      ],
      "EXPORTACION": ["Despachos"],
      "PRODUCCION": ["Asistencia", "Envasado", "StockProduccion", "MateriaPrima"],
      "CAMARA": ["Asistencia", "Despachos"],
      "CALIDAD": ["MateriaPrima", "Envasado"],
  }
  return permisos.get(rol_clean, ["Asistencia"])


# --- FORMULARIO DE INICIO DE SESIÓN ---
def login_form():
  st.markdown(
      "<h2 style='text-align: center; color: #1E3D59;'>❄️ OPERACIONES / WMS"
      " Frigosa - ERP Acceso</h2>",
      unsafe_allow_html=True,
  )
  col1, col2, col3 = st.columns([1, 1.2, 1])

  with col2:
    with st.form("login_form"):
      usuario_input = st.text_input("Usuario").strip().lower()
      pin_input = st.text_input("PIN (Clave)", type="password").strip()
      submit = st.form_submit_button(
          "Ingresar al Sistema", use_container_width=True
      )

      if submit:
        try:
          df_users = cargar_datos("Usuarios")
          # Normalización de columnas de la hoja Usuarios
          df_users["usuario"] = (
              df_users["usuario"].astype(str).str.strip().str.lower()
          )
          df_users["pin"] = df_users["pin"].astype(str).str.strip()
          df_users["estado"] = (
              df_users["estado"].astype(str).str.strip().str.capitalize()
          )

          # Validación exacta por Usuario + PIN + Estado Activo
          match = df_users[
              (df_users["usuario"] == usuario_input)
              & (df_users["pin"] == pin_input)
              & (df_users["estado"] == "Activo")
          ]

          if not match.empty:
            st.session_state.logged_in = True
            st.session_state.user_info = match.iloc[0].to_dict()
            st.session_state.modulo_activo = "Home"
            st.rerun()
          else:
            st.error("Usuario o PIN incorrecto.")
        except Exception as e:
          st.error(f"Error de conexión con Usuarios: {e}")


if not st.session_state.logged_in:
  login_form()
  st.stop()

# --- DATOS DEL USUARIO EN SESIÓN ---
user = st.session_state.user_info
rol = str(user.get("rol", "Visualizador")).strip()
nombre = user.get("nombre_completo", user.get("usuario"))
codigo_per = user.get("codigo_personal", "P000")

# Módulos a los que tiene derecho el usuario según su rol
modulos_autorizados = obtener_modulos_permitidos(rol)

# --- BARRA LATERAL ---
with st.sidebar:
  st.markdown("### 🏢 **ECAPRO Suite**")
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
        <h1 style="margin: 0; font-size: 26px;">❄️ OPERACIONES - Enterprise Resource Planning (Frigosa)</h1>
        <p style="margin: 5px 0 0 0; font-size: 15px; opacity: 0.85;">Sistema Integrado de Control Logístico, Producción y Personal</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ==========================================================
# VISTA 1: DASHBOARD PRINCIPAL (HOME) FILTRADO POR ROLES
# ==========================================================
if st.session_state.modulo_activo == "Home":
  st.markdown("### 🎛️ Panel de Módulos del Sistema")
  st.caption(
      "Seleccione un módulo habilitado para su perfil de usuario para gestionar"
      " operaciones."
  )

  col_card1, col_card2 = st.columns(2)

  # --- COLUMNA 1 ---
  with col_card1:
    # MÓDULO 1: ASISTENCIA
    if "Asistencia" in modulos_autorizados:
      st.markdown(
          """
                <div style="background-color: #f8f9fa; border: 2px solid #1E3D59; border-radius: 10px; padding: 20px; text-align: center; margin-bottom: 15px;">
                    <h3 style="color: #1E3D59; margin-top: 0;">⏱️ Módulo 1</h3>
                    <h4 style="color: #333;">Control de Asistencia y Bolsa de Horas</h4>
                    <p style="font-size: 13px; color: #666;">Gestión de ingresos, salidas, cálculo de horas extras y compensaciones.</p>
                </div>
                """,
          unsafe_allow_html=True,
      )
      if st.button(
          "🚀 Ingresar a Asistencia", use_container_width=True, key="btn_m1"
      ):
        st.session_state.modulo_activo = "Asistencia"
        st.rerun()
      st.markdown("<br>", unsafe_allow_html=True)

    # MÓDULO 3: ENVASADO
    if "Envasado" in modulos_autorizados:
      st.markdown(
          """
                <div style="background-color: #f8f9fa; border: 2px solid #ff8800; border-radius: 10px; padding: 20px; text-align: center; margin-bottom: 15px;">
                    <h3 style="color: #e67e22; margin-top: 0;">📦 Módulo 3</h3>
                    <h4 style="color: #333;">Envasado y Control de Plaqueros</h4>
                    <p style="font-size: 13px; color: #666;">Registro de túneles, plaqueros P1-P18, tiempos de congelación y rendimientos.</p>
                </div>
                """,
          unsafe_allow_html=True,
      )
      if st.button(
          "🚀 Ingresar a Envasado", use_container_width=True, key="btn_m_env"
      ):
        st.session_state.modulo_activo = "Envasado"
        st.rerun()
      st.markdown("<br>", unsafe_allow_html=True)

    # MÓDULO 5: STOCK Y CONTROL DE PRODUCCIÓN
    if "StockProduccion" in modulos_autorizados:
      st.markdown(
          """
                <div style="background-color: #f8f9fa; border: 2px solid #6f42c1; border-radius: 10px; padding: 20px; text-align: center; margin-bottom: 15px;">
                    <h3 style="color: #6f42c1; margin-top: 0;">📊 Módulo 5</h3>
                    <h4 style="color: #333;">Stock y Control de Producción</h4>
                    <p style="font-size: 13px; color: #666;">Entradas a túnel, salidas de despacho, balance virtual L1/L2 e inventario físico.</p>
                </div>
                """,
          unsafe_allow_html=True,
      )
      if st.button(
          "🚀 Ingresar a Stock Producción",
          use_container_width=True,
          key="btn_m_stock",
      ):
        st.session_state.modulo_activo = "StockProduccion"
        st.rerun()

  # --- COLUMNA 2 ---
  with col_card2:
    # MÓDULO 4: DESPACHOS Y EMBARQUES
    if "Despachos" in modulos_autorizados:
      st.markdown(
          """
                <div style="background-color: #f8f9fa; border: 2px solid #28a745; border-radius: 10px; padding: 20px; text-align: center; margin-bottom: 15px;">
                    <h3 style="color: #28a745; margin-top: 0;">📤 Módulo 4</h3>
                    <h4 style="color: #333;">Despachos y Embarques</h4>
                    <p style="font-size: 13px; color: #666;">Salidas de palets, control de embarques, filtros de contenedores y descargas.</p>
                </div>
                """,
          unsafe_allow_html=True,
      )
      if st.button(
          "🚀 Ingresar a Despachos", use_container_width=True, key="btn_m4"
      ):
        st.session_state.modulo_activo = "Despachos"
        st.rerun()
      st.markdown("<br>", unsafe_allow_html=True)

    # MÓDULO 6: MATERIA PRIMA (TOLVA)
    if "MateriaPrima" in modulos_autorizados:
      st.markdown(
          """
                <div style="background-color: #f8f9fa; border: 2px solid #17a2b8; border-radius: 10px; padding: 20px; text-align: center; margin-bottom: 15px;">
                    <h3 style="color: #17a2b8; margin-top: 0;">🐟 Módulo 6</h3>
                    <h4 style="color: #333;">Materia Prima (Tolva / Descarga)</h4>
                    <p style="font-size: 13px; color: #666;">Registro ágil de tolvas, embarcaciones, matrículas, pesadas y tiempos.</p>
                </div>
                """,
          unsafe_allow_html=True,
      )
      if st.button(
          "🚀 Ingresar a Materia Prima (Tolva)",
          use_container_width=True,
          key="btn_m_mp",
      ):
        st.session_state.modulo_activo = "MateriaPrima"
        st.rerun()

# ==========================================================
# VISTA 2: RENDERIZADO DEL MÓDULO SELECCIONADO
# ==========================================================
else:
  if st.button("⬅️ Volver al Panel de Módulos (Home)", type="secondary"):
    st.session_state.modulo_activo = "Home"
    st.rerun()

  st.markdown("---")

  # Verificación de seguridad de rol
  if st.session_state.modulo_activo not in modulos_autorizados:
    st.error("⛔ No tienes permisos asignados para acceder a este módulo.")
    st.session_state.modulo_activo = "Home"
    st.stop()

  # Ejecución de submódulos
  if st.session_state.modulo_activo == "Asistencia":
    asistencia.render_module(user, get_sheet, cargar_datos)
  elif st.session_state.modulo_activo == "Envasado":
    envasado.render_module(user, get_sheet, cargar_datos)
  elif st.session_state.modulo_activo == "Despachos":
    embarque.render_module(user, get_gspread_client)
  elif st.session_state.modulo_activo == "StockProduccion":
    stock_produccion.render_module(user, get_gspread_client)
  elif st.session_state.modulo_activo == "MateriaPrima":
    mp.render_module(user, get_gspread_client)
