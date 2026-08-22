import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="WMS Frigosa - Control de Cámaras y Asistencia",
    page_icon="❄️",
    layout="wide"
)

# ID directo de Google Sheets
SPREADSHEET_ID = "1Yi5OwKDnidykEFG7d2xSEjBCwl2nYFKOU7ZX86nlroU"

# Listas maestras para selección rápida
LISTA_PRODUCTOS = [
    "Aleta Fresca",
    "Tubo de Pota",
    "Tentáculo / Rejo",
    "Pota Entera",
    "Filete de Pota",
    "Anillas / Rabas",
    "Aleta Congelada",
    "Bloque de Pota",
    "Otro (Escribir)"
]

LISTA_CALIBRES = [
    "0-300 gr",
    "300-500 gr",
    "500-1000 gr",
    "1000 UP",
    "1000-2000 gr",
    "2000-3000 gr",
    "3000 UP",
    "S/C (Sin Calibre)",
    "Otro (Escribir)"
]

# --- CONEXIÓN A GOOGLE SHEETS ---
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

# --- CÁLCULO DE HORAS EXTRAS SEGÚN REGLA RR.HH. ---
def calcular_horas_extras(hora_salida_dt, modo_turno):
    fmt = "%H:%M"
    hora_str = hora_salida_dt.strftime(fmt)
    h_salida = datetime.strptime(hora_str, fmt)
    
    horas_extras_totales = 0.0
    horas_pagadas = 0.0
    horas_bolsa = 0.0
    
    if modo_turno == "Sin Producción":
        limite_normal = datetime.strptime("18:00", fmt)
        if h_salida > limite_normal:
            horas_extras_totales = (h_salida - limite_normal).seconds / 3600.0
            horas_bolsa = horas_extras_totales
            
    elif modo_turno == "Con Producción":
        limite_produccion = datetime.strptime("20:00", fmt)
        if h_salida > limite_produccion:
            horas_extras_totales = (h_salida - limite_produccion).seconds / 3600.0
            if horas_extras_totales >= 1.0:
                horas_pagadas = 1.0
                horas_bolsa = horas_extras_totales - 1.0
            else:
                horas_pagadas = horas_extras_totales
                horas_bolsa = 0.0
                
    return round(horas_extras_totales, 2), round(horas_pagadas, 2), round(horas_bolsa, 2)

# --- GESTIÓN DE SESIÓN Y LOGIN ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_info = None

def login_form():
    st.markdown("<h2 style='text-align: center; color: #1E3D59;'>❄️ ECAPRO / WMS Frigosa - Acceso</h2>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        with st.form("login_form"):
            usuario = st.text_input("Usuario").strip().lower()
            # Ahora usa codigo_personal en vez de pin
            codigo_ingresado = st.text_input("Código de Personal / Clave", type="password").strip()
            submit = st.form_submit_button("Ingresar al Sistema", use_container_width=True)
            
            if submit:
                if not usuario or not codigo_ingresado:
                    st.warning("Por favor ingresa usuario y código de personal.")
                    return
                try:
                    df_users = cargar_datos("Usuarios")
                    if df_users.empty:
                        st.error("No se encontraron registros en la tabla de Usuarios.")
                        return
                    
                    df_users["usuario"] = df_users["usuario"].astype(str).str.strip().str.lower()
                    df_users["codigo_personal"] = df_users["codigo_personal"].astype(str).str.strip()
                    df_users["estado"] = df_users["estado"].astype(str).str.strip().str.capitalize()

                    match = df_users[(df_users["usuario"] == usuario) & (df_users["codigo_personal"] == codigo_ingresado) & (df_users["estado"] == "Activo")]
                    
                    if not match.empty:
                        user_data = match.iloc[0].to_dict()
                        st.session_state.logged_in = True
                        st.session_state.user_info = user_data
                        st.rerun()
                    else:
                        st.error("Usuario o Código incorrecto, o usuario inactivo.")
                except Exception as e:
                    st.error(f"Error de conexión: {e}")

if not st.session_state.logged_in:
    login_form()
    st.stop()

# --- DATOS DEL USUARIO AUTENTICADO ---
user = st.session_state.user_info
rol = user.get("rol", "Visualizador")
nombre = user.get("nombre_completo", user.get("usuario"))
codigo_per = user.get("codigo_personal", "P000")

# --- BARRA LATERAL ---
with st.sidebar:
    st.markdown(f"### 👤 **{nombre}**")
    st.markdown(f"**Código:** `{codigo_per}`")
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

st.title("❄️ ECAPRO - Gestión Integral Frigosa")

# --- DEFINICIÓN DE PESTAÑAS SEGÚN ROL ---
roles_operativos = ["Administrador", "Operador de Cámara", "SUPERVISOR DE PRODUCCION", "JEFE DE TURNO"]

if rol in roles_operativos:
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🗺️ Layout Cámara", 
        "📥 Ingreso Palet", 
        "📤 Despacho / Embarque", 
        "📊 Stock General",
        "⏱️ Control Asistencia"
    ])
