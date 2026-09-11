import streamlit as st
import pandas as pd
from datetime import date
import io
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

def generar_pdf_control_pesos(cabecera, presentaciones_data, resumen):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, leftMargin=30, rightMargin=30, topMargin=30, bottomMargin=30)
    story = []
    styles = getSampleStyleSheet()

    # Título
    titulo_style = ParagraphStyle(
        'Titulo',
        parent=styles['Heading1'],
        fontSize=14,
        leading=16,
        textColor=colors.HexColor("#1A365D"),
        alignment=1
    )
    story.append(Paragraph("SEGUIMIENTO DE CONTROL DE PESO - FRIGOSA SAC", titulo_style))
    story.append(Spacer(1, 10))

    # Cabecera
    data_cab = [
        ["FECHA:", cabecera['fecha'], "N° CONTENEDOR:", cabecera['contenedor']],
        ["PAYLOAD (KG):", f"{cabecera['payload']:,.2f}", "PESO NETO TOTAL:", f"{resumen['peso_total']:,.2f} KG"],
        ["TOTAL BULTOS:", f"{resumen['total_bultos']:,}", "PESO A FAVOR:", f"{resumen['peso_a_favor']:,.2f} KG"],
        ["RESPONSABLE:", cabecera['responsable'], "PROMEDIO GLOBAL:", f"{resumen['promedio_global']:.3f} KG"]
    ]
    t_cab = Table(data_cab, colWidths=[110, 150, 120, 150])
    t_cab.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor("#1A365D")),
        ('TEXTCOLOR', (2, 0), (2, -1), colors.HexColor("#1A365D")),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F0F4F8")),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
        ('ALIGN', (1, 0), (1, -1), 'CENTER'),
        ('ALIGN', (3, 0), (3, -1), 'CENTER'),
    ]))
    story.append(t_cab)
    story.append(Spacer(1, 15))

    # Tabla de Pesos de Muestreo (Columnas dinámicas por presentación)
    headers = [p['nombre'][:18] for p in presentaciones_data]
    matrix_pesos = [headers]
    for r in range(30):
        fila = [f"{p['pesos'][r]:.2f}" if r < len(p['pesos']) and p['pesos'][r] > 0 else "-" for p in presentaciones_data]
        matrix_pesos.append(fila)

    # Fila de totales y promedios por presentación
    fila_bultos = [f"Bultos: {p['bultos']}" for p in presentaciones_data]
    fila_prom = [f"Prom: {p['promedio']:.3f}" for p in presentaciones_data]
    fila_tot = [f"Tot: {p['total_kg']:,.1f}k" for p in presentaciones_data]
    matrix_pesos.append(fila_bultos)
    matrix_pesos.append(fila_prom)
    matrix_pesos.append(fila_tot)

    col_w = 530 / max(len(presentaciones_data), 1)
    t_muestreo = Table(matrix_pesos, colWidths=[col_w] * len(presentaciones_data))
    t_muestreo.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 7),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#2B6CB0")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ('BACKGROUND', (0, -3), (-1, -1), colors.HexColor("#EDF2F7")),
        ('FONTNAME', (0, -3), (-1, -1), 'Helvetica-Bold'),
    ]))
    story.append(t_muestreo)

    doc.build(story)
    buffer.seek(0)
    return buffer

