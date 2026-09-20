import streamlit as st
import pandas as pd
from datetime import date, datetime
import io
import base64
import urllib.parse
from PIL import Image as PILImage, ImageOps
import streamlit.components.v1 as components
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image as RLImage
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

def optimizar_bytes_imagen(b_in, max_side=900, calidad=65):
    """Comprime la imagen para garantizar almacenamiento eficiente sin desbordar celdas."""
    if not b_in:
        return None
    try:
        img = PILImage.open(io.BytesIO(b_in))
        img = ImageOps.exif_transpose(img)
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        orig_w, orig_h = img.size
        if max(orig_w, orig_h) > max_side:
            ratio = max_side / float(max(orig_w, orig_h))
            nuevo_tamano = (int(orig_w * ratio), int(orig_h * ratio))
            img = img.resize(nuevo_tamano, PILImage.LANCZOS)
            
        buf = io.BytesIO()
        img.save(buf, format='JPEG', quality=calidad, optimize=True)
        return buf.getvalue()
    except Exception:
        return b_in

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
# GESTIÓN PERSISTENTE DE FOTOS EN SHEETS CON CHUNKING (SIN LÍMITE DE CELDA)
# =========================================================================
def obtener_hoja_adjuntos_fotos(get_gspread_client):
    client = get_gspread_client()
    try:
        sh = client.open_by_key(ID_SPREADSHEET_PRODUCCION)
    except Exception:
        sh = client.open("BD_PRODUCCION_ARCHI_001")
    
    try:
        return sh.worksheet("ADJUNTOS_FOTOS")
    except Exception:
        ws = sh.add_worksheet(title="ADJUNTOS_FOTOS", rows=1000, cols=6)
        ws.append_row(["CONTENEDOR", "TIPO_FOTO", "PARTE", "FECHA_REGISTRO", "BASE64_DATA"])
        return ws

def guardar_foto_en_sheets(get_gspread_client, num_contenedor, tipo_foto, b_data):
    if not b_data or not num_contenedor:
        return
    try:
        ws = obtener_hoja_adjuntos_fotos(get_gspread_client)
        registros = ws.get_all_values()
        num_c_clean = str(num_contenedor).strip().upper()
        tipo_clean = str(tipo_foto).strip().upper()
        fec_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        b64_full = base64.b64encode(b_data).decode('utf-8')
        tamano_chunk = 30000
        partes = [b64_full[i:i + tamano_chunk] for i in range(0, len(b64_full), tamano_chunk)]

        filas_a_eliminar = []
        for idx, r in enumerate(registros):
            if len(r) > 1 and r[0].strip().upper() == num_c_clean and r[1].strip().upper() == tipo_clean and idx > 0:
                filas_a_eliminar.append(idx + 1)

        for f_del in reversed(filas_a_eliminar):
            ws.delete_rows(f_del)

        nuevas_filas = []
        for idx_p, trozo in enumerate(partes):
            nuevas_filas.append([num_c_clean, tipo_clean, str(idx_p + 1), fec_actual, trozo])

        if nuevas_filas:
            ws.append_rows(nuevas_filas)
    except Exception as e:
        st.warning(f"Error al registrar foto en Sheets: {e}")

def recuperar_fotos_de_sheets(get_gspread_client, num_contenedor):
    resultado = {"IR": None, "TEMP": None, "PACK": None}
    if not num_contenedor:
        return resultado
    try:
        ws = obtener_hoja_adjuntos_fotos(get_gspread_client)
        registros = ws.get_all_values()
        num_c_clean = str(num_contenedor).strip().upper()

        chunks_dict = {"IR": {}, "TEMP": {}, "PACK": {}}

        for r in registros[1:]:
            if len(r) > 4 and r[0].strip().upper() == num_c_clean:
                t_f = r[1].strip().upper()
                try:
                    num_parte = int(r[2].strip())
                except Exception:
                    num_parte = 1
                trozo = r[4].strip()

                if t_f in chunks_dict:
                    chunks_dict[t_f][num_parte] = trozo

        for clave in ["IR", "TEMP", "PACK"]:
            partes_ord = chunks_dict[clave]
            if partes_ord:
                b64_unido = "".join([partes_ord[k] for k in sorted(partes_ord.keys())])
                try:
                    resultado[clave] = base64.b64decode(b64_unido)
                except Exception:
                    pass

        return resultado
    except Exception:
        return resultado

# =========================================================================
# ESCALADO DE IMAGEN: 1 PÁGINA EXACTA POR FOTO
# =========================================================================
def crear_imagen_maximizada(b_data, max_w=540, max_h=510):
    try:
        pil_img = PILImage.open(io.BytesIO(b_data))
        orig_w, orig_h = pil_img.size

        ratio = min(max_w / orig_w, max_h / orig_h)
        final_w = orig_w * ratio
        final_h = orig_h * ratio

        img_io = io.BytesIO(b_data)
        return RLImage(img_io, width=final_w, height=final_h)
    except Exception:
        return None