else:
    tab1, tab4, tab5 = st.tabs([
        "🗺️ Layout Cámara", 
        "📊 Stock General",
        "⏱️ Control Asistencia"
    ])

camaras_disponibles = ["Camara 01", "Camara 02", "Camara 03"]

# --- TAB 1: LAYOUT VISUAL DE CÁMARA ---
with tab1:
    cam_sel = st.selectbox("Seleccionar Cámara:", camaras_disponibles, key="select_cam_layout")
    df_cam = df_inv[df_inv["camara"] == cam_sel] if not df_inv.empty and "camara" in df_inv.columns else pd.DataFrame()

    total_posiciones = 180
    ocupadas = len(df_cam[df_cam["estado"].str.strip().str.capitalize() == "Ocupado"]) if not df_cam.empty and "estado" in df_cam.columns else 0
    libres = max(0, total_posiciones - ocupadas)
    pct_ocupacion = (ocupadas / total_posiciones) * 100 if total_posiciones > 0 else 0

    m1, m2, m3 = st.columns(3)
    m1.metric("Ocupación", f"{pct_ocupacion:.1f}%")
    m2.metric("Ocupadas", ocupadas)
    m3.metric("Libres", libres)

    filtro_busqueda = st.text_input("🔍 Buscar Producto, Calibre o Lote:", "").strip().lower()

    st.subheader(f"Distribución Física: {cam_sel}")
    st.caption("🟩 Verde = Libre | 🟥 Rojo = Ocupado | 🟨 Amarillo = Coincidencia de búsqueda")

    ocupadas_map = {}
    if not df_cam.empty and "posicion" in df_cam.columns and "estado" in df_cam.columns:
        for _, row in df_cam[df_cam["estado"].str.strip().str.capitalize() == "Ocupado"].iterrows():
            pos_key = str(row["posicion"]).strip().upper()
            ocupadas_map[pos_key] = row

    niveles = ["C", "B", "A"]
    cols_num = 20
    cam_id_num = cam_sel.split()[-1].replace("0", "")

    for niv in niveles:
        cols_ui = st.columns([1] + [1] * cols_num)
        cols_ui[0].markdown(f"**Nivel {niv}**")
        for col_idx in range(1, cols_num + 1):
            pos_label = f"{niv}{col_idx}-C{cam_id_num}"
            
            if pos_label in ocupadas_map:
                item = ocupadas_map[pos_label]
                prod = str(item.get("producto", "")).strip().upper()
                cal = str(item.get("calibre", "")).strip()
                palet = str(item.get("codigo_palet", "")).strip()
                cajas = item.get("cajas", "")

                btn_label = f"🟥 [{pos_label}]\n{prod}"
                hover_text = f"📍 Posición: {pos_label}\n📦 Palet: {palet}\n🐟 Producto: {prod} ({cal})\n📊 Cajas: {cajas}"

                if filtro_busqueda and (filtro_busqueda in prod.lower() or filtro_busqueda in cal.lower() or filtro_busqueda in palet.lower()):
                    btn_label = f"🟨 [{pos_label}]\n{prod}"
            else:
                btn_label = f"🟩 [{pos_label}]"
                hover_text = f"Posición: {pos_label} (Libre)"

            cols_ui[col_idx].button(btn_label, key=f"btn_{cam_sel}_{pos_label}", help=hover_text)

