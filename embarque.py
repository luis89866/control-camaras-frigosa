import streamlit as st
import pandas as pd
from datetime import date, datetime
import io
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

ID_SPREADSHEET_PRODUCCION = "1cX-C1Lrgp8SznxDs-_cjiMN6DptNusCmNoNopxBmJlg"

LISTA_PRESENTACIONES_FRIGOSA = [
    "AF 300 - 500 g/pza",
    "AF 500- 1000 g/pza",
    "AF 1000 g/pza - UP",
    "AF 1000 g/pza - CV",
    "APC 300 g/pza - UP",
    "ANILLAS S/M S/T",
    "BOTONES S/M S/T",
    "CONOS",
    "FF S/M S/T 2000-4000 g/pza",
    "FF C/M C/T 500 g/pza - 1000 g/pz",
    "FF C/M C/T 1000 g/pza - 2000 g/pza",
    "FF C/M C/T 2000 g/pza - 4000 g/pza",
    "FF C/M C/T 2000 g/pza - 4000 g/pza MANTO ",
    "FF C/M C/T 2000 g/pza - 4000 g/pza CORTADO ",
    "FPC 7mm - 10 mm",
    "FPC PANZA 7mm - 10 mm",
    "FPC MEMBRANA 7mm - 10 mm",
    "FPC PANZA 8 mm - 14 mm",
    "FPC MEMBRANA 8 mm - 14 mm",
    "DESHILACHADO",
    "DESHILACHADO F2",
    "FPC 10mm - 14 mm",
    "NF 100 g/pza - 300 g/pza",
    "NF 300 g/pza - 500 g/pza",
    "NF 500g/pza -UP",
    "NF 0 -50 g/pza",
    "RECORTE PRECOCIDO",
    "RECORTE FRESCO S/M S/T",
    "REPRODUCTOR MAYOR A 50 cm",
    "REPRODUCTOR MENOR A 50 cm",
    "TB C/U C/V 300 g/pza - 500 g/pza",
    "TB C/U C/V 500 g/pza - 1000 g/pza",
    "TB S/U S/V 300 g/pza - 500 g/pza",
    "TB S/U S/V 2000 g/pza - 3000 g/pza",
    "TB S/U S/V 1000g /pza-UP",
    "OTRO (Digitar manualmente)"
]

MESES_ESP = {1: "ENERO", 2: "FEBRERO", 3: "MARZO", 4: "ABRIL", 5: "MAYO", 6: "JUNIO",
             7: "JULIO", 8: "AGOSTO", 9: "SETIEMBRE", 10: "OCTUBRE", 11: "NOVIEMBRE", 12: "DICIEMBRE"}

def generar_lote_juliano(fecha_obj):
    try:
        yy = str(fecha_obj.year)[-2:]
        juliano = fecha_obj.timetuple().tm_yday
        return f"LT 0{yy}.{juliano:03d}"
    except Exception:
        return "LT 026.001"

def calcular_matriz_estiba(filas_capacidades, lista_elementos):
    num_filas = len(filas_capacidades)
    num_cols = len(lista_elementos)
    matriz = [[0 for _ in range(num_cols)] for _ in range(num_filas)]
    col_idx = 0
    remanente = lista_elementos[col_idx]['cantidad'] if num_cols > 0 else 0

    for f_idx in range(num_filas):
        espacio_fila = filas_capacidades[f_idx]
        while espacio_fila > 0 and col_idx < num_cols:
            if remanente <= 0:
                col_idx += 1
                if col_idx < num_cols:
                    remanente = lista_elementos[col_idx]['cantidad']
                else:
                    break
            asignar = min(espacio_fila, remanente)
            matriz[f_idx][col_idx] += asignar
            espacio_fila -= asignar
            remanente -= asignar
    return matriz

