import streamlit as st
import pandas as pd
from datetime import date

# ID del Google Sheet BD_PRODUCCION_ARCHI_001
SPREADSHEET_ID_PRODUCCION = "1cX-C1Lrgp8SznxDs-_cjiMN6DptNusCmNoNopxBmJlg"

def render_stock_produccion(get_gspread_client):
    st.title("📦 Control de Stock y Producción")

    # Conectar al libro usando el cliente global
    client = get_gspread_client()
    sh = client.open_by_key(SPREADSHEET_ID_PRODUCCION)

    # Carga de catálogo de productos desde la hoja 'stock'
    @st.cache_data(ttl=60)
    def cargar_catalogo():
        ws = sh.worksheet("stock")
        df = pd.DataFrame(ws.get_all_records())
        return df[["CODIGO", "PRESENTACION"]].dropna().to_dict('records')

    try:
        productos = cargar_catalogo()
        opciones_prod = [f"{p['CODIGO']} - {p['PRESENTACION']}" for p in productos if p['CODIGO'] != '']
    except Exception as e:
        st.error(f"Error al cargar catálogo de productos: {e}")
        opciones_prod = []

    # Pestañas de operación
    tab_entradas, tab_salidas, tab_stock, tab_inventario = st.tabs([
        "📥 Entradas", "📤 Salidas", "📊 Stock Virtual", "📋 Inventario Físico"
    ])

    meses = ["ENERO", "FEBRERO", "MARZO", "ABRIL", "MAYO", "JUNIO", 
             "JULIO", "AGOSTO", "SETIEMBRE", "OCTUBRE", "NOVIEMBRE", "DICIEMBRE"]

    # -----------------------------
    # 1. ENTRADAS
    # -----------------------------
    with tab_entradas:
        st.subheader("Registro de Ingresos a Cámara")
        tipo_ent = st.radio("Destino de Entrada:", ["entradas (Línea 1)", "entradas2 (Línea 2)"], horizontal=True)
        hoja_ent = "entradas" if "Línea 1" in tipo_ent else "entradas2"

        with st.form("form_entradas", clear_on_submit=True):
            col1, col2, col3 = st.columns(3)
            with col1:
                id_ent = st.text_input("ID")
                fecha_ent = st.date_input("Fecha", value=date.today())
                prod_ent = st.selectbox("Código / Presentación", opciones_prod)
            with col2:
                cant_ent = st.number_input("Cantidad", min_value=0.0, step=0.01, format="%.2f")
                tunel_ent = st.text_input("Túnel")
                placa_ent = st.text_input("Placa")
            with col3:
                mes_ent = st.selectbox("Mes", meses)
                subf_ent = st.text_input("Subfamilia")
                lote_ent = st.text_input("Lote")

            if st.form_submit_button("💾 Guardar Entrada"):
                cod = prod_ent.split(" - ")[0]
                pres = prod_ent.split(" - ")[1]
                fila = [id_ent, str(fecha_ent), cod, pres, cant_ent, tunel_ent, placa_ent, mes_ent, subf_ent, lote_ent]
                sh.worksheet(hoja_ent).append_row(fila)
                st.success(f"Entrada agregada exitosamente en '{hoja_ent}'.")

    # -----------------------------
    # 2. SALIDAS
    # -----------------------------
    with tab_salidas:
        st.subheader("Registro de Despacho / Embarques")
        tipo_sal = st.radio("Destino de Salida:", ["salidas (Línea 1)", "salidas2 (Línea 2)"], horizontal=True)
        hoja_sal = "salidas" if "Línea 1" in tipo_sal else "salidas2"

        with st.form("form_salidas", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            with c1:
                mes_sal = st.selectbox("Mes", meses, key="s_mes")
                fecha_sal = st.date_input("Fecha Embarque", value=date.today(), key="s_fecha")
                lote_sal = st.text_input("Lote", key="s_lote")
                sudfa_sal = st.text_input("SUDFA")
                tipo_op = st.text_input("Tipo")
            with c2:
                prod_sal = st.selectbox("Producto", opciones_prod, key="s_prod")
                cant_sal = st.number_input("Cantidad", min_value=0.0, step=0.01, format="%.2f", key="s_cant")
                booking = st.text_input("Booking")
                cliente = st.text_input("Cliente")
            with c3:
                pi = st.text_input("P.I.")
                pais_dest = st.text_input("País Destino")
                pais = st.text_input("País")
                contenedor = st.text_input("Contenedor")

            if st.form_submit_button("📤 Guardar Salida"):
                cod_s = prod_sal.split(" - ")[0]
                pres_s = prod_sal.split(" - ")[1]
                fila_sal = [mes_sal, str(fecha_sal), lote_sal, sudfa_sal, tipo_op, cod_s, pres_s, cant_sal, booking, cliente, pi, pais_dest, pais, contenedor]
                sh.worksheet(hoja_sal).append_row(fila_sal)
                st.success(f"Salida registrada exitosamente en '{hoja_sal}'.")

    # -----------------------------
    # 3. STOCK VIRTUAL
    # -----------------------------
    with tab_stock:
        st.subheader("Balance de Stock Virtual")
        hoja_ver = st.radio("Ver hoja:", ["stock (Línea 1)", "stock2 (Línea 2)"], horizontal=True)
        nombre_h = "stock" if "Línea 1" in hoja_ver else "stock2"
        
        if st.button("🔄 Refrescar Datos"):
            cargar_catalogo.clear()

        df_stock = pd.DataFrame(sh.worksheet(nombre_h).get_all_records())
        st.dataframe(df_stock, use_container_width=True)

    # -----------------------------
    # 4. INVENTARIO FÍSICO
    # -----------------------------
    with tab_inventario:
        st.subheader("Toma de Inventario Físico")
        with st.form("form_inv", clear_on_submit=True):
            i1, i2 = st.columns(2)
            with i1:
                id_inv = st.text_input("ID")
                fecha_inv = st.date_input("Fecha Conteo", value=date.today(), key="i_fecha")
                prod_inv = st.selectbox("Producto", opciones_prod, key="i_prod")
            with i2:
                cant_inv = st.number_input("Cantidad Física", min_value=0.0, step=0.01, format="%.2f", key="i_cant")
                tunel_inv = st.text_input("Túnel", key="i_tun")
                placas_inv = st.text_input("Placas", key="i_pla")
                obs_inv = st.text_area("Observación")

            if st.form_submit_button("📋 Guardar Conteo"):
                cod_i = prod_inv.split(" - ")[0]
                pres_i = prod_inv.split(" - ")[1]
                fila_i = [id_inv, str(fecha_inv), cod_i, pres_i, cant_inv, tunel_inv, placas_inv, obs_inv]
                sh.worksheet("INVENTARIADO_FISICO").append_row(fila_i)
                st.success("Inventario físico registrado correctamente.")