# =========================================================================
# TABLAS DE ESTIBA EN PDF
# =========================================================================
def construir_flowables_tabla_estiba(df_in, titulo_tab, color_header, cabecera, styles):
    elementos = []
    if df_in is None or df_in.empty:
        return elementos

    titulo_style = ParagraphStyle('TitF', parent=styles['Heading1'], fontSize=10.5, leading=12, textColor=colors.HexColor("#0D3B66"), alignment=1)
    sub_style = ParagraphStyle('SubF', parent=styles['Heading2'], fontSize=7.5, leading=9.5, textColor=colors.HexColor("#2B6CB0"), alignment=1)
    
    cols_totales = list(df_in.columns)
    cols_fijas = ["N° FILA", "TM", "CANT/FILA"] if "CANT/FILA" in cols_totales else ["N° FILA", "TM ESTIMADO", "TOTAL BULTOS"]
    cols_dinamicas = [c for c in cols_totales if c not in cols_fijas]
    num_lotes = len(cols_dinamicas)

    tamano_bloque = 8 if num_lotes <= 8 else 5
    bloques = [cols_dinamicas[i:i + tamano_bloque] for i in range(0, len(cols_dinamicas), tamano_bloque)]
    if not bloques:
        bloques = [[]]

    for num_b, bloque_cols in enumerate(bloques):
        if num_b > 0:
            elementos.append(PageBreak())

        sub_sufijo = f" (PARTE {num_b + 1})" if len(bloques) > 1 else ""
        elementos.append(Paragraph(titulo_tab + sub_sufijo, titulo_style))
        elementos.append(Paragraph(f"CONTENEDOR: {cabecera['contenedor']} | FECHA: {cabecera['fecha']} | CLIENTE: {cabecera.get('cliente', '-')}", sub_style))
        elementos.append(Spacer(1, 4))

        cols_actuales = cols_fijas + bloque_cols
        total_cols = len(cols_actuales)

        if total_cols > 9:
            f_size = 4.8
            leading_h = 5.8
            w_fijas = [28, 40, 42]
        elif total_cols > 6:
            f_size = 5.3
            leading_h = 6.4
            w_fijas = [32, 44, 46]
        else:
            f_size = 6.0
            leading_h = 7.2
            w_fijas = [38, 50, 52]

        cell_head_style = ParagraphStyle('CH', parent=styles['Normal'], fontSize=f_size, leading=leading_h, textColor=colors.white, alignment=1, fontName="Helvetica-Bold")
        num_din = len(bloque_cols)
        w_resto = (576 - sum(w_fijas)) / max(num_din, 1)
        col_widths = w_fijas + [w_resto] * num_din

        header_row = [Paragraph(str(c).replace(" | ", "<br/>").replace("\n", "<br/>"), cell_head_style) for c in cols_actuales]
        t_data = [header_row]

        for _, r in df_in.iterrows():
            row_vals = []
            for c in cols_actuales:
                val = r[c]
                if isinstance(val, (int, float)):
                    row_vals.append(f"{val:.2f}" if ("TM" in c.upper()) else str(int(val)))
                else:
                    row_vals.append(str(val))
            t_data.append(row_vals)

        tot_row = []
        for idx_c, col_name in enumerate(cols_actuales):
            if idx_c == 0:
                tot_row.append("TOTAL")
            else:
                try:
                    sum_val = df_in[col_name].astype(float).sum()
                    tot_row.append(f"{sum_val:,.2f}" if "TM" in col_name.upper() else f"{int(sum_val):,}")
                except Exception:
                    tot_row.append("-")
            t_data.append(tot_row)

        t_pdf = Table(t_data, colWidths=col_widths)
        t_pdf.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 1), (-1, -1), f_size),
            ('TOPPADDING', (0, 0), (-1, -1), 1.1),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 1.1),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(color_header)),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor("#FEFCBF")),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.HexColor("#F7FAFC")]),
        ]))
        elementos.append(t_pdf)

    return elementos

