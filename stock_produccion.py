import streamlit as st
import pandas as pd
from datetime import date

# ID del Google Sheet BD_PRODUCCION_ARCHI_001
SPREADSHEET_ID_PRODUCCION = "1cX-C1Lrgp8SznxDs-_cjiMN6DptNusCmNoNopxBmJlg"

def render_module(user, get_gspread_client):
    st.subheader("📊 Módulo 5: Control de Stock y Producción")
    st.caption(f"Usuario activo: {user.get('nombre_completo', user.get('usuario'))} | Conectado a: BD_PRODUCCION_ARCHI_001")

    # Obtener conexión cliente
    try:
        client = get_gspread_client()
        sh = client.open_by_key(SPREADSHEET_ID_PRODUCCION)
    except Exception as e:
        st.error(f"Error al conectar con Google Sheet: {e}")
        st.info("Verifica que diste permisos de Editor al correo del robot de servicio en la hoja BD_PRODUCCION_ARCHI_001.")
        return

    # Cargar catálogo de productos
    def obtener_catalogo():
        try:
            ws = sh.worksheet("stock")
            filas = ws.get_all_values()
            if len(filas) > 1:
                df = pd.DataFrame(filas[1:], columns=filas[0])
                df = df[df["CODIGO"].astype(str).str.strip() != ""]
                return df[["CODIGO", "PRESENTACION"]].to_dict("records")
        except Exception:
            pass
        return []

    catalogo = obtener_catalogo()
    opciones_prod = [f"{p['CODIGO']} - {p['PRESENTACION']}" for p in catalogo] if catalogo else ["-"]

    tab_entradas, tab_salidas, tab_stock, tab_inventario = st.tabs([
        "📥 Registro Entradas", "📤 Registro Salidas", "📈 Balance Stock Virtual", "📋 Inventario Físico"
    ])

    meses = ["ENERO", "FEBRERO", "MARZO", "ABRIL", "MAYO", "JUNIO", 
             "JULIO", "AGOSTO", "SETIEMBRE", "OCTUBRE", "NOVIEMBRE", "DICIEMBRE"]

    # --- TAB 1: ENTRADAS ---
    with tab_entradas:
        st.write("#### Ingreso a Túnel / Cámara")
        destino_ent = st.radio("Línea de Entrada:", ["entradas (Línea 1)", "entradas2 (Línea 2)"], horizontal=True)
        hoja_ent = "entradas" if "Línea 1" in destino_ent else "entradas2"

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

            btn_ent = st.form_submit_button("💾 Guardar Entrada")
            if btn_ent:
                cod, pres = prod_ent.split(" - ", 1) if " - " in prod_ent else ("", "")
                fila = [id_ent, str(fecha_ent), cod, pres, cant_ent, tunel_ent, placa_ent, mes_ent, subf_ent, lote_ent]
                try:
                    sh.worksheet(hoja_ent).append_row(fila)
                    st.success(f"✅ Entrada registrada en '{hoja_ent}'.")
                except Exception as ex:
                    st.error(f"Error al guardar: {ex}")

    # --- TAB 2: SALIDAS ---
    with tab_salidas:
        st.write("#### Despacho / Salidas")
        destino_sal = st.radio("Línea de Salida:", ["salidas (Línea 1)", "salidas2 (Línea 2)"], horizontal=True)
        hoja_sal = "salidas" if "Línea 1" in destino_sal else "salidas2"

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

            btn_sal = st.form_submit_button("📤 Guardar Salida")
            if btn_sal:
                cod_s, pres_s = prod_sal.split(" - ", 1) if " - " in prod_sal else ("", "")
                fila_sal = [mes_sal, str(fecha_sal), lote_sal, sudfa_sal, tipo_op, cod_s, pres_s, cant_sal, booking, cliente, pi, pais_dest, pais, contenedor]
                try:
                    sh.worksheet(hoja_sal).append_row(fila_sal)
                    st.success(f"✅ Salida registrada en '{hoja_sal}'.")
                except Exception as ex:
                    st.error(f"Error al guardar: {ex}")

    # --- TAB 3: STOCK VIRTUAL ---
    with tab_stock:
        st.write("#### Balance Virtual de Stock")
        hoja_stk_sel = st.radio("Seleccione hoja:", ["stock (Línea 1)", "stock2 (Línea 2)"], horizontal=True)
        nombre_stk = "stock" if "Línea 1" in hoja_stk_sel else "stock2"

        if st.button("🔄 Refrescar"):
            st.rerun()

        try:
            filas_stk = sh.worksheet(nombre_stk).get_all_values()
            if len(filas_stk) > 1:
                df_stk = pd.DataFrame(filas_stk[1:], columns=filas_stk[0])
                st.dataframe(df_stk, use_container_width=True)
            else:
                st.info("Sin registros en esta hoja.")
        except Exception as ex:
            st.error(f"Error al leer datos: {ex}")

    # --- TAB 4: INVENTARIO FÍSICO ---
    with tab_inventario:
        st.write("#### Toma de Inventario Físico")
        with st.form("form_inv", clear_on_submit=True):
            i1, i2 = st.columns(2)
            with i1:
                id_inv = st.text_input("ID")
                fecha_inv = st.date_input("Fecha Conteo", value=date.today(), key="i_fecha")
                prod_inv = st.selectbox("Producto contado", opciones_prod, key="i_prod")
            with i2:
                cant_inv = st.number_input("Cantidad Física", min_value=0.0, step=0.01, format="%.2f", key="i_cant")
                tunel_inv = st.text_input("Túnel", key="i_tun")
                placas_inv = st.text_input("Placas", key="i_pla")
                obs_inv = st.text_area("Observaciones")

            btn_inv = st.form_submit_button("📋 Registrar Conteo")
            if btn_inv:
                cod_i, pres_i = prod_inv.split(" - ", 1) if " - " in prod_inv else ("", "")
                fila_inv = [id_inv, str(fecha_inv), cod_i, pres_i, cant_inv, tunel_inv, placas_inv, obs_inv]
                try:
                    sh.worksheet("INVENTARIADO_FISICO").append_row(fila_inv)
                    st.success("✅ Inventario físico guardado.")
                except Exception as ex:
                    st.error(f"Error al guardar: {ex}")
              
