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
# GENERADOR DE REPORTE PDF OFICIAL FRIGOSA SAC
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

    # Abreviamos el nombre para que encaje elegante en el PDF
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
# FUNCIÓN PRINCIPAL DE DESPACHOS
# -------------------------------------------------------------------------
def render_module(user, get_gspread_client):
    nombre_user = user.get("nombre_completo", user.get("usuario", "LUIS ENRIQUE FIESTAS ECA"))

    st.subheader("🚢 Módulo 4: Despachos y Control de Pesos de Embarque")
    st.caption(f"Supervisor a cargo: **{nombre_user}** | Planta: **Frigosa SAC**")

    # Conexión con Google Sheet
    try:
        client = get_gspread_client()
        sh = client.open_by_url(URL_PRODUCCION)
    except Exception:
        try:
            sh = client.open("BD_PRODUCCION_ARCHI_001")
        except Exception as e:
            st.error(f"Error al conectar con base de datos de producción: {e}")
            return

    # Controles generales del contenedor
    with st.expander("📋 Parámetros del Contenedor", expanded=True):
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            fec_desp = st.date_input("Fecha de Embarque:", date.today(), key="dp_fec")
        with c2:
            num_cont = st.text_input("N° Contenedor:", value="MEDU-", key="dp_cont")
        with c3:
            payload = st.number_input("Payload Máximo (kg):", min_value=15000.0, max_value=32000.0, value=27000.0, step=500.0, key="dp_pay")
        with c4:
            num_pres = st.number_input("N° de Presentaciones a cargar:", min_value=1, max_value=6, value=4, step=1, key="dp_npres")

    st.markdown("---")
    st.markdown("#### ⚖️ Muestreo de Pesos por Presentación (Hasta 30 lecturas)")
    st.caption("Seleccione la presentación de la lista y pegue los pesos separados por comas o saltos de línea.")

    cols = st.columns(int(num_pres))
    presentaciones_data = []

    for i, col in enumerate(cols):
        with col:
            st.markdown(f"**Presentación {i+1}**")
            
            # LISTA DESPLEGABLE CON EL CATÁLOGO OFICIAL
            idx_default = min(i, len(LISTA_PRESENTACIONES_FRIGOSA) - 2)
            pres_seleccionada = st.selectbox(
                f"Presentación {i+1}:", 
                LISTA_PRESENTACIONES_FRIGOSA, 
                index=idx_default, 
                key=f"d_sel_pres_{i}"
            )
            
            # Campo alternativo si eligió "OTRO"
            if pres_seleccionada == "OTRO (Digitar manualmente)":
                nom_p = st.text_input(f"Especificar Producto {i+1}:", key=f"d_txt_otro_{i}")
            else:
                nom_p = pres_seleccionada

            tipo_envase = st.selectbox("Tipo de Envase:", ["Saco (~22 kg)", "Caja (~12 kg)", "Otro"], key=f"d_env_{i}")
            cant_bultos = st.number_input(f"Cantidad Total Bultos:", min_value=0, step=50, value=650 if "Saco" in tipo_envase else 300, key=f"d_bul_{i}")

            val_base = 22.10 if "Saco" in tipo_envase else 11.90
            texto_pesos = st.text_area(
                f"Pesos de muestreo (kg):",
                value=f"{val_base:.2f}, {val_base+0.05:.2f}, {val_base-0.08:.2f}, {val_base+0.12:.2f}, {val_base-0.02:.2f}",
                height=150,
                key=f"d_txt_{i}"
            )

            pesos_limpios = []
            for p in texto_pesos.replace("\n", ",").split(","):
                try:
                    val = float(p.strip())
                    if val > 0:
                        pesos_limpios.append(val)
                except Exception:
                    pass

            prom_unit = (sum(pesos_limpios) / len(pesos_limpios)) if pesos_limpios else val_base
            subtot_kg = prom_unit * cant_bultos

            st.markdown(f"📊 Muestras: **{len(pesos_limpios)}**")
            st.markdown(f"🎯 Promedio: **{prom_unit:.3f} kg**")
            st.markdown(f"📦 Subtotal: **{subtot_kg:,.2f} kg**")

            presentaciones_data.append({
                "nombre": nom_p if nom_p else f"Presentación {i+1}",
                "bultos": cant_bultos,
                "pesos": pesos_limpios,
                "promedio": prom_unit,
                "total_kg": subtot_kg
            })

    # Consolidado General Ponderado
    total_bultos_gral = sum(p['bultos'] for p in presentaciones_data)
    peso_total_gral = sum(p['total_kg'] for p in presentaciones_data)
    prom_global = (peso_total_gral / total_bultos_gral) if total_bultos_gral > 0 else 0.0
    peso_a_favor = payload - peso_total_gral

    st.markdown("---")
    st.markdown("### 📈 Balance y Liquidación de Embarque")

    r1, r2, r3, r4 = st.columns(4)
    r1.metric("📦 Bultos Totales", f"{total_bultos_gral:,}")
    r2.metric("⚖️ Promedio Ponderado", f"{prom_global:.3f} kg")
    r3.metric("🚛 Peso Neto Total", f"{peso_total_gral:,.2f} kg")

    color_delta = "normal" if peso_a_favor >= 0 else "inverse"
    r4.metric("🎯 Margen / Peso a Favor", f"{peso_a_favor:,.2f} kg", delta=f"{peso_a_favor:,.2f} kg", delta_color=color_delta)

    if peso_a_favor < 0:
        st.error(f"🚨 **ALERTA DE SOBREPESO:** El contenedor excede el Payload por **{abs(peso_a_favor):,.2f} kg**.")
    else:
        st.success(f"✅ **CARGA PERMITIDA:** Margen disponible de **{peso_a_favor:,.2f} kg**.")

    st.markdown("---")

    cabecera = {
        "fecha": str(fec_desp),
        "contenedor": num_cont.strip(),
        "payload": payload,
        "responsable": nombre_user
    }
    resumen = {
        "total_bultos": total_bultos_gral,
        "peso_total": peso_total_gral,
        "promedio_global": prom_global,
        "peso_a_favor": peso_a_favor
    }

    c_btn1, c_btn2 = st.columns(2)
    with c_btn1:
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

    with c_btn2:
        if st.button("💾 Guardar en Google Sheets (Control_Pesos_Embarque)", use_container_width=True):
            try:
                ws_desp = sh.worksheet("Control_Pesos_Embarque")
                id_dp = f"DSP-{date.today().strftime('%y%m%d%H%M%S')}"
                detalle_txt = " | ".join([f"{p['nombre']}: {p['bultos']} bultos (prom: {p['promedio']:.2f}k)" for p in presentaciones_data])
                
                fila_guardar = [
                    id_dp,
                    str(fec_desp),
                    num_cont.strip(),
                    float(payload),
                    int(total_bultos_gral),
                    float(round(peso_total_gral, 2)),
                    float(round(prom_global, 3)),
                    float(round(peso_a_favor, 2)),
                    nombre_user,
                    detalle_txt
                ]
                ws_desp.append_row(fila_guardar)
                st.success(f"✅ Registro del contenedor {num_cont} guardado en Google Sheets.")
            except Exception as e:
                st.error(f"Error al guardar en Google Sheets: {e}")
    