def render_calculador_pesos(user):
    st.subheader("⚖️ Calculador y Muestreo de Pesos por Contenedor")

    # Controles superiores
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        fec_desp = st.date_input("Fecha Despacho:", date.today())
    with c2:
        num_cont = st.text_input("N° Contenedor:", placeholder="Ej: MEDU1234567")
    with c3:
        payload = st.number_input("Payload Máx (KG):", min_value=10000.0, max_value=32000.0, value=27000.0, step=500.0)
    with c4:
        num_pres = st.number_input("N° de Presentaciones a cargar:", min_value=1, max_value=8, value=4, step=1)

    st.markdown("---")

    # Columnas dinámicas para muestreo
    cols = st.columns(int(num_pres))
    presentaciones_data = []

    for i, col in enumerate(cols):
        with col:
            st.markdown(f"**Presentación {i+1}**")
            nom_pres = st.text_input(f"Producto {i+1}:", value="Sacos Pota" if i % 2 == 0 else "Cajas Pota", key=f"nom_p_{i}")
            tipo_envase = st.selectbox("Envase:", ["Sacos (~22kg)", "Cajas (~12kg)", "Otro"], key=f"env_{i}")
            cant_bultos = st.number_input(f"Cantidad Total (Bultos):", min_value=0, step=50, value=600 if "Sacos" in tipo_envase else 400, key=f"cant_b_{i}")

            val_default = 22.10 if "Sacos" in tipo_envase else 11.90
            texto_pesos = st.text_area(
                f"Pesos muestra (hasta 30, separados por coma o salto):",
                value=f"{val_default}, {val_default+0.05}, {val_default-0.08}",
                key=f"txt_pesos_{i}",
                height=130
            )

            # Parsear pesos ingresados
            pesos_limpios = []
            for p in texto_pesos.replace("\n", ",").split(","):
                try:
                    val = float(p.strip())
                    if val > 0:
                        pesos_limpios.append(val)
                except:
                    pass

            promedio_p = (sum(pesos_limpios) / len(pesos_limpios)) if pesos_limpios else val_default
            total_kg_p = promedio_p * cant_bultos

            st.caption(f"Promedio: **{promedio_p:.3f} kg**")
            st.caption(f"Total Estimado: **{total_kg_p:,.2f} kg**")

            presentaciones_data.append({
                "nombre": nom_pres,
                "bultos": cant_bultos,
                "pesos": pesos_limpios,
                "promedio": promedio_p,
                "total_kg": total_kg_p
            })

    # Consolidado General
    total_bultos_gral = sum(p['bultos'] for p in presentaciones_data)
    peso_total_gral = sum(p['total_kg'] for p in presentaciones_data)
    prom_global = (peso_total_gral / total_bultos_gral) if total_bultos_gral > 0 else 0.0
    peso_a_favor = payload - peso_total_gral

    st.markdown("---")
    st.markdown("### 📊 Resumen Ejecutivo del Embarque")

    r1, r2, r3, r4 = st.columns(4)
    r1.metric("📦 Bultos Totales", f"{total_bultos_gral:,}")
    r2.metric("⚖️ Promedio Global", f"{prom_global:.3f} kg")
    r3.metric("🚛 Peso Total Estimado", f"{peso_total_gral:,.2f} kg")
    
    delta_color = "normal" if peso_a_favor >= 0 else "inverse"
    r4.metric("🎯 Peso a Favor (Margen)", f"{peso_a_favor:,.2f} kg", delta=f"{peso_a_favor:,.2f} kg", delta_color=delta_color)

    if peso_a_favor < 0:
        st.error(f"⚠️ ¡ALERTA DE SOBREPESO! El contenedor excede el Payload por {abs(peso_a_favor):,.2f} kg.")

    # Exportación a PDF
    cabecera = {
        "fecha": str(fec_desp),
        "contenedor": num_cont if num_cont else "S/N",
        "payload": payload,
        "responsable": user.get('nombre_completo', user.get('usuario', 'LUIS ENRIQUE FIESTAS ECA'))
    }
    resumen = {
        "total_bultos": total_bultos_gral,
        "peso_total": peso_total_gral,
        "promedio_global": prom_global,
        "peso_a_favor": peso_a_favor
    }

    pdf_bytes = generar_pdf_control_pesos(cabecera, presentaciones_data, resumen)

    st.download_button(
        label="📄 Descargar Reporte de Control de Peso en PDF",
        data=pdf_bytes,
        file_name=f"Control_Peso_{num_cont}_{fec_desp}.pdf",
        mime="application/pdf",
        use_container_width=True
    )
