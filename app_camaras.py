import streamlit as st
import pandas as pd
import os

# Configuración de pantalla
st.set_page_config(page_title="WMS Frigosa - Cámaras", page_icon="❄️", layout="wide")

EXCEL_PATH = "POSICIONAMIENTO FISICO DE PRODUCTO CAMARAS FRIGOSA SAC 2025.xlsx"

# Listas desplegables estándar
LISTA_PRODUCTOS = [
    "ALETA FRESCA",
    "ALETA CONGELADA",
    "TRONCO",
    "LOMO",
    "FILETE",
    "TENTÁCULOS",
    "OTROS"
]

LISTA_CALIBRES = [
    "0-300",
    "300-500",
    "500-1000",
    "1000-2000",
    "2000+",
    "ESTÁNDAR"
]

# Cargar o inicializar datos asegurando tipo texto (object)
def cargar_datos():
    if not os.path.exists(EXCEL_PATH):
        posiciones = []
        # Cámara 01: 60 columnas
        for i in list(range(1, 31)) + list(range(31, 61)):
            for nivel in ['A', 'B', 'C']:
                posiciones.append({
                    'Posicion': f"{nivel}{i}-C1",
                    'Camara': 'Camara 01',
                    'Nivel': nivel,
                    'Columna': i,
                    'Estado': 'Libre',
                    'Producto': '',
                    'Calibre': '',
                    'Sacos': 0,
                    'Contenedor': ''
                })
        # Cámara 02: 17 columnas
        for i in range(1, 18):
            for nivel in ['A', 'B', 'C']:
                posiciones.append({
                    'Posicion': f"{nivel}{i}-C2",
                    'Camara': 'Camara 02',
                    'Nivel': nivel,
                    'Columna': i,
                    'Estado': 'Libre',
                    'Producto': '',
                    'Calibre': '',
                    'Sacos': 0,
                    'Contenedor': ''
                })
        df = pd.DataFrame(posiciones)
        df.to_excel(EXCEL_PATH, sheet_name='Ubicaciones', index=False)
        return df
    else:
        df_cargado = pd.read_excel(EXCEL_PATH, sheet_name='Ubicaciones')
        # Limpieza forzada para evitar errores de float64
        df_cargado['Producto'] = df_cargado['Producto'].fillna('').astype(str)
        df_cargado['Calibre'] = df_cargado['Calibre'].fillna('').astype(str)
        df_cargado['Contenedor'] = df_cargado['Contenedor'].fillna('').astype(str)
        df_cargado['Estado'] = df_cargado['Estado'].fillna('Libre').astype(str)
        df_cargado['Sacos'] = pd.to_numeric(df_cargado['Sacos'], errors='coerce').fillna(0).astype(int)
        return df_cargado

def guardar_datos(df):
    df.to_excel(EXCEL_PATH, sheet_name='Ubicaciones', index=False)

df = cargar_datos()

# ----------------- BARRA SUPERIOR / FILTROS -----------------
st.title("❄️ Control de Cámaras - Frigosa")

camara_sel = st.selectbox("Seleccionar Cámara:", ["Camara 01", "Camara 02"])
df_cam = df[df['Camara'] == camara_sel]

# Indicadores
total_pos = len(df_cam)
ocupadas = len(df_cam[df_cam['Estado'] == 'Ocupado'])
libres = total_pos - ocupadas
porc_ocupacion = int((ocupadas / total_pos) * 100) if total_pos > 0 else 0

col1, col2, col3 = st.columns(3)
col1.metric("Ocupación", f"{porc_ocupacion}%")
col2.metric("Ocupadas", ocupadas)
col3.metric("Libres", libres)

buscar_prod = st.text_input("🔍 Buscar Producto o Calibre (Resalta en amarillo):", "").strip().lower()

# ----------------- TABS PRINCIPALES -----------------
tab_mapa, tab_ingreso, tab_salida, tab_stock = st.tabs(["🗺️ Layout Cámara", "📥 Ingreso Palet", "📤 Despacho / Embarque", "📊 Stock Total"])

