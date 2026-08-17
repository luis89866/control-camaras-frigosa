import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="WMS Frigosa - Control de Cámaras",
    page_icon="❄️",
    layout="wide"
)

# ID directo de tu Google Sheets
SPREADSHEET_ID = "1Yi5OwKDnidykEFG7d2xSEjBCwl2nYFKOU7ZX86nlroU"

# --- CONEXIÓN DIRECTA Y ROBUSTA A GOOGLE SHEETS ---
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

# --- GESTIÓN DE SESIÓN Y LOGIN ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_info = None

def login_form():
    st.markdown("<h2 style='text-align: center; color: #1E3D59;'>❄️ WMS Frigosa - Acceso al Sistema</h2>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        with st.form("login_form"):
            usuario = st.text_input("Usuario").strip().lower()
            pin = st.text_input("PIN / Clave", type="password").strip()
            submit = st.form_submit_button("Ingresar al Sistema", use_container_width=True)
            
            if submit:
                if not usuario or not pin:
                    st.warning("Por favor ingresa usuario y PIN.")
                    return
                try:
                    df_users = cargar_datos("Usuarios")
                    if df_users.empty:
                        st.error("No se encontraron registros en la tabla de Usuarios.")
                        return
                    
                    df_users["usuario"] = df_users["usuario"].astype(str).str.strip().str.lower()
                    df_users["pin"] = df_users["pin"].astype(str).str.strip()
                    df_users["estado"] = df_users["estado"].astype(str).str.strip().str.capitalize()

                    match = df_users[(df_users["usuario"] == usuario) & (df_users["pin"] == pin) & (df_users["estado"] == "Activo")]
                    
                    if not match.empty:
                        user_data = match.iloc[0].to_dict()
                        st.session_state.logged_in = True
                        st.session_state.user_info = user_data
                        st.rerun()
                    else:
                        st.error("Usuario o PIN incorrecto, o usuario inactivo.")
                except Exception as e:
                    st.error(f"Error de conexión: {e}")

if not st.session_state.logged_in:
    login_form()
    st.stop()

# --- DATOS DEL USUARIO AUTENTICADO ---
user = st.session_state.user_info
rol = user.get("rol", "Visualizador")
nombre = user.get("nombre_completo", user.get("usuario"))

# --- BARRA LATERAL ---
with st.sidebar:
    st.markdown(f"### 👤 Usuario: **{nombre}**")
    st.markdown(f"**Rol:** `{rol}`")
    st.markdown("---")
    if st.button("🚪 Cerrar Sesión", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.user_info = None
        st.rerun()

# --- CARGA PRINCIPAL DE INVENTARIO ---
try:
    df_inv = cargar_datos("Inventario")
except Exception as e:
    st.error(f"Error cargando inventario: {e}")
    st.stop()

st.title("❄️ Control de Cámaras - Frigosa")

# Selector de Cámara
camaras_disponibles = ["Camara 01", "Camara 02", "Camara 03"]
cam_sel = st.selectbox("Seleccionar Cámara:", camaras_disponibles)

# Filtrar datos de la cámara actual
df_cam = df_inv[df_inv["camara"] == cam_sel] if not df_inv.empty and "camara" in df_inv.columns else pd.DataFrame()

# Métricas
total_posiciones = 180
ocupadas = len(df_cam[df_cam["estado"].str.strip().str.capitalize() == "Ocupado"]) if not df_cam.empty and "estado" in df_cam.columns else 0
libres = max(0, total_posiciones - ocupadas)
pct_ocupacion = (ocupadas / total_posiciones) * 100 if total_posiciones > 0 else 0

m1, m2, m3 = st.columns(3)
m1.metric("Ocupación", f"{pct_ocupacion:.1f}%")
m2.metric("Ocupadas", ocupadas)
m3.metric("Libres", libres)

filtro_busqueda = st.text_input("🔍 Buscar Producto, Calibre o Lote (Resalta coincidencias):", "").strip().lower()

# --- GESTIÓN DE PESTAÑAS SEGÚN ROL ---
if rol in ["Administrador", "Operador de Cámara"]:
    tab1, tab2, tab3, tab4 = st.tabs(["🗺️ Layout Cámara", "📥 Ingreso Palet", "📤 Despacho / Embarque", "📊 Stock General"])
else:
    tab1, tab4 = st.tabs(["🗺️ Layout Cámara", "📊 Stock General"])

# --- TAB 1: LAYOUT VISUAL DE CÁMARA ---
with tab1:
    st.subheader(f"Distribución Física: {cam_sel}")
    st.caption("🟢 Verde = Libre | 🔴 Rojo = Ocupado | 🟡 Amarillo = Coincidencia de búsqueda")

    ocupadas_map = {}
    if not df_cam.empty and "posicion" in df_cam.columns and "estado" in df_cam.columns:
        for _, row in df_cam[df_cam["estado"].str.strip().str.capitalize() == "Ocupado"].iterrows():
            ocupadas_map[str(row["posicion"]).strip().upper()] = row

    niveles = ["C", "B", "A"]
    cols_num = 20
    cam_id_num = cam_sel.split()[-1].replace("0", "")

    for niv in niveles:
        cols_ui = st.columns([1] + [1] * cols_num)
        cols_ui[0].markdown(f"**Nivel {niv}**")
        for col_idx in range(1, cols_num + 1):
            pos_label = f"{niv}{col_idx}-C{cam_id_num}"
            btn_color = "🟢"
            hover_text = f"Pos: {pos_label} (Libre)"

            if pos_label in ocupadas_map:
                item = ocupadas_map[pos_label]
                prod = str(item.get("producto", ""))
                cal = str(item.get("calibre", ""))
                palet = str(item.get("codigo_palet", ""))
                cajas = item.get("cajas", "")

                hover_text = f"Palet: {palet} | {prod} ({cal}) | Cajas: {cajas}"

                if filtro_busqueda and (filtro_busqueda in prod.lower() or filtro_busqueda in cal.lower() or filtro_busqueda in palet.lower()):
                    btn_color = "🟡"
                else:
                    btn_color = "🔴"

            cols_ui[col_idx].button(f"{btn_color}", key=f"btn_{cam_sel}_{pos_label}", help=hover_text)

# --- TAB 2: INGRESO DE PALET ---
if rol in ["Administrador", "Operador de Cámara"]:
    with tab2:
        st.subheader("Registrar Nuevo Ingreso a Cámara")
        with st.form("form_ingreso", clear_on_submit=True):
            ci1, ci2 = st.columns(2)
            with ci1:
                in_camara = st.selectbox("Cámara de Destino", camaras_disponibles)
                in_posicion = st.text_input("Código de Posición (Ej: A1-C1, B5-C2)").strip().upper()
                in_codigo_palet = st.text_input("Código de Palet / Lote").strip()
                in_producto = st.text_input("Descripción del Producto").strip()
            with ci2:
                in_calibre = st.text_input("Calibre / Especificación").strip()
                in_cajas = st.number_input("Cantidad de Cajas / Sacos", min_value=1, step=1, value=40)
                in_peso = st.number_input("Peso Total (kg)", min_value=0.0, step=0.5, value=1000.0)
            
            btn_guardar_ingreso = st.form_submit_button("📥 Confirmar Ingreso y Guardar en Nube", use_container_width=True)

            if btn_guardar_ingreso:
                if not in_posicion or not in_codigo_palet or not in_producto:
                    st.error("Completa la posición, código de palet y producto para guardar.")
                else:
                    ws_inv = get_sheet("Inventario")
                    fecha_hoy = datetime.now().strftime("%Y-%m-%d %H:%M")
                    ws_inv.append_row([
                        in_camara, in_posicion, str(in_codigo_palet), in_producto,
                        in_calibre, str(in_cajas), str(in_peso), fecha_hoy, nombre, "Ocupado"
                    ])
                    registrar_log("INGRESO", in_camara, in_posicion, in_codigo_palet, in_producto, in_cajas, nombre)
                    st.success(f"Palet {in_codigo_palet} registrado con éxito en {in_posicion}.")
                    st.rerun()

# --- TAB 3: DESPACHO / EMBARQUE ---
if rol in ["Administrador", "Operador de Cámara"]:
    with tab3:
        st.subheader("Despacho / Salida de Palet")
        if df_inv.empty or len(df_inv[df_inv["estado"].str.strip().str.capitalize() == "Ocupado"]) == 0:
            st.info("No hay palets registrados en inventario para despachar.")
        else:
            df_ocupados = df_inv[df_inv["estado"].str.strip().str.capitalize() == "Ocupado"]
            opciones_despacho = [
                f"{row['codigo_palet']} | {row['camara']} - Pos: {row['posicion']} | {row['producto']} ({row['cajas']} cjs)"
                for _, row in df_ocupados.iterrows()
            ]
            seleccion = st.selectbox("Seleccione el Palet a Despachar:", opciones_despacho)

            if st.button("📤 Procesar Salida / Despacho", use_container_width=True):
                palet_sel = seleccion.split(" | ")[0].strip()
                ws_inv = get_sheet("Inventario")
                celda = ws_inv.find(palet_sel)
                
                if celda:
                    fila_num = celda.row
                    valores_fila = ws_inv.row_values(fila_num)
                    cam = valores_fila[0] if len(valores_fila) > 0 else ""
                    pos = valores_fila[1] if len(valores_fila) > 1 else ""
                    prod = valores_fila[3] if len(valores_fila) > 3 else ""
                    cjs = valores_fila[5] if len(valores_fila) > 5 else 0

                    ws_inv.update_cell(fila_num, 10, "Despachado")
                    registrar_log("DESPACHO", cam, pos, palet_sel, prod, cjs, nombre)
                    st.success(f"Palet {palet_sel} despachado correctamente.")
                    st.rerun()
                else:
                    st.error("No se encontró el registro en la hoja de cálculo.")

# --- TAB 4: STOCK GENERAL Y REPORTES ---
with tab4:
    st.subheader("Reporte General de Stock en Cámaras")
    if not df_inv.empty:
        df_stock = df_inv[df_inv["estado"].str.strip().str.capitalize() == "Ocupado"]
        st.dataframe(df_stock, use_container_width=True)

        if rol in ["Administrador", "Jefatura Auditoría"]:
            st.download_button(
                label="📥 Descargar Reporte Completo a CSV",
                data=df_stock.to_csv(index=False).encode("utf-8"),
                file_name=f"Reporte_Camaras_Frigosa_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
    else:
        st.info("Sin registros cargados.")
