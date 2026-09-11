import streamlit as st
import pandas as pd
from datetime import date

# URL directa del Google Sheet
URL_PRODUCCION = "https://docs.google.com/spreadsheets/d/1cX-C1Lrgp8SznxDs-_cjiMN6DptNusCmNoNopxBmJlg/edit"

# 1. Catálogo Línea 1 (entradas / salidas)
CATALOGO_LINEA_1 = [
    {"CODIGO": "FRG002", "PRESENTACION": "ALETA FRESCA DE POTA CONGELADA 300 g/pza - 500 g/pza"},
    {"CODIGO": "FRG003", "PRESENTACION": "ALETA FRESCA DE POTA CONGELADA 500 g/pza - 1000 g/pza"},
    {"CODIGO": "FRG004", "PRESENTACION": "ALETA FRESCA DE POTA CONGELADA 1000 g/pza - UP"},
    {"CODIGO": "FRG034", "PRESENTACION": "ALETA FRESCA DE POTA CONGELADA 1000 g/pza - CV"},
    {"CODIGO": "FRG006", "PRESENTACION": "ALETA PRECOCIDA DE POTA CONGELADA 300 g/pza - UP"},
    {"CODIGO": "FRG038", "PRESENTACION": "ANILLAS BLANCAS DE POTA CONGELADA S/M S/T"},
    {"CODIGO": "FRG041", "PRESENTACION": "BOTONES BLANCOS DE POTA CONGELADA S/M S/T"},
    {"CODIGO": "FRG056", "PRESENTACION": "CONOS DE POTA CONGELADA"},
    {"CODIGO": "FRG050", "PRESENTACION": "FILETE FRESCO DE POTA CONGELADA S/PIEL S/M S/T 2000 g/pza - 4000 g/pza"},
    {"CODIGO": "FRG051", "PRESENTACION": "FILETE FRESCO DE POTA CONGELADA S/PIEL C/M C/T 500 g/pza - 1000 g/pz"},
    {"CODIGO": "FRG012", "PRESENTACION": "FILETE FRESCO DE POTA CONGELADA S/PIEL C/M C/T 1000 g/pza - 2000 g/pza"},
    {"CODIGO": "FRG013", "PRESENTACION": "FILETE FRESCO DE POTA CONGELADA S/PIEL C/M C/T 2000 g/pza - 4000 g/pza"},
    {"CODIGO": "FRG017", "PRESENTACION": "FILETE PRECOCIDO DE POTA CONGELADA 7mm - 10 mm"},
    {"CODIGO": "FRG046", "PRESENTACION": "FILETE PRECOCIDO DE POTA CONGELADA LADO PANZA 7mm - 10 mm"},
    {"CODIGO": "FRG047", "PRESENTACION": "FILETE PRECOCIDO DE POTA CONGELADA LADO MEMBRANA 7mm - 10 mm"},
    {"CODIGO": "FRG048", "PRESENTACION": "FILETE PRECOCIDO DE POTA CONGELADA LADO PANZA 8 mm - 14 mm"},
    {"CODIGO": "FRG057", "PRESENTACION": "FILETE PRECOCIDO DE POTA CONGELADA LADO MEMBRANA 8 mm - 14 mm"},
    {"CODIGO": "FRG058", "PRESENTACION": "DESHILACHADO SAZONADO DE POTA CONGELADA -F1"},
    {"CODIGO": "FRG060", "PRESENTACION": "DESHILACHADO SAZONADO DE POTA CONGELADA-F2"},
    {"CODIGO": "FRG018", "PRESENTACION": "FILETE PRECOCIDO DE POTA CONGELADA 10mm - 14 mm"},
    {"CODIGO": "FRG019", "PRESENTACION": "NUCAS DE POTA CONGELADA 100 g/pza - 300 g/pza"},
    {"CODIGO": "FRG020", "PRESENTACION": "NUCAS DE POTA CONGELADA 300 g/pza - 500 g/pza"},
    {"CODIGO": "FRG021", "PRESENTACION": "NUCAS DE POTA CONGELADA 500g/pza -UP"},
    {"CODIGO": "FRG090", "PRESENTACION": "NUCAS DE POTA CONGELADA 0 -50 g/pza"},
    {"CODIGO": "FRG022", "PRESENTACION": "RECORTE PRECOCIDO DE POTA CONGELADA"},
    {"CODIGO": "FRG039", "PRESENTACION": "RECORTE FRESCO BLANCO DE POTA CONGELADA S/M S/T"},
    {"CODIGO": "FRG023", "PRESENTACION": "REPRODUCTOR DE POTA CONGELADA S/PUNTA S/U S/V MAYOR A 50 cm"},
    {"CODIGO": "FRG024", "PRESENTACION": "REPRODUCTOR DE POTA CONGELADA S/PUNTA S/U S/V MENOR A 50 cm"},
    {"CODIGO": "FRG062", "PRESENTACION": "TENTACULO BAILARINA DE POTA CONGELADA C/U C/V 300 g/pza - 500 g/pza"},
    {"CODIGO": "FRG027", "PRESENTACION": "TENTACULO BAILARINA DE POTA CONGELADA C/U C/V 500 g/pza - 1000 g/pza"},
    {"CODIGO": "FRG054", "PRESENTACION": "TENTACULO BAILARINA DE POTA CONGELADA S/U S/V 300 g/pza - 500 g/pza"},
    {"CODIGO": "FRG055", "PRESENTACION": "TENTACULO BAILARINA DE POTA CONGELADA S/U S/V 2000 g/pza - 3000 g/pza"},
    {"CODIGO": "FRG030", "PRESENTACION": "TENTACULO BAILARINA DE POTA CONGELADA S/U S/V 1000g /pza-UP"}
]

