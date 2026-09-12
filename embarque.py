import streamlit as st
import pandas as pd
from datetime import date
import io
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

URL_PRODUCCION = "https://docs.google.com/spreadsheets/d/1cX-C1Lrgp8SznxDs-_cjiMN6DptNusCmNoNopxBmJlg/edit"

LISTA_PRESENTACIONES_FRIGOSA = [
    "ALETA FRESCA DE POTA CONGELADA 300 g/pza - 500 g/pza",
    "ALETA FRESCA DE POTA CONGELADA 500 g/pza- 1000 g/pza",
    "ALETA FRESCA DE POTA CONGELADA 1000 g/pza - UP",
    "ALETA FRESCA DE POTA CONGELADA 1000 g/pza - CV",
    "ALETA PRECOCIDA DE POTA CONGELADA 300 g/pza - UP",
    "ANILLAS BLANCAS DE POTA CONGELADA S/M S/T",
    "BOTONES BLANCOS DE POTA CONGELADA S/M S/T",
    "CONOS DE POTA CONGELADA",
    "FILETE FRESCO DE POTA CONGELADA S/PIEL S/M S/T 2000 g/pza - 4000 g/pza",
    "FILETE FRESCO DE POTA CONGELADA S/PIEL C/M C/T 500 g/pza - 1000 g/pz",
    "FILETE FRESCO DE POTA CONGELADA S/PIEL C/M C/T 1000 g/pza - 2000 g/pza",
    "FILETE FRESCO DE POTA CONGELADA S/PIEL C/M C/T 2000 g/pza - 4000 g/pza",
    "FILETE PRECOCIDO DE POTA CONGELADA 7mm - 10 mm",
    "FILETE PRECOCIDO DE POTA CONGELADA LADO PANZA 7mm - 10 mm",
    "FILETE PRECOCIDO DE POTA CONGELADA LADO MEMBRANA 7mm - 10 mm",
    "FILETE PRECOCIDO DE POTA CONGELADA LADO PANZA 8 mm - 14 mm",
    "FILETE PRECOCIDO DE POTA CONGELADA LADO MEMBRANA 8 mm - 14 mm",
    "DESHILACHADO SAZONADO DE POTA CONGELADA -F1",
    "DESHILACHADO SAZONADO DE POTA CONGELADA-F2",
    "FILETE PRECOCIDO DE POTA CONGELADA 10mm - 14 mm",
    "NUCAS DE POTA CONGELADA 100 g/pza - 300 g/pza",
    "NUCAS DE POTA CONGELADA 300 g/pza - 500 g/pza",
    "NUCAS DE POTA CONGELADA 500g/pza -UP",
    "NUCAS DE POTA CONGELADA 0 -50 g/pza",
    "RECORTE PRECOCIDO DE POTA CONGELADA",
    "RECORTE FRESCO BLANCO DE POTA CONGELADA S/M S/T",
    "REPRODUCTOR DE POTA CONGELADA S/PUNTA S/U S/V MAYOR A 50 cm",
    "REPRODUCTOR DE POTA CONGELADA S/PUNTA S/U S/V MENOR A 50 cm",
    "TENTACULO BAILARINA DE POTA CONGELADA C/U C/V 300 g/pza - 500 g/pza",
    "TENTACULO BAILARINA DE POTA CONGELADA C/U C/V 500 g/pza - 1000 g/pza",
    "TENTACULO BAILARINA DE POTA CONGELADA S/U S/V 300 g/pza - 500 g/pza",
    "TENTACULO BAILARINA DE POTA CONGELADA S/U S/V 2000 g/pza - 3000 g/pza",
    "TENTACULO BAILARINA DE POTA CONGELADA S/U S/V 1000g /pza-UP",
    "OTRO (Digitar manualmente)"
]

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