# =========================================================================
# GENERACIÓN DE REPORTES PDF
# =========================================================================
def generar_pdf_planos_estiba(cabecera, df_estiba_lotes, df_estiba_pres):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, leftMargin=18, rightMargin=18, topMargin=18, bottomMargin=18)
    story = []
    styles = getSampleStyleSheet()

    titulo_style = ParagraphStyle('TitF', parent=styles['Heading1'], fontSize=10.5, leading=12, textColor=colors.HexColor("#0D3B66"), alignment=1)
    sub_style = ParagraphStyle('SubF', parent=styles['Heading2'], fontSize=7.5, leading=9.5, textColor=colors.HexColor("#2B6CB0"), alignment=1)
    cell_head_style = ParagraphStyle('CH', parent=styles['Normal'], fontSize=5.5, leading=6.5, textColor=colors.white, alignment=1, fontName="Helvetica-Bold")

    def agregar_tabla(df_in, titulo_tab, color_header):
        if df_in is not None and not df_in.empty:
            story.append(Paragraph(titulo_tab, titulo_style))
            story.append(Paragraph(f"CONTENEDOR: {cabecera['contenedor']} | FECHA: {cabecera['fecha']} | CLIENTE: {cabecera.get('cliente', '-')}", sub_style))
            story.append(Spacer(1, 5))

            cols = list(df_in.columns)
            num_cols = len(cols)
            if num_cols > 3:
                w_prim = [38, 50, 52]
                w_resto = (576 - sum(w_prim)) / (num_cols - 3)
                col_widths = w_prim + [w_resto] * (num_cols - 3)
            else:
                col_widths = [576 / num_cols] * num_cols

            header_row = [Paragraph(str(c).replace(" | ", "<br/>").replace("\n", "<br/>"), cell_head_style) for c in cols]
            t_data = [header_row]

            for _, r in df_in.iterrows():
                row_vals = []
                for c in cols:
                    val = r[c]
                    if isinstance(val, (int, float)):
                        row_vals.append(f"{val:.2f}" if ("TM" in c.upper()) else str(int(val)))
                    else:
                        row_vals.append(str(val))
                t_data.append(row_vals)

            tot_row = []
            for idx_c, col_name in enumerate(cols):
                if idx_c == 0:
                    tot_row.append("TOTAL")
                else:
                    try:
                        sum_val = df_in[col_name].astype(float).sum()
                        tot_row.append(f"{sum_val:,.2f}" if "TM" in col_name.upper() else f"{int(sum_val):,}")
                    except Exception:
                        tot_row.append("-")
            t_data.append(tot_row)

            f_size = 5.2 if num_cols > 6 else (5.8 if num_cols > 4 else 6.2)
            t_pdf = Table(t_data, colWidths=col_widths)
            t_pdf.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 1), (-1, -1), f_size),
                ('TOPPADDING', (0, 0), (-1, -1), 1.2),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 1.2),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(color_header)),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
                ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor("#FEFCBF")),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.HexColor("#F7FAFC")]),
            ]))
            story.append(t_pdf)

    agregar_tabla(df_estiba_lotes, "PLANO DE ESTIBA POR FECHAS Y LOTES - FRIGOSA SAC", "#2B6CB0")
    story.append(PageBreak())
    agregar_tabla(df_estiba_pres, "PLANO DE ESTIBA POR PRESENTACIONES - FRIGOSA SAC", "#2F855A")

    doc.build(story)
    buffer.seek(0)
    return buffer