# =========================================================================
# DOSSIER UNIFICADO COMPLETO
# =========================================================================
def generar_dossier_unificado(cabecera, df_lotes, df_pres, df_sistema, presentaciones_data, resumen, foto_ir_bytes=None, foto_temp_bytes=None, foto_pack_bytes=None):
    buffer_dossier = io.BytesIO()
    doc = SimpleDocTemplate(buffer_dossier, pagesize=letter, leftMargin=18, rightMargin=18, topMargin=18, bottomMargin=18)
    story = []
    styles = getSampleStyleSheet()

    titulo_style = ParagraphStyle('TitD', parent=styles['Heading1'], fontSize=11, leading=13, textColor=colors.HexColor("#0D3B66"), alignment=1)
    sub_style = ParagraphStyle('SubD', parent=styles['Heading2'], fontSize=8, leading=10, textColor=colors.HexColor("#2B6CB0"), alignment=1)
    cell_head_style = ParagraphStyle('CHD', parent=styles['Normal'], fontSize=6.0, leading=7.5, textColor=colors.white, alignment=1, fontName="Helvetica-Bold")

    # PÁGINA 1: FICHA LOGÍSTICA Y CONTROL DE PESOS
    story.append(Paragraph("EXPEDIENTE TÉCNICO Y CONTROL DE EMBARQUE - FRIGOSA SAC", titulo_style))
    story.append(Paragraph(f"CONTENEDOR: {cabecera['contenedor']} | PI: {cabecera.get('pi', '-')} | BOOKING: {cabecera.get('booking', '-')}", sub_style))
    story.append(Spacer(1, 5))

    data_cab = [
        ["FECHA:", cabecera['fecha'], "N° CONTENEDOR:", cabecera['contenedor']],
        ["CLIENTE:", cabecera.get('cliente', '-'), "DESTINO:", cabecera.get('destino', '-')],
        ["BOOKING:", cabecera.get('booking', '-'), "P.I. (PEDIDO):", cabecera.get('pi', '-')],
        ["PAYLOAD MÁX (KG):", f"{cabecera['payload']:,.2f}", "PESO BRUTO ESTIMADO:", f"{resumen['peso_total']:,.2f} KG"],
        ["TOTAL BULTOS:", f"{resumen['total_bultos']:,}", "MARGEN (A FAVOR):", f"{resumen['peso_a_favor']:,.2f} KG"],
        ["SUPERVISOR DE EMBARQUE:", "LUIS ENRIQUE FIESTAS ECA", "PROMEDIO GLOBAL:", f"{resumen['promedio_global']:.3f} KG"]
    ]
    t_cab = Table(data_cab, colWidths=[140, 140, 115, 177])
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
    story.append(Spacer(1, 6))

    if presentaciones_data:
        headers_w = [Paragraph(f"<b>{p['nombre'].strip()}</b>", cell_head_style) for p in presentaciones_data]
        matrix_pesos = [headers_w]
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

    # PÁGINA 2: PLANO DE LOTES (1 PÁGINA EXACTA)
    if df_lotes is not None and not df_lotes.empty:
        story.append(PageBreak())
        story.extend(construir_flowables_tabla_estiba(df_lotes, "PLANO DE ESTIBA POR FECHAS Y LOTES - FRIGOSA SAC", "#2B6CB0", cabecera, styles))

    # PÁGINA 3: PLANO DE PRESENTACIONES
    if df_pres is not None and not df_pres.empty:
        story.append(PageBreak())
        story.extend(construir_flowables_tabla_estiba(df_pres, "PLANO DE ESTIBA POR PRESENTACIONES - FRIGOSA SAC", "#2F855A", cabecera, styles))

    # PÁGINA 4: DISTRIBUCIÓN POR SISTEMA
    if df_sistema is not None and not df_sistema.empty:
        story.append(PageBreak())
        story.append(Paragraph("DISTRIBUCIÓN POR SISTEMA: PLACAS / TÚNEL / IQF", titulo_style))
        story.append(Paragraph(f"CONTENEDOR: {cabecera['contenedor']} | FECHA: {cabecera['fecha']} | CLIENTE: {cabecera.get('cliente', '-')}", sub_style))
        story.append(Spacer(1, 6))

        cols_s = list(df_sistema.columns)
        w_s = 572 / len(cols_s)
        h_s = [Paragraph(str(c), cell_head_style) for c in cols_s]
        t_s_data = [h_s]
        for _, r in df_sistema.iterrows():
            t_s_data.append([str(r[c]) for c in cols_s])

        tot_s = ["TOTAL"]
        for c in cols_s[1:]:
            try:
                val_s = df_sistema[c].astype(float).sum()
                tot_s.append(f"{val_s:,.2f}" if "TM" in c.upper() else f"{int(val_s):,}")
            except Exception:
                tot_s.append("-")
        t_s_data.append(tot_s)

        t_s_pdf = Table(t_s_data, colWidths=[w_s] * len(cols_s))
        t_s_pdf.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 1), (-1, -1), 6.5),
            ('TOPPADDING', (0, 0), (-1, -1), 1.5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 1.5),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#D69E2E")),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor("#FEFCBF")),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.HexColor("#F7FAFC")]),
        ]))
        story.append(t_s_pdf)

    # ANEXOS FOTOGRÁFICOS: 1 PÁGINA LIMPIA POR FOTO
    fotos_anexo = [
        ("ANEXO: REPORTE DE INSPECCIÓN (IR / EIR)", "REGISTRO FOTOGRÁFICO DE INSPECCIÓN TÉCNICA DEL CONTENEDOR", foto_ir_bytes),
        ("ANEXO: CONTROL DE TEMPERATURA / TERMOKING", "REGISTRO VISUAL DEL DISPLAY DE TEMPERATURA DE SETEO / SALIDA", foto_temp_bytes),
        ("ANEXO: PACKING LIST / GUÍA DE EMBARQUE", "REGISTRO FOTOGRÁFICO DEL PACKING LIST OFICIAL DE PLANTA", foto_pack_bytes)
    ]

    for tit_anexo, sub_rotulo, b_img in fotos_anexo:
        if b_img:
            story.append(PageBreak())
            story.append(Paragraph(tit_anexo, titulo_style))
            story.append(Paragraph(f"CONTENEDOR: {cabecera['contenedor']} | SUPERVISOR: LUIS ENRIQUE FIESTAS ECA", sub_style))
            story.append(Spacer(1, 4))

            rl_img = crear_imagen_maximizada(b_img, max_w=540, max_h=510)
            if rl_img:
                lbl = Paragraph(f"<b>{sub_rotulo}</b>", ParagraphStyle('LblT', parent=styles['Normal'], fontSize=7.5, leading=9.5, alignment=1, textColor=colors.HexColor("#1A365D")))
                t_foto = Table([[rl_img], [lbl]], colWidths=[540])
                t_foto.setStyle(TableStyle([
                    ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                    ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                    ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E0")),
                    ('BACKGROUND', (0,1), (-1,1), colors.HexColor("#F7FAFC")),
                    ('TOPPADDING', (0,0), (-1,-1), 2),
                    ('BOTTOMPADDING', (0,0), (-1,-1), 2),
                ]))
                story.append(t_foto)

    doc.build(story)
    buffer_dossier.seek(0)
    return buffer_dossier