def generar_dossier_pdf_completo(cabecera, presentaciones_data, resumen, df_estiba_lotes, df_estiba_pres, df_estiba_sistema):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=letter, 
        leftMargin=20, 
        rightMargin=20, 
        topMargin=20, 
        bottomMargin=20
    )
    story = []
    styles = getSampleStyleSheet()

    titulo_style = ParagraphStyle('TitF', parent=styles['Heading1'], fontSize=11, leading=13, textColor=colors.HexColor("#0D3B66"), alignment=1)
    sub_style = ParagraphStyle('SubF', parent=styles['Heading2'], fontSize=8, leading=10, textColor=colors.HexColor("#2B6CB0"), alignment=1)

    # ------------------ PÁGINA 1: CONTROL DE PESOS (MÁX 20 PESOS) ------------------
    story.append(Paragraph("SEGUIMIENTO DE CONTROL DE PESO - FRIGOSA SAC", titulo_style))
    story.append(Paragraph(f"CONTENEDOR: {cabecera['contenedor']} | SEMANA N°: {cabecera.get('semana', '-')}", sub_style))
    story.append(Spacer(1, 6))

    data_cab = [
        ["FECHA:", cabecera['fecha'], "N° CONTENEDOR:", cabecera['contenedor']],
        ["PAYLOAD MÁX (KG):", f"{cabecera['payload']:,.2f}", "PESO BRUTO ESTIMADO:", f"{resumen['peso_total']:,.2f} KG"],
        ["TOTAL BULTOS:", f"{resumen['total_bultos']:,}", "MARGEN (A FAVOR):", f"{resumen['peso_a_favor']:,.2f} KG"],
        ["SUPERVISOR:", cabecera['responsable'], "PROMEDIO GLOBAL:", f"{resumen['promedio_global']:.3f} KG"]
    ]
    t_cab = Table(data_cab, colWidths=[110, 165, 125, 172])
    t_cab.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 7),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F4F6F9")),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
        ('ALIGN', (1, 0), (1, -1), 'CENTER'),
        ('ALIGN', (3, 0), (3, -1), 'CENTER'),
    ]))
    story.append(t_cab)
    story.append(Spacer(1, 6))

    # Matriz compacta ajustada exactamente a 20 pesos para evitar salto de hoja
    headers = [f"{p['nombre'][:20]}" for p in presentaciones_data]
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
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
        ('BACKGROUND', (0, -3), (-1, -1), colors.HexColor("#EDF2F7")),
        ('FONTNAME', (0, -3), (-1, -1), 'Helvetica-Bold'),
    ]))
    story.append(t_muestreo)

    # ------------------ FUNCIÓN DE TABLAS COMPACTAS DE ESTIBA ------------------
    def agregar_pagina_tabla_compacta(df_in, titulo_tab, color_header):
        if df_in is not None and not df_in.empty:
            story.append(PageBreak())
            story.append(Paragraph(titulo_tab, titulo_style))
            story.append(Paragraph(f"CONTENEDOR: {cabecera['contenedor']} | FECHA: {cabecera['fecha']}", sub_style))
            story.append(Spacer(1, 6))

            cols = list(df_in.columns)
            num_cols = len(cols)
            
            # Ancho proporcional: primeras columnas fijas más angostas, lotes distribuidos
            if num_cols > 3:
                w_prim = [45, 55, 55]
                w_resto = (572 - sum(w_prim)) / (num_cols - 3)
                col_widths = w_prim + [w_resto] * (num_cols - 3)
            else:
                col_widths = [572 / num_cols] * num_cols

            t_data = [[c[:16] for c in cols]]
            for _, r in df_in.iterrows():
                row_vals = []
                for c in cols:
                    val = r[c]
                    if isinstance(val, (int, float)):
                        row_vals.append(f"{val:.2f}" if ("TM" in c.upper()) else str(int(val)))
                    else:
                        row_vals.append(str(val))
                t_data.append(row_vals)

            # FILA DE TOTALES EN EL PDF
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

            # Ajuste de tamaño de fuente según cantidad de columnas
            f_size = 5.5 if num_cols > 7 else (6.0 if num_cols > 5 else 6.5)

            t_pdf = Table(t_data, colWidths=col_widths)
            t_pdf.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), f_size),
                ('TOPPADDING', (0, 0), (-1, -1), 1.8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 1.8),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(color_header)),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
                ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor("#FEFCBF")),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.HexColor("#F7FAFC")]),
            ]))
            story.append(t_pdf)

    agregar_pagina_tabla_compacta(df_estiba_lotes, "PLANO DE ESTIBA POR FECHAS Y LOTES - FRIGOSA SAC", "#2B6CB0")
    agregar_pagina_tabla_compacta(df_estiba_pres, "PLANO DE ESTIBA POR PRESENTACIONES - FRIGOSA SAC", "#2F855A")
    agregar_pagina_tabla_compacta(df_estiba_sistema, "DISTRIBUCIÓN POR SISTEMA: PLACAS / TÚNEL / IQF", "#D69E2E")

    doc.build(story)
    buffer.seek(0)
    return buffer