# 2. Catálogo Línea 2 (entradas2 / salidas2)
CATALOGO_LINEA_2 = [
    {"CODIGO": "L2-BOTON", "PRESENTACION": "BOTON"},
    {"CODIGO": "L2-FIL01", "PRESENTACION": "FILETE 2-4 CM CT CORTADO"},
    {"CODIGO": "L2-FIL02", "PRESENTACION": "FILETE 2-4 CM CT MANTO"},
    {"CODIGO": "L2-ALTCV", "PRESENTACION": "ALETA CV TUNEL"},
    {"CODIGO": "L2-ALTUP", "PRESENTACION": "ALETA 1000 UP TUNEL"}
]

# 3. Lista de Subfamilias
LISTA_SUBFAMILIAS = [
    "ALETA FRESCA",
    "ANILLAS",
    "ALETA PRECOCIDA",
    "BOTONES",
    "CONOS",
    "FILETE FRESCO",
    "FILETE PRECOCIDO",
    "DESHILACHADO",
    "NUCAS",
    "RECORTE PRECOCIDO",
    "RECORTE FRESCO",
    "REPRODUCTOR",
    "TENTACULO",
    "TUBO"
]

def autocalcular_lote(fecha_obj):
    dia_del_anio = fecha_obj.timetuple().tm_yday
    return f"LT {dia_del_anio:03d}"

def sugerir_subfamilia(nombre_producto):
    nom_upper = str(nombre_producto).upper()
    if "BOTON" in nom_upper:
        return "BOTONES"
    elif "ALETA" in nom_upper:
        return "ALETA FRESCA"
    elif "FILETE" in nom_upper:
        return "FILETE FRESCO"
    for subf in LISTA_SUBFAMILIAS:
        if subf in nom_upper:
            return subf
    return LISTA_SUBFAMILIAS[0]

