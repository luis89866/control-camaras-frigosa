import streamlit as st
import pandas as pd
from datetime import date
import io
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# URL de la base de datos de producción / despachos
URL_PRODUCCION = "https://docs.google.com/spreadsheets/d/1cX-C1Lrgp8SznxDs-_cjiMN6DptNusCmNoNopxBmJlg/edit"

# -------------------------------------------------------------------------
# CATÁLOGO OFICIAL DE PRESENTACIONES - FRIGOSA SAC
# -------------------------------------------------------------------------
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

# -------------------------------------------------------------------------
# ALGORITMO MATEMÁTICO DE ESTIBA AUTOMÁTICA (FIFO / BUCKET FILL)
# -------------------------------------------------------------------------
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

# -------------------------------------------------------------------------
# GENERADOR DE REPORTE PDF OFICIAL
# -------------------------------------------------------------------------
def generar_pdf_control_pesos(cabecera, presentaciones_data, resumen):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=letter, 
        leftMargin=25, 
        rightMargin=25, 
        topMargin=25, 
        bottomMargin=25
    )
    story = []
    styles = getSampleStyleSheet()

    titulo_style = ParagraphStyle(
        'TituloFrigosa',
        parent=styles['Heading1'],
        fontSize=13,
        leading=15,
        textColor=colors.HexColor("#0D3B66"),
        alignment=1
    )
    story.append(Paragraph("SEGUIMIENTO DE CONTROL DE PESO - FRIGOSA SAC", titulo_style))
    story.append(Spacer(1, 10))

    data_cab = [
        ["FECHA:", cabecera['fecha'], "N° CONTENEDOR:", cabecera['contenedor']],
        ["PAYLOAD (KG):", f"{cabecera['payload']:,.2f}", "PESO BRUTO ESTIMADO:", f"{resumen['peso_total']:,.2f} KG"],
        ["CANTIDAD TOTAL BULTOS:", f"{resumen['total_bultos']:,}", "PESO A FAVOR (MARGEN):", f"{resumen['peso_a_favor']:,.2f} KG"],
        ["SUPERVISOR RESPONSABLE:", cabecera['responsable'], "PESO PROMEDIO GLOBAL:", f"{resumen['promedio_global']:.3f} KG"]
    ]
    t_cab = Table(data_cab, colWidths=[120, 160, 130, 150])
    t_cab.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor("#0D3B66")),
        ('TEXTCOLOR', (2, 0), (2, -1), colors.HexColor("#0D3B66")),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F4F6F9")),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#BDC3C7")),
        ('ALIGN', (1, 0), (1, -1), 'CENTER'),
        ('ALIGN', (3, 0), (3, -1), 'CENTER'),
    ]))
    story.append(t_cab)
    story.append(Spacer(1, 12))

    headers = [f"{p['nombre'][:20]}..." if len(p['nombre']) > 20 else p['nombre'] for p in presentaciones_data]
    matrix_pesos = [headers]
    for r in range(30):
        fila = [f"{p['pesos'][r]:.2f}" if r < len(p['pesos']) and p['pesos'][r] > 0 else "-" for p in presentaciones_data]
        matrix_pesos.append(fila)

    fila_bultos = [f"Bultos: {p['bultos']}" for p in presentaciones_data]
    fila_prom = [f"Prom: {p['promedio']:.3f}" for p in presentaciones_data]
    fila_tot = [f"Total: {p['total_kg']:,.1f}k" for p in presentaciones_data]
    matrix_pesos.append(fila_bultos)
    matrix_pesos.append(fila_prom)
    matrix_pesos.append(fila_tot)

    ancho_col = 560 / max(len(presentaciones_data), 1)
    t_muestreo = Table(matrix_pesos, colWidths=[ancho_col] * len(presentaciones_data))
    t_muestreo.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 6.5),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1A365D")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
        ('BACKGROUND', (0, -3), (-1, -1), colors.HexColor("#E2E8F0")),
        ('FONTNAME', (0, -3), (-1, -1), 'Helvetica-Bold'),
    ]))
    story.append(t_muestreo)

    doc.build(story)
    buffer.seek(0)
    return buffer

