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
# REPORTES EN PDF
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
        ('FONTSIZE', (0, 1), (-1, -1), 6.5),
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
# LÓGICA DE SHEETS (CON PERSISTENCIA Y ANTI-DUPLICADOS)
# =========================================================================
def obtener_hoja_distribuciones(get_gspread_client):
    client = get_gspread_client()
    try:
        sh = client.open_by_key(ID_SPREADSHEET_PRODUCCION)
    except Exception:
        sh = client.open("BD_PRODUCCION_ARCHI_001")
    return sh.worksheet("DISTRIBUCIONES")

def guardar_o_actualizar_contenedor(get_gspread_client, datos_fila, forzar_nuevo=False):
    ws = obtener_hoja_distribuciones(get_gspread_client)
    contenedores_col = ws.col_values(2)  # Columna B: CONTENEDOR
    num_cont = str(datos_fila[1]).strip().upper()

    fila_idx = None
    for idx, c_val in enumerate(contenedores_col):
        if str(c_val).strip().upper() == num_cont and idx > 0:
            fila_idx = idx + 1
            break

    if forzar_nuevo and fila_idx:
        return False, f"El contenedor '{num_cont}' ya existe en la fila {fila_idx}. Cambie al modo 'Cargar / Editar' para modificarlo."

    if fila_idx:
        rango = f"A{fila_idx}:AO{fila_idx}"
        ws.update(rango, [datos_fila])
        return True, f"Actualizado exitosamente (Fila {fila_idx})"
    else:
        ws.append_row(datos_fila)
        return True, "Registrado como nuevo registro"

