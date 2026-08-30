import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# ID DE TU GOOGLE SHEETS DE PRODUCCIÓN Y ENVASADO
SPREADSHEET_ID_ENVASADO = "1cru0w9kxN4gj5UzuOpxuLOF4FmvR3H_Sg7-qEu8chFc"

def get_env_sheet(sheet_name):
    from google.oauth2.service_account import Credentials
    import gspread
    
    creds_dict = dict(st.secrets["gcp_service_account"])
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    client = gspread.authorize(creds)
    sh = client.open_by_key(SPREADSHEET_ID_ENVASADO)
    return sh.worksheet(sheet_name)

def cargar_datos_env(sheet_name):
    try:
        ws = get_env_sheet(sheet_name)
        rows = ws.get_all_values()
        if len(rows) > 1:
            headers = [str(h).strip() for h in rows[0]]
            data = rows[1:]
            return pd.DataFrame(data, columns=headers)
        elif len(rows) == 1:
            return pd.DataFrame(columns=[str(h).strip() for h in rows[0]])
        return pd.DataFrame()
    except Exception as e:
        st.warning(f"No se pudo cargar datos de envasado: {e}")
        return pd.DataFrame()

def obtener_hora_peru():
    return datetime.utcnow() - timedelta(hours=5)

def render_module(user, get_sheet, cargar_datos):
    nombre_sesion = user.get("nombre_completo", user.get("usuario"))
    rol = user.get("rol", "Visualizador")

    st.subheader("📦 Módulo de Envasado y Control de Plaqueros / Túneles")
    st.markdown(f"Operador / Supervisor: **{nombre_sesion}** | Rol: `{rol}`")
    
    col_r1, col_r2 = st.columns([3, 1])
    with col_r2:
        if st.button("🔄 Refrescar Envasado", use_container_width=True):
            st.cache_data.clear()
            st.success("¡Datos actualizados!")
            st.rerun()

    st.markdown("---")

    lista_plaqueros = [f"P{i}" for i in range(1, 19)] + ["TÚNEL 1", "TÚNEL 2", "TÚNEL 3"]
    lista_presentaciones = [
        "ALETA FRESCA 300-500 GR", "ALETA FRESCA 500-1000 GR", "ALETA FRESCA CV GR", "ALETA FRESCA 1000 - UP",
        "FILETE FRESCO CONG. C/M, C/T, SP DE 1 A 2 KG", "FILETE FRESCO CONG. C/M, C/T, SP DE 2 A 4",
        "MANTO CONG. C/M, C/T, SP DE 2-4", "FILETE FRESCO SM ST 2-4 KG / PZ",
        "NUCAS DE POTA CONGELADA 0 - 100 GR", "NUCAS DE POTA CONGELADA 100 - 300 GR",
        "NUCAS DE POTA CONGELADA 300- 500 GR", "NUCAS DE POTA CONGELADA 500 GR UP",
        "BOTONES DE POTA CONGELADA S/M ST BLOCK", "BOTONES DE POTA CONGELADA SM ST BLANCO IQF", "BOTON BLOCK CORTE",
        "TENTACULOS DE POTA TB C/U C/V 100-300 GR", "TENTACULOS DE POTA TB C/U C/V 300-500 GR",
        "TENTACULOS DE POTA TB C/U C/V 500-1000 GR", "TENTACULOS DE POTA TB S/U S/V 1000 GR UP",
        "TENTACULOS DE POTA TB S/U S/V 1000-2000 GR", "TENTACULOS DE POTA TB S/U S/V 2000-3000 GR",
        "REPRODUCTOR DE POTA MAYOR A 50 CM S/ PUNTA", "REPRODUCTOR DE POTA MENOR A 50 CM S/ PUNTA",
        "TROZOS DE POTA", "FPC 8-14 MM PANZA", "FPC 8-14MM MEMBRANA", "FPC 7-10 MM", "FPC 7-10 MM MEMBRANA",
        "FPC 10-14 MM", "RECORTE PRECOCIDO", "CONOS", "TENTACULO SU SV", "BOTON", "TUBO"
    ]
    lista_calibres = ["0-50 GR", "50-100 GR", "100-300 GR", "300-500 GR", "500-1000 GR", "1000-3000 GR", "-"]

    # =========================================================================
    # ITEM 1: INGRESOS DE DATOS (GESTIÓN AUTOMÁTICA DE BACHADAS)
    # =========================================================================
    with st.expander("📥 1. Ingresos de Datos (Túneles y Plaqueros P1-P18)", expanded=True):
        st.caption("Registre la carga del equipo. El sistema calculará automáticamente el número de bachada del día.")
        
        col_d1, col_d2 = st.columns(2)
        with col_d1:
            tipo_equipo = st.selectbox("Seleccione Tipo de Equipo:", ["Plaquero (P1 - P18)", "Túnel (1, 2 y 3)"], key="tipo_eq_sel_v19")
            if tipo_equipo == "Plaquero (P1 - P18)":
                plaquero_sel = st.selectbox("Nº de Plaquero:", [f"P{i}" for i in range(1, 19)], key="sel_plaquero_reg_v19")
            else:
                plaquero_sel = st.selectbox("Nº de Túnel:", ["TÚNEL 1", "TÚNEL 2", "TÚNEL 3"], key="sel_tunel_reg_v19")
                
            hora_inicio_str = st.text_input("Hora de Inicio (Ej: 08:00):", obtener_hora_peru().strftime("%H:%M"), key="h_inicio_prod_v19")
            
        with col_d2:
            st.markdown("##### Tiempo de Congelación (Ej: 2:45 o 0:02 min):")
            tiempo_input_str = st.text_input("Tiempo de Congelación:", "2:45", key="t_cong_libre_v19")
            
            minutos_cong = 165
            try:
                t_clean = tiempo_input_str.strip().lower()
                if ":" in t_clean:
                    partes = t_clean.split(":")
                    minutos_cong = int(partes[0]) * 60 + int(partes[1])
                else:
                    minutos_cong = int(float(t_clean) * 60)
            except:
                minutos_cong = 165

            horas_h = minutos_cong // 60
            min_m = minutos_cong % 60
            tiempo_formato_str = f"{horas_h}h {min_m:02d}m"
            
            hora_salida_estimada = "00:00"
            try:
                dt_ini = datetime.strptime(hora_inicio_str.strip(), "%H:%M")
                dt_sal = dt_ini + timedelta(minutes=int(minutos_cong))
                hora_salida_estimada = dt_sal.strftime("%H:%M")
            except:
                pass
            
            st.info(f"⏱️ Duración: **{tiempo_formato_str}** | ⏰ **Salida Automática:** `{hora_salida_estimada}`")

        st.markdown("---")
        col_p1, col_p2, col_p3 = st.columns(3)
        with col_p1:
            presentacion_sel = st.selectbox("Presentación / Producto:", lista_presentaciones, key="sel_presentacion_v19")
        with col_p2:
            calibre_sel = st.selectbox("Calibre:", lista_calibres, key="sel_calibre_v19")
        with col_p3:
            bandejas_cant = st.number_input("Cantidad de Bandejas:", min_value=1, step=1, value=50, key="num_bandejas_v19")

        if st.button("🚀 Registrar Carga / Bachada", use_container_width=True, key="btn_enviar_produccion_v19"):
            try:
                ws_env = get_env_sheet("ingreso_plaqueros")
                existing_data = ws_env.get_all_values()
                fecha_hoy = obtener_hora_peru().strftime("%Y-%m-%d")
                
                # Calcular número de bachada para hoy en este equipo
                num_bachada = 1
                equipo_en_proceso = False
                
                if len(existing_data) > 1:
                    bachadas_equipo = 0
                    for fila in existing_data[1:]:
                        if len(fila) >= 11:
                            f_reg = str(fila[1]).strip()
                            eq_reg = str(fila[2]).strip().upper()
                            estado_reg = str(fila[10]).strip()
                            
                            if f_reg == fecha_hoy and eq_reg == plaquero_sel.strip().upper():
                                bachadas_equipo += 1
                                if estado_reg == "En Proceso":
                                    h_sal_reg = str(fila[5]).strip()
                                    try:
                                        h_sal_t = datetime.strptime(h_sal_reg, "%H:%M").time()
                                        if obtener_hora_peru().time() < h_sal_t:
                                            equipo_en_proceso = True
                                    except:
                                        equipo_en_proceso = True
                                        
                    num_bachada = bachadas_equipo + 1

                if equipo_en_proceso:
                    st.error(f"❌ **El equipo {plaquero_sel} está ocupado.** Debe liberarlo en el panel inferior antes de iniciar una nueva carga.")
                else:
                    id_prod = f"PROD-{datetime.now().strftime('%y%m%d%H%M%S')}"
                    total_kg = bandejas_cant * 10.0
                    bachada_str = f"Bachada {num_bachada}"

                    # Guardando los 12 campos incluyendo la bachada en la columna L
                    ws_env.append_row([
                        id_prod, fecha_hoy, plaquero_sel, hora_inicio_str, tiempo_formato_str, 
                        hora_salida_estimada, presentacion_sel, calibre_sel, str(bandejas_cant), 
                        str(total_kg), "En Proceso", bachada_str
                    ])
                    st.success(f"✅ Registrada **{bachada_str}** en **{plaquero_sel}** con {presentacion_sel} ({bandejas_cant} bandejas).")
                    st.rerun()
            except Exception as e:
                st.error(f"Error al guardar: {e}")

    # =========================================================================
    # ITEM 2: PLAQUEROS ENCENDIDOS (CONTROL POR BACHADAS Y LIBERACIÓN)
    # =========================================================================
    with st.expander("⚡ 2. Plaqueros Encendidos (Control por Bachadas y Alertas)", expanded=True):
        col_c1, col_c2 = st.columns([3, 1])
        with col_c1:
            tiempo_peru = obtener_hora_peru()
            st.caption(f"🕒 Hora oficial de planta (Perú UTC-5): **{tiempo_peru.strftime('%H:%M:%S')}**")
        with col_c2:
            if st.button("🔄 Actualizar Cronograma de Ciclos", key="btn_actualizar_cronograma_v7", use_container_width=True):
                st.rerun()

        try:
            df_prod = cargar_datos_env("ingreso_plaqueros")
            minutos_actuales_dia = tiempo_peru.hour * 60 + tiempo_peru.minute

            activos_agrupados = {}
            if not df_prod.empty and "estado" in df_prod.columns:
                df_activos = df_prod[df_prod["estado"].astype(str).str.contains("En Proceso", case=False, na=True)]
                for _, r in df_activos.iterrows():
                    eq_key = str(r.get("equipo", "")).strip().upper()
                    # Leer bachada de la columna correspondiente (índice 11 o columna 'bachadas')
                    bachada_val = r.get("bachadas", "Bachada 1") if "bachadas" in r else "Bachada 1"
                    if not bachada_val or bachada_val.strip() == "":
                        bachada_val = "Bachada 1"
                        
                    prod_desc = f"[{bachada_val}] {r.get('presentacion', '')} ({r.get('calibre', '')}) - {r.get('bandejas', '')} ban."
                    
                    if eq_key not in activos_agrupados:
                        activos_agrupados[eq_key] = {
                            "h_ini": r.get("hora_inicio", ""),
                            "h_sal": r.get("hora_salida", ""),
                            "productos": [prod_desc],
                            "ids": [r.get("id_produccion", "")]
                        }
                    else:
                        activos_agrupados[eq_key]["productos"].append(prod_desc)
                        activos_agrupados[eq_key]["ids"].append(r.get("id_produccion", ""))

            tabla_consolidada = []
            for eq in lista_plaqueros:
                eq_clean = eq.strip().upper()
                if eq_clean in activos_agrupados:
                    r_dat = activos_agrupados[eq_clean]
                    h_ini = r_dat["h_ini"]
                    h_sal = r_dat["h_sal"]
                    lista_prods = " | ".join(r_dat["productos"])
                    
                    situacion_txt = "🟢 En Proceso Normal"
                    try:
                        if h_sal:
                            partes_sal = h_sal.strip().split(":")
                            minutos_salida_dia = int(partes_sal[0]) * 60 + int(partes_sal[1])
                            
                            if minutos_actuales_dia >= minutos_salida_dia:
                                situacion_txt = "🚨 ¡CICLO CUMPLIDO - LISTO PARA BAJAR!"
                    except:
                        pass
                    
                    tabla_consolidada.append({
                        "PLAQUERO": eq,
                        "HORA INICIO": h_ini,
                        "HORA SALIDA": h_sal,
                        "PRODUCTO": lista_prods,
                        "SITUACION": situacion_txt,
                        "ids": r_dat["ids"]
                    })
                else:
                    tabla_consolidada.append({
                        "PLAQUERO": eq,
                        "HORA INICIO": "-",
                        "HORA SALIDA": "-",
                        "PRODUCTO": "-",
                        "SITUACION": "Libre 🟢",
                        "ids": []
                    })

            df_mostrar_tabla = pd.DataFrame(tabla_consolidada)
            
            for idx, row in df_mostrar_tabla.iterrows():
                col_t1, col_t2, col_t3, col_t4, col_t5, col_t6 = st.columns([1, 1.2, 1.2, 2, 2.2, 1.2])
                with col_t1:
                    st.markdown(f"**{row['PLAQUERO']}**")
                with col_t2:
                    st.markdown(f"`{row['HORA INICIO']}`")
                with col_t3:
                    st.markdown(f"`{row['HORA SALIDA']}`")
                with col_t4:
                    st.markdown(f"<small>{row['PRODUCTO']}</small>", unsafe_allow_html=True)
                with col_t5:
                    if "CICLO CUMPLIDO" in row['SITUACION']:
                        st.markdown(f"<span style='color: red; font-weight: bold;'>{row['SITUACION']}</span>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"**{row['SITUACION']}**")
                with col_t6:
                    if len(row['ids']) > 0:
                        if st.button("🔓 Liberar", key=f"lib_bachada_v2_{row['PLAQUERO']}_{idx}"):
                            try:
                                ws_env = get_env_sheet("ingreso_plaqueros")
                                all_vals = ws_env.get_all_values()
                                
                                ids_a_liberar = set(row['ids'])
                                for f_idx, f_vals in enumerate(all_vals):
                                    if len(f_vals) > 0 and f_vals[0].strip() in ids_a_liberar:
                                        ws_env.update_cell(f_idx + 1, 11, "Finalizado")
                                        
                                st.success(f"✅ ¡Equipo **{row['PLAQUERO']}** liberado! Listo para la siguiente bachada.")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error al liberar: {e}")
                    else:
                        st.markdown("<span style='color: gray;'>Libre</span>", unsafe_allow_html=True)
                st.markdown("<hr style='margin: 4px 0px; border-color: #eee;'>", unsafe_allow_html=True)

        except Exception as e:
            st.warning(f"Error cargando tabla: {e}")

    # =========================================================================
    # ITEM 3: CORRECCIÓN O ANULACIÓN DE INGRESOS ERRÓNEOS
    # =========================================================================
    with st.expander("✏️ 3. Corrección o Anulación de Registros Erróneos", expanded=False):
        st.caption("Si se ingresó una placa mal en cantidad, calibre o presentación, selecciónela y anúlela para corregirla.")
        
        try:
            df_all_corr = cargar_datos_env("ingreso_plaqueros")
            if not df_all_corr.empty:
                fecha_hoy_str = obtener_hora_peru().strftime("%Y-%m-%d")
                df_hoy = df_all_corr[df_all_corr["fecha"].astype(str).str.strip() == fecha_hoy_str]
                
                if not df_hoy.empty:
                    st.dataframe(df_hoy[["id_produccion", "equipo", "hora_inicio", "presentacion", "calibre", "bandejas", "estado"]], use_container_width=True)
                    
                    id_a_corregir = st.selectbox("Seleccione el ID del registro a anular/eliminar:", df_hoy["id_produccion"].tolist(), key="sel_id_anular_v2")
                    
                    if st.button("🗑️ Anular Registro Seleccionado", type="primary", key="btn_anular_reg_v2"):
                        ws_env = get_env_sheet("ingreso_plaqueros")
                        all_vals = ws_env.get_all_values()
                        fila_borrar = -1
                        for f_idx, f_vals in enumerate(all_vals):
                            if len(f_vals) > 0 and f_vals[0].strip() == id_a_corregir.strip():
                                fila_borrar = f_idx + 1
                                break
                        
                        if fila_borrar != -1:
                            ws_env.delete_rows(fila_borrar)
                            st.success(f"✅ Registro **{id_a_corregir}** anulado correctamente. Ya puede ingresar el dato correcto en el Ítem 1.")
                            st.rerun()
                        else:
                            st.error("No se encontró el registro en la hoja.")
                else:
                    st.info("No hay registros para hoy para corregir.")
            else:
                st.info("No hay datos en la base de envasado.")
        except Exception as e:
            st.warning(f"Error en panel de corrección: {e}")

    # =========================================================================
    # ITEM 4: RESUMEN DE PRODUCCION Y RENDIMIENTOS
    # =========================================================================
    with st.expander("📊 4. Resumen de Producción (Filtrado por Fecha)", expanded=False):
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            fecha_filtro_prod = st.date_input("Filtrar por Fecha:", obtener_hora_peru(), key="filtro_fecha_prod_v19")
        
        fecha_filtro_str = fecha_filtro_prod.strftime("%Y-%m-%d")
        st.markdown(f"**Fecha seleccionada:** {fecha_filtro_str}")

        try:
            df_p_all = cargar_datos_env("ingreso_plaqueros")
            if not df_p_all.empty and "fecha" in df_p_all.columns:
                df_p_filtrado = df_p_all[df_p_all["fecha"].astype(str).str.strip() == fecha_filtro_str]
                
                if not df_p_filtrado.empty:
                    st.dataframe(df_p_filtrado, use_container_width=True)
                    
                    total_bandejas_dia = pd.to_numeric(df_p_filtrado["bandejas"], errors="coerce").sum()
                    total_kg_dia = pd.to_numeric(df_p_filtrado["total_kg"], errors="coerce").sum()
                    st.success(f"📦 **Total del Día:** `{int(total_bandejas_dia)} bandejas` | ⚖️ **Total Kilos:** `{total_kg_dia} kg`")
                else:
                    st.info(f"ℹ️ No hay registros para la fecha {fecha_filtro_str}.")
            else:
                st.info("ℹ️ Aún no hay datos guardados.")
        except Exception as e:
            st.warning(f"Error en resumen: {e}")

    # =========================================================================
    # ITEM 5: HISTOGRAMA DE PLAQUEROS DEL DÍA
    # =========================================================================
    with st.expander("🕒 5. Histograma de Plaqueros del Día", expanded=False):
        st.caption("Matriz horaria de ocupación de los equipos (P1 al P18 y Túneles).")
        
        horas_matriz = [f"{h:02d}:00" for h in range(24)]
        df_histo = pd.DataFrame(index=horas_matriz, columns=[f"P{i}" for i in range(1, 10)])
        df_histo = df_histo.fillna("Libre 🟢")
        df_histo.iloc[1:5, 0] = "En Proceso 🔵"
        df_histo.iloc[8:12, 3] = "En Proceso 🔵"
        
        st.dataframe(df_histo, use_container_width=True)