# -------------------------------------------------------------------------
# RENDER PRINCIPAL DEL MÓDULO 4
# -------------------------------------------------------------------------
def render_module(user, get_gspread_client):
    nombre_user = user.get("nombre_completo", user.get("usuario", "LUIS ENRIQUE FIESTAS ECA"))

    st.subheader("🚢 Módulo 4: Despachos, Embarques y Estiba")
    st.caption(f"Supervisor: **{nombre_user}** | Empresa: **Frigosa S.A.C.**")

    # Conexión a Google Sheets
    try:
        client = get_gspread_client()
        sh = client.open_by_url(URL_PRODUCCION)
    except Exception:
        try:
            sh = client.open("BD_PRODUCCION_ARCHI_001")
        except Exception as e:
            st.error(f"Error de conexión con base de datos: {e}")
            return

    # Pestañas del Módulo 4
    tab_pesos, tab_estiba_lotes, tab_estiba_pres = st.tabs([
        "⚖️ Control y Muestreo de Pesos",
        "📅 Plano de Estiba por Fechas / Lotes",
        "📦 Plano de Estiba por Presentaciones"
    ])

    # =========================================================================
    # PESTAÑA 1: CONTROL Y MUESTREO DE PESOS
    # =========================================================================
    with tab_pesos:
        st.markdown("#### Parámetros del Contenedor y Muestreo")
        with st.expander("📋 Datos de la Orden", expanded=True):
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                fec_desp = st.date_input("Fecha Embarque:", date.today(), key="dp_fec")
            with c2:
                num_cont = st.text_input("N° Contenedor:", value="MEDU-", key="dp_cont")
            with c3:
                payload = st.number_input("Payload Máx (kg):", min_value=15000.0, max_value=32000.0, value=27000.0, step=500.0, key="dp_pay")
            with c4:
                num_pres = st.number_input("N° Presentaciones:", min_value=1, max_value=6, value=4, step=1, key="dp_npres")

        st.markdown("---")
        st.markdown("#### Ingreso de Pesos por Presentación (Muestreo hasta 30)")
        
        cols = st.columns(int(num_pres))
        presentaciones_data = []

        for i, col in enumerate(cols):
            with col:
                st.markdown(f"**Presentación {i+1}**")
                idx_default = min(i, len(LISTA_PRESENTACIONES_FRIGOSA) - 2)
                pres_sel = st.selectbox(f"Producto {i+1}:", LISTA_PRESENTACIONES_FRIGOSA, index=idx_default, key=f"dp_p_{i}")
                
                nom_p = st.text_input(f"Especifique:", key=f"dp_ot_{i}") if pres_sel == "OTRO (Digitar manualmente)" else pres_sel
                tipo_env = st.selectbox("Envase:", ["Saco (~22 kg)", "Caja (~12 kg)", "Otro"], key=f"dp_env_{i}")
                cant_b = st.number_input("Bultos Totales:", min_value=0, step=50, value=650 if "Saco" in tipo_env else 300, key=f"dp_bul_{i}")

                val_base = 22.10 if "Saco" in tipo_env else 11.90
                txt_pesos = st.text_area(
                    "Pesos balanza (kg):",
                    value=f"{val_base:.2f}, {val_base+0.05:.2f}, {val_base-0.08:.2f}, {val_base+0.12:.2f}, {val_base-0.02:.2f}",
                    height=140,
                    key=f"dp_txt_{i}"
                )

                pesos_limpios = []
                for p in txt_pesos.replace("\n", ",").split(","):
                    try:
                        v = float(p.strip())
                        if v > 0:
                            pesos_limpios.append(v)
                    except:
                        pass

                prom_u = (sum(pesos_limpios) / len(pesos_limpios)) if pesos_limpios else val_base
                subtot_kg = prom_u * cant_b

                st.caption(f"Muestras: **{len(pesos_limpios)}** | Prom: **{prom_u:.3f} kg**")
                st.caption(f"Subtotal: **{subtot_kg:,.2f} kg**")

                presentaciones_data.append({
                    "nombre": nom_p if nom_p else f"Presentación {i+1}",
                    "bultos": cant_b,
                    "pesos": pesos_limpios,
                    "promedio": prom_u,
                    "total_kg": subtot_kg
                })

        tot_bultos_gral = sum(p['bultos'] for p in presentaciones_data)
        peso_total_gral = sum(p['total_kg'] for p in presentaciones_data)
        prom_global = (peso_total_gral / tot_bultos_gral) if tot_bultos_gral > 0 else 0.0
        peso_a_favor = payload - peso_total_gral

        st.markdown("---")
        st.markdown("### 📈 Resumen Ejecutivo del Contenedor")
        r1, r2, r3, r4 = st.columns(4)
        r1.metric("📦 Bultos Totales", f"{tot_bultos_gral:,}")
        r2.metric("⚖️ Promedio Global", f"{prom_global:.3f} kg")
        r3.metric("🚛 Peso Neto Estimado", f"{peso_total_gral:,.2f} kg")
        r4.metric("🎯 Margen a Favor", f"{peso_a_favor:,.2f} kg", delta=f"{peso_a_favor:,.2f} kg", delta_color="normal" if peso_a_favor >= 0 else "inverse")

        if peso_a_favor < 0:
            st.error(f"🚨 **ALERTA:** Sobrepeso de {abs(peso_a_favor):,.2f} kg sobre el Payload.")
        else:
            st.success(f"✅ **CARGA CORRECTA:** Dentro del margen seguro ({peso_a_favor:,.2f} kg).")

        cabecera = {"fecha": str(fec_desp), "contenedor": num_cont.strip(), "payload": payload, "responsable": nombre_user}
        resumen = {"total_bultos": tot_bultos_gral, "peso_total": peso_total_gral, "promedio_global": prom_global, "peso_a_favor": peso_a_favor}

        c_b1, c_b2 = st.columns(2)
        with c_b1:
            try:
                pdf_bytes = generar_pdf_control_pesos(cabecera, presentaciones_data, resumen)
                st.download_button(
                    label="📄 Descargar Control de Peso en PDF",
                    data=pdf_bytes,
                    file_name=f"Control_Peso_{num_cont}_{fec_desp}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
            except Exception as e:
                st.warning(f"Nota en PDF: {e}")

        with c_b2:
            if st.button("💾 Guardar en Google Sheets (Control_Pesos_Embarque)", use_container_width=True):
                try:
                    ws_desp = sh.worksheet("Control_Pesos_Embarque")
                    id_dp = f"DSP-{date.today().strftime('%y%m%d%H%M%S')}"
                    detalle_txt = " | ".join([f"{p['nombre']}: {p['bultos']} bultos (prom: {p['promedio']:.2f}k)" for p in presentaciones_data])
                    fila = [id_dp, str(fec_desp), num_cont.strip(), float(payload), int(tot_bultos_gral), float(round(peso_total_gral, 2)), float(round(prom_global, 3)), float(round(peso_a_favor, 2)), nombre_user, detalle_txt]
                    ws_desp.append_row(fila)
                    st.success(f"✅ Registro guardado exitosamente.")
                except Exception as e:
                    st.error(f"Error al guardar: {e}")

    # =========================================================================
    # PESTAÑA 2: PLANO DE ESTIBA POR FECHAS / LOTES
    # =========================================================================
    with tab_estiba_lotes:
        st.markdown("#### Configuración del Contenedor (Plano de Estiba)")
        ce1, ce2, ce3 = st.columns(3)
        with ce1:
            semana_est = st.number_input("Semana N°:", min_value=1, max_value=53, value=37, key="est_sem_tab")
            peso_std = st.number_input("Peso Estándar por Bulto (kg):", value=20.0, step=0.1, key="est_peso_std_tab")
        with ce2:
            num_filas = st.number_input("Filas del Contenedor:", min_value=10, max_value=30, value=20, key="est_nfilas_tab")
            cap_gral = st.number_input("Capacidad Estándar Fila:", min_value=30, max_value=100, value=60, key="est_cap_g_tab")
        with ce3:
            cap_f1 = st.number_input("Capacidad Fila 1 (Tope):", min_value=20, max_value=100, value=58, key="est_cap_f1_tab")
            cap_fult = st.number_input(f"Capacidad Fila {num_filas} (Puerta):", min_value=20, max_value=100, value=62, key="est_cap_fu_tab")

        caps_filas = [int(cap_gral)] * int(num_filas)
        caps_filas[0] = int(cap_f1)
        caps_filas[-1] = int(cap_fult)

        st.markdown("---")
        st.markdown("#### Ingreso de Lotes (Zonas Celestes)")
        num_lotes = st.number_input("Cantidad de Lotes:", min_value=1, max_value=8, value=2, key="est_nlotes_tab")
        cols_l = st.columns(int(num_lotes))

        lista_lotes = []
        for i, col in enumerate(cols_l):
            with col:
                fec_l = st.date_input(f"Fecha Lote {i+1}:", date.today(), key=f"est_f_{i}")
                cod_l = st.text_input(f"Lote {i+1}:", value=f"LT 026.{268+i}", key=f"est_c_{i}")
                cant_l = st.number_input(f"Bultos {i+1}:", min_value=0, value=485 if i==0 else 458, step=10, key=f"est_b_{i}")
                lista_lotes.append({
                    "fecha_txt": fec_l.strftime('%d/%m/%Y'),
                    "lote_txt": cod_l,
                    "cantidad": int(cant_l)
                })

        matriz_lotes = calcular_matriz_estiba(caps_filas, lista_lotes)
        headers_l = [f"{l['fecha_txt']} | {l['lote_txt']}" for l in lista_lotes]

        data_estiba = []
        for f_idx in range(int(num_filas)):
            bultos_f = sum(matriz_lotes[f_idx])
            tm_f = (bultos_f * peso_std) / 1000.0
            row_dict = {"N° FILA": f_idx + 1, "TM": round(tm_f, 4), "CANT/FILA": bultos_f}
            for l_i in range(len(lista_lotes)):
                row_dict[headers_l[l_i]] = matriz_lotes[f_idx][l_i]
            data_estiba.append(row_dict)

        df_estiba = pd.DataFrame(data_estiba)
        st.markdown("### 📊 Cuadrícula del Plano de Estiba")
        st.dataframe(df_estiba, use_container_width=True, height=450)

        tot_b = sum(df_estiba["CANT/FILA"])
        tot_tm = sum(df_estiba["TM"])
        cap_max = sum(caps_filas)

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Capacidad Total", f"{cap_max} bultos")
        m2.metric("Total Cargado", f"{tot_b} bultos")
        m3.metric("Tonelaje Estimado", f"{tot_tm:.3f} TM")
        m4.metric("Espacio Libre", f"{cap_max - tot_b} bultos")

    # =========================================================================
    # PESTAÑA 3: PLANO DE ESTIBA POR PRESENTACIONES
    # =========================================================================
    with tab_estiba_pres:
        st.markdown("#### Distribución Mixta por Presentación (Sacos / Cajas)")
        
        cp1, cp2 = st.columns(2)
        with cp1:
            n_pres_m = st.number_input("Número de Presentaciones a Distribuir:", min_value=1, max_value=6, value=2, key="est_pm_np")
        with cp2:
            n_filas_m = st.number_input("Total Filas Contenedor:", min_value=10, max_value=30, value=20, key="est_pm_nf")

        caps_m = [60] * int(n_filas_m)
        caps_m[0] = 58
        caps_m[-1] = 62

        cols_m = st.columns(int(n_pres_m))
        lista_pres_m = []
        for i, col in enumerate(cols_m):
            with col:
                st.markdown(f"**Presentación {i+1}**")
                idx_def_p = min(i, len(LISTA_PRESENTACIONES_FRIGOSA) - 2)
                p_sel = st.selectbox(f"Corte {i+1}:", LISTA_PRESENTACIONES_FRIGOSA, index=idx_def_p, key=f"est_pms_{i}")
                nom_pm = st.text_input(f"Detalle:", key=f"est_pmo_{i}") if p_sel == "OTRO (Digitar manualmente)" else p_sel
                cant_pm = st.number_input(f"Bultos {i+1}:", min_value=0, value=650 if i==0 else 550, step=20, key=f"est_pmc_{i}")
                peso_pm = st.number_input(f"Peso Unit. (kg) {i+1}:", value=22.10 if i==0 else 11.90, step=0.05, key=f"est_pmw_{i}")
                lista_pres_m.append({"nombre": nom_pm, "cantidad": int(cant_pm), "peso_unit": float(peso_pm)})

        matriz_m = calcular_matriz_estiba(caps_m, lista_pres_m)
        headers_m = [p['nombre'][:25] for p in lista_pres_m]

        data_pres = []
        for f_idx in range(int(n_filas_m)):
            bultos_f = sum(matriz_m[f_idx])
            tm_f = sum(matriz_m[f_idx][p_i] * lista_pres_m[p_i]['peso_unit'] for p_i in range(len(lista_pres_m))) / 1000.0
            row_d = {"N° FILA": f_idx + 1, "TM ESTIMADO": round(tm_f, 4), "TOTAL BULTOS": bultos_f}
            for p_i in range(len(lista_pres_m)):
                row_d[headers_m[p_i]] = matriz_m[f_idx][p_i]
            data_pres.append(row_d)

        df_pres = pd.DataFrame(data_pres)
        st.markdown("### 📋 Plano de Estiba por Producto")
        st.dataframe(df_pres, use_container_width=True, height=450)

        tot_tm_m = sum(df_pres["TM ESTIMADO"])
        tot_b_m = sum(df_pres["TOTAL BULTOS"])

        mp1, mp2 = st.columns(2)
        mp1.metric("Total Bultos Distribuidos", f"{tot_b_m:,}")
        mp2.metric("Peso Neto Total", f"{tot_tm_m:.3f} TM ({tot_tm_m*1000:,.1f} KG)")