# --- TAB 1: LAYOUT ---
with tab_mapa:
    st.subheader(f"Distribución Física: {camara_sel}")
    st.caption("🟩 Verde = Libre | 🟥 Rojo = Ocupado | 🟨 Amarillo = Coincidencia")
    
    columnas_disponibles = sorted(df_cam['Columna'].unique())
    niveles = ['C', 'B', 'A']
    
    tabla_visual = []
    for niv in niveles:
        fila = {'Nivel': f"Nivel {niv}"}
        for col in columnas_disponibles:
            pos_id = f"{niv}{col}-C{'1' if camara_sel == 'Camara 01' else '2'}"
            item = df_cam[df_cam['Posicion'] == pos_id]
            
            if not item.empty:
                estado = item.iloc[0]['Estado']
                prod = str(item.iloc[0]['Producto'])
                cal = str(item.iloc[0]['Calibre'])
                sacos = item.iloc[0]['Sacos']
                
                es_busqueda = buscar_prod != "" and (buscar_prod in prod.lower() or buscar_prod in cal.lower())
                
                if es_busqueda:
                    icono = f"🟨 [{pos_id}] {prod[:6]} ({sacos})"
                elif estado == "Ocupado":
                    icono = f"🟥 [{pos_id}] {prod[:6]} ({sacos})"
                else:
                    icono = f"🟩 [{pos_id}]"
                fila[f"Col {col}"] = icono
            else:
                fila[f"Col {col}"] = "⬜"
        tabla_visual.append(fila)
        
    df_layout = pd.DataFrame(tabla_visual).set_index('Nivel')
    st.dataframe(df_layout, width='stretch')

# --- TAB 2: INGRESO DE PALET ---
with tab_ingreso:
    st.subheader(f"📥 Registro de Ingreso - {camara_sel}")
    with st.form("form_ingreso"):
        # Muestra solo las posiciones libres de la cámara seleccionada arriba
        pos_libres = df_cam[df_cam['Estado'] == 'Libre']['Posicion'].tolist()
        pos_destino = st.selectbox("Posición Destino (Solo Libres):", pos_libres if pos_libres else ["Sin posiciones libres"])
        
        # Desplegables directos
        producto = st.selectbox("Producto:", LISTA_PRODUCTOS)
        calibre = st.selectbox("Calibre:", LISTA_CALIBRES)
        sacos = st.number_input("Cantidad de Sacos / Cajas:", min_value=1, value=50, step=1)
        
        btn_guardar = st.form_submit_button("✅ Guardar Ingreso")
        
        if btn_guardar:
            if pos_destino and pos_destino != "Sin posiciones libres":
                idx = df[df['Posicion'] == pos_destino].index[0]
                df.at[idx, 'Estado'] = 'Ocupado'
                df.at[idx, 'Producto'] = str(producto)
                df.at[idx, 'Calibre'] = str(calibre)
                df.at[idx, 'Sacos'] = int(sacos)
                guardar_datos(df)
                st.success(f"Palet ingresado con éxito en {pos_destino}")
                st.rerun()
            else:
                st.error("No hay posiciones libres disponibles en esta cámara.")

# --- TAB 3: DESPACHO ---
with tab_salida:
    st.subheader(f"📤 Registrar Salida - {camara_sel}")
    pos_ocupadas = df_cam[df_cam['Estado'] == 'Ocupado']['Posicion'].tolist()
    
    if not pos_ocupadas:
        st.info(f"No hay posiciones ocupadas en {camara_sel}.")
    else:
        with st.form("form_despacho"):
            pos_a_liberar = st.selectbox("Seleccionar Posición a Retirar:", pos_ocupadas)
            nro_contenedor = st.text_input("Nº de Contenedor / Booking:", placeholder="Ej. MEDU123456-7")
            btn_despachar = st.form_submit_button("🚚 Confirmar Embarque y Liberar Posición")
            
            if btn_despachar:
                idx = df[df['Posicion'] == pos_a_liberar].index[0]
                prod_retirado = df.at[idx, 'Producto']
                df.at[idx, 'Estado'] = 'Libre'
                df.at[idx, 'Producto'] = ''
                df.at[idx, 'Calibre'] = ''
                df.at[idx, 'Sacos'] = 0
                guardar_datos(df)
                st.success(f"Posición {pos_a_liberar} liberada ({prod_retirado} enviado al contenedor {nro_contenedor}).")
                st.rerun()

# --- TAB 4: STOCK TOTAL ---
with tab_stock:
    st.subheader("📊 Inventario General de Cámaras")
    df_stock = df[df['Estado'] == 'Ocupado'][['Camara', 'Posicion', 'Producto', 'Calibre', 'Sacos']]
    if not df_stock.empty:
        st.dataframe(df_stock, width='stretch')
        st.metric("Total Sacos Almacenados (Todas las cámaras)", int(df_stock['Sacos'].sum()))
    else:
        st.write("No hay stock registrado actualmente.")