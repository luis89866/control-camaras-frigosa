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
# 1. PDF PLANOS DE ESTIBA (LOTES Y PRESENTACIONES)
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
            
            # Anchos calculados con holgura para evitar desbordes
            if num_cols > 3:
                w_prim = [40, 52, 55]
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

# =========================================================================
# 2. PDF TIPO DE CONGELADO (PLACAS / TÚNEL / IQF)
# =========================================================================
def generar_pdf_congelado(cabecera, df_estiba_sistema):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, leftMargin=20, rightMargin=20, topMargin=20, bottomMargin=20)
    story = []
    styles = getSampleStyleSheet()

    titulo_style = ParagraphStyle('TitF', parent=styles['Heading1'], fontSize=11, leading=13, textColor=colors.HexColor("#0D3B66"), alignment=1)
    sub_style = ParagraphStyle('SubF', parent=styles['Heading2'], fontSize=8, leading=10, textColor=colors.HexColor("#2B6CB0"), alignment=1)
    cell_head_style = ParagraphStyle('CH', parent=styles['Normal'], fontSize=6.5, leading=8.0, textColor=colors.white, alignment=1, fontName="Helvetica-Bold")

    story.append(Paragraph("DISTRIBUCIÓN POR SISTEMA: PLACAS / TÚNEL / IQF", titulo_style))
    story.append(Paragraph(f"CONTENEDOR: {cabecera['contenedor']} | FECHA: {cabecera['fecha']} | CLIENTE: {cabecera.get('cliente', '-')}", sub_style))
    story.append(Spacer(1, 8))

    cols = list(df_estiba_sistema.columns)
    w_col = 572 / len(cols)
    header_row = [Paragraph(str(c), cell_head_style) for c in cols]
    t_data = [header_row]

    for _, r in df_estiba_sistema.iterrows():
        t_data.append([str(r[c]) for c in cols])

    tot_row = ["TOTAL"]
    for c in cols[1:]:
        try:
            val_s = df_estiba_sistema[c].astype(float).sum()
            tot_row.append(f"{val_s:,.2f}" if "TM" in c.upper() else f"{int(val_s):,}")
        except Exception:
            tot_row.append("-")
    t_data.append(tot_row)

    t_pdf = Table(t_data, colWidths=[w_col] * len(cols))
    t_pdf.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 1), (-1, -1), 6.5),
        ('TOPPADDING', (0, 0), (-1, -1), 1.8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 1.8),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#D69E2E")),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor("#FEFCBF")),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.HexColor("#F7FAFC")]),
    ]))
    story.append(t_pdf)

    doc.build(story)
    buffer.seek(0)
    return buffer

# =========================================================================
# 3. PDF CONTROL DE PESOS (SOLO BALANZA Y LIQUIDACIÓN)
# =========================================================================
def generar_pdf_pesos_solos(cabecera, presentaciones_data, resumen):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, leftMargin=20, rightMargin=20, topMargin=20, bottomMargin=20)
    story = []
    styles = getSampleStyleSheet()

    titulo_style = ParagraphStyle('TitF', parent=styles['Heading1'], fontSize=11, leading=13, textColor=colors.HexColor("#0D3B66"), alignment=1)
    sub_style = ParagraphStyle('SubF', parent=styles['Heading2'], fontSize=8, leading=10, textColor=colors.HexColor("#2B6CB0"), alignment=1)
    cell_head_style = ParagraphStyle('CH', parent=styles['Normal'], fontSize=6.0, leading=7.5, textColor=colors.white, alignment=1, fontName="Helvetica-Bold")

    story.append(Paragraph("SEGUIMIENTO DE CONTROL DE PESO Y BALANZA - FRIGOSA SAC", titulo_style))
    story.append(Paragraph(f"CONTENEDOR: {cabecera['contenedor']} | SEMANA: {cabecera.get('semana', '-')} | PI: {cabecera.get('pi', '-')} | BOOKING: {cabecera.get('booking', '-')}", sub_style))
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