def generar_pdf_pesos_solos(cabecera, presentaciones_data, resumen):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, leftMargin=20, rightMargin=20, topMargin=20, bottomMargin=20)
    story = []
    styles = getSampleStyleSheet()

    titulo_style = ParagraphStyle('TitF', parent=styles['Heading1'], fontSize=11, leading=13, textColor=colors.HexColor("#0D3B66"), alignment=1)
    sub_style = ParagraphStyle('SubF', parent=styles['Heading2'], fontSize=8, leading=10, textColor=colors.HexColor("#2B6CB0"), alignment=1)
    cell_head_style = ParagraphStyle('CH', parent=styles['Normal'], fontSize=6.0, leading=7.5, textColor=colors.white, alignment=1, fontName="Helvetica-Bold")

    story.append(Paragraph("SEGUIMIENTO DE CONTROL DE PESO Y BALANZA - FRIGOSA SAC", titulo_style))
    story.append(Paragraph(f"CONTENEDOR: {cabecera['contenedor']} | PI: {cabecera.get('pi', '-')} | BOOKING: {cabecera.get('booking', '-')}", sub_style))
    story.append(Spacer(1, 6))

    data_cab = [
        ["FECHA:", cabecera['fecha'], "N° CONTENEDOR:", cabecera['contenedor']],
        ["CLIENTE:", cabecera.get('cliente', '-'), "DESTINO:", cabecera.get('destino', '-')],
        ["BOOKING:", cabecera.get('booking', '-'), "P.I. (PEDIDO):", cabecera.get('pi', '-')],
        ["PAYLOAD MÁX (KG):", f"{cabecera['payload']:,.2f}", "PESO BRUTO ESTIMADO:", f"{resumen['peso_total']:,.2f} KG"],
        ["TOTAL BULTOS:", f"{resumen['total_bultos']:,}", "MARGEN (A FAVOR):", f"{resumen['peso_a_favor']:,.2f} KG"],
        ["SUPERVISOR:", cabecera['responsable'], "PROMEDIO GLOBAL:", f"{resumen['promedio_global']:.3f} KG"]
    ]
    t_cab = Table(data_cab, colWidths=[105, 175, 115, 177])
    t_cab.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 6.5),
        ('TOPPADDING', (0, 0), (-1, -1), 1.8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 1.8),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F4F6F9")),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
        ('ALIGN', (1, 0), (1, -1), 'CENTER'),
        ('ALIGN', (3, 0), (3, -1), 'CENTER'),
    ]))
    story.append(t_cab)
    story.append(Spacer(1, 8))

    headers = [Paragraph(f"<b>{p['nombre'][:20]}</b>", ParagraphStyle('PNH', parent=cell_head_style, fontSize=6)) for p in presentaciones_data]
    matrix_pesos = [headers]
    for r in range(20):
        fila = [f"{p['pesos'][r]:.2f}" if r < len(p['pesos']) and p['pesos'][r] > 0 else "-" for p in presentaciones_data]
        matrix_pesos.append(fila)

    matrix_pesos.append([f"Bultos: {p['bultos']}" for p in presentaciones_data])
    matrix_pesos.append([f"Prom: {p['promedio']:.3f}" for p in presentaciones_data])
    matrix_pesos.append([f"Total: {p['total_kg']:,.1f} kg" for p in presentaciones_data])

    ancho_col = 572 / max(len(presentaciones_data), 1)
    t_muestreo = Table(matrix_pesos, colWidths=[ancho_col] * len(presentaciones_data))
    t_muestreo.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 6.5),
        ('TOPPADDING', (0, 0), (-1, -1), 1.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 1.5),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1A365D")),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
        ('BACKGROUND', (0, -3), (-1, -1), colors.HexColor("#EDF2F7")),
        ('FONTNAME', (0, -3), (-1, -1), 'Helvetica-Bold'),
    ]))
    story.append(t_muestreo)

    doc.build(story)
    buffer.seek(0)
    return buffer

# =========================================================================
# LÓGICA DE ACTUALIZACIÓN / GUARDADO EN GOOGLE SHEETS
# =========================================================================
def obtener_hoja_distribuciones(get_gspread_client):
    client = get_gspread_client()
    try:
        sh = client.open_by_key(ID_SPREADSHEET_PRODUCCION)
    except Exception:
        sh = client.open("BD_PRODUCCION_ARCHI_001")
    return sh.worksheet("DISTRIBUCIONES")

def guardar_o_actualizar_contenedor(get_gspread_client, datos_fila):
    """Guarda si es nuevo, o actualiza la fila existente si el contenedor ya está en la hoja."""
    ws = obtener_hoja_distribuciones(get_gspread_client)
    contenedores_col = ws.col_values(2)  # Columna B: CONTENEDOR
    num_cont = str(datos_fila[1]).strip()

    fila_idx = None
    for idx, c_val in enumerate(contenedores_col):
        if str(c_val).strip() == num_cont and idx > 0:
            fila_idx = idx + 1
            break

    if fila_idx:
        # Actualiza la fila existente (Columnas A a AI)
        rango = f"A{fila_idx}:AI{fila_idx}"
        ws.update(rango, [datos_fila])
        return f"Actualizado (Fila {fila_idx})"
    else:
        # Inserta nueva fila al final
        ws.append_row(datos_fila)
        return "Registrado como nuevo"