# =========================================================================
# MÓDULO PRINCIPAL
# =========================================================================
def render_module(user, get_gspread_client):
    nombre_user = user.get("nombre_completo", user.get("usuario", "LUIS ENRIQUE FIESTAS ECA"))
    st.subheader("🚢 Módulo 4: Despachos, Estiba y Embarques")

    if "form_version" not in st.session_state:
        st.session_state.form_version = 0

    if "emb_id" not in st.session_state:
        st.session_state.emb_id = f"EMB-{date.today().strftime('%y%m%d%H%M%S')}"
    if "cont_val" not in st.session_state:
        st.session_state.cont_val = ""
    if "fec_val" not in st.session_state:
        st.session_state.fec_val = date.today()
    if "mes_val" not in st.session_state:
        st.session_state.mes_val = MESES_ESP.get(date.today().month, "SETIEMBRE")
    if "pi_val" not in st.session_state:
        st.session_state.pi_val = ""
    if "bk_val" not in st.session_state:
        st.session_state.bk_val = ""
    if "cli_val" not in st.session_state:
        st.session_state.cli_val = "Shandong sheenier"
    if "dest_val" not in st.session_state:
        st.session_state.dest_val = "Yantai china"
    if "pais_val" not in st.session_state:
        st.session_state.pais_val = "CHINA"
    if "pay_val" not in st.session_state:
        st.session_state.pay_val = 30400.0

    if "nfil_val" not in st.session_state:
        st.session_state.nfil_val = 18
    if "capg_val" not in st.session_state:
        st.session_state.capg_val = 75
    if "capf1_val" not in st.session_state:
        st.session_state.capf1_val = 75
    if "capfu_val" not in st.session_state:
        st.session_state.capfu_val = 75
    if "wstd_val" not in st.session_state:
        st.session_state.wstd_val = 20.00

    if "pres_items" not in st.session_state:
        st.session_state.pres_items = [
            {"nombre": "FF C/M C/T 2000 g/pza - 4000 g/pza MANTO ", "bultos": 800, "peso": 20.00},
            {"nombre": "FF C/M C/T 2000 g/pza - 4000 g/pza CORTADO ", "bultos": 550, "peso": 20.00}
        ]
    if "lotes_items" not in st.session_state:
        st.session_state.lotes_items = [
            {"fecha": date.today(), "lote": generar_lote_juliano(date.today()), "bultos": 650},
            {"fecha": date.today(), "lote": generar_lote_juliano(date.today()), "bultos": 700}
        ]
    if "txt_pesos_mem" not in st.session_state:
        st.session_state.txt_pesos_mem = {}

    v = st.session_state.form_version

    col_sel1, col_sel2 = st.columns([3, 1])
    with col_sel1:
        try:
            ws_d = obtener_hoja_distribuciones(get_gspread_client)
            registros = ws_d.get_all_values()
        except Exception:
            registros = []

        modo_operacion = st.radio(
            "Modo de Trabajo:",
            ["Nuevo Contenedor", "Cargar / Editar Contenedor Existente"],
            horizontal=True
        )

        if modo_operacion == "Cargar / Editar Contenedor Existente" and len(registros) > 1:
            st.markdown("##### 🔍 Buscar Contenedor Registrado")
            c_f1, c_f2 = st.columns([1.5, 2])
            with c_f1:
                ver_todos = st.checkbox("Ver todo el histórico", value=False)
                if not ver_todos:
                    fecha_filtro = st.date_input("Filtrar por Fecha de Despacho:", value=date.today(), key="f_filtro_cont")
            
            # Filtro inteligente de contenedores
            opciones_conts = []
            for r in registros[1:]:
                if len(r) > 3 and r[1].strip():
                    c_num = r[1].strip()
                    c_fec = r[3].strip()
                    c_cli = r[6].strip() if len(r) > 6 else ""
                    
                    if ver_todos:
                        opciones_conts.append((c_num, f"{c_num} | {c_fec} | {c_cli}"))
                    else:
                        if c_fec == str(fecha_filtro):
                            opciones_conts.append((c_num, f"{c_num} | {c_fec} | {c_cli}"))

            with c_f2:
                if opciones_conts:
                    map_display = {disp: c_id for c_id, disp in opciones_conts}
                    sel_display = st.selectbox("Seleccionar Contenedor encontrado:", list(map_display.keys()))
                    cont_seleccionado = map_display[sel_display]
                else:
                    st.info("No hay contenedores registrados en la fecha elegida.")
                    cont_seleccionado = None

            if cont_seleccionado and st.button("📥 Cargar Datos de este Contenedor"):
                fila_encontrada = None
                for r in registros[1:]:
                    if len(r) > 1 and r[1].strip() == cont_seleccionado:
                        fila_encontrada = r
                        break

                if fila_encontrada:
                    st.session_state.emb_id = fila_encontrada[0]
                    st.session_state.cont_val = fila_encontrada[1].strip()
                    st.session_state.mes_val = fila_encontrada[2].strip() if len(fila_encontrada) > 2 and fila_encontrada[2].strip() else "SETIEMBRE"
                    
                    try:
                        st.session_state.fec_val = datetime.strptime(fila_encontrada[3].strip(), "%Y-%m-%d").date()
                    except Exception:
                        st.session_state.fec_val = date.today()

                    st.session_state.pi_val = fila_encontrada[4].strip() if len(fila_encontrada) > 4 else ""
                    st.session_state.bk_val = fila_encontrada[5].strip() if len(fila_encontrada) > 5 else ""
                    st.session_state.cli_val = fila_encontrada[6].strip() if len(fila_encontrada) > 6 else ""
                    st.session_state.dest_val = fila_encontrada[7].strip() if len(fila_encontrada) > 7 else ""
                    st.session_state.pais_val = fila_encontrada[8].strip() if len(fila_encontrada) > 8 else "CHINA"

                    try:
                        st.session_state.pay_val = float(fila_encontrada[26]) if len(fila_encontrada) > 26 and fila_encontrada[26].strip() else 30400.0
                    except Exception:
                        st.session_state.pay_val = 30400.0

                    try:
                        if len(fila_encontrada) > 35 and fila_encontrada[35].strip():
                            st.session_state.nfil_val = int(fila_encontrada[35].strip())
                        if len(fila_encontrada) > 36 and fila_encontrada[36].strip():
                            st.session_state.capg_val = int(fila_encontrada[36].strip())
                        if len(fila_encontrada) > 37 and fila_encontrada[37].strip():
                            st.session_state.capf1_val = int(fila_encontrada[37].strip())
                        if len(fila_encontrada) > 38 and fila_encontrada[38].strip():
                            st.session_state.capfu_val = int(fila_encontrada[38].strip())
                        if len(fila_encontrada) > 39 and fila_encontrada[39].strip():
                            st.session_state.wstd_val = float(fila_encontrada[39].strip())
                    except Exception:
                        pass

                    cargadas_pres = []
                    for p_i in range(10, 26, 2):
                        if len(fila_encontrada) > p_i + 1:
                            nom_p = fila_encontrada[p_i].strip()
                            cant_str = fila_encontrada[p_i + 1].strip()
                            if nom_p and cant_str:
                                try:
                                    cargadas_pres.append({"nombre": nom_p, "bultos": int(cant_str), "peso": st.session_state.wstd_val})
                                except Exception:
                                    pass
                    if cargadas_pres:
                        st.session_state.pres_items = cargadas_pres

                    if len(fila_encontrada) > 34 and fila_encontrada[34].strip():
                        det_lotes_str = fila_encontrada[34].strip()
                        partes_l = det_lotes_str.split(" | ")
                        nuevos_lotes = []
                        for pl in partes_l:
                            try:
                                cod_lote = pl.split(" (")[0].strip()
                                rest = pl.split(" (")[1]
                                fec_str = rest.split("): ")[0].strip()
                                b_val = int(rest.split("): ")[1].replace("b", "").strip())
                                f_obj = datetime.strptime(fec_str, "%d/%m/%Y").date()
                                nuevos_lotes.append({"fecha": f_obj, "lote": cod_lote, "bultos": b_val})
                            except Exception:
                                pass
                        if nuevos_lotes:
                            st.session_state.lotes_items = nuevos_lotes

                    if len(fila_encontrada) > 40 and fila_encontrada[40].strip():
                        raw_pesos = fila_encontrada[40].strip().split(" ;; ")
                        st.session_state.txt_pesos_mem = {}
                        for item_p in raw_pesos:
                            if "::" in item_p:
                                p_idx, p_vals = item_p.split("::", 1)
                                st.session_state.txt_pesos_mem[p_idx.strip()] = p_vals.strip()

                    # Resetear tablas editadas para regenerar con nueva data
                    if "df_congelado_edit" in st.session_state:
                        del st.session_state["df_congelado_edit"]
                    if "df_lotes_editor" in st.session_state:
                        del st.session_state["df_lotes_editor"]

                    st.session_state.form_version += 1
                    st.success(f"✅ ¡Contenedor {cont_seleccionado} cargado con éxito!")
                    st.rerun()

    with col_sel2:
        if st.button("🧹 Limpiar Pantalla"):
            st.session_state.emb_id = f"EMB-{date.today().strftime('%y%m%d%H%M%S')}"
            st.session_state.cont_val = ""
            st.session_state.fec_val = date.today()
            st.session_state.mes_val = MESES_ESP.get(date.today().month, "SETIEMBRE")
            st.session_state.pi_val = ""
            st.session_state.bk_val = ""
            st.session_state.cli_val = ""
            st.session_state.dest_val = ""
            st.session_state.pais_val = ""
            st.session_state.pay_val = 30400.0
            st.session_state.nfil_val = 18
            st.session_state.capg_val = 75
            st.session_state.capf1_val = 75
            st.session_state.capfu_val = 75
            st.session_state.wstd_val = 20.00
            st.session_state.pres_items = [{"nombre": LISTA_PRESENTACIONES_FRIGOSA[0], "bultos": 0, "peso": 20.0}]
            st.session_state.lotes_items = [{"fecha": date.today(), "lote": generar_lote_juliano(date.today()), "bultos": 0}]
            st.session_state.txt_pesos_mem = {}
            if "df_congelado_edit" in st.session_state:
                del st.session_state["df_congelado_edit"]
            if "df_lotes_editor" in st.session_state:
                del st.session_state["df_lotes_editor"]
            st.session_state.form_version += 1
            st.rerun()

    # --- CABECERA ---
    with st.expander("⚙️ Datos Principales del Contenedor", expanded=True):
        cp1, cp2, cp3, cp4 = st.columns(4)
        with cp1:
            st.session_state.fec_val = st.date_input("Fecha:", value=st.session_state.fec_val, key=f"fec_emb_{v}")
            st.session_state.cont_val = st.text_input("N° Contenedor:", value=st.session_state.cont_val, key=f"cont_emb_{v}").upper().strip()
            mes_idx = list(MESES_ESP.values()).index(st.session_state.mes_val) if st.session_state.mes_val in MESES_ESP.values() else 8
            st.session_state.mes_val = st.selectbox("Mes:", list(MESES_ESP.values()), index=mes_idx, key=f"mes_emb_{v}")
        with cp2:
            st.session_state.bk_val = st.text_input("Booking:", value=st.session_state.bk_val, key=f"bk_emb_{v}").strip()
            st.session_state.pi_val = st.text_input("N° P.I. (Pedido):", value=st.session_state.pi_val, key=f"pi_emb_{v}").strip()
        with cp3:
            st.session_state.cli_val = st.text_input("Cliente:", value=st.session_state.cli_val, key=f"cli_emb_{v}").strip()
            st.session_state.dest_val = st.text_input("Destino (Puerto):", value=st.session_state.dest_val, key=f"dest_emb_{v}").strip()
        with cp4:
            st.session_state.pais_val = st.text_input("País:", value=st.session_state.pais_val, key=f"pais_emb_{v}").strip().upper()
            st.session_state.pay_val = st.number_input("Payload Máx (kg):", min_value=15000.0, max_value=34000.0, value=float(st.session_state.pay_val), step=100.0, key=f"pay_emb_{v}")

    tab_estiba_lotes, tab_estiba_pres, tab_placa_tunel, tab_pesos = st.tabs([
        "📅 1. Plano Estiba (Lotes)",
        "📦 2. Plano Estiba (Presentaciones)",
        "❄️ 3. Placas / Túnel / IQF",
        "⚖️ 4. Control de Pesos (Balanza)"
    ])

    # =========================================================================
    # TAB 1: LOTES (CON BALANCEO Y EDICIÓN MANUAL LIBRE)
    # =========================================================================
    with tab_estiba_lotes:
        st.markdown("#### Configuración de Filas y Capacidad")
        cf1, cf2, cf3, cf4 = st.columns(4)
        with cf1:
            st.session_state.nfil_val = int(st.number_input("Total Filas:", min_value=10, max_value=30, value=int(st.session_state.nfil_val), key=f"nfil_{v}"))
        with cf2:
            st.session_state.capg_val = int(st.number_input("Capacidad Estándar Fila:", min_value=20, max_value=100, value=int(st.session_state.capg_val), key=f"capg_{v}"))
        with cf3:
            st.session_state.capf1_val = int(st.number_input("Capacidad Fila 1:", min_value=20, max_value=100, value=int(st.session_state.capf1_val), key=f"capf1_{v}"))
        with cf4:
            st.session_state.capfu_val = int(st.number_input(f"Capacidad Fila {st.session_state.nfil_val}:", min_value=20, max_value=100, value=int(st.session_state.capfu_val), key=f"capfu_{v}"))
            st.session_state.wstd_val = float(st.number_input("Peso Estándar Bulto (kg):", value=float(st.session_state.wstd_val), step=0.1, key=f"wstd_{v}"))

        caps_filas_base = [int(st.session_state.capg_val)] * int(st.session_state.nfil_val)
        caps_filas_base[0] = int(st.session_state.capf1_val)
        caps_filas_base[-1] = int(st.session_state.capfu_val)

        n_lotes = st.number_input("Cantidad de Lotes:", min_value=1, max_value=10, value=max(len(st.session_state.lotes_items), 1), key=f"nlot_c_{v}")
        while len(st.session_state.lotes_items) < n_lotes:
            st.session_state.lotes_items.append({"fecha": date.today(), "lote": generar_lote_juliano(date.today()), "bultos": 0})
        while len(st.session_state.lotes_items) > n_lotes:
            st.session_state.lotes_items.pop()

        cols_l = st.columns(int(n_lotes))
        lista_lotes_calc = []
        for i, col in enumerate(cols_l):
            item_l = st.session_state.lotes_items[i]
            with col:
                fl = st.date_input(f"Fecha {i+1}:", value=item_l["fecha"], key=f"fl_{i}_{v}")
                lot_txt = st.text_input(f"Lote {i+1}:", value=item_l["lote"], key=f"cl_{i}_{v}")
                bl = st.number_input(f"Bultos {i+1}:", min_value=0, value=int(item_l["bultos"]), step=10, key=f"bl_{i}_{v}")
                item_l["fecha"] = fl
                item_l["lote"] = lot_txt
                item_l["bultos"] = int(bl)
                lista_lotes_calc.append({"fecha_txt": fl.strftime('%d/%m/%Y'), "lote_txt": lot_txt.strip(), "cantidad": int(bl)})

        headers_l = [f"{l['fecha_txt']} | {l['lote_txt']}" for l in lista_lotes_calc]

        # Si el DataFrame no existe o cambió el tamaño de filas o columnas, inicializar cálculo
        if "df_lotes_editor" not in st.session_state or len(st.session_state.df_lotes_editor) != int(st.session_state.nfil_val):
            matriz_lotes_init = calcular_matriz_estiba(caps_filas_base, lista_lotes_calc)
            data_init = []
            for f_idx in range(int(st.session_state.nfil_val)):
                b_f = sum(matriz_lotes_init[f_idx])
                r_dict = {"N° FILA": f_idx + 1, "TM": round((b_f * float(st.session_state.wstd_val)) / 1000.0, 4), "CANT/FILA": b_f}
                for l_i in range(len(lista_lotes_calc)):
                    r_dict[headers_l[l_i]] = matriz_lotes_init[f_idx][l_i]
                data_init.append(r_dict)
            st.session_state.df_lotes_editor = pd.DataFrame(data_init)

        st.info("💡 Puedes editar directamente los bultos en cada fila para balancear (+1, -1, etc.).")
        
        df_lotes_editado = st.data_editor(
            st.session_state.df_lotes_editor,
            disabled=["N° FILA", "TM", "CANT/FILA"],
            hide_index=True,
            use_container_width=True,
            height=300,
            key=f"editor_lotes_{v}_{st.session_state.nfil_val}"
        )

        # Recálculo en tiempo real de filas y tonelajes tras edición manual
        cols_lote_activas = [c for c in df_lotes_editado.columns if c not in ["N° FILA", "TM", "CANT/FILA"]]
        df_lotes_editado["CANT/FILA"] = df_lotes_editado[cols_lote_activas].sum(axis=1)
        df_lotes_editado["TM"] = round((df_lotes_editado["CANT/FILA"] * float(st.session_state.wstd_val)) / 1000.0, 4)
        st.session_state.df_lotes_editor = df_lotes_editado

        # ESTA LISTA ES LA MATRIZ MAESTRA REAL DE BULTOS POR FILA QUE ALIMENTA TODO EL SISTEMA
        caps_filas_reales = df_lotes_editado["CANT/FILA"].tolist()

        tot_b_cargados = sum(caps_filas_reales)
        tot_tm_cargados = sum(df_lotes_editado["TM"])

        m1, m2 = st.columns(2)
        m1.metric("Total Bultos Cargados (Lotes)", f"{tot_b_cargados:,} bultos")
        m2.metric("Tonelaje Total", f"{tot_tm_cargados:.3f} TM")

    # =========================================================================
    # TAB 2: PRESENTACIONES (ALIMENTADA DE LA MATRIZ REAL DE LOTES)
    # =========================================================================
    with tab_estiba_pres:
        st.markdown("#### Presentaciones a Embarcar (Hasta 8 según la hoja)")
        np_m = st.number_input("Número de Presentaciones:", min_value=1, max_value=8, value=max(len(st.session_state.pres_items), 1), key=f"npres_c_{v}")
        while len(st.session_state.pres_items) < np_m:
            st.session_state.pres_items.append({"nombre": LISTA_PRESENTACIONES_FRIGOSA[0], "bultos": 0, "peso": st.session_state.wstd_val})
        while len(st.session_state.pres_items) > np_m:
            st.session_state.pres_items.pop()

        cols_p = st.columns(int(np_m))
        lista_pres_calc = []
        for i, col in enumerate(cols_p):
            p_item = st.session_state.pres_items[i]
            with col:
                st.markdown(f"**Presentación {i+1}**")
                idx_p_sel = LISTA_PRESENTACIONES_FRIGOSA.index(p_item["nombre"]) if p_item["nombre"] in LISTA_PRESENTACIONES_FRIGOSA else 0
                sel_nom = st.selectbox(f"Corte {i+1}:", LISTA_PRESENTACIONES_FRIGOSA, index=idx_p_sel, key=f"sp_{i}_{v}")
                cant_b = st.number_input(f"Bultos {i+1}:", min_value=0, value=int(p_item["bultos"]), step=10, key=f"bp_{i}_{v}")
                p_item["nombre"] = sel_nom
                p_item["bultos"] = int(cant_b)
                lista_pres_calc.append({"nombre": sel_nom, "cantidad": int(cant_b), "peso_unit": float(p_item.get("peso", st.session_state.wstd_val))})

        # Estiba calculada respetando los bultos reales por fila ajustados en Tab 1
        matriz_pres = calcular_matriz_estiba(caps_filas_reales, lista_pres_calc)
        headers_pres = [f"{p['nombre']} (P{idx+1})" for idx, p in enumerate(lista_pres_calc)]
        data_pres = []
        for f_idx in range(len(caps_filas_reales)):
            b_f = sum(matriz_pres[f_idx])
            tm_f = sum(matriz_pres[f_idx][p_i] * lista_pres_calc[p_i]['peso_unit'] for p_i in range(len(lista_pres_calc))) / 1000.0
            r_d = {"N° FILA": f_idx + 1, "TM ESTIMADO": round(tm_f, 4), "TOTAL BULTOS": b_f}
            for p_i in range(len(lista_pres_calc)):
                r_d[headers_pres[p_i]] = matriz_pres[f_idx][p_i]
            data_pres.append(r_d)

        df_pres = pd.DataFrame(data_pres)
        st.dataframe(df_pres, hide_index=True, use_container_width=True, height=280)

        cabecera_estiba = {
            "contenedor": st.session_state.cont_val,
            "booking": st.session_state.bk_val,
            "pi": st.session_state.pi_val,
            "cliente": st.session_state.cli_val,
            "fecha": str(st.session_state.fec_val)
        }
        try:
            pdf_planos = generar_pdf_planos_estiba(cabecera_estiba, df_lotes_editado, df_pres)
            st.download_button("📄 Descargar PDF Distribución (Lotes + Pres)", data=pdf_planos, file_name=f"Distribucion_{st.session_state.cont_val}.pdf", mime="application/pdf")
        except Exception:
            pass

    # =========================================================================
    # TAB 3: PLACAS / TÚNEL / IQF (ALIMENTADA DE LA MATRIZ REAL DE LOTES)
    # =========================================================================
    with tab_placa_tunel:
        st.markdown("#### Configuración de Sistema de Congelación")

        def on_change_modo_cong():
            opc = st.session_state.get(f"rad_cong_{v}")
            num_f = len(caps_filas_reales)
            if opc == "Mixto (Ingreso Manual Fila por Fila)":
                filas_clean = []
                for f_idx in range(num_f):
                    filas_clean.append({
                        "N° FILA": f_idx + 1,
                        "TM": 0.0,
                        "PLACAS": 0,
                        "TUNEL": 0,
                        "IQF": 0,
                        "TOTAL": 0
                    })
                st.session_state.df_congelado_edit = pd.DataFrame(filas_clean)

        modo_cong_opc = st.radio(
            "Carga predominante:",
            ["Solo Placas (100% de la carga)", "Solo Túnel (100% de la carga)", "Mixto (Ingreso Manual Fila por Fila)"],
            horizontal=True,
            key=f"rad_cong_{v}",
            on_change=on_change_modo_cong
        )

        num_filas_actual = len(caps_filas_reales)

        if "df_congelado_edit" not in st.session_state or len(st.session_state.df_congelado_edit) != num_filas_actual:
            filas_sist = []
            for f_idx in range(num_filas_actual):
                cap_f = caps_filas_reales[f_idx]
                filas_sist.append({
                    "N° FILA": f_idx + 1,
                    "TM": round((cap_f * float(st.session_state.wstd_val)) / 1000.0, 4),
                    "PLACAS": cap_f,
                    "TUNEL": 0,
                    "IQF": 0,
                    "TOTAL": cap_f
                })
            st.session_state.df_congelado_edit = pd.DataFrame(filas_sist)

        df_editor_source = st.session_state.df_congelado_edit.copy()

        if modo_cong_opc == "Solo Placas (100% de la carga)":
            for idx in range(num_filas_actual):
                cap_f = caps_filas_reales[idx]
                df_editor_source.at[idx, "PLACAS"] = cap_f
                df_editor_source.at[idx, "TUNEL"] = 0
                df_editor_source.at[idx, "IQF"] = 0
                df_editor_source.at[idx, "TOTAL"] = cap_f
        elif modo_cong_opc == "Solo Túnel (100% de la carga)":
            for idx in range(num_filas_actual):
                cap_f = caps_filas_reales[idx]
                df_editor_source.at[idx, "PLACAS"] = 0
                df_editor_source.at[idx, "TUNEL"] = cap_f
                df_editor_source.at[idx, "IQF"] = 0
                df_editor_source.at[idx, "TOTAL"] = cap_f

        st.info("💡 En 'Mixto' la tabla se limpia en 0 para digitar directamente fila por fila:")
        
        df_congelado_resultado = st.data_editor(
            df_editor_source,
            disabled=["N° FILA", "TM", "TOTAL"],
            hide_index=True,
            use_container_width=True,
            height=320,
            key=f"grid_cong_{v}_{num_filas_actual}"
        )

        df_congelado_resultado["TOTAL"] = df_congelado_resultado["PLACAS"] + df_congelado_resultado["TUNEL"] + df_congelado_resultado["IQF"]
        df_congelado_resultado["TM"] = round((df_congelado_resultado["TOTAL"] * float(st.session_state.wstd_val)) / 1000.0, 4)
        st.session_state.df_congelado_edit = df_congelado_resultado

        tot_placas_sum = int(df_congelado_resultado["PLACAS"].sum())
        tot_tunel_sum = int(df_congelado_resultado["TUNEL"].sum())
        tot_iqf_sum = int(df_congelado_resultado["IQF"].sum())

        s1, s2, s3, s4 = st.columns(4)
        s1.metric("Total Placas", f"{tot_placas_sum:,} b")
        s2.metric("Total Túnel", f"{tot_tunel_sum:,} b")
        s3.metric("Total IQF", f"{tot_iqf_sum:,} b")
        s4.metric("Total Congelado", f"{tot_placas_sum + tot_tunel_sum + tot_iqf_sum:,} b")

        try:
            pdf_cong = generar_pdf_congelado(cabecera_estiba, df_congelado_resultado)
            st.download_button("📄 Descargar PDF Placas / Túnel / IQF", data=pdf_cong, file_name=f"Congelacion_{st.session_state.cont_val}.pdf", mime="application/pdf")
        except Exception:
            pass

    # =========================================================================
    # TAB 4: CONTROL DE PESOS
    # =========================================================================
    with tab_pesos:
        st.markdown("#### Pesos de Balanza")
        cols_w = st.columns(max(len(lista_pres_calc), 1))
        presentaciones_data = []

        for i, col in enumerate(cols_w):
            with col:
                st.markdown(f"**{lista_pres_calc[i]['nombre'][:20]}**")
                val_mem = st.session_state.txt_pesos_mem.get(str(i), "20.00, 20.05, 19.98")
                txt_p = st.text_area(f"Pesos balanza ({i+1}):", value=val_mem, height=90, key=f"pw_box_{i}_{v}")
                st.session_state.txt_pesos_mem[str(i)] = txt_p

                pesos_clean = []
                for p in txt_p.replace("\n", ",").split(","):
                    try:
                        val_num = float(p.strip())
                        if val_num > 0:
                            pesos_clean.append(val_num)
                    except Exception:
                        pass
                pesos_clean = pesos_clean[:20]
                prom_u = (sum(pesos_clean) / len(pesos_clean)) if pesos_clean else float(st.session_state.wstd_val)
                tot_k = prom_u * lista_pres_calc[i]["cantidad"]
                st.caption(f"Prom: **{prom_u:.3f} kg** | Subtotal: **{tot_k:,.1f} kg**")
                presentaciones_data.append({
                    "nombre": lista_pres_calc[i]["nombre"],
                    "bultos": lista_pres_calc[i]["cantidad"],
                    "pesos": pesos_clean,
                    "promedio": prom_u,
                    "total_kg": tot_k
                })

        tot_b_gral = sum(p['bultos'] for p in presentaciones_data)
        peso_tot_gral = sum(p['total_kg'] for p in presentaciones_data)
        prom_global = (peso_tot_gral / tot_b_gral) if tot_b_gral > 0 else 0.0
        peso_a_favor = float(st.session_state.pay_val) - peso_tot_gral

        st.markdown("---")
        r1, r2, r3, r4 = st.columns(4)
        r1.metric("Bultos Totales", f"{tot_b_gral:,}")
        r2.metric("Promedio Global", f"{prom_global:.3f} kg")
        r3.metric("Peso Bruto", f"{peso_tot_gral:,.2f} kg")
        r4.metric("Margen a Favor", f"{peso_a_favor:,.2f} kg")

        cabecera_pdf_pesos = {
            "fecha": str(st.session_state.fec_val),
            "contenedor": st.session_state.cont_val,
            "payload": float(st.session_state.pay_val),
            "responsable": nombre_user,
            "pi": st.session_state.pi_val,
            "booking": st.session_state.bk_val,
            "cliente": st.session_state.cli_val,
            "destino": st.session_state.dest_val
        }
        resumen_pdf_pesos = {
            "total_bultos": tot_b_gral,
            "peso_total": peso_tot_gral,
            "promedio_global": prom_global,
            "peso_a_favor": peso_a_favor
        }

        try:
            pdf_pesos_bytes = generar_pdf_pesos_solos(cabecera_pdf_pesos, presentaciones_data, resumen_pdf_pesos)
            st.download_button("📄 Descargar PDF Pesos y Balanza", data=pdf_pesos_bytes, file_name=f"Pesos_{st.session_state.cont_val}.pdf", mime="application/pdf")
        except Exception:
            pass

    # =========================================================================
    # GUARDADO / ACTUALIZACIÓN CENTRALIZADO (ANTI-DUPLICADOS)
    # =========================================================================
    st.markdown("---")
    btn_label = f"💾 Guardar / Actualizar Información de {st.session_state.cont_val or 'Contenedor'} en Sheets"
    if st.button(btn_label, type="primary", use_container_width=True):
        if not st.session_state.cont_val.strip():
            st.warning("⚠️ Debe ingresar el N° de Contenedor antes de guardar.")
        else:
            try:
                pres_cols = []
                for idx in range(8):
                    if idx < len(lista_pres_calc):
                        pres_cols.extend([lista_pres_calc[idx]["nombre"], int(lista_pres_calc[idx]["cantidad"])])
                    else:
                        pres_cols.extend(["", ""])

                detalle_lotes_str = " | ".join([f"{l['lote_txt']} ({l['fecha_txt']}): {l['cantidad']}b" for l in lista_lotes_calc if l['cantidad'] > 0])

                serial_pesos = []
                for k_p, v_p in st.session_state.txt_pesos_mem.items():
                    clean_v = v_p.replace("\n", " ").strip()
                    if clean_v:
                        serial_pesos.append(f"{k_p}::{clean_v}")
                detalle_pesos_str = " ;; ".join(serial_pesos)

                fila_maestra = [
                    st.session_state.emb_id,                       # A: ID_EMBARQUE
                    str(st.session_state.cont_val).strip(),        # B: CONTENEDOR
                    str(st.session_state.mes_val),                 # C: MES
                    str(st.session_state.fec_val),                # D: FECHA
                    str(st.session_state.pi_val).strip(),          # E: N°_PI
                    str(st.session_state.bk_val).strip(),          # F: BOOKING
                    str(st.session_state.cli_val).strip(),         # G: CLIENTE
                    str(st.session_state.dest_val).strip(),        # H: Destino
                    str(st.session_state.pais_val).strip(),        # I: PAIS
                    str(nombre_user),                              # J: supervisor
                    *pres_cols,                                    # K a Z: PRESENTACION_1..8 y BULTOS_1..8
                    float(st.session_state.pay_val),               # AA: payload_contenedor
                    int(tot_b_gral),                               # AB: total_bultos
                    float(round(peso_tot_gral, 2)),               # AC: peso_bruto
                    float(round(peso_a_favor, 2)),                # AD: margen_a_favor
                    float(round(prom_global, 3)),                 # AE: promedio_global
                    int(tot_placas_sum),                           # AF: placas
                    int(tot_tunel_sum),                            # AG: tunel
                    int(tot_iqf_sum),                              # AH: iqf
                    detalle_lotes_str,                             # AI: detalle_lotes_fechas
                    int(st.session_state.nfil_val),                # AJ: total_filas
                    int(st.session_state.capg_val),                # AK: cap_estandar_fila
                    int(st.session_state.capf1_val),               # AL: cap_fila_1
                    int(st.session_state.capfu_val),               # AM: cap_fila_puerta
                    float(st.session_state.wstd_val),              # AN: peso_std_bulto
                    detalle_pesos_str                              # AO: detalle_pesos_balanza
                ]

                es_modo_nuevo = (modo_operacion == "Nuevo Contenedor")
                ok, res_msg = guardar_o_actualizar_contenedor(get_gspread_client, fila_maestra, forzar_nuevo=es_modo_nuevo)

                if ok:
                    st.success(f"✅ Contenedor {st.session_state.cont_val} {res_msg} en 'DISTRIBUCIONES'.")
                else:
                    st.error(f"🚫 {res_msg}")
            except Exception as e:
                st.error(f"Error al guardar en Sheets: {e}") 