def render_module(user, get_gspread_client):
    st.subheader("📊 Módulo 5: Control de Stock y Producción")
    st.caption(f"Usuario activo: {user.get('nombre_completo', user.get('usuario'))} | Conectado a: BD_PRODUCCION_ARCHI_001")

    # Conexión resiliente
    try:
        client = get_gspread_client()
        sh = client.open_by_url(URL_PRODUCCION)
    except Exception:
        try:
            sh = client.open("BD_PRODUCCION_ARCHI_001")
        except Exception as e:
            st.error(f"Error al conectar con Google Sheet: {e}")
            st.info("Verifica que el archivo esté compartido con streamlit-frigosa@frigosa-wms.iam.gserviceaccount.com")
            return

    tab_entradas, tab_salidas, tab_stock, tab_inventario = st.tabs([
        "📥 Registro Entradas", "📤 Registro Salidas", "📈 Balance Stock Virtual", "📋 Inventario Físico"
    ])

    meses = [
        "ENERO", "FEBRERO", "MARZO", "ABRIL", "MAYO", "JUNIO", 
        "JULIO", "AGOSTO", "SETIEMBRE", "OCTUBRE", "NOVIEMBRE", "DICIEMBRE"
    ]

    # --- TAB 1: ENTRADAS ---
    with tab_entradas:
        st.write("#### Ingreso a Túnel / Cámara")
        destino_ent = st.radio("Línea de Entrada:", ["entradas (Línea 1)", "entradas2 (Línea 2)"], horizontal=True, key="rad_ent_linea")
        es_linea_2 = "Línea 2" in destino_ent
        hoja_ent = "entradas2" if es_linea_2 else "entradas"

        # Selección de catálogo según línea activa
        catalogo_activo = CATALOGO_LINEA_2 if es_linea_2 else CATALOGO_LINEA_1
        opciones_prod_ent = [f"{p['CODIGO']} - {p['PRESENTACION']}" for p in catalogo_activo]

        c_top1, c_top2 = st.columns(2)
        with c_top1:
            fecha_ent = st.date_input("Fecha de Producción / Entrada", value=date.today(), key="ent_fecha_val")
            lote_autocalculado = autocalcular_lote(fecha_ent)
        with c_top2:
            prod_ent = st.selectbox("Código / Presentación de Producto", opciones_prod_ent, key=f"ent_prod_{hoja_ent}")
            subf_sugerida = sugerir_subfamilia(prod_ent)

        with st.form("form_entradas", clear_on_submit=True):
            col1, col2, col3 = st.columns(3)
            with col1:
                id_ent = st.text_input("ID Ingreso (Opcional)")
                cant_ent = st.number_input("Cantidad (TM)", min_value=0.0, step=0.001, format="%.3f")
                tunel_ent = st.text_input("Túnel de Congelación")
            with col2:
                idx_subf = LISTA_SUBFAMILIAS.index(subf_sugerida) if subf_sugerida in LISTA_SUBFAMILIAS else 0
                subf_ent = st.selectbox("Subfamilia", LISTA_SUBFAMILIAS, index=idx_subf, key=f"ent_subf_{hoja_ent}")
                lote_ent = st.text_input("Lote (Autocalculado por fecha)", value=lote_autocalculado, key=f"ent_lote_{hoja_ent}")
            with col3:
                mes_sugerido_idx = fecha_ent.month - 1
                mes_ent = st.selectbox("Mes Operativo", meses, index=mes_sugerido_idx, key=f"ent_mes_{hoja_ent}")
                placa_ent = st.text_input("Placa / Vehículo")

            btn_ent = st.form_submit_button("💾 Guardar Entrada a Túnel")
            if btn_ent:
                cod, pres = prod_ent.split(" - ", 1) if " - " in prod_ent else ("", "")
                fila = [
                    id_ent.strip(), 
                    str(fecha_ent), 
                    cod.strip(), 
                    pres.strip(), 
                    float(cant_ent), 
                    tunel_ent.strip(), 
                    placa_ent.strip(), 
                    mes_ent, 
                    subf_ent, 
                    lote_ent.strip()
                ]
                try:
                    sh.worksheet(hoja_ent).append_row(fila)
                    st.success(f"✅ Entrada registrada en '{hoja_ent}': {cod} | Lote: {lote_ent} ({cant_ent} TM).")
                except Exception as ex:
                    st.error(f"Error al guardar: {ex}")

    # --- TAB 2: SALIDAS ---
    with tab_salidas:
        st.write("#### Despacho / Salidas")
        destino_sal = st.radio("Línea de Salida:", ["salidas (Línea 1)", "salidas2 (Línea 2)"], horizontal=True, key="rad_sal_linea")
        es_salida_2 = "Línea 2" in destino_sal
        hoja_sal = "salidas2" if es_salida_2 else "salidas"

        catalogo_sal_activo = CATALOGO_LINEA_2 if es_salida_2 else CATALOGO_LINEA_1
        opciones_prod_sal = [f"{p['CODIGO']} - {p['PRESENTACION']}" for p in catalogo_sal_activo]

        c_sal_top1, c_sal_top2 = st.columns(2)
        with c_sal_top1:
            fecha_sal = st.date_input("Fecha Embarque", value=date.today(), key="s_fecha_val")
            lote_sal_auto = autocalcular_lote(fecha_sal)
        with c_sal_top2:
            prod_sal = st.selectbox("Producto a Despachar", opciones_prod_sal, key=f"s_prod_{hoja_sal}")

        with st.form("form_salidas", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            with c1:
                mes_sal_idx = fecha_sal.month - 1
                mes_sal = st.selectbox("Mes Embarque", meses, index=mes_sal_idx, key=f"s_mes_{hoja_sal}")
                lote_sal = st.text_input("Lote Embarque", value=lote_sal_auto, key=f"s_lote_{hoja_sal}")
                subf_sal_sug = sugerir_subfamilia(prod_sal)
                idx_subf_sal = LISTA_SUBFAMILIAS.index(subf_sal_sug) if subf_sal_sug in LISTA_SUBFAMILIAS else 0
                sudfa_sal = st.selectbox("Subfamilia (SUDFA)", LISTA_SUBFAMILIAS, index=idx_subf_sal, key=f"s_sudfa_{hoja_sal}")
                tipo_op = st.text_input("Tipo de Operación", value="Exportación")
            with c2:
                cant_sal = st.number_input("Cantidad Despachada (TM)", min_value=0.0, step=0.001, format="%.3f", key=f"s_cant_{hoja_sal}")
                booking = st.text_input("Booking")
                cliente = st.text_input("Cliente")
            with c3:
                pi = st.text_input("P.I.")
                pais_dest = st.text_input("País Destino")
                pais = st.text_input("País")
                contenedor = st.text_input("Contenedor")

            btn_sal = st.form_submit_button("📤 Guardar Salida / Despacho")
            if btn_sal:
                cod_s, pres_s = prod_sal.split(" - ", 1) if " - " in prod_sal else ("", "")
                fila_sal = [
                    mes_sal, 
                    str(fecha_sal), 
                    lote_sal.strip(), 
                    sudfa_sal, 
                    tipo_op.strip(), 
                    cod_s.strip(), 
                    pres_s.strip(), 
                    float(cant_sal), 
                    booking.strip(), 
                    cliente.strip(), 
                    pi.strip(), 
                    pais_dest.strip(), 
                    pais.strip(), 
                    contenedor.strip()
                ]
                try:
                    sh.worksheet(hoja_sal).append_row(fila_sal)
                    st.success(f"✅ Salida registrada en '{hoja_sal}': {cod_s} ({cant_sal} TM).")
                except Exception as ex:
                    st.error(f"Error al guardar: {ex}")

    # --- TAB 3: STOCK VIRTUAL ---
    with tab_stock:
        st.write("#### Balance Virtual de Stock")
        hoja_stk_sel = st.radio("Seleccione hoja de balance:", ["stock (Línea 1)", "stock2 (Línea 2)"], horizontal=True, key="rad_stk_sel")
        nombre_stk = "stock2" if "Línea 2" in hoja_stk_sel else "stock"

        if st.button("🔄 Refrescar Balance"):
            st.rerun()

        try:
            filas_stk = sh.worksheet(nombre_stk).get_all_values()
            if len(filas_stk) > 1:
                df_stk = pd.DataFrame(filas_stk[1:], columns=filas_stk[0])
                st.dataframe(df_stk, use_container_width=True)
            else:
                st.info(f"Sin registros disponibles en la hoja '{nombre_stk}'.")
        except Exception as ex:
            st.error(f"Error al leer stock: {ex}")

    # --- TAB 4: INVENTARIO FÍSICO ---
    with tab_inventario:
        st.write("#### Toma de Inventario Físico")
        # Combina ambos catálogos para permitir inventariar cualquier producto de planta
        opciones_totales = [f"{p['CODIGO']} - {p['PRESENTACION']}" for p in (CATALOGO_LINEA_1 + CATALOGO_LINEA_2)]
        
        with st.form("form_inv", clear_on_submit=True):
            i1, i2 = st.columns(2)
            with i1:
                id_inv = st.text_input("ID Inventario")
                fecha_inv = st.date_input("Fecha de Conteo", value=date.today(), key="i_fecha_val")
                prod_inv = st.selectbox("Producto Contado", opciones_totales, key="i_prod_sel")
            with i2:
                cant_inv = st.number_input("Cantidad Física Contada (TM)", min_value=0.0, step=0.001, format="%.3f", key="i_cant_val")
                tunel_inv = st.text_input("Cámara / Túnel", key="i_tun_val")
                placas_inv = st.text_input("Placas / Racks", key="i_pla_val")
                obs_inv = st.text_area("Observaciones de Auditoría")

            btn_inv = st.form_submit_button("📋 Registrar Conteo Físico")
            if btn_inv:
                cod_i, pres_i = prod_inv.split(" - ", 1) if " - " in prod_inv else ("", "")
                fila_inv = [
                    id_inv.strip(), 
                    str(fecha_inv), 
                    cod_i.strip(), 
                    pres_i.strip(), 
                    float(cant_inv), 
                    tunel_inv.strip(), 
                    placas_inv.strip(), 
                    obs_inv.strip()
                ]
                try:
                    sh.worksheet("INVENTARIADO_FISICO").append_row(fila_inv)
                    st.success(f"✅ Conteo guardado para {cod_i}.")
                except Exception as ex:
                    st.error(f"Error al registrar inventario físico: {ex}")
              