# =========================================================================
# HOJA DISTRIBUCIONES (REGISTRO MAESTRO)
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
    contenedores_col = ws.col_values(2)
    num_cont = str(datos_fila[1]).strip().upper()

    fila_idx = None
    for idx, c_val in enumerate(contenedores_col):
        if str(c_val).strip().upper() == num_cont and idx > 0:
            fila_idx = idx + 1
            break

    if forzar_nuevo and fila_idx:
        return False, f"El contenedor '{num_cont}' ya existe en la fila {fila_idx}. Cambie al modo 'Cargar / Editar' para modificarlo."

    if fila_idx:
        rango = f"A{fila_idx}:AR{fila_idx}"
        ws.update(rango, [datos_fila])
        return True, f"Actualizado exitosamente (Fila {fila_idx})"
    else:
        ws.append_row(datos_fila)
        return True, "Registrado como nuevo registro"

# =========================================================================
# MÓDULO PRINCIPAL
# =========================================================================
def render_module(user, get_gspread_client):
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

    if "fotos_contenedor_db" not in st.session_state:
        st.session_state.fotos_contenedor_db = {}

    v = st.session_state.form_version

    # =========================================================================
    # BARRA SUPERIOR
    # =========================================================================
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
                    fecha_filtro = st.date_input("Filtrar por Fecha:", value=date.today(), key="f_filtro_cont")
            
            opciones_conts = []
            for r in registros[1:]:
                if len(r) > 3 and r[1].strip():
                    c_num = r[1].strip()
                    c_fec = r[3].strip()
                    c_cli = r[6].strip() if len(r) > 6 else ""
                    if ver_todos or c_fec == str(fecha_filtro):
                        opciones_conts.append((c_num, f"{c_num} | {c_fec} | {c_cli}"))

            with c_f2:
                if opciones_conts:
                    map_display = {disp: c_id for c_id, disp in opciones_conts}
                    sel_display = st.selectbox("Seleccionar Contenedor:", list(map_display.keys()))
                    cont_seleccionado = map_display[sel_display]
                else:
                    st.info("No hay contenedores en la fecha seleccionada.")
                    cont_seleccionado = None

            c_btn_c1, c_btn_c2 = st.columns([1.5, 2])
            with c_btn_c1:
                btn_cargar_datos = st.button("📥 Cargar en Pantalla", use_container_width=True) if cont_seleccionado else False

            if btn_cargar_datos:
                fila_encontrada = None
                for r in registros[1:]:
                    if len(r) > 1 and r[1].strip() == cont_seleccionado:
                        fila_encontrada = r
                        break

                if fila_encontrada:
                    st.session_state.emb_id = fila_encontrada[0]
                    num_c_cargado = fila_encontrada[1].strip()
                    st.session_state.cont_val = num_c_cargado
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

                    with st.spinner("Sincronizando fotos guardadas desde la base de datos..."):
                        fotos_recuperadas = recuperar_fotos_de_sheets(get_gspread_client, num_c_cargado)
                        if num_c_cargado not in st.session_state.fotos_contenedor_db:
                            st.session_state.fotos_contenedor_db[num_c_cargado] = {}
                        
                        db_c = st.session_state.fotos_contenedor_db[num_c_cargado]
                        db_c["bytes_ir"] = fotos_recuperadas.get("IR")
                        db_c["bytes_temp"] = fotos_recuperadas.get("TEMP")
                        db_c["bytes_pack"] = fotos_recuperadas.get("PACK")

                    if "df_congelado_edit" in st.session_state:
                        del st.session_state["df_congelado_edit"]
                    if "caps_filas_override" in st.session_state:
                        del st.session_state["caps_filas_override"]

                    st.session_state.form_version += 1
                    st.success(f"✅ ¡Contenedor {num_c_cargado} cargado con sus fotos!")
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
            if "caps_filas_override" in st.session_state:
                del st.session_state["caps_filas_override"]
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

    # =========================================================================
    # PREPARACIÓN DE MATRICES
    # =========================================================================
    caps_filas_default = [int(st.session_state.capg_val)] * int(st.session_state.nfil_val)
    caps_filas_default[0] = int(st.session_state.capf1_val)
    caps_filas_default[-1] = int(st.session_state.capfu_val)

    if "caps_filas_override" not in st.session_state or len(st.session_state.caps_filas_override) != int(st.session_state.nfil_val):
        st.session_state.caps_filas_override = caps_filas_default.copy()

    caps_reales_actuales = [int(x) for x in st.session_state.caps_filas_override]

    # Matriz Lotes
    lista_lotes_mem = [{"fecha_txt": l["fecha"].strftime('%d/%m/%Y'), "lote_txt": l["lote"].strip(), "cantidad": int(l["bultos"])} for l in st.session_state.lotes_items]
    headers_l = [f"{l['fecha_txt']} | {l['lote_txt']}" for l in lista_lotes_mem]
    matriz_lotes_auto = calcular_matriz_estiba(caps_reales_actuales, lista_lotes_mem)

    data_filas_tabla = []
    for f_idx in range(int(st.session_state.nfil_val)):
        b_f = caps_reales_actuales[f_idx]
        tm_f = round((b_f * float(st.session_state.wstd_val)) / 1000.0, 4)
        r_dict = {"N° FILA": f_idx + 1, "TM": tm_f, "CANT/FILA": b_f}
        for l_i in range(len(lista_lotes_mem)):
            r_dict[headers_l[l_i]] = matriz_lotes_auto[f_idx][l_i]
        data_filas_tabla.append(r_dict)
    df_lotes_global = pd.DataFrame(data_filas_tabla)

    # Matriz Presentaciones
    lista_pres_mem = [{"nombre": p["nombre"], "cantidad": int(p["bultos"]), "peso_unit": float(p.get("peso", st.session_state.wstd_val))} for p in st.session_state.pres_items]
    matriz_pres_auto = calcular_matriz_estiba(caps_reales_actuales, lista_pres_mem)
    headers_pres = [f"{p['nombre']} (P{idx+1})" for idx, p in enumerate(lista_pres_mem)]
    data_pres_tabla = []
    for f_idx in range(len(caps_reales_actuales)):
        b_f = sum(matriz_pres_auto[f_idx])
        tm_f = sum(matriz_pres_auto[f_idx][p_i] * lista_pres_mem[p_i]['peso_unit'] for p_i in range(len(lista_pres_mem))) / 1000.0
        r_d = {"N° FILA": f_idx + 1, "TM ESTIMADO": round(tm_f, 4), "TOTAL BULTOS": b_f}
        for p_i in range(len(lista_pres_mem)):
            r_d[headers_pres[p_i]] = matriz_pres_auto[f_idx][p_i]
        data_pres_tabla.append(r_d)
    df_pres_global = pd.DataFrame(data_pres_tabla)

    # Matriz Congelado
    if "df_congelado_edit" not in st.session_state or len(st.session_state.df_congelado_edit) != len(caps_reales_actuales):
        filas_sist_init = []
        for f_idx in range(len(caps_reales_actuales)):
            cap_f = caps_reales_actuales[f_idx]
            filas_sist_init.append({
                "N° FILA": f_idx + 1,
                "TM": round((cap_f * float(st.session_state.wstd_val)) / 1000.0, 4),
                "PLACAS": cap_f,
                "TUNEL": 0,
                "IQF": 0,
                "TOTAL": cap_f
            })
        st.session_state.df_congelado_edit = pd.DataFrame(filas_sist_init)

    # Pesos
    presentaciones_data_global = []
    for i, p_item in enumerate(lista_pres_mem):
        val_mem = st.session_state.txt_pesos_mem.get(str(i), "20.00, 20.05, 19.98")
        pesos_clean = []
        for p in val_mem.replace("\n", ",").split(","):
            try:
                val_num = float(p.strip())
                if val_num > 0:
                    pesos_clean.append(val_num)
            except Exception:
                pass
        pesos_clean = pesos_clean[:20]
        prom_u = (sum(pesos_clean) / len(pesos_clean)) if pesos_clean else float(st.session_state.wstd_val)
        tot_k = prom_u * p_item["cantidad"]
        presentaciones_data_global.append({
            "nombre": p_item["nombre"],
            "bultos": p_item["cantidad"],
            "pesos": pesos_clean,
            "promedio": prom_u,
            "total_kg": tot_k
        })

    tot_b_gral = sum(p['bultos'] for p in presentaciones_data_global)
    peso_tot_gral = sum(p['total_kg'] for p in presentaciones_data_global)
    prom_global = (peso_tot_gral / tot_b_gral) if tot_b_gral > 0 else 0.0
    peso_a_favor = float(st.session_state.pay_val) - peso_tot_gral

    # Recuperación de bytes para el contenedor
    curr_c_id = st.session_state.cont_val.strip()
    if curr_c_id and curr_c_id not in st.session_state.fotos_contenedor_db:
        st.session_state.fotos_contenedor_db[curr_c_id] = {}

    db_actual = st.session_state.fotos_contenedor_db.get(curr_c_id, {})
    bytes_ir_actual = db_actual.get("bytes_ir")
    bytes_temp_actual = db_actual.get("bytes_temp")
    bytes_pack_actual = db_actual.get("bytes_pack")

    cabecera_pdf_maestra = {
        "fecha": str(st.session_state.fec_val),
        "contenedor": st.session_state.cont_val,
        "payload": float(st.session_state.pay_val),
        "responsable": "LUIS ENRIQUE FIESTAS ECA",
        "pi": st.session_state.pi_val,
        "booking": st.session_state.bk_val,
        "cliente": st.session_state.cli_val,
        "destino": st.session_state.dest_val
    }
    resumen_pdf_maestro = {
        "total_bultos": tot_b_gral,
        "peso_total": peso_tot_gral,
        "promedio_global": prom_global,
        "peso_a_favor": peso_a_favor
    }

    # Generación de bytes del Dossier para botón y lector
    pdf_dossier_bytes_cache = None
    if st.session_state.cont_val:
        try:
            pdf_dossier_bytes_cache = generar_dossier_unificado(
                cabecera_pdf_maestra,
                df_lotes_global,
                df_pres_global,
                st.session_state.df_congelado_edit,
                presentaciones_data_global,
                resumen_pdf_maestro,
                bytes_ir_actual,
                bytes_temp_actual,
                bytes_pack_actual
            ).getvalue()
        except Exception:
            pdf_dossier_bytes_cache = None

    # Botón directo superior
    if modo_operacion == "Cargar / Editar Contenedor Existente" and st.session_state.cont_val and pdf_dossier_bytes_cache:
        with c_btn_c2:
            st.download_button(
                label=f"📦 Descargar Dossier Completo ({st.session_state.cont_val})",
                data=pdf_dossier_bytes_cache,
                file_name=f"Dossier_Completo_{st.session_state.cont_val}.pdf",
                mime="application/pdf",
                use_container_width=True
            )

    # =========================================================================
    # PESTAÑAS
    # =========================================================================
    tab_estiba_lotes, tab_estiba_pres, tab_placa_tunel, tab_pesos, tab_adjuntos, tab_lector = st.tabs([
        "📅 1. Plano Estiba (Lotes)",
        "📦 2. Plano Estiba (Presentaciones)",
        "❄️ 3. Placas / Túnel / IQF",
        "⚖️ 4. Control de Pesos (Balanza)",
        "📸 5. IR, Temperatura & Packing List",
        "👁️ 6. Visor Lector de PDF"
    ])

    # ------------------ TAB 1: LOTES ------------------
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

        n_lotes = st.number_input("Cantidad de Lotes:", min_value=1, max_value=12, value=max(len(st.session_state.lotes_items), 1), key=f"nlot_c_{v}")
        while len(st.session_state.lotes_items) < n_lotes:
            st.session_state.lotes_items.append({"fecha": date.today(), "lote": generar_lote_juliano(date.today()), "bultos": 0})
        while len(st.session_state.lotes_items) > n_lotes:
            st.session_state.lotes_items.pop()

        cols_l = st.columns(min(int(n_lotes), 4))
        lista_lotes_calc = []
        for i in range(int(n_lotes)):
            col_target = cols_l[i % 4]
            item_l = st.session_state.lotes_items[i]
            with col_target:
                fl = st.date_input(f"Fecha {i+1}:", value=item_l["fecha"], key=f"fl_{i}_{v}")
                lot_txt = st.text_input(f"Lote {i+1}:", value=item_l["lote"], key=f"cl_{i}_{v}")
                bl = st.number_input(f"Bultos {i+1}:", min_value=0, value=int(item_l["bultos"]), step=10, key=f"bl_{i}_{v}")
                item_l["fecha"] = fl
                item_l["lote"] = lot_txt
                item_l["bultos"] = int(bl)
                lista_lotes_calc.append({"fecha_txt": fl.strftime('%d/%m/%Y'), "lote_txt": lot_txt.strip(), "cantidad": int(bl)})

        cols_bloqueadas = ["N° FILA", "TM"] + headers_l
        st.info("💡 Solo edita el número en **CANT/FILA** si deseas balancear (+1, -1). El resto se recalcula solo.")

        df_lotes_editado = st.data_editor(
            df_lotes_global,
            disabled=cols_bloqueadas,
            hide_index=True,
            use_container_width=True,
            height=300,
            key=f"editor_cantfila_only_{v}_{st.session_state.nfil_val}"
        )

        nuevas_capacidades = df_lotes_editado["CANT/FILA"].astype(int).tolist()
        if nuevas_capacidades != st.session_state.caps_filas_override:
            st.session_state.caps_filas_override = nuevas_capacidades
            st.rerun()

        tot_b_cargados = sum(caps_reales_actuales)
        tot_tm_cargados = (tot_b_cargados * float(st.session_state.wstd_val)) / 1000.0

        m1, m2 = st.columns(2)
        m1.metric("Total Bultos Cargados (Lotes)", f"{tot_b_cargados:,} bultos")
        m2.metric("Tonelaje Total", f"{tot_tm_cargados:.3f} TM")

    # ------------------ TAB 2: PRESENTACIONES ------------------
    with tab_estiba_pres:
        st.markdown("#### Presentaciones a Embarcar (Hasta 8 según la hoja)")
        np_m = st.number_input("Número de Presentaciones:", min_value=1, max_value=8, value=max(len(st.session_state.pres_items), 1), key=f"npres_c_{v}")
        while len(st.session_state.pres_items) < np_m:
            st.session_state.pres_items.append({"nombre": LISTA_PRESENTACIONES_FRIGOSA[0], "bultos": 0, "peso": st.session_state.wstd_val})
        while len(st.session_state.pres_items) > np_m:
            st.session_state.pres_items.pop()

        cols_p = st.columns(min(int(np_m), 4))
        for i in range(int(np_m)):
            col_target_p = cols_p[i % 4]
            p_item = st.session_state.pres_items[i]
            with col_target_p:
                st.markdown(f"**Presentación {i+1}**")
                idx_p_sel = LISTA_PRESENTACIONES_FRIGOSA.index(p_item["nombre"]) if p_item["nombre"] in LISTA_PRESENTACIONES_FRIGOSA else 0
                sel_nom = st.selectbox(f"Corte {i+1}:", LISTA_PRESENTACIONES_FRIGOSA, index=idx_p_sel, key=f"sp_{i}_{v}")
                cant_b = st.number_input(f"Bultos {i+1}:", min_value=0, value=int(p_item["bultos"]), step=10, key=f"bp_{i}_{v}")
                p_item["nombre"] = sel_nom
                p_item["bultos"] = int(cant_b)

        st.dataframe(df_pres_global, hide_index=True, use_container_width=True, height=280)

    # ------------------ TAB 3: PLACAS / TÚNEL / IQF ------------------
    with tab_placa_tunel:
        st.markdown("#### Configuración de Sistema de Congelación")

        def on_change_modo_cong():
            opc = st.session_state.get(f"rad_cong_{v}")
            num_f = len(caps_reales_actuales)
            if opc == "Mixto (Ingreso Manual Fila por Fila)":
                filas_clean = []
                for f_idx in range(num_f):
                    filas_clean.append({
                        "N° FILA": f_idx + 1, "TM": 0.0, "PLACAS": 0, "TUNEL": 0, "IQF": 0, "TOTAL": 0
                    })
                st.session_state.df_congelado_edit = pd.DataFrame(filas_clean)

        modo_cong_opc = st.radio(
            "Carga predominante:",
            ["Solo Placas (100% de la carga)", "Solo Túnel (100% de la carga)", "Mixto (Ingreso Manual Fila por Fila)"],
            horizontal=True,
            key=f"rad_cong_{v}",
            on_change=on_change_modo_cong
        )

        num_filas_actual = len(caps_reales_actuales)
        df_editor_source = st.session_state.df_congelado_edit.copy()

        if modo_cong_opc == "Solo Placas (100% de la carga)":
            for idx in range(num_filas_actual):
                cap_f = caps_reales_actuales[idx]
                df_editor_source.at[idx, "PLACAS"] = cap_f
                df_editor_source.at[idx, "TUNEL"] = 0
                df_editor_source.at[idx, "IQF"] = 0
                df_editor_source.at[idx, "TOTAL"] = cap_f
        elif modo_cong_opc == "Solo Túnel (100% de la carga)":
            for idx in range(num_filas_actual):
                cap_f = caps_reales_actuales[idx]
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

    # ------------------ TAB 4: CONTROL DE PESOS ------------------
    with tab_pesos:
        st.markdown("#### Pesos de Balanza")
        cols_w = st.columns(max(len(lista_pres_mem), 1))

        for i, col in enumerate(cols_w):
            with col:
                nom_completo = lista_pres_mem[i]['nombre'].strip()
                st.markdown(f"**{nom_completo}**")
                val_mem = st.session_state.txt_pesos_mem.get(str(i), "20.00, 20.05, 19.98")
                txt_p = st.text_area(f"Pesos balanza ({i+1}):", value=val_mem, height=90, key=f"pw_box_{i}_{v}")
                st.session_state.txt_pesos_mem[str(i)] = txt_p

        st.markdown("---")
        r1, r2, r3, r4 = st.columns(4)
        r1.metric("Bultos Totales", f"{tot_b_gral:,}")
        r2.metric("Promedio Global", f"{prom_global:.3f} kg")
        r3.metric("Peso Bruto", f"{peso_tot_gral:,.2f} kg")
        r4.metric("Margen a Favor", f"{peso_a_favor:,.2f} kg")

    # ------------------ TAB 5: ADJUNTOS CON PERSISTENCIA DIRECTA EN GOOGLE SHEETS ------------------
    with tab_adjuntos:
        st.markdown("#### 📸 Panel Documental Fotográfico del Contenedor")
        st.caption("Al presionar el botón rojo de guardado inferior, las fotos se guardan directamente en la base de datos de Sheets. No se pierden nunca.")

        c_f1, c_f2, c_f3 = st.columns(3)

        # 1. FOTO DEL IR
        with c_f1:
            st.markdown("##### 📄 1. Foto de Inspección (IR / EIR)")
            foto_ir = st.file_uploader("Subir foto Reporte IR:", type=["jpg", "jpeg", "png"], key=f"up_ir_{v}")
            if foto_ir:
                b_opt = optimizar_bytes_imagen(foto_ir.getvalue())
                db_actual["bytes_ir"] = b_opt
                st.image(b_opt, caption="Foto IR Cargada", use_container_width=True)
            elif db_actual.get("bytes_ir"):
                st.image(db_actual["bytes_ir"], caption="Foto IR Activa (Guardada)", use_container_width=True)

        # 2. FOTO DE TEMPERATURA
        with c_f2:
            st.markdown("##### ❄️ 2. Foto de Temperatura")
            foto_temp = st.file_uploader("Subir foto Display Termoking:", type=["jpg", "jpeg", "png"], key=f"up_temp_{v}")
            if foto_temp:
                b_opt_t = optimizar_bytes_imagen(foto_temp.getvalue())
                db_actual["bytes_temp"] = b_opt_t
                st.image(b_opt_t, caption="Display Termoking Cargado", use_container_width=True)
            elif db_actual.get("bytes_temp"):
                st.image(db_actual["bytes_temp"], caption="Display Termoking Activo (Guardado)", use_container_width=True)

        # 3. FOTO DEL PACKING LIST
        with c_f3:
            st.markdown("##### 📋 3. Foto de Lista de Empaque")
            foto_pack = st.file_uploader("Subir foto del Packing List:", type=["jpg", "jpeg", "png"], key=f"up_pack_{v}")
            if foto_pack:
                b_opt_p = optimizar_bytes_imagen(foto_pack.getvalue())
                db_actual["bytes_pack"] = b_opt_p
                st.image(b_opt_p, caption="Packing List Cargado", use_container_width=True)
            elif db_actual.get("bytes_pack"):
                st.image(db_actual["bytes_pack"], caption="Packing List Activo (Guardado)", use_container_width=True)

    # ------------------ TAB 6: VISOR LECTOR DE PDF NATIVO LIGERO ------------------
    with tab_lector:
        st.markdown("#### 👁️ Visor del Expediente Técnico Completo")
        if pdf_dossier_bytes_cache:
            st.caption(f"Documento consolidado de **{st.session_state.cont_val}** listo para inspección:")
            
            # Botón de apertura directa para visor nativo completo
            b64_pdf = base64.b64encode(pdf_dossier_bytes_cache).decode('utf-8')
            btn_html = f"""
            <div style="margin-bottom: 12px;">
                <a href="data:application/pdf;base64,{b64_pdf}" target="_blank" download="Dossier_Completo_{st.session_state.cont_val}.pdf"
                   style="background-color: #2B6CB0; color: white; padding: 10px 18px; text-decoration: none; border-radius: 6px; font-weight: bold; font-family: sans-serif; display: inline-block;">
                   🔍 Abrir Documento en Pantalla Completa / Descargar
                </a>
            </div>
            """
            st.markdown(btn_html, unsafe_allow_html=True)

            # Visor embebido con motor PDF.js ligero
            pdf_data_uri = f"data:application/pdf;base64,{b64_pdf}"
            encoded_uri = urllib.parse.quote(pdf_data_uri)
            visor_html = f"""
            <iframe src="https://mozilla.github.io/pdf.js/web/viewer.html?file={encoded_uri}" 
                    width="100%" height="700px" style="border: 1px solid #CBD5E0; border-radius: 8px;">
            </iframe>
            """
            components.html(visor_html, height=720)
        else:
            st.info("⚠️ Seleccione o ingrese un número de contenedor para activar el visor del PDF.")

    # =========================================================================
    # GUARDADO CENTRALIZADO: REGISTRA DATOS Y GUARDA FOTOS EN SHEETS
    # =========================================================================
    st.markdown("---")
    btn_label = f"💾 Guardar / Actualizar Información de {st.session_state.cont_val or 'Contenedor'} en Sheets"
    if st.button(btn_label, type="primary", use_container_width=True):
        if not st.session_state.cont_val.strip():
            st.warning("⚠️ Debe ingresar el N° de Contenedor antes de guardar.")
        else:
            try:
                num_c_guardar = st.session_state.cont_val.strip().upper()
                db_c_guardar = st.session_state.fotos_contenedor_db.get(num_c_guardar, {})

                with st.spinner("Guardando fotos de forma permanente en la base de datos..."):
                    if db_c_guardar.get("bytes_ir"):
                        guardar_foto_en_sheets(get_gspread_client, num_c_guardar, "IR", db_c_guardar["bytes_ir"])
                    if db_c_guardar.get("bytes_temp"):
                        guardar_foto_en_sheets(get_gspread_client, num_c_guardar, "TEMP", db_c_guardar["bytes_temp"])
                    if db_c_guardar.get("bytes_pack"):
                        guardar_foto_en_sheets(get_gspread_client, num_c_guardar, "PACK", db_c_guardar["bytes_pack"])

                pres_cols = []
                for idx in range(8):
                    if idx < len(lista_pres_mem):
                        pres_cols.extend([lista_pres_mem[idx]["nombre"], int(lista_pres_mem[idx]["cantidad"])])
                    else:
                        pres_cols.extend(["", ""])

                detalle_lotes_str = " | ".join([f"{l['lote_txt']} ({l['fecha_txt']}): {l['cantidad']}b" for l in lista_lotes_mem if l['cantidad'] > 0])

                serial_pesos = []
                for k_p, v_p in st.session_state.txt_pesos_mem.items():
                    clean_v = v_p.replace("\n", " ").strip()
                    if clean_v:
                        serial_pesos.append(f"{k_p}::{clean_v}")
                detalle_pesos_str = " ;; ".join(serial_pesos)

                link_ir_final = "REGISTRADO_EN_SHEETS" if db_c_guardar.get("bytes_ir") else ""
                link_temp_final = "REGISTRADO_EN_SHEETS" if db_c_guardar.get("bytes_temp") else ""
                link_pack_final = "REGISTRADO_EN_SHEETS" if db_c_guardar.get("bytes_pack") else ""

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
                    "LUIS ENRIQUE FIESTAS ECA",                    # J: supervisor
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
                    detalle_pesos_str,                             # AO: detalle_pesos_balanza
                    link_ir_final,                                 # AP: link_foto_ir
                    link_temp_final,                               # AQ: link_foto_temperatura
                    link_pack_final                                # AR: link_foto_packing
                ]

                es_modo_nuevo = (modo_operacion == "Nuevo Contenedor")
                ok, res_msg = guardar_o_actualizar_contenedor(get_gspread_client, fila_maestra, forzar_nuevo=es_modo_nuevo)

                if ok:
                    st.success(f"✅ Contenedor {st.session_state.cont_val} guardado con sus fotos en la base de datos.")
                else:
                    st.error(f"🚫 {res_msg}")
            except Exception as e:
                st.error(f"Error al guardar en Sheets: {e}")