def render_module(user, get_gspread_client):
    nombre_user = user.get("nombre_completo", user.get("usuario", "LUIS ENRIQUE FIESTAS ECA"))
    st.subheader("🚢 Módulo 4: Despachos, Estiba y Embarques")

    # Multicontenedor (3 contenedores independientes)
    c_sel1, c_sel2 = st.columns([2, 2])
    with c_sel1:
        cont_activo_key = st.radio(
            "Seleccionar Contenedor en Operación:",
            ["Contenedor 1", "Contenedor 2", "Contenedor 3"],
            horizontal=True
        )
    with c_sel2:
        st.info(f"Operando sobre: **{cont_activo_key}** (Estiba y pesos independientes)")

    if "contenedores_data" not in st.session_state:
        st.session_state.contenedores_data = {
            "Contenedor 1": {"cont": "MSGU-101", "pay": 27000.0, "sem": 37, "nfil": 20, "cap_g": 60, "cap_f1": 58, "cap_fu": 62, "w_std": 20.0},
            "Contenedor 2": {"cont": "MSGU-102", "pay": 27000.0, "sem": 37, "nfil": 20, "cap_g": 60, "cap_f1": 58, "cap_fu": 62, "w_std": 20.0},
            "Contenedor 3": {"cont": "MSGU-103", "pay": 27000.0, "sem": 37, "nfil": 20, "cap_g": 60, "cap_f1": 58, "cap_fu": 62, "w_std": 20.0}
        }

    c_state = st.session_state.contenedores_data[cont_activo_key]

    with st.expander(f"⚙️ Configuración Global - {cont_activo_key}", expanded=True):
        cp1, cp2, cp3, cp4 = st.columns(4)
        with cp1:
            fec_desp = st.date_input("Fecha Embarque:", date.today(), key=f"fec_{cont_activo_key}")
        with cp2:
            num_cont = st.text_input("N° Contenedor:", value=c_state["cont"], key=f"num_{cont_activo_key}")
            c_state["cont"] = num_cont
        with cp3:
            payload = st.number_input("Payload Máx (kg):", min_value=15000.0, max_value=32000.0, value=c_state["pay"], step=500.0, key=f"pay_{cont_activo_key}")
            c_state["pay"] = payload
        with cp4:
            semana_est = st.number_input("Semana N°:", min_value=1, max_value=53, value=c_state["sem"], key=f"sem_{cont_activo_key}")
            c_state["sem"] = semana_est

    tab_estiba_lotes, tab_estiba_pres, tab_placa_tunel, tab_pesos = st.tabs([
        "📅 1. Plano Estiba (Lotes)",
        "📦 2. Plano Estiba (Presentaciones)",
        "❄️ 3. Distribución Placas / Túnel / IQF",
        "⚖️ 4. Control de Pesos (Final)"
    ])

    # =========================================================================
    # TAB 1: PLANO DE ESTIBA POR LOTES
    # =========================================================================
    with tab_estiba_lotes:
        st.markdown("#### Configuración de Filas y Carga de Lotes")
        cf1, cf2, cf3, cf4 = st.columns(4)
        with cf1:
            n_filas = st.number_input("Total Filas:", min_value=10, max_value=30, value=c_state["nfil"], key=f"nfil_{cont_activo_key}")
            c_state["nfil"] = int(n_filas)
        with cf2:
            cap_gral = st.number_input("Capacidad Estándar Fila:", min_value=30, max_value=100, value=c_state["cap_g"], key=f"capg_{cont_activo_key}")
            c_state["cap_g"] = int(cap_gral)
        with cf3:
            cap_f1 = st.number_input("Capacidad Fila 1 (Tope):", min_value=20, max_value=100, value=c_state["cap_f1"], key=f"capf1_{cont_activo_key}")
            c_state["cap_f1"] = int(cap_f1)
        with cf4:
            cap_fult = st.number_input(f"Capacidad Fila {n_filas} (Puerta):", min_value=20, max_value=100, value=c_state["cap_fu"], key=f"capfu_{cont_activo_key}")
            c_state["cap_fu"] = int(cap_fult)
            peso_std = st.number_input("Peso Estándar Bulto (kg):", value=c_state["w_std"], step=0.1, key=f"wstd_{cont_activo_key}")
            c_state["w_std"] = float(peso_std)

        # Vector maestro de capacidades sincronizado para todas las pestañas
        caps_filas_maestro = [int(cap_gral)] * int(n_filas)
        caps_filas_maestro[0] = int(cap_f1)
        caps_filas_maestro[-1] = int(cap_fult)
        c_state["cfg_filas"] = caps_filas_maestro

        st.markdown("---")
        st.markdown("#### Lotes a Cargar (Zonas Celestes)")
        n_lotes = st.number_input("Cantidad de Lotes:", min_value=1, max_value=10, value=3, key=f"nlot_{cont_activo_key}")
        cols_l = st.columns(int(n_lotes))

        lista_lotes = []
        for i, col in enumerate(cols_l):
            with col:
                fec_l = st.date_input(f"Fecha {i+1}:", date.today(), key=f"fl_{i}_{cont_activo_key}")
                cod_l = st.text_input(f"Lote {i+1}:", value=f"LT 026.{268+i}", key=f"cl_{i}_{cont_activo_key}")
                cant_l = st.number_input(f"Bultos {i+1}:", min_value=0, value=485 if i==0 else (458 if i==1 else 400), step=10, key=f"bl_{i}_{cont_activo_key}")
                lista_lotes.append({"fecha_txt": fec_l.strftime('%d/%m/%Y'), "lote_txt": cod_l, "cantidad": int(cant_l)})

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

        # Render sin índice cero
        st.dataframe(df_lotes, hide_index=True, use_container_width=True, height=400)
        
        tot_b = sum(df_lotes["CANT/FILA"])
        tot_tm = sum(df_lotes["TM"])
        cap_max = sum(caps_filas_maestro)

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Capacidad Total", f"{cap_max} bultos")
        m2.metric("Total Cargado", f"{tot_b} bultos")
        m3.metric("Tonelaje Estiba", f"{tot_tm:.3f} TM")
        m4.metric("Espacio Libre", f"{cap_max - tot_b} bultos")

    # =========================================================================
    # TAB 2: PLANO DE ESTIBA POR PRESENTACIONES
    # =========================================================================
    with tab_estiba_pres:
        st.markdown("#### Distribución de Presentaciones (Sincronizado con Fila y Capacidades de Lotes)")
        st.caption(f"Filas activas: **{len(caps_filas_maestro)} filas** | Capacidad Total: **{sum(caps_filas_maestro)} bultos**")

        np_m = st.number_input("Número de Presentaciones a Cargar:", min_value=1, max_value=6, value=2, key=f"npm_{cont_activo_key}")
        cols_pm = st.columns(int(np_m))

        lista_pres_m = []
        for i, col in enumerate(cols_pm):
            with col:
                st.markdown(f"**Presentación {i+1}**")
                idx_def_p = min(i, len(LISTA_PRESENTACIONES_FRIGOSA) - 2)
                p_sel = st.selectbox(f"Corte {i+1}:", LISTA_PRESENTACIONES_FRIGOSA, index=idx_def_p, key=f"selp_{i}_{cont_activo_key}")
                nom_pm = st.text_input(f"Detalle {i+1}:", key=f"otrp_{i}_{cont_activo_key}") if p_sel == "OTRO (Digitar manualmente)" else p_sel
                cant_pm = st.number_input(f"Cantidad Total Bultos {i+1}:", min_value=0, value=650 if i==0 else 550, step=20, key=f"cantp_{i}_{cont_activo_key}")
                peso_pm = st.number_input(f"Peso Promedio (kg) {i+1}:", value=22.10 if i==0 else 11.90, step=0.05, key=f"wpr_{i}_{cont_activo_key}")
                lista_pres_m.append({"nombre": nom_pm, "cantidad": int(cant_pm), "peso_unit": float(peso_pm)})

        matriz_m = calcular_matriz_estiba(caps_filas_maestro, lista_pres_m)
        headers_m = [p['nombre'][:25] for p in lista_pres_m]

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

        # Render sin índice cero
        st.dataframe(df_pres, hide_index=True, use_container_width=True, height=400)
        tot_tm_m = sum(df_pres["TM ESTIMADO"])
        tot_b_m = sum(df_pres["TOTAL BULTOS"])

        mp1, mp2 = st.columns(2)
        mp1.metric("Total Bultos por Presentación", f"{tot_b_m:,} bultos")
        mp2.metric("Peso Neto Estimado", f"{tot_tm_m:.3f} TM ({tot_tm_m*1000:,.1f} KG)")

    # =========================================================================
    # TAB 3: DISTRIBUCIÓN PLACAS / TÚNEL / IQF
    # =========================================================================
    with tab_placa_tunel:
        st.markdown("#### Distribución de Congelación por Fila (Placas / Túnel / IQF)")
        st.caption("Edita los bultos por sistema en cada fila respetando la capacidad nominal.")

        data_sist = []
        for f_idx in range(len(caps_filas_maestro)):
            bultos_fila_target = caps_filas_maestro[f_idx]
            data_sist.append({
                "N° FILA": f_idx + 1,
                "TM": round((bultos_fila_target * peso_std) / 1000.0, 4),
                "PLACAS": bultos_fila_target if f_idx < 10 else 0,
                "TUNEL": bultos_fila_target if f_idx >= 10 else 0,
                "IQF": 0,
                "TOTAL": bultos_fila_target
            })

        df_sist_editor = pd.DataFrame(data_sist)
        df_editado = st.data_editor(
            df_sist_editor,
            disabled=["N° FILA", "TM", "TOTAL"],
            hide_index=True,  # Elimina columna con índice 0
            use_container_width=True,
            height=400,
            key=f"editor_sist_{cont_activo_key}"
        )
        df_editado["TOTAL"] = df_editado["PLACAS"] + df_editado["TUNEL"] + df_editado["IQF"]
        df_editado["TM"] = round((df_editado["TOTAL"] * peso_std) / 1000.0, 4)
        c_state["df_sist"] = df_editado

        tot_placas = df_editado["PLACAS"].sum()
        tot_tunel = df_editado["TUNEL"].sum()
        tot_iqf = df_editado["IQF"].sum()

        s1, s2, s3, s4 = st.columns(4)
        s1.metric("Total Placas", f"{tot_placas:,} bultos")
        s2.metric("Total Túnel", f"{tot_tunel:,} bultos")
        s3.metric("Total IQF", f"{tot_iqf:,} bultos")
        s4.metric("Total General", f"{tot_placas + tot_tunel + tot_iqf:,} bultos")

    # =========================================================================
    # TAB 4: CONTROL Y MUESTREO DE PESOS (MÁXIMO 20 PESOS)
    # =========================================================================
    with tab_pesos:
        st.markdown(f"#### Control de Balanza / Pesos ({cont_activo_key} - {num_cont})")
        st.caption("Pega o digita hasta 20 lecturas reales de balanza tomadas durante el embarque.")

        num_pres_pesos = st.number_input("Presentaciones a Evaluar:", min_value=1, max_value=6, value=len(lista_pres_m), key=f"npw_{cont_activo_key}")
        cols_w = st.columns(int(num_pres_pesos))
        presentaciones_data = []

        for i, col in enumerate(cols_w):
            with col:
                st.markdown(f"**Presentación {i+1}**")
                pres_def = lista_pres_m[i]["nombre"] if i < len(lista_pres_m) else LISTA_PRESENTACIONES_FRIGOSA[0]
                idx_sel = LISTA_PRESENTACIONES_FRIGOSA.index(pres_def) if pres_def in LISTA_PRESENTACIONES_FRIGOSA else 0
                p_nom = st.selectbox(f"Producto {i+1}:", LISTA_PRESENTACIONES_FRIGOSA, index=idx_sel, key=f"pwp_{i}_{cont_activo_key}")
                
                bultos_def = lista_pres_m[i]["cantidad"] if i < len(lista_pres_m) else 600
                bultos_val = st.number_input(f"Bultos:", min_value=0, value=bultos_def, step=20, key=f"bwp_{i}_{cont_activo_key}")

                val_base = 22.10 if i == 0 else 11.90
                txt_p = st.text_area(
                    "Pesos balanza (hasta 20):",
                    value=f"{val_base:.2f}, {val_base+0.05:.2f}, {val_base-0.08:.2f}, {val_base+0.12:.2f}, {val_base-0.02:.2f}",
                    height=120,
                    key=f"txw_{i}_{cont_activo_key}"
                )

                pesos_clean = []
                for p in txt_p.replace("\n", ",").split(","):
                    try:
                        v = float(p.strip())
                        if v > 0:
                            pesos_clean.append(v)
                    except:
                        pass

                # Truncar a máximo 20 lecturas para formato de página única
                pesos_clean = pesos_clean[:20]

                prom_u = (sum(pesos_clean) / len(pesos_clean)) if pesos_clean else val_base
                tot_k = prom_u * bultos_val
                st.caption(f"Muestras: **{len(pesos_clean)}/20** | Prom: **{prom_u:.3f} kg**")
                st.caption(f"Subtotal: **{tot_k:,.1f} kg**")

                presentaciones_data.append({"nombre": p_nom, "bultos": bultos_val, "pesos": pesos_clean, "promedio": prom_u, "total_kg": tot_k})

        tot_b_gral = sum(p['bultos'] for p in presentaciones_data)
        peso_tot_gral = sum(p['total_kg'] for p in presentaciones_data)
        prom_global = (peso_tot_gral / tot_b_gral) if tot_b_gral > 0 else 0.0
        peso_a_favor = payload - peso_tot_gral

        st.markdown("---")
        st.markdown("### 📊 Liquidación Final de Carga")
        r1, r2, r3, r4 = st.columns(4)
        r1.metric("Bultos Totales", f"{tot_b_gral:,}")
        r2.metric("Promedio Global", f"{prom_global:.3f} kg")
        r3.metric("Peso Total Neto", f"{peso_tot_gral:,.2f} kg")
        r4.metric("Margen a Favor", f"{peso_a_favor:,.2f} kg", delta=f"{peso_a_favor:,.2f} kg", delta_color="normal" if peso_a_favor >= 0 else "inverse")

        if peso_a_favor < 0:
            st.error(f"🚨 **SOBREPESO:** Contenedor excede el Payload por **{abs(peso_a_favor):,.2f} kg**.")
        else:
            st.success(f"✅ **CARGA PERMITIDA:** Margen de seguridad de **{peso_a_favor:,.2f} kg**.")

        cabecera_pdf = {
            "fecha": str(fec_desp),
            "contenedor": num_cont.strip(),
            "payload": payload,
            "semana": semana_est,
            "responsable": nombre_user
        }
        resumen_pdf = {
            "total_bultos": tot_b_gral,
            "peso_total": peso_tot_gral,
            "promedio_global": prom_global,
            "peso_a_favor": peso_a_favor
        }

        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            try:
                pdf_bytes = generar_dossier_pdf_completo(
                    cabecera_pdf,
                    presentaciones_data,
                    resumen_pdf,
                    c_state.get("df_lotes"),
                    c_state.get("df_pres"),
                    c_state.get("df_sist")
                )
                st.download_button(
                    label=f"📄 Descargar Dossier PDF Unificado ({num_cont})",
                    data=pdf_bytes,
                    file_name=f"Dossier_{num_cont}_{fec_desp}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
            except Exception as e:
                st.warning(f"Nota en PDF: {e}")

        with col_btn2:
            if st.button(f"💾 Guardar en Google Sheets ({num_cont})", use_container_width=True, key=f"btn_save_{cont_activo_key}"):
                try:
                    client = get_gspread_client()
                    sh = client.open_by_url(URL_PRODUCCION)
                    ws_desp = sh.worksheet("Control_Pesos_Embarque")
                    
                    id_dp = f"DSP-{date.today().strftime('%y%m%d%H%M%S')}"
                    resumen_sist = f"Placas: {tot_placas} | Tunel: {tot_tunel} | IQF: {tot_iqf}"
                    detalle_txt = " | ".join([f"{p['nombre']}: {p['bultos']}b" for p in presentaciones_data])
                    
                    fila = [
                        id_dp,
                        str(fec_desp),
                        num_cont.strip(),
                        resumen_sist,
                        float(payload),
                        int(tot_b_gral),
                        float(round(peso_tot_gral, 2)),
                        float(round(prom_global, 3)),
                        float(round(peso_a_favor, 2)),
                        nombre_user,
                        detalle_txt
                    ]
                    ws_desp.append_row(fila)
                    st.success(f"✅ Contenedor {num_cont} guardado en 'Control_Pesos_Embarque'.")
                except Exception as ex:
                    st.error(f"Error al guardar: {ex}")
