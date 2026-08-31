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
        return pd.DataFrame()

def obtener_calibres_dinamicos():
    """Lee la lista de calibres desde Google Sheets (pestaña CALIBRE)"""
    lista_cal_def = ["0-50 GR/PZA", "50-100 GR/PZA", "100-300 GR/PZA", "-"]
    for nombre_pestana in ["CALIBRE", "Calibre", "calibre"]:
        try:
            ws = get_env_sheet(nombre_pestana)
            columna_cal = ws.col_values(1)
            if len(columna_cal) > 0:
                valores = [str(v).strip() for v in columna_cal if str(v).strip() != "" and str(v).strip().upper() != "CALIBRE"]
                if len(valores) > 0:
                    lista_cal_def = valores
                    break
        except:
            continue
    return lista_cal_def

def obtener_lote_por_fecha(fecha_str):
    """Busca en la pestaña LOTE el código de lote correspondiente a la fecha ingresada"""
    lote_encontrado = f"LOTE-{fecha_str.replace('-', '')}"
    for nombre_pestana in ["LOTE", "Lote", "lote"]:
        try:
            ws = get_env_sheet(nombre_pestana)
            filas = ws.get_all_values()
            for fila in filas:
                if len(fila) >= 2:
                    f_Hoja = str(fila[0]).strip()
                    l_Hoja = str(fila[1]).strip()
                    if f_Hoja == fecha_str:
                        lote_encontrado = l_Hoja
                        break
            break
        except:
            continue
    return lote_encontrado

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
    
    dic_presentaciones = {
        "ALETA FRESCA": "SUB001",
        "ALETA PRECOCIDA": "SUB002",
        "TENTACULO SU SV": "SUB003",
        "TENTACULO CU CV": "SUB004",
        "RECORTE FRESCO SM ST": "SUB005",
        "RECORTE PRECOCIDO": "SUB006",
        "ANILLAS SM ST": "SUB007",
        "BOTON SM ST": "SUB008",
        "FILETE FRESCO SM ST": "SUB009",
        "FILETE FRESCO CM CT": "SUB010",
        "FILETE PRECOCIDO": "SUB011",
        "NUCAS FRESCAS": "SUB012",
        "PICOS": "SUB013",
        "CONOS": "SUB014",
        "REPRODUCTOR": "SUB015"
    }
    
    lista_presentaciones = list(dic_presentaciones.keys())
    lista_calibres = obtener_calibres_dinamicos()

    # =========================================================================
    # ITEM 1: INGRESOS DE DATOS (CON LOTE AUTOMÁTICO Y DUPLICADOS)
    # =========================================================================
    with st.expander("📥 1. Ingresos de Datos (Túneles y Plaqueros P1-P18)", expanded=True):
        st.caption("Registre la carga del equipo. El lote se asigna automáticamente según la fecha.")
        
        col_d1, col_d2 = st.columns(2)
        with col_d1:
            tipo_equipo = st.selectbox("Seleccione Tipo de Equipo:", ["Plaquero (P1 - P18)", "Túnel (1, 2 y 3)"], key="tipo_eq_sel_v32")
            if tipo_equipo == "Plaquero (P1 - P18)":
                plaquero_sel = st.selectbox("Nº de Plaquero:", [f"P{i}" for i in range(1, 19)], key="sel_plaquero_reg_v32")
            else:
                plaquero_sel = st.selectbox("Nº de Túnel:", ["TÚNEL 1", "TÚNEL 2", "TÚNEL 3"], key="sel_tunel_reg_v32")
                
            fecha_ingreso_obj = st.date_input("Fecha de Producción:", obtener_hora_peru(), key="f_prod_reg_v32")
            fecha_ingreso_str = fecha_ingreso_obj.strftime("%Y-%m-%d")
            
            # Obtener Lote automático por fecha
            lote_automatico = obtener_lote_por_fecha(fecha_ingreso_str)
            st.info(f"📦 **Lote asignado:** `{lote_automatico}`")

            hora_inicio_str = st.text_input("Hora de Inicio (Ej: 08:00):", obtener_hora_peru().strftime("%H:%M"), key="h_inicio_prod_v32")
            
        with col_d2:
            st.markdown("##### Tiempo de Congelación (Ej: 2:45 o 0:02 min):")
            tiempo_input_str = st.text_input("Tiempo de Congelación:", "2:45", key="t_cong_libre_v32")
            
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
            presentacion_sel = st.selectbox("Presentación / Producto:", lista_presentaciones, key="sel_presentacion_v32")
        with col_p2:
            calibre_sel = st.selectbox("Calibre:", lista_calibres, key="sel_calibre_v32")
        with col_p3:
            bandejas_cant = st.number_input("Cantidad de Bandejas:", min_value=1, step=1, value=50, key="num_bandejas_v32")

        if st.button("🚀 Registrar / Agregar Presentación", use_container_width=True, key="btn_enviar_produccion_v32"):
            try:
                ws_env = get_env_sheet("ingreso_plaqueros")
                existing_data = ws_env.get_all_values()
                
                num_bachada = 1
                producto_duplicado = False
                
                if len(existing_data) > 1:
                    bachadas_registradas_hoy = set()
                    en_proceso_activo = False
                    for fila in existing_data[1:]:
                        if len(fila) >= 11:
                            f_reg = str(fila[1]).strip()
                            eq_reg = str(fila[2]).strip().upper()
                            pres_reg = str(fila[6]).strip().upper()
                            cal_reg = str(fila[7]).strip().upper()
                            estado_reg = str(fila[10]).strip()
                            bachada_val = str(fila[11]).strip() if len(fila) > 11 else "Bachada 1"
                            
                            if f_reg == fecha_ingreso_str and eq_reg == plaquero_sel.strip().upper():
                                if bachada_val:
                                    bachadas_registradas_hoy.add(bachada_val)
                                if estado_reg == "En Proceso":
                                    en_proceso_activo = True
                                    num_bachada = int(bachada_val.replace("Bachada", "").strip()) if "Bachada" in bachada_val else len(bachadas_registradas_hoy)
                                    
                                    if pres_reg == presentacion_sel.strip().upper() and cal_reg == calibre_sel.strip().upper():
                                        producto_duplicado = True

                    if not en_proceso_activo and len(bachadas_registradas_hoy) > 0:
                        num_bachada = len(bachadas_registradas_hoy) + 1

                if producto_duplicado:
                    st.error(f"❌ **Acción rechazada:** El producto **{presentacion_sel}** con calibre **{calibre_sel}** ya se encuentra registrado y activo en el equipo **{plaquero_sel}**.")
                else:
                    id_prod = f"PROD-{datetime.now().strftime('%y%m%d%H%M%S')}"
                    total_kg = bandejas_cant * 10.0
                    bachada_str = f"Bachada {num_bachada}"
                    codigo_pres = dic_presentaciones.get(presentacion_sel, "")

                    ws_env.append_row([
                        id_prod, fecha_ingreso_str, plaquero_sel, hora_inicio_str, tiempo_formato_str, 
                        hora_salida_estimada, presentacion_sel, calibre_sel, str(bandejas_cant), 
                        str(total_kg), "En Proceso", bachada_str, codigo_pres, lote_automatico
                    ])
                    st.success(f"✅ Se registró **{presentacion_sel}** ({bandejas_cant} ban.) en **{plaquero_sel}** bajo `[{bachada_str}]` (Lote: {lote_automatico})!")
                    st.rerun()
            except Exception as e:
                st.error(f"Error al guardar: {e}")

    # =========================================================================
    # ITEM 2: PLAQUEROS ENCENDIDOS
    # =========================================================================
    with st.expander("⚡ 2. Plaqueros Encendidos (Control de Ciclos y Retrasos)", expanded=True):
        tiempo_peru = obtener_hora_peru()
        col_c1, col_c2 = st.columns([3, 1])
        with col_c1:
            st.caption(f"🕒 Hora oficial de planta (Perú UTC-5): **{tiempo_peru.strftime('%H:%M:%S')}**")
        with col_c2:
            if st.button("🔄 Actualizar Cronograma", key="btn_actualizar_cronograma_v20", use_container_width=True):
                st.rerun()

        try:
            df_prod = cargar_datos_env("ingreso_plaqueros")
            minutos_actuales_dia = tiempo_peru.hour * 60 + tiempo_peru.minute

            activos_agrupados = {}
            if not df_prod.empty and "estado" in df_prod.columns:
                df_activos = df_prod[df_prod["estado"].astype(str).str.contains("En Proceso", case=False, na=True)]
                for _, r in df_activos.iterrows():
                    eq_key = str(r.get("equipo", "")).strip().upper()
                    bachada_val = r.get("bachadas", "Bachada 1") if "bachadas" in r else "Bachada 1"
                    if not bachada_val or bachada_val.strip() == "":
                        bachada_val = "Bachada 1"
                        
                    bandejas_val = int(r.get('bandejas', 0)) if str(r.get('bandejas', '0')).isdigit() else 0
                    prod_desc = f"**{bachada_val}**: {r.get('presentacion', '')} ({r.get('calibre', '')}) - {bandejas_val} ban."
                    
                    if eq_key not in activos_agrupados:
                        activos_agrupados[eq_key] = {
                            "h_ini": r.get("hora_inicio", ""),
                            "h_sal": r.get("hora_salida", ""),
                            "productos": [prod_desc],
                            "total_bandejas": bandejas_val,
                            "ids": [r.get("id_produccion", "")]
                        }
                    else:
                        activos_agrupados[eq_key]["productos"].append(prod_desc)
                        activos_agrupados[eq_key]["total_bandejas"] += bandejas_val
                        activos_agrupados[eq_key]["ids"].append(r.get("id_produccion", ""))

            tabla_consolidada = []
            for eq in lista_plaqueros:
                eq_clean = eq.strip().upper()
                if eq_clean in activos_agrupados:
                    r_dat = activos_agrupados[eq_clean]
                    h_ini = r_dat["h_ini"]
                    h_sal = r_dat["h_sal"]
                    
                    lista_prods = "<br>".join(r_dat["productos"])
                    lista_prods += f"<br><br>📦 <b>Total Bandejas:</b> <span style='color: #007bff;'>{r_dat['total_bandejas']} ban.</span>"
                    
                    situacion_txt = "🟡 En Proceso Normal"
                    minutos_retraso = 0
                    try:
                        if h_sal:
                            partes_sal = h_sal.strip().split(":")
                            minutos_salida_dia = int(partes_sal[0]) * 60 + int(partes_sal[1])
                            
                            if minutos_actuales_dia >= minutos_salida_dia:
                                minutos_retraso = minutos_actuales_dia - minutos_salida_dia
                                h_ret_h = minutos_retraso // 60
                                h_ret_m = minutos_retraso % 60
                                tiempo_ret_str = f"{h_ret_h}h {h_ret_m:02d}m" if h_ret_h > 0 else f"{h_ret_m} min"
                                situacion_txt = f"🔴 ¡CICLO CUMPLIDO!<br><span style='color: #d9534f; font-size: 13px;'>⏱️ Retraso sin bajar: <b>{tiempo_ret_str}</b></span>"
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
                        "SITUACION": "🟢 Libre",
                        "ids": []
                    })

            df_mostrar_tabla = pd.DataFrame(tabla_consolidada)
            
            for idx, row in df_mostrar_tabla.iterrows():
                col_t1, col_t2, col_t3, col_t4, col_t5, col_t6 = st.columns([1, 1.2, 1.2, 2.2, 2.2, 1.2])
                with col_t1:
                    st.markdown(f"**{row['PLAQUERO']}**")
                with col_t2:
                    st.markdown(f"`{row['HORA INICIO']}`")
                with col_t3:
                    st.markdown(f"`{row['HORA SALIDA']}`")
                with col_t4:
                    st.markdown(row['PRODUCTO'], unsafe_allow_html=True)
                with col_t5:
                    if "CICLO CUMPLIDO" in row['SITUACION']:
                        st.markdown(row['SITUACION'], unsafe_allow_html=True)
                    elif "Libre" in row['SITUACION']:
                        st.markdown(f"<span style='color: #28a745; font-weight: bold;'>{row['SITUACION']}</span>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"<span style='color: #f0ad4e; font-weight: bold;'>{row['SITUACION']}</span>", unsafe_allow_html=True)
                with col_t6:
                    if len(row['ids']) > 0:
                        if st.button("🔓 Liberar", key=f"lib_fix_sel_v2_{row['PLAQUERO']}_{idx}"):
                            try:
                                ws_env = get_env_sheet("ingreso_plaqueros")
                                all_vals = ws_env.get_all_values()
                                
                                ids_a_liberar = set(row['ids'])
                                for f_idx, f_vals in enumerate(all_vals):
                                    if len(f_vals) > 0 and f_vals[0].strip() in ids_a_liberar:
                                        ws_env.update_cell(f_idx + 1, 11, "Finalizado")
                                        
                                st.success(f"✅ ¡Equipo **{row['PLAQUERO']}** liberado!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error al liberar: {e}")
                    else:
                        st.markdown("<span style='color: gray; font-size: 13px;'>Libre</span>", unsafe_allow_html=True)
                st.markdown("<hr style='margin: 6px 0px; border-color: #eee;'>", unsafe_allow_html=True)

        except Exception as e:
            st.warning(f"Error cargando tabla: {e}")

    # =========================================================================
    # ITEM 3: MODIFICACIÓN O ELIMINACIÓN DE REGISTROS (CORREGIDO)
    # =========================================================================
    with st.expander("✏️ 3. Modificación o Eliminación de Registros", expanded=False):
        st.caption("Seleccione un registro para modificar sus valores correctamente o eliminarlo.")
        
        try:
            df_all_mod = cargar_datos_env("ingreso_plaqueros")
            if not df_all_mod.empty:
                fecha_hoy_str = obtener_hora_peru().strftime("%Y-%m-%d")
                df_hoy = df_all_mod[df_all_mod["fecha"].astype(str).str.strip() == fecha_hoy_str]
                
                if not df_hoy.empty:
                    st.dataframe(df_hoy[["id_produccion", "equipo", "hora_inicio", "presentacion", "calibre", "bandejas", "estado", "bachadas"]], use_container_width=True)
                    
                    id_a_editar = st.selectbox("Seleccione el ID del registro:", df_hoy["id_produccion"].tolist(), key="sel_id_mod_v13")
                    
                    fila_act = df_hoy[df_hoy["id_produccion"] == id_a_editar].iloc[0]
                    
                    pres_actual = str(fila_act['presentacion']).strip()
                    cal_actual = str(fila_act['calibre']).strip()
                    band_actual = int(fila_act['bandejas']) if str(fila_act['bandejas']).isdigit() else 50
                    
                    idx_pres = lista_presentaciones.index(pres_actual) if pres_actual in lista_presentaciones else 0
                    idx_cal = lista_calibres.index(cal_actual) if cal_actual in lista_calibres else 0
                    
                    st.markdown(f"**Registro seleccionado:** `{id_a_editar}` ({fila_act['equipo']} - {fila_act.get('bachadas', '')})")
                    
                    col_m1, col_m2, col_m3 = st.columns(3)
                    with col_m1:
                        nueva_pres = st.selectbox("Presentación:", lista_presentaciones, index=idx_pres, key="mod_pres_v13")
                    with col_m2:
                        nuevo_cal = st.selectbox("Calibre:", lista_calibres, index=idx_cal, key="mod_cal_v13")
                    with col_m3:
                        nuevas_band = st.number_input("Cantidad de Bandejas:", min_value=1, step=1, value=band_actual, key="mod_band_v13")

                    col_btn1, col_btn2 = st.columns(2)
                    with col_btn1:
                        if st.button("💾 Guardar Cambios (Modificar)", type="primary", key="btn_guardar_mod_v13", use_container_width=True):
                            ws_env = get_env_sheet("ingreso_plaqueros")
                            all_vals = ws_env.get_all_values()
                            fila_tabla = -1
                            for f_idx, f_vals in enumerate(all_vals):
                                if len(f_vals) > 0 and f_vals[0].strip() == id_a_editar.strip():
                                    fila_tabla = f_idx + 1
                                    break
                            
                            if fila_tabla != -1:
                                nuevo_total_kg = nuevas_band * 10.0
                                nuevo_codigo = dic_presentaciones.get(nueva_pres, "")
                                
                                ws_env.update_cell(fila_tabla, 7, nueva_pres)
                                ws_env.update_cell(fila_tabla, 8, nuevo_cal)
                                ws_env.update_cell(fila_tabla, 9, str(nuevas_band))
                                ws_env.update_cell(fila_tabla, 10, str(nuevo_total_kg))
                                ws_env.update_cell(fila_tabla, 13, nuevo_codigo)
                                
                                st.success(f"✅ ¡Registro **{id_a_editar}** actualizado correctamente!")
                                st.rerun()
                            else:
                                st.error("No se encontró la fila en Google Sheets.")
                    
                    with col_btn2:
                        if st.button("🗑️ Eliminar Registro", type="secondary", key="btn_eliminar_reg_v13", use_container_width=True):
                            ws_env = get_env_sheet("ingreso_plaqueros")
                            all_vals = ws_env.get_all_values()
                            fila_tabla = -1
                            for f_idx, f_vals in enumerate(all_vals):
                                if len(f_vals) > 0 and f_vals[0].strip() == id_a_editar.strip():
                                    fila_tabla = f_idx + 1
                                    break
                            
                            if fila_tabla != -1:
                                ws_env.delete_rows(fila_tabla)
                                st.success(f"🗑️ ¡Registro **{id_a_editar}** eliminado exitosamente!")
                                st.rerun()
                            else:
                                st.error("No se encontró la fila para eliminar.")
                else:
                    st.info("No hay registros para hoy para modificar o eliminar.")
            else:
                st.info("No hay datos en la base de envasado.")
        except Exception as e:
            st.warning(f"Error en panel de gestión: {e}")

    # =========================================================================
    # ITEM 4: RESUMEN DE PRODUCCION Y RENDIMIENTOS (CON FILTROS DE FECHA Y LOTE)
    # =========================================================================
    with st.expander("📊 4. Resumen de Producción (Filtrado por Fecha y Lote)", expanded=False):
        st.markdown("##### Filtrar Historial de Producción:")
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            filtro_fecha_obj = st.date_input("Filtrar por Fecha:", obtener_hora_peru(), key="filtro_fecha_hist_v32")
        with col_f2:
            try:
                df_all_lotes = cargar_datos_env("ingreso_plaqueros")
                lotes_disponibles = ["TODOS"]
                if not df_all_lotes.empty and "lote" in df_all_lotes.columns:
                    lotes_unicos = df_all_lotes["lote"].dropna().astype(str).str.strip().unique().tolist()
                    lotes_disponibles += [l for l in lotes_unicos if l != ""]
            except:
                lotes_disponibles = ["TODOS"]
                
            filtro_lote_sel = st.selectbox("Filtrar por Lote:", lotes_disponibles, key="filtro_lote_sel_v32")

        filtro_fecha_str = filtro_fecha_obj.strftime("%Y-%m-%d")

        try:
            df_p_all = cargar_datos_env("ingreso_plaqueros")
            if not df_p_all.empty and "fecha" in df_p_all.columns:
                df_p_filtrado = df_p_all[df_p_all["fecha"].astype(str).str.strip() == filtro_fecha_str]
                
                if filtro_lote_sel != "TODOS" and "lote" in df_p_filtrado.columns:
                    df_p_filtrado = df_p_filtrado[df_p_filtrado["lote"].astype(str).str.strip() == filtro_lote_sel]
                
                if not df_p_filtrado.empty:
                    st.dataframe(df_p_filtrado, use_container_width=True)
                    
                    total_bandejas_dia = pd.to_numeric(df_p_filtrado["bandejas"], errors="coerce").sum()
                    total_kg_dia = pd.to_numeric(df_p_filtrado["total_kg"], errors="coerce").sum()
                    st.success(f"📦 **Total Filtrado:** `{int(total_bandejas_dia)} bandejas` | ⚖️ **Total Kilos:** `{total_kg_dia} kg`")
                else:
                    st.info(f"ℹ️ No hay registros para la fecha {filtro_fecha_str} con el lote '{filtro_lote_sel}'.")
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