def obtener_hoja_google(get_gspread_client, nombre_hoja):
    client = get_gspread_client()
    try:
        sh = client.open_by_key(ID_SPREADSHEET_PRODUCCION)
    except Exception:
        sh = client.open("BD_PRODUCCION_ARCHI_001")
    return sh.worksheet(nombre_hoja)

def render_module(user, get_gspread_client):
    nombre_user = user.get("nombre_completo", user.get("usuario", "LUIS ENRIQUE FIESTAS ECA"))
    st.subheader("🚢 Módulo 4: Despachos, Estiba y Embarques")

    if "embarque_state" not in st.session_state:
        st.session_state.embarque_state = {
            "cont": "MSGU-101", "pay": 30400.0, "sem": 38, "nfil": 20,
            "cap_g": 67, "cap_f1": 77, "cap_fu": 67, "w_std": 21.68,
            "pi": "", "booking": "", "cliente": "Shandong sheenier", "destino": "Yantai china",
            "modo_congelacion": "Solo Placas (100% de la carga)",
            "txt_pesos": {},
            "lotes_input": [
                {"fecha": date.today(), "lote": generar_lote_juliano(date.today()), "bultos": 650},
                {"fecha": date.today(), "lote": generar_lote_juliano(date.today()), "bultos": 700}
            ]
        }

    c_state = st.session_state.embarque_state

    col_top1, col_top2 = st.columns([3, 1])
    with col_top2:
        if st.button("🧹 Limpiar Ventanas / Nuevo", help="Limpia todos los campos para iniciar otro contenedor", use_container_width=True):
            st.session_state.embarque_state = {
                "cont": "", "pay": 30400.0, "sem": 38, "nfil": 20,
                "cap_g": 67, "cap_f1": 77, "cap_fu": 67, "w_std": 20.0,
                "pi": "", "booking": "", "cliente": "", "destino": "",
                "modo_congelacion": "Solo Placas (100% de la carga)",
                "txt_pesos": {},
                "lotes_input": [
                    {"fecha": date.today(), "lote": generar_lote_juliano(date.today()), "bultos": 0}
                ]
            }
            st.rerun()

    with st.expander("⚙️ Datos de Cabecera y Booking (Global)", expanded=True):
        cp1, cp2, cp3, cp4 = st.columns(4)
        with cp1:
            fec_desp = st.date_input("Fecha Embarque:", date.today(), key="fec_emb_main")
            num_cont = st.text_input("N° Contenedor:", value=c_state.get("cont", ""), key="cont_emb_main")
            c_state["cont"] = num_cont
        with cp2:
            booking = st.text_input("Booking:", value=c_state.get("booking", ""), key="bk_emb_main")
            c_state["booking"] = booking
            pi_val = st.text_input("N° P.I. (Pedido):", value=c_state.get("pi", ""), key="pi_emb_main")
            c_state["pi"] = pi_val
        with cp3:
            cliente = st.text_input("Cliente:", value=c_state.get("cliente", ""), key="cli_emb_main")
            c_state["cliente"] = cliente
            destino = st.text_input("Destino (País/Puerto):", value=c_state.get("destino", ""), key="dest_emb_main")
            c_state["destino"] = destino
        with cp4:
            payload = st.number_input("Payload Máx (kg):", min_value=15000.0, max_value=33000.0, value=float(c_state.get("pay", 30400.0)), step=100.0, key="pay_emb_main")
            c_state["pay"] = payload
            semana_est = st.number_input("Semana N°:", min_value=1, max_value=53, value=int(c_state.get("sem", 38)), key="sem_emb_main")
            c_state["sem"] = semana_est

    tab_estiba_lotes, tab_estiba_pres, tab_placa_tunel, tab_pesos = st.tabs([
        "📅 1. Plano Estiba (Lotes)",
        "📦 2. Plano Estiba (Presentaciones)",
        "❄️ 3. Placas / Túnel / IQF",
        "⚖️ 4. Control de Pesos (Final)"
    ])

    # =========================================================================
    # TAB 1: PLANO ESTIBA POR LOTES
    # =========================================================================
    with tab_estiba_lotes:
        st.markdown("#### Configuración de Filas y Capacidad")
        cf1, cf2, cf3, cf4 = st.columns(4)
        with cf1:
            n_filas = st.number_input("Total Filas:", min_value=10, max_value=30, value=int(c_state["nfil"]), key="nfil_main")
            c_state["nfil"] = int(n_filas)
        with cf2:
            cap_gral = st.number_input("Capacidad Estándar Fila:", min_value=30, max_value=100, value=int(c_state["cap_g"]), key="capg_main")
            c_state["cap_g"] = int(cap_gral)
        with cf3:
            cap_f1 = st.number_input("Capacidad Fila 1 (Tope):", min_value=20, max_value=100, value=int(c_state["cap_f1"]), key="capf1_main")
            c_state["cap_f1"] = int(cap_f1)
        with cf4:
            cap_fult = st.number_input(f"Capacidad Fila {n_filas} (Puerta):", min_value=20, max_value=100, value=int(c_state["cap_fu"]), key="capfu_main")
            c_state["cap_fu"] = int(cap_fult)
            peso_std = st.number_input("Peso Estándar Bulto (kg):", value=float(c_state["w_std"]), step=0.1, key="wstd_main")
            c_state["w_std"] = float(peso_std)

        caps_filas_maestro = [int(cap_gral)] * int(n_filas)
        caps_filas_maestro[0] = int(cap_f1)
        caps_filas_maestro[-1] = int(cap_fult)
        c_state["cfg_filas"] = caps_filas_maestro

        st.markdown("---")
        st.markdown("#### Lotes a Cargar")
        n_lotes = st.number_input("Cantidad de Lotes:", min_value=1, max_value=10, value=len(c_state["lotes_input"]), key="nlot_main")

        while len(c_state["lotes_input"]) < n_lotes:
            c_state["lotes_input"].append({"fecha": date.today(), "lote": generar_lote_juliano(date.today()), "bultos": 0})
        while len(c_state["lotes_input"]) > n_lotes:
            c_state["lotes_input"].pop()

        cols_l = st.columns(int(n_lotes))
        lista_lotes = []

        for i, col in enumerate(cols_l):
            item_lote = c_state["lotes_input"][i]
            with col:
                fec_l = st.date_input(f"Fecha {i+1}:", value=item_lote["fecha"], key=f"fl_{i}_main")
                lote_sugerido = generar_lote_juliano(fec_l) if fec_l != item_lote["fecha"] else item_lote["lote"]
                cod_l = st.text_input(f"Lote {i+1}:", value=lote_sugerido, key=f"cl_{i}_main")
                cant_l = st.number_input(f"Bultos {i+1}:", min_value=0, value=int(item_lote["bultos"]), step=10, key=f"bl_{i}_main")

                item_lote["fecha"] = fec_l
                item_lote["lote"] = cod_l
                item_lote["bultos"] = int(cant_l)

                lista_lotes.append({
                    "fecha_txt": fec_l.strftime('%d/%m/%Y'),
                    "lote_txt": cod_l.strip(),
                    "cantidad": int(cant_l)
                })

        matriz_lotes = calcular_matriz_estiba(caps_filas_maestro, lista_lotes)
        headers_l = [f"{l['fecha_txt']} | {l['lote_txt']}" for l in lista_lotes]

        data_estiba = []
        for f_idx in range(int(n_filas)):
            bultos_f = sum(matriz_lotes[f_idx])
            tm_f = (bultos_f * peso_std) / 1000.0
            row_dict = {"N° FILA": f_idx + 1, "TM": round(tm_f, 4), "CANT/FILA": bultos_f}
            for l_i in range(len(lista_lotes)):
                row_dict[headers_l[l_i]] = matriz_lotes[f_idx][l_i]
            data_estiba.append(row_dict)

        df_lotes = pd.DataFrame(data_estiba)
        c_state["df_lotes"] = df_lotes
        c_state["lista_lotes"] = lista_lotes
        st.dataframe(df_lotes, hide_index=True, use_container_width=True, height=320)

        tot_b = sum(df_lotes["CANT/FILA"])
        tot_tm = sum(df_lotes["TM"])
        cap_max = sum(caps_filas_maestro)

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Capacidad Máx", f"{cap_max} bultos")
        m2.metric("Total Cargado", f"{tot_b} bultos")
        m3.metric("Tonelaje", f"{tot_tm:.3f} TM")
        m4.metric("Espacio Libre", f"{cap_max - tot_b} bultos")

    # =========================================================================
    # TAB 2: PLANO ESTIBA POR PRESENTACIONES (CORREGIDO SIN COLAPSO DE COLUMNAS)
    # =========================================================================
    with tab_estiba_pres:
        st.markdown("#### Presentaciones a Embarcar")
        np_m = st.number_input("Número de Presentaciones:", min_value=1, max_value=6, value=2, key="npm_main")
        cols_pm = st.columns(int(np_m))

        lista_pres_m = []
        for i, col in enumerate(cols_pm):
            with col:
                st.markdown(f"**Presentación {i+1}**")
                idx_def_p = 12 if i == 0 else (13 if i == 1 else 0)
                p_sel = st.selectbox(f"Corte {i+1}:", LISTA_PRESENTACIONES_FRIGOSA, index=min(idx_def_p, len(LISTA_PRESENTACIONES_FRIGOSA)-1), key=f"selp_{i}_main")
                nom_pm = st.text_input(f"Detalle {i+1}:", key=f"otrp_{i}_main") if p_sel == "OTRO (Digitar manualmente)" else p_sel.strip()
                cant_pm = st.number_input(f"Bultos {i+1}:", min_value=0, value=800 if i==0 else (550 if i==1 else 0), step=10, key=f"cantp_{i}_main")
                peso_pm = st.number_input(f"Peso Promedio (kg) {i+1}:", value=21.68 if i==0 else 20.0, step=0.05, key=f"wpr_{i}_main")
                lista_pres_m.append({"nombre": nom_pm, "cantidad": int(cant_pm), "peso_unit": float(peso_pm)})

        matriz_m = calcular_matriz_estiba(caps_filas_maestro, lista_pres_m)
        
        # Encabezado único garantizado para no colapsar columnas duplicadas
        headers_m = [f"{p['nombre']} (P{idx_p+1})" for idx_p, p in enumerate(lista_pres_m)]

        data_pres = []
        for f_idx in range(len(caps_filas_maestro)):
            bultos_f = sum(matriz_m[f_idx])
            tm_f = sum(matriz_m[f_idx][p_i] * lista_pres_m[p_i]['peso_unit'] for p_i in range(len(lista_pres_m))) / 1000.0
            row_d = {"N° FILA": f_idx + 1, "TM ESTIMADO": round(tm_f, 4), "TOTAL BULTOS": bultos_f}
            for p_i in range(len(lista_pres_m)):
                row_d[headers_m[p_i]] = matriz_m[f_idx][p_i]
            data_pres.append(row_d)

        df_pres = pd.DataFrame(data_pres)
        c_state["df_pres"] = df_pres
        c_state["lista_pres_m"] = lista_pres_m
        st.dataframe(df_pres, hide_index=True, use_container_width=True, height=320)

        st.markdown("---")
        st.markdown("#### 📄 Acciones de Distribución (PDF + Guardar en Sheets)")
        cabecera_estiba = {
            "contenedor": num_cont.strip(),
            "booking": booking.strip(),
            "pi": pi_val.strip(),
            "cliente": cliente.strip(),
            "fecha": str(fec_desp)
        }

        col_d1, col_d2 = st.columns(2)
        with col_d1:
            try:
                pdf_planos_bytes = generar_pdf_planos_estiba(cabecera_estiba, df_lotes, df_pres)
                st.download_button(
                    label="📄 Descargar PDF Distribución (Lotes + Pres)",
                    data=pdf_planos_bytes,
                    file_name=f"Distribucion_{num_cont}_{fec_desp}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
            except Exception as e:
                st.warning(f"Error generando PDF Distribución: {e}")

        with col_d2:
            if st.button("💾 Guardar en Hoja 'DISTRIBUCIONES'", use_container_width=True, key="btn_save_distribuciones"):
                try:
                    ws_dist = obtener_hoja_google(get_gspread_client, "DISTRIBUCIONES")
                    id_dp = f"DSP-{date.today().strftime('%y%m%d%H%M%S')}"
                    
                    detalle_pres_txt = " | ".join([f"{p['nombre']}: {p['cantidad']}b" for p in lista_pres_m if p['cantidad'] > 0])
                    detalle_lotes_txt = " | ".join([f"{l['lote_txt']} ({l['fecha_txt']}): {l['cantidad']}b" for l in lista_lotes if l['cantidad'] > 0])

                    fila_dist = [
                        id_dp,
                        str(fec_desp),
                        str(num_cont).strip(),
                        str(pi_val).strip(),
                        str(booking).strip(),
                        str(cliente).strip(),
                        str(destino).strip(),
                        str(nombre_user),
                        detalle_pres_txt,
                        detalle_lotes_txt
                    ]
                    ws_dist.append_row(fila_dist)
                    st.success(f"✅ Distribución del contenedor {num_cont} guardada en hoja 'DISTRIBUCIONES'.")
                except Exception as ex:
                    st.error(f"Error al guardar en Sheets: {ex}")

    # =========================================================================
    # TAB 3: PLACAS / TÚNEL / IQF + PDF Y GUARDADO EN 'tipo_de_congelado'
    # =========================================================================
    with tab_placa_tunel:
        st.markdown("#### Selección de Sistema de Congelación")
        
        modo_sistema = st.radio(
            "Seleccionar tipo de carga predominante:",
            ["Solo Placas (100% de la carga)", "Solo Túnel (100% de la carga)", "Mixto (Personalizado fila por fila)"],
            index=0 if c_state.get("modo_congelacion") == "Solo Placas (100% de la carga)" else (1 if c_state.get("modo_congelacion") == "Solo Túnel (100% de la carga)" else 2),
            horizontal=True,
            key="rad_modo_main"
        )
        c_state["modo_congelacion"] = modo_sistema

        data_sist = []
        for f_idx in range(len(caps_filas_maestro)):
            bultos_target = caps_filas_maestro[f_idx]
            if modo_sistema == "Solo Placas (100% de la carga)":
                p_val, t_val, iqf_val = bultos_target, 0, 0
            elif modo_sistema == "Solo Túnel (100% de la carga)":
                p_val, t_val, iqf_val = 0, bultos_target, 0
            else:
                p_val = bultos_target if f_idx < 10 else 0
                t_val = bultos_target if f_idx >= 10 else 0
                iqf_val = 0

            data_sist.append({
                "N° FILA": f_idx + 1,
                "TM": round((bultos_target * peso_std) / 1000.0, 4),
                "PLACAS": p_val,
                "TUNEL": t_val,
                "IQF": iqf_val,
                "TOTAL": bultos_target
            })

        df_sist_editor = pd.DataFrame(data_sist)

        if modo_sistema == "Mixto (Personalizado fila por fila)":
            st.info("💡 Edita las cantidades de Placas, Túnel o IQF directamente en la tabla:")
            df_editado = st.data_editor(
                df_sist_editor,
                disabled=["N° FILA", "TM", "TOTAL"],
                hide_index=True,
                use_container_width=True,
                height=320,
                key="editor_sist_main"
            )
            df_editado["TOTAL"] = df_editado["PLACAS"] + df_editado["TUNEL"] + df_editado["IQF"]
            df_editado["TM"] = round((df_editado["TOTAL"] * peso_std) / 1000.0, 4)
            df_final_sist = df_editado
        else:
            st.dataframe(df_sist_editor, hide_index=True, use_container_width=True, height=320)
            df_final_sist = df_sist_editor

        c_state["df_sist"] = df_final_sist

        tot_placas = int(df_final_sist["PLACAS"].sum())
        tot_tunel = int(df_final_sist["TUNEL"].sum())
        tot_iqf = int(df_final_sist["IQF"].sum())

        s1, s2, s3, s4 = st.columns(4)
        s1.metric("Total Placas", f"{tot_placas:,} b")
        s2.metric("Total Túnel", f"{tot_tunel:,} b")
        s3.metric("Total IQF", f"{tot_iqf:,} b")
        s4.metric("Total General", f"{tot_placas + tot_tunel + tot_iqf:,} b")

        st.markdown("---")
        st.markdown("#### 📄 Acciones de Congelación (PDF + Guardar en Sheets)")
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            try:
                pdf_cong_bytes = generar_pdf_congelado(cabecera_estiba, df_final_sist)
                st.download_button(
                    label="📄 Descargar PDF Placas / Túnel / IQF",
                    data=pdf_cong_bytes,
                    file_name=f"Congelacion_{num_cont}_{fec_desp}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
            except Exception as e:
                st.warning(f"Error generando PDF Congelado: {e}")

        with col_c2:
            if st.button("💾 Guardar en Hoja 'tipo_de_congelado'", use_container_width=True, key="btn_save_congelado"):
                try:
                    ws_cong = obtener_hoja_google(get_gspread_client, "tipo_de_congelado")
                    id_dp = f"DSP-{date.today().strftime('%y%m%d%H%M%S')}"

                    fila_cong = [
                        id_dp,
                        str(fec_desp),
                        str(num_cont).strip(),
                        str(pi_val).strip(),
                        str(booking).strip(),
                        str(cliente).strip(),
                        str(destino).strip(),
                        str(nombre_user),
                        int(tot_placas),
                        int(tot_tunel),
                        int(tot_iqf)
                    ]
                    ws_cong.append_row(fila_cong)
                    st.success(f"✅ Datos de congelación del contenedor {num_cont} guardados en 'tipo_de_congelado'.")
                except Exception as ex:
                    st.error(f"Error al guardar en Sheets: {ex}")

    # =========================================================================
    # TAB 4: CONTROL DE PESOS + PDF Y GUARDADO EN 'pesos'
    # =========================================================================
    with tab_pesos:
        st.markdown(f"#### Control de Balanza y Liquidación de Carga")
        st.caption(f"Contenedor: **{num_cont}** | PI: **{pi_val}** | Destino: **{destino}**")

        lista_pres_reg = c_state.get("lista_pres_m", [])
        num_pres_pesos = st.number_input("Presentaciones a Evaluar:", min_value=1, max_value=6, value=max(len(lista_pres_reg), 1), key="npw_main")
        cols_w = st.columns(int(num_pres_pesos))
        presentaciones_data = []

        for i, col in enumerate(cols_w):
            with col:
                st.markdown(f"**Presentación {i+1}**")
                def_nom = lista_pres_reg[i]["nombre"] if i < len(lista_pres_reg) else LISTA_PRESENTACIONES_FRIGOSA[0]
                idx_sel = LISTA_PRESENTACIONES_FRIGOSA.index(def_nom) if def_nom in LISTA_PRESENTACIONES_FRIGOSA else 0
                p_nom = st.selectbox(f"Producto {i+1}:", LISTA_PRESENTACIONES_FRIGOSA, index=idx_sel, key=f"pwp_{i}_main")

                def_cant = lista_pres_reg[i]["cantidad"] if i < len(lista_pres_reg) else 1350
                bultos_val = st.number_input(f"Bultos {i+1}:", min_value=0, value=def_cant, step=10, key=f"bwp_{i}_main")

                val_pesos_def = c_state.get("txt_pesos", {}).get(str(i), "21.60, 21.75, 21.65, 21.70, 21.62")
                txt_p = st.text_area(
                    "Pesos balanza (hasta 20):",
                    value=val_pesos_def,
                    height=100,
                    key=f"pesos_txt_{i}_main"
                )
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
                prom_u = (sum(pesos_clean) / len(pesos_clean)) if pesos_clean else float(c_state.get("w_std", 21.68))
                tot_k = prom_u * bultos_val
                st.caption(f"Muestras: **{len(pesos_clean)}/20** | Prom: **{prom_u:.3f} kg**")
                st.caption(f"Subtotal: **{tot_k:,.1f} kg**")

                presentaciones_data.append({"nombre": p_nom, "bultos": bultos_val, "pesos": pesos_clean, "promedio": prom_u, "total_kg": tot_k})

        tot_b_gral = sum(p['bultos'] for p in presentaciones_data)
        peso_tot_gral = sum(p['total_kg'] for p in presentaciones_data)
        prom_global = (peso_tot_gral / tot_b_gral) if tot_b_gral > 0 else 0.0
        peso_a_favor = payload - peso_tot_gral

        st.markdown("---")
        st.markdown("### 📊 Liquidación Final de Pesaje")
        r1, r2, r3, r4 = st.columns(4)
        r1.metric("Bultos Totales", f"{tot_b_gral:,}")
        r2.metric("Promedio Global", f"{prom_global:.3f} kg")
        r3.metric("Peso Neto Total", f"{peso_tot_gral:,.2f} kg")
        r4.metric("Margen a Favor", f"{peso_a_favor:,.2f} kg", delta=f"{peso_a_favor:,.2f} kg", delta_color="normal" if peso_a_favor >= 0 else "inverse")

        if peso_a_favor < 0:
            st.error(f"🚨 **SOBREPESO:** Contenedor excede el Payload por **{abs(peso_a_favor):,.2f} kg**.")
        else:
            st.success(f"✅ **CARGA PERMITIDA:** Margen de seguridad de **{peso_a_favor:,.2f} kg**.")

        cabecera_pdf_pesos = {
            "fecha": str(fec_desp),
            "contenedor": num_cont.strip(),
            "payload": payload,
            "semana": semana_est,
            "responsable": nombre_user,
            "pi": pi_val,
            "booking": booking,
            "cliente": cliente,
            "destino": destino
        }
        resumen_pdf_pesos = {
            "total_bultos": tot_b_gral,
            "peso_total": peso_tot_gral,
            "promedio_global": prom_global,
            "peso_a_favor": peso_a_favor
        }

        col_w1, col_w2 = st.columns(2)
        with col_w1:
            try:
                pdf_pesos_bytes = generar_pdf_pesos_solos(cabecera_pdf_pesos, presentaciones_data, resumen_pdf_pesos)
                st.download_button(
                    label="📄 Descargar PDF Control de Pesos",
                    data=pdf_pesos_bytes,
                    file_name=f"Pesos_{num_cont}_{fec_desp}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
            except Exception as e:
                st.warning(f"Error generando PDF Pesos: {e}")

        with col_w2:
            if st.button("💾 Guardar en Hoja 'pesos'", use_container_width=True, key="btn_save_pesos"):
                try:
                    ws_pesos = obtener_hoja_google(get_gspread_client, "pesos")
                    id_dp = f"DSP-{date.today().strftime('%y%m%d%H%M%S')}"

                    fila_pesos = [
                        id_dp,
                        str(fec_desp),
                        str(num_cont).strip(),
                        str(pi_val).strip(),
                        str(booking).strip(),
                        str(cliente).strip(),
                        str(destino).strip(),
                        str(nombre_user),
                        float(payload),
                        int(tot_b_gral),
                        float(round(peso_tot_gral, 2)),
                        float(round(peso_a_favor, 2)),
                        float(round(prom_global, 3))
                    ]
                    ws_pesos.append_row(fila_pesos)
                    st.success(f"✅ Control de pesos del contenedor {num_cont} guardado exitosamente en hoja 'pesos'.")
                except Exception as ex:
                    st.error(f"Error al guardar en Sheets: {ex}")