# =========================================================================
# RENDER DEL MÓDULO
# =========================================================================
def render_module(user, get_gspread_client):
    nombre_user = user.get("nombre_completo", user.get("usuario", "LUIS ENRIQUE FIESTAS ECA"))
    st.subheader("🚢 Módulo 4: Despachos, Estiba y Embarques")

    # Inicialización de estado
    if "embarque_state" not in st.session_state:
        st.session_state.embarque_state = {
            "id_emb": f"EMB-{date.today().strftime('%y%m%d%H%M%S')}",
            "cont": "", "mes": MESES_ESP.get(date.today().month, "SETIEMBRE"),
            "fec": date.today(), "pi": "", "bk": "", "cli": "Shandong sheenier",
            "dest": "Yantai china", "pais": "CHINA", "nfil": 20, "cap_g": 67,
            "cap_f1": 77, "cap_fu": 67, "w_std": 21.68, "pay": 30400.0,
            "pres_list": [
                {"nombre": "FF C/M C/T 2000 g/pza - 4000 g/pza MANTO ", "bultos": 800, "peso": 21.68},
                {"nombre": "FF C/M C/T 2000 g/pza - 4000 g/pza CORTADO ", "bultos": 550, "peso": 20.00}
            ],
            "lotes_list": [
                {"fecha": date.today(), "lote": generar_lote_juliano(date.today()), "bultos": 650},
                {"fecha": date.today(), "lote": generar_lote_juliano(date.today()), "bultos": 700}
            ],
            "placas": 1350, "tunel": 0, "iqf": 0, "modo_cong": "Solo Placas (100%)",
            "txt_pesos": {}
        }

    c_state = st.session_state.embarque_state

    # Selector superior para cargar contenedores existentes o crear uno nuevo
    col_sel1, col_sel2 = st.columns([3, 1])
    with col_sel1:
        try:
            ws_d = obtener_hoja_distribuciones(get_gspread_client)
            registros = ws_d.get_all_values()
            conts_existentes = [r[1] for r in registros[1:] if len(r) > 1 and r[1].strip()]
        except Exception:
            conts_existentes = []

        modo_operacion = st.radio(
            "Modo de Trabajo:",
            ["Nuevo Contenedor", "Cargar / Editar Contenedor Existente"],
            horizontal=True
        )

        if modo_operacion == "Cargar / Editar Contenedor Existente" and conts_existentes:
            cont_seleccionado = st.selectbox("Seleccionar Contenedor registrado en Sheets:", conts_existentes)
            if st.button("📥 Cargar Datos de este Contenedor"):
                for r in registros[1:]:
                    if len(r) > 1 and r[1].strip() == cont_seleccionado:
                        c_state["id_emb"] = r[0]
                        c_state["cont"] = r[1]
                        c_state["mes"] = r[2] if len(r) > 2 else c_state["mes"]
                        c_state["pi"] = r[4] if len(r) > 4 else ""
                        c_state["bk"] = r[5] if len(r) > 5 else ""
                        c_state["cli"] = r[6] if len(r) > 6 else ""
                        c_state["dest"] = r[7] if len(r) > 7 else ""
                        c_state["pais"] = r[8] if len(r) > 8 else ""
                        c_state["pay"] = float(r[26]) if len(r) > 26 and r[26] else 30400.0
                        c_state["placas"] = int(r[31]) if len(r) > 31 and r[31] else 1350
                        c_state["tunel"] = int(r[32]) if len(r) > 32 and r[32] else 0
                        c_state["iqf"] = int(r[33]) if len(r) > 33 and r[33] else 0
                        st.success(f"Datos de {cont_seleccionado} cargados correctamente.")
                        st.rerun()
                        break

    with col_sel2:
        if st.button("🧹 Limpiar Pantalla"):
            st.session_state.embarque_state = {
                "id_emb": f"EMB-{date.today().strftime('%y%m%d%H%M%S')}",
                "cont": "", "mes": MESES_ESP.get(date.today().month, "SETIEMBRE"),
                "fec": date.today(), "pi": "", "bk": "", "cli": "",
                "dest": "", "pais": "", "nfil": 20, "cap_g": 67,
                "cap_f1": 77, "cap_fu": 67, "w_std": 20.0, "pay": 30400.0,
                "pres_list": [], "lotes_list": [],
                "placas": 0, "tunel": 0, "iqf": 0, "modo_cong": "Solo Placas (100%)",
                "txt_pesos": {}
            }
            st.rerun()

    # --- CABECERA (Columnas A - J y AA de la hoja) ---
    with st.expander("⚙️ Datos Principales del Contenedor", expanded=True):
        cp1, cp2, cp3, cp4 = st.columns(4)
        with cp1:
            fec_desp = st.date_input("Fecha:", value=c_state.get("fec", date.today()), key="fec_emb")
            c_state["fec"] = fec_desp
            num_cont = st.text_input("N° Contenedor:", value=c_state.get("cont", ""), key="cont_emb").upper().strip()
            c_state["cont"] = num_cont
            mes_sel = st.selectbox("Mes:", list(MESES_ESP.values()), index=list(MESES_ESP.values()).index(c_state.get("mes", "SETIEMBRE")))
            c_state["mes"] = mes_sel
        with cp2:
            booking = st.text_input("Booking:", value=c_state.get("bk", ""), key="bk_emb").strip()
            c_state["bk"] = booking
            pi_val = st.text_input("N° P.I. (Pedido):", value=c_state.get("pi", ""), key="pi_emb").strip()
            c_state["pi"] = pi_val
        with cp3:
            cliente = st.text_input("Cliente:", value=c_state.get("cli", ""), key="cli_emb").strip()
            c_state["cli"] = cliente
            destino = st.text_input("Destino (Puerto):", value=c_state.get("dest", ""), key="dest_emb").strip()
            c_state["dest"] = destino
        with cp4:
            pais_val = st.text_input("País:", value=c_state.get("pais", "CHINA"), key="pais_emb").strip().upper()
            c_state["pais"] = pais_val
            payload = st.number_input("Payload Máx (kg):", min_value=15000.0, max_value=34000.0, value=float(c_state.get("pay", 30400.0)), step=100.0)
            c_state["pay"] = payload

    tab_estiba_lotes, tab_estiba_pres, tab_placa_tunel, tab_pesos = st.tabs([
        "📅 1. Plano Estiba (Lotes)",
        "📦 2. Plano Estiba (Presentaciones)",
        "❄️ 3. Placas / Túnel / IQF",
        "⚖️ 4. Control de Pesos (Balanza)"
    ])

    caps_filas_maestro = [int(c_state["cap_g"])] * int(c_state["nfil"])
    caps_filas_maestro[0] = int(c_state["cap_f1"])
    caps_filas_maestro[-1] = int(c_state["cap_fu"])

    # =========================================================================
    # TAB 1: PLANO ESTIBA POR LOTES
    # =========================================================================
    with tab_estiba_lotes:
        st.markdown("#### Configuración de Filas y Lotes")
        cf1, cf2, cf3, cf4 = st.columns(4)
        with cf1:
            n_filas = st.number_input("Total Filas:", min_value=10, max_value=30, value=int(c_state["nfil"]))
            c_state["nfil"] = int(n_filas)
        with cf2:
            cap_gral = st.number_input("Capacidad Estándar Fila:", min_value=30, max_value=100, value=int(c_state["cap_g"]))
            c_state["cap_g"] = int(cap_gral)
        with cf3:
            cap_f1 = st.number_input("Capacidad Fila 1:", min_value=20, max_value=100, value=int(c_state["cap_f1"]))
            c_state["cap_f1"] = int(cap_f1)
        with cf4:
            cap_fult = st.number_input(f"Capacidad Fila {n_filas}:", min_value=20, max_value=100, value=int(c_state["cap_fu"]))
            c_state["cap_fu"] = int(cap_fult)
            peso_std = st.number_input("Peso Estándar (kg):", value=float(c_state["w_std"]), step=0.1)
            c_state["w_std"] = float(peso_std)

        n_lotes = st.number_input("Cantidad de Lotes:", min_value=1, max_value=10, value=max(len(c_state["lotes_list"]), 1))
        while len(c_state["lotes_list"]) < n_lotes:
            c_state["lotes_list"].append({"fecha": date.today(), "lote": generar_lote_juliano(date.today()), "bultos": 0})
        while len(c_state["lotes_list"]) > n_lotes:
            c_state["lotes_list"].pop()

        cols_l = st.columns(int(n_lotes))
        lista_lotes = []
        for i, col in enumerate(cols_l):
            item_l = c_state["lotes_list"][i]
            with col:
                fl = st.date_input(f"Fecha {i+1}:", value=item_l["fecha"], key=f"f_lot_{i}")
                lot_txt = st.text_input(f"Lote {i+1}:", value=item_l["lote"], key=f"c_lot_{i}")
                bl = st.number_input(f"Bultos {i+1}:", min_value=0, value=int(item_l["bultos"]), step=10, key=f"b_lot_{i}")
                item_l["fecha"] = fl
                item_l["lote"] = lot_txt
                item_l["bultos"] = int(bl)
                lista_lotes.append({"fecha_txt": fl.strftime('%d/%m/%Y'), "lote_txt": lot_txt.strip(), "cantidad": int(bl)})

        matriz_lotes = calcular_matriz_estiba(caps_filas_maestro, lista_lotes)
        headers_l = [f"{l['fecha_txt']} | {l['lote_txt']}" for l in lista_lotes]
        data_estiba = []
        for f_idx in range(int(n_filas)):
            b_f = sum(matriz_lotes[f_idx])
            r_dict = {"N° FILA": f_idx + 1, "TM": round((b_f * peso_std) / 1000.0, 4), "CANT/FILA": b_f}
            for l_i in range(len(lista_lotes)):
                r_dict[headers_l[l_i]] = matriz_lotes[f_idx][l_i]
            data_estiba.append(r_dict)

        df_lotes = pd.DataFrame(data_estiba)
        c_state["df_lotes"] = df_lotes
        st.dataframe(df_lotes, hide_index=True, use_container_width=True, height=280)

    # =========================================================================
    # TAB 2: PRESENTACIONES (Columnas K hasta Z)
    # =========================================================================
    with tab_estiba_pres:
        st.markdown("#### Presentaciones a Embarcar (Hasta 8 según la hoja)")
        np_m = st.number_input("Número de Presentaciones:", min_value=1, max_value=8, value=max(len(c_state["pres_list"]), 1))
        while len(c_state["pres_list"]) < np_m:
            c_state["pres_list"].append({"nombre": LISTA_PRESENTACIONES_FRIGOSA[0], "bultos": 0, "peso": 20.0})
        while len(c_state["pres_list"]) > np_m:
            c_state["pres_list"].pop()

        cols_p = st.columns(int(np_m))
        lista_pres_m = []
        for i, col in enumerate(cols_p):
            p_item = c_state["pres_list"][i]
            with col:
                st.markdown(f"**Presentación {i+1}**")
                idx_sel = LISTA_PRESENTACIONES_FRIGOSA.index(p_item["nombre"]) if p_item["nombre"] in LISTA_PRESENTACIONES_FRIGOSA else 0
                sel_nom = st.selectbox(f"Corte {i+1}:", LISTA_PRESENTACIONES_FRIGOSA, index=idx_sel, key=f"sel_p_{i}")
                cant_b = st.number_input(f"Bultos {i+1}:", min_value=0, value=int(p_item["bultos"]), step=10, key=f"b_pres_{i}")
                p_item["nombre"] = sel_nom
                p_item["bultos"] = int(cant_b)
                lista_pres_m.append({"nombre": sel_nom, "cantidad": int(cant_b), "peso_unit": float(p_item.get("peso", 20.0))})

        matriz_pres = calcular_matriz_estiba(caps_filas_maestro, lista_pres_m)
        headers_pres = [f"{p['nombre']} (P{idx+1})" for idx, p in enumerate(lista_pres_m)]
        data_pres = []
        for f_idx in range(len(caps_filas_maestro)):
            b_f = sum(matriz_pres[f_idx])
            tm_f = sum(matriz_pres[f_idx][p_i] * lista_pres_m[p_i]['peso_unit'] for p_i in range(len(lista_pres_m))) / 1000.0
            r_d = {"N° FILA": f_idx + 1, "TM ESTIMADO": round(tm_f, 4), "TOTAL BULTOS": b_f}
            for p_i in range(len(lista_pres_m)):
                r_d[headers_pres[p_i]] = matriz_pres[f_idx][p_i]
            data_pres.append(r_d)

        df_pres = pd.DataFrame(data_pres)
        c_state["df_pres"] = df_pres
        st.dataframe(df_pres, hide_index=True, use_container_width=True, height=280)

        # Botón para descargar el PDF inicial
        cabecera_estiba = {"contenedor": num_cont, "booking": booking, "pi": pi_val, "cliente": cliente, "fecha": str(fec_desp)}
        try:
            pdf_planos = generar_pdf_planos_estiba(cabecera_estiba, df_lotes, df_pres)
            st.download_button("📄 Descargar PDF Distribución (Lotes + Pres)", data=pdf_planos, file_name=f"Distribucion_{num_cont}.pdf", mime="application/pdf")
        except Exception:
            pass

    # =========================================================================
    # TAB 3: PLACAS / TÚNEL / IQF (Columnas AF, AG, AH)
    # =========================================================================
    with tab_placa_tunel:
        st.markdown("#### Tipo de Congelación")
        modo_cong = st.radio("Carga predominante:", ["Solo Placas (100%)", "Solo Túnel (100%)", "Personalizado"], horizontal=True)
        tot_bultos_estiba = sum(p["cantidad"] for p in lista_pres_m)

        if modo_cong == "Solo Placas (100%)":
            c_state["placas"], c_state["tunel"], c_state["iqf"] = tot_bultos_estiba, 0, 0
        elif modo_cong == "Solo Túnel (100%)":
            c_state["placas"], c_state["tunel"], c_state["iqf"] = 0, tot_bultos_estiba, 0
        else:
            c1, c2, c3 = st.columns(3)
            with c1:
                c_state["placas"] = st.number_input("Bultos Placas:", min_value=0, value=int(c_state.get("placas", tot_bultos_estiba)))
            with c2:
                c_state["tunel"] = st.number_input("Bultos Túnel:", min_value=0, value=int(c_state.get("tunel", 0)))
            with c3:
                c_state["iqf"] = st.number_input("Bultos IQF:", min_value=0, value=int(c_state.get("iqf", 0)))

        st.metric("Total Congelado", f"{c_state['placas'] + c_state['tunel'] + c_state['iqf']:,} bultos")

    # =========================================================================
    # TAB 4: CONTROL DE PESOS (Columnas AB, AC, AD, AE)
    # =========================================================================
    with tab_pesos:
        st.markdown("#### Pesos de Balanza")
        cols_w = st.columns(max(len(lista_pres_m), 1))
        presentaciones_data = []

        for i, col in enumerate(cols_w):
            with col:
                st.markdown(f"**{lista_pres_m[i]['nombre'][:20]}**")
                txt_p = st.text_area(f"Pesos balanza ({i+1}):", value=c_state.get("txt_pesos", {}).get(str(i), "21.65, 21.70, 21.68"), height=90, key=f"pw_{i}")
                if "txt_pesos" not in c_state:
                    c_state["txt_pesos"] = {}
                c_state["txt_pesos"][str(i)] = txt_p

                pesos_clean = []
                for p in txt_p.replace("\n", ",").split(","):
                    try:
                        v = float(p.strip())
                        if v > 0:
                            pesos_clean.append(v)
                    except:
                        pass
                pesos_clean = pesos_clean[:20]
                prom_u = (sum(pesos_clean) / len(pesos_clean)) if pesos_clean else float(c_state["w_std"])
                tot_k = prom_u * lista_pres_m[i]["cantidad"]
                st.caption(f"Prom: **{prom_u:.3f} kg** | Subtotal: **{tot_k:,.1f} kg**")
                presentaciones_data.append({"nombre": lista_pres_m[i]["nombre"], "bultos": lista_pres_m[i]["cantidad"], "pesos": pesos_clean, "promedio": prom_u, "total_kg": tot_k})

        tot_b_gral = sum(p['bultos'] for p in presentaciones_data)
        peso_tot_gral = sum(p['total_kg'] for p in presentaciones_data)
        prom_global = (peso_tot_gral / tot_b_gral) if tot_b_gral > 0 else 0.0
        peso_a_favor = payload - peso_tot_gral

        st.markdown("---")
        r1, r2, r3, r4 = st.columns(4)
        r1.metric("Bultos Totales", f"{tot_b_gral:,}")
        r2.metric("Promedio Global", f"{prom_global:.3f} kg")
        r3.metric("Peso Bruto", f"{peso_tot_gral:,.2f} kg")
        r4.metric("Margen a Favor", f"{peso_a_favor:,.2f} kg")

        cabecera_pdf_pesos = {"fecha": str(fec_desp), "contenedor": num_cont, "payload": payload, "responsable": nombre_user, "pi": pi_val, "booking": booking, "cliente": cliente, "destino": destino}
        resumen_pdf_pesos = {"total_bultos": tot_b_gral, "peso_total": peso_tot_gral, "promedio_global": prom_global, "peso_a_favor": peso_a_favor}

        try:
            pdf_pesos_bytes = generar_pdf_pesos_solos(cabecera_pdf_pesos, presentaciones_data, resumen_pdf_pesos)
            st.download_button("📄 Descargar PDF Pesos y Balanza", data=pdf_pesos_bytes, file_name=f"Pesos_{num_cont}.pdf", mime="application/pdf")
        except Exception:
            pass

    # =========================================================================
    # BOTÓN MAESTRO DE GUARDADO / ACTUALIZACIÓN (HOJA 'DISTRIBUCIONES')
    # =========================================================================
    st.markdown("---")
    if st.button(f"💾 Guardar / Actualizar Información de {num_cont or 'Contenedor'} en Sheets", type="primary", use_container_width=True):
        if not num_cont:
            st.warning("⚠️ Debe ingresar el N° de Contenedor antes de guardar.")
        else:
            try:
                # 1. Empaquetar presentaciones hasta 8 columnas (K hasta Z)
                pres_cols = []
                for idx in range(8):
                    if idx < len(lista_pres_m):
                        pres_cols.extend([lista_pres_m[idx]["nombre"], int(lista_pres_m[idx]["cantidad"])])
                    else:
                        pres_cols.extend(["", ""])

                # 2. Empaquetar detalle de lotes y fechas (Columna AI)
                detalle_lotes_str = " | ".join([f"{l['lote_txt']} ({l['fecha_txt']}): {l['cantidad']}b" for l in lista_lotes if l['cantidad'] > 0])

                # 3. Ensamblado exacto de fila (A hasta AI)
                fila_maestra = [
                    c_state["id_emb"],          # A: ID_EMBARQUE
                    str(num_cont).strip(),       # B: CONTENEDOR
                    str(mes_sel),                # C: MES
                    str(fec_desp),               # D: FECHA
                    str(pi_val).strip(),         # E: N°_PI
                    str(booking).strip(),        # F: BOOKING
                    str(cliente).strip(),        # G: CLIENTE
                    str(destino).strip(),        # H: Destino (País / Puerto)
                    str(pais_val).strip(),       # I: PAIS
                    str(nombre_user),            # J: supervisor
                    *pres_cols,                  # K a Z: PRESENTACION_1..8 y BULTOS_1..8
                    float(payload),              # AA: payload_contenedor
                    int(tot_b_gral),             # AB: total_bultos
                    float(round(peso_tot_gral, 2)), # AC: peso_bruto
                    float(round(peso_a_favor, 2)),  # AD: margen_a_favor
                    float(round(prom_global, 3)),   # AE: promedio_global
                    int(c_state["placas"]),      # AF: placas
                    int(c_state["tunel"]),       # AG: tunel
                    int(c_state["iqf"]),         # AH: iqf
                    detalle_lotes_str            # AI: detalle_lotes_fechas
                ]

                res_msg = guardar_o_actualizar_contenedor(get_gspread_client, fila_maestra)
                st.success(f"✅ Contenedor {num_cont} {res_msg} correctamente en la hoja 'DISTRIBUCIONES'.")
            except Exception as e:
                st.error(f"Error al conectar o guardar en Sheets: {e}")