# --- TAB 2: INGRESO DE PALET ---
if rol in roles_operativos:
    with tab2:
        st.subheader("Registrar Nuevo Ingreso a Cámara")
        with st.form("form_ingreso", clear_on_submit=True):
            ci1, ci2 = st.columns(2)
            with ci1:
                in_camara = st.selectbox("Cámara de Destino", camaras_disponibles)
                
                col_pos1, col_pos2 = st.columns(2)
                with col_pos1:
                    nivel_sel = st.selectbox("Nivel", ["Nivel A (Piso)", "Nivel B (Medio)", "Nivel C (Alto)"])
                with col_pos2:
                    columna_sel = st.selectbox("Columna", [f"Col {i}" for i in range(1, 21)])
                
                n_letra = nivel_sel.split()[1]
                c_num = columna_sel.split()[1]
                cam_n = in_camara.split()[-1].replace("0", "")
                pos_calculada = f"{n_letra}{c_num}-C{cam_n}"
                
                in_posicion = st.text_input("Código de Posición Asignado:", value=pos_calculada)
                in_codigo_palet = st.text_input("Código de Palet / Lote (Ej: PAL-2026-001)").strip()

            with ci2:
                prod_sel = st.selectbox("Producto:", LISTA_PRODUCTOS)
                in_producto = st.text_input("Especifique el Producto:").strip() if prod_sel == "Otro (Escribir)" else prod_sel

                cal_sel = st.selectbox("Calibre / Especificación:", LISTA_CALIBRES)
                in_calibre = st.text_input("Especifique el Calibre:").strip() if cal_sel == "Otro (Escribir)" else cal_sel

                in_cajas = st.number_input("Cantidad de Cajas / Sacos", min_value=1, step=1, value=40)
                in_peso = st.number_input("Peso Total (kg)", min_value=0.0, step=0.5, value=1000.0)
            
            btn_guardar_ingreso = st.form_submit_button("📥 Confirmar Ingreso y Guardar", use_container_width=True)

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
if rol in roles_operativos:
    with tab3:
        st.subheader("Despacho / Salida de Palet")
        if df_inv.empty or len(df_inv[df_inv["estado"].str.strip().str.capitalize() == "Ocupado"]) == 0:
            st.info("No hay palets registrados en inventario para despachar.")
        else:
            df_ocupados = df_inv[df_inv["estado"].str.strip().str.capitalize() == "Ocupado"]
            opciones_despacho = [
                f"{row['codigo_palet']} | {row['camara']} - Pos: {row['posicion']} | {row['producto']} ({row.get('calibre', '')}) - {row['cajas']} cjs"
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

# --- TAB 5: CONTROL DE ASISTENCIA Y HORAS EXTRAS ---
with tab5:
    st.subheader("⏱️ Registro de Asistencia y Horas Extras")
    st.markdown(f"Colaborador: **{nombre}** | Código: `{codigo_per}` | Rol: `{rol}`")
    
    col_t1, col_t2 = st.columns(2)
    with col_t1:
        modo_turno = st.selectbox("Modalidad del Turno de Hoy:", ["Sin Producción", "Con Producción"], key="asist_modo_turno")
    with col_t2:
        fecha_actual_str = datetime.now().strftime("%Y-%m-%d")
        st.info(f"📅 Fecha actual del sistema: **{fecha_actual_str}**")
        
    st.markdown("---")
    
    col_btn1, col_btn2 = st.columns(2)
    
    with col_btn1:
        st.markdown("#### 📥 Ingreso Diario")
        if st.button("Marcar Mi Hora de Entrada", use_container_width=True):
            try:
                ws_asist = get_sheet("Asistencia_Personal")
                hora_in = datetime.now().strftime("%H:%M")
                id_registro = f"REG-{datetime.now().strftime('%y%m%d%H%M%S')}"
                
                ws_asist.append_row([
                    id_registro, codigo_per, fecha_actual_str, hora_in, "", "0", "", "Pendiente", ""
                ])
                st.success(f"✅ ¡Entrada registrada con éxito a las {hora_in} hrs!")
            except Exception as e:
                st.error(f"Error al guardar entrada: {e}")
                
    with col_btn2:
        st.markdown("#### 📤 Salida Diaria")
        ahora_dt = datetime.now()
        hora_out_str = ahora_dt.strftime("%H:%M")
        
        he_tot, h_pag, h_bolsa = calcular_horas_extras(ahora_dt, modo_turno)
        
        if he_tot > 0:
            st.warning(f"⚠️ Se detectaron **{he_tot} hrs extras** (Pagadas: {h_pag}h | Bolsa: {h_bolsa}h).")
            obs_texto = st.text_input("Observación obligatoria del sobretiempo:", key="obs_input_he")
            
            if st.button("Confirmar Salida con Horas Extras", use_container_width=True):
                if not obs_texto.strip():
                    st.error("❌ La observación es obligatoria cuando se generan horas extras.")
                else:
                    try:
                        ws_asist = get_sheet("Asistencia_Personal")
                        id_registro = f"REG-{datetime.now().strftime('%y%m%d%H%M%S')}"
                        
                        ws_asist.append_row([
                            id_registro, codigo_per, fecha_actual_str, "08:00", hora_out_str, str(he_tot), obs_texto, "Pendiente", ""
                        ])
                        st.success(f"✅ Salida registrada a las {hora_out_str}. Horas extras enviadas a revisión.")
                    except Exception as e:
                        st.error(f"Error al guardar salida: {e}")
        else:
            if st.button("Marcar Salida Normal", use_container_width=True):
                try:
                    ws_asist = get_sheet("Asistencia_Personal")
                    id_registro = f"REG-{datetime.now().strftime('%y%m%d%H%M%S')}"
                    
                    ws_asist.append_row([
                        id_registro, codigo_per, fecha_actual_str, "08:00", hora_out_str, "0", "Jornada Regular", "Completado", ""
                    ])
                    st.success(f"✅ Salida regular registrada a las {hora_out_str} hrs.")
                except Exception as e:
                    st.error(f"Error al guardar salida: {e}")
