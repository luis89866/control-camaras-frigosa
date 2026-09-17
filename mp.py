import streamlit as st
import pandas as pd
from datetime import date, datetime, time

# ID del Google Sheet de Producción / Embarques
ID_SPREADSHEET_PRODUCCION = "1cX-C1Lrgp8SznxDs-_cjiMN6DptNusCmNoNopxBmJlg"

def obtener_hoja_mp(get_gspread_client):
    client = get_gspread_client()
    try:
        sh = client.open_by_key(ID_SPREADSHEET_PRODUCCION)
    except Exception:
        sh = client.open("BD_PRODUCCION_ARCHI_001")
    return sh.worksheet("mp")

def render_module(user, get_gspread_client):
    nombre_user = user.get("nombre_completo", user.get("usuario", "OPERADOR MP"))
    
    st.markdown("### 🐟 Módulo MP: Registro de Materia Prima / Tolva")
    st.caption(f"Operador en turno: **{nombre_user}** | Hoja destino: **mp**")

    # Formulario ágil de captura
    with st.form("form_registro_mp", clear_on_submit=True):
        st.markdown("##### 📝 Datos de Recepción y Tolva")
        
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            no_tolva = st.text_input("N° Tolva:", placeholder="Ej. T-01 / 1")
            fec_mp = st.date_input("Fecha:", date.today())
        with c2:
            num_reporte = st.text_input("N° Reporte:", placeholder="Ej. REP-2026-001")
            nom_embarcacion = st.text_input("Nombre Embarcación:", placeholder="Ej. MI ROSITA").upper()
        with c3:
            matricula = st.text_input("Matrícula:", placeholder="Ej. PT-12345-CM").upper()
            placas_vehiculo = st.text_input("Placa Vehículo:", placeholder="Ej. P1A-890").upper()
        with c4:
            # Campos por defecto y fijos según indicación
            especie_val = st.text_input("Especie:", value="8", disabled=True)
            destino_val = st.text_input("Destino:", value="congelado", disabled=True)

        st.markdown("---")
        st.markdown("##### ⚖️ Pesaje y Tiempos de Descarga")
        
        cp1, cp2, cp3, cp4 = st.columns(4)
        with cp1:
            cant_pesadas = st.number_input("Cantidad de Pesadas:", min_value=0, value=0, step=1)
        with cp2:
            peso_acumulativo = st.number_input("Peso Acumulativo (Kg / TM):", min_value=0.0, value=0.0, step=10.0, format="%.2f")
        with cp3:
            hora_inicio = st.time_input("Hora Inicio:", value=datetime.now().time())
        with cp4:
            hora_fin = st.time_input("Hora Fin:", value=datetime.now().time())

        btn_guardar_mp = st.form_submit_button("💾 Guardar Registro en Tolva", use_container_width=True)

        if btn_guardar_mp:
            if not no_tolva or not nom_embarcacion:
                st.warning("⚠️ Ingrese al menos el N° de Tolva y el Nombre de la Embarcación.")
            else:
                try:
                    ws_mp = obtener_hoja_mp(get_gspread_client)
                    
                    # Estructura de columnas exacta de la hoja 'mp':
                    # no_tolva | fecha | reporte | nombre_embarcacion | matricula | especie | destino | cantidad_pesadas | peso_acumulativo | h_inicio | h_fin | placas_vehiculo
                    nueva_fila = [
                        str(no_tolva).strip(),
                        str(fec_mp),
                        str(num_reporte).strip(),
                        str(nom_embarcacion).strip(),
                        str(matricula).strip(),
                        "8",           # Fijo
                        "congelado",   # Fijo
                        int(cant_pesadas),
                        float(peso_acumulativo),
                        hora_inicio.strftime("%H:%M"),
                        hora_fin.strftime("%H:%M"),
                        str(placas_vehiculo).strip()
                    ]
                    
                    ws_mp.append_row(nueva_fila)
                    st.success(f"✅ Tolva '{no_tolva}' ({nom_embarcacion}) guardada exitosamente en la hoja 'mp'.")
                except Exception as ex:
                    st.error(f"❌ Error al conectar o guardar en Sheets: {ex}")

    # =========================================================================
    # VISUALIZADOR DE REGISTROS DEL DÍA
    # =========================================================================
    st.markdown("---")
    st.markdown("##### 📋 Últimas Descargas Registradas en Hoja 'mp'")
    try:
        ws_mp_read = obtener_hoja_mp(get_gspread_client)
        data_sheet = ws_mp_read.get_all_records()
        if data_sheet:
            df_hist_mp = pd.DataFrame(data_sheet)
            st.dataframe(df_hist_mp.tail(10), use_container_width=True, hide_index=True)
        else:
            st.info("Aún no hay descargas registradas en la hoja 'mp'.")
    except Exception:
        st.caption("Conectando con Google Sheets para previsualizar registros...")
