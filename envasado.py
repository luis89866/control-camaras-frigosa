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

def obtener_lote_por_fecha(fecha_dt):
    """Busca en la pestaña LOTE cruzando estrictamente el día, mes y año"""
    fecha_iso = fecha_dt.strftime("%Y-%m-%d")
    fecha_latina = fecha_dt.strftime("%d/%m/%Y")
    lote_encontrado = f"LT-{fecha_iso.replace('-', '')}"

    for nombre_pestana in ["LOTE", "Lote", "lote"]:
        try:
            ws = get_env_sheet(nombre_pestana)
            filas = ws.get_all_values()
            for fila in filas:
                if len(fila) >= 2:
                    f_Hoja = str(fila[0]).strip()
                    l_Hoja = str(fila[1]).strip()
                    if f_Hoja == "" or f_Hoja.upper() == "FECHA":
                        continue
                    
                    if f_Hoja == fecha_latina or f_Hoja == fecha_iso:
                        lote_encontrado = l_Hoja
                        break
                    
                    try:
                        dt_hoja = pd.to_datetime(f_Hoja, dayfirst=True).strftime("%Y-%m-%d")
                        if dt_hoja == fecha_iso:
                            lote_encontrado = l_Hoja
                            break
                    except:
                        pass
            if lote_encontrado != f"LT-{fecha_iso.replace('-', '')}":
                break
        except:
            continue
    return lote_encontrado

def obtener_mp_por_fecha(fecha_str):
    """Obtiene los kilos de Materia Prima (MP) registrados para una fecha específica"""
    try:
        df_mp = cargar_datos_env("MP")
        if not df_mp.empty and len(df_mp.columns) >= 2:
            for _, row in df_mp.iterrows():
                f_mp = str(row.iloc[0]).strip()
                k_mp = str(row.iloc[1]).strip()
                try:
                    if pd.to_datetime(f_mp).strftime("%Y-%m-%d") == fecha_str:
                        return float(k_mp) if k_mp.replace('.', '', 1).isdigit() else 0.0
                except:
                    if f_mp == fecha_str:
                        return float(k_mp) if k_mp.replace('.', '', 1).isdigit() else 0.0
    except:
        pass
    return 0.0

def actualizar_rendimientos_para_fecha(fecha_objetivo_str):
    """Recalcula y actualiza automáticamente los rendimientos en Google Sheets para una fecha específica"""
    try:
        ws_env = get_env_sheet("ingreso_plaqueros")
        all_vals = ws_env.get_all_values()
        if len(all_vals) > 1:
            headers = [str(h).strip().lower() for h in all_vals[0]]
            
            idx_fecha = headers.index("fecha") if "fecha" in headers else 1
            idx_kg = headers.index("total_kg") if "total_kg" in headers else 9
            col_rend_idx = 15 # Columna O (rendimientos)
            
            mp_dia = obtener_mp_por_fecha(fecha_objetivo_str)
            
            for f_idx in range(1, len(all_vals)):
                fila = all_vals[f_idx]
                if len(fila) >= max(idx_fecha, idx_kg) + 1:
                    f_reg = str(fila[idx_fecha]).strip()
                    
                    if f_reg == fecha_objetivo_str:
                        try:
                            kg_reg = float(fila[idx_kg])
                        except:
                            kg_reg = 0.0
                        
                        if mp_dia > 0:
                            rend_val = f"{(kg_reg / mp_dia * 100):.2f}%"
                        else:
                            rend_val = "0.00%"
                        
                        try:
                            ws_env.update_cell(f_idx + 1, col_rend_idx, rend_val)
                        except:
                            pass
    except:
        pass

def obtener_hora_peru():
    return datetime.utcnow() - timedelta(hours=5)

def render_module(user, get_sheet, cargar_datos):
    nombre_sesion = user.get("nombre_completo", user.get("usuario"))
    rol = user.get("rol", "Visualizador")

    st.subheader("📦 Módulo de Envasado y Control de Plaqueros / Túneles / IQF")
    st.markdown(f"Operador / Supervisor: **{nombre_sesion}** | Rol: `{rol}`")
    
    col_r1, col_r2 = st.columns([3, 1])
    with col_r2:
        if st.button("🔄 Refrescar Envasado", use_container_width=True):
            st.cache_data.clear()
            st.success("¡Datos actualizados!")
            st.rerun()

    st.markdown("---")

    lista_plaqueros = [f"P{i}" for i in range(1, 19)] + ["TÚNEL 1", "TÚNEL 2", "TÚNEL 3", "IQF 1", "IQF 2"]
    
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
    # ITEM 1: INGRESOS DE DATOS
    # =========================================================================
    with st.expander("📥 1. Ingresos de Datos (Plaqueros, Túneles e IQF)", expanded=True):
        st.caption("Registre la carga del equipo. El lote se busca y asigna automáticamente desde la pestaña LOTE.")
        
        col_d1, col_d2 = st.columns(2)
        with col_d1:
            tipo_equipo = st.selectbox("Seleccione Tipo de Equipo:", ["Plaquero (P1 - P18)", "Túnel (1, 2 y 3)", "Equipo IQF (1 y 2)"], key="tipo_eq_sel_v57")
            if tipo_equipo == "Plaquero (P1 - P18)":
                plaquero_sel = st.selectbox("Nº de Plaquero:", [f"P{i}" for i in range(1, 19)], key="sel_plaquero_reg_v57")
            elif tipo_equipo == "Túnel (1, 2 y 3)":
                plaquero_sel = st.selectbox("Nº de Túnel:", ["TÚNEL 1", "TÚNEL 2", "TÚNEL 3"], key="sel_tunel_reg_v57")
            else:
                plaquero_sel = st.selectbox("Nº de IQF:", ["IQF 1", "IQF 2"], key="sel_iqf_reg_v57")
                
            fecha_ingreso_obj = st.date_input("Fecha de Producción:", obtener_hora_peru(), key="f_prod_reg_v57")
            fecha_ingreso_str = fecha_ingreso_obj.strftime("%Y-%m-%d")
            
            lote_automatico = obtener_lote_por_fecha(fecha_ingreso_obj)
            st.info(f"📦 **Lote asignado automáticamente:** `{lote_automatico}`")

            hora_inicio_str = st.text_input("Hora de Inicio (Ej: 08:00):", obtener_hora_peru().strftime("%H:%M"), key="h_inicio_prod_v57")
            
        with col_d2:
            st.markdown("##### Tiempo de Congelación (Ej: 2:45 o 0:02 min):")
            tiempo_input_str = st.text_input("Tiempo de Congelación:", "2:45", key="t_cong_libre_v57")
            
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
            presentacion_sel = st.selectbox("Presentación / Producto:", lista_presentaciones, key="sel_presentacion_v57")
        with col_p2:
            calibre_sel = st.selectbox("Calibre:", lista_calibres, key="sel_calibre_v57")
        with col_p3:
            bandejas_cant = st.number_input("Cantidad de Bandejas:", min_value=1, step=1, value=50, key="num_bandejas_v57")

        if st.button("🚀 Registrar / Agregar Presentación", use_container_width=True, key="btn_enviar_produccion_v57"):
            try:
                ws_env = get_env_sheet("ingreso_plaqueros")
                existing_data = ws_env.get_all_values()
                
                num_bachada = 1
                producto_duplicado = False
                conflicto_hora = False
                hora_activa_encontrada = ""
                
                if len(existing_data) > 1:
                    bachadas_registradas_hoy = set()
                    en_proceso_activo = False
                    for fila in existing_data[1:]:
                        if len(fila) >= 11:
                            f_reg = str(fila[1]).strip()
                            eq_reg = str(fila[2]).strip().upper()
                            h_ini_reg = str(fila[3]).strip()
                            pres_reg = str(fila[6]).strip().upper()
                            cal_reg = str(fila[7]).strip().upper()
                            estado_reg = str(fila[10]).strip()
                            bachada_val = str(fila[11]).strip() if len(fila) > 11 else "Bachada 1"
                            
                            if f_reg == fecha_ingreso_str and eq_reg == plaquero_sel.strip().upper():
                                if bachada_val:
                                    bachadas_registradas_hoy.add(bachada_val)
                                if estado_reg == "En Proceso":
                                    en_proceso_activo = True
                                    hora_activa_encontrada = h_ini_reg
                                    num_bachada = int(bachada_val.replace("Bachada", "").strip()) if "Bachada" in bachada_val else len(bachadas_registradas_hoy)
                                    
                                    if h_ini_reg != hora_inicio_str.strip():
                                        conflicto_hora = True

                                    if pres_reg == presentacion_sel.strip().upper() and cal_reg == calibre_sel.strip().upper():
                                        producto_duplicado = True

                    if not en_proceso_activo and len(bachadas_registradas_hoy) > 0:
                        num_bachada = len(bachadas_registradas_hoy) + 1

                if conflicto_hora:
                    st.error(f"❌ **Acción rechazada:** El equipo **{plaquero_sel}** ya se encuentra **En Proceso** con hora de inicio **{hora_activa_encontrada}**. Para agregar más presentaciones a este ciclo, debes usar la misma hora de inicio (`{hora_activa_encontrada}`). Si es un nuevo ciclo, debes liberar primero el equipo.")
                elif producto_duplicado:
                    st.error(f"❌ **Acción rechazada:** El producto **{presentacion_sel}** con calibre **{calibre_sel}** ya se encuentra activo en **{plaquero_sel}**.")
                else:
                    id_prod = f"PROD-{datetime.now().strftime('%y%m%d%H%M%S')}"
                    total_kg = bandejas_cant * 10.0
                    bachada_str = f"Bachada {num_bachada}"
                    codigo_pres = dic_presentaciones.get(presentacion_sel, "")
                    
                    mp_dia = obtener_mp_por_fecha(fecha_ingreso_str)
                    rend_val = f"{(total_kg / mp_dia * 100):.2f}%" if mp_dia > 0 else "0.00%"

                    ws_env.append_row([
                        id_prod, fecha_ingreso_str, plaquero_sel, hora_inicio_str, tiempo_formato_str, 
                        hora_salida_estimada, presentacion_sel, calibre_sel, str(bandejas_cant), 
                        str(total_kg), "En Proceso", bachada_str, codigo_pres, lote_automatico, rend_val
                    ])
                    st.success(f"✅ Se registró **{presentacion_sel}** ({bandejas_cant} ban.) en **{plaquero_sel}** bajo `[{bachada_str}]` (Lote: {lote_automatico})!")
                    st.rerun()
            except Exception as e:
                st.error(f"Error al guardar: {e}")

    # =========================================================================
    # ITEM 2: EQUIPOS ENCENDIDOS
    # =========================================================================
    with st.expander("⚡ 2. Equipos Encendidos (Plaqueros, Túneles e IQF)", expanded=False):
        tiempo_peru = obtener_hora_peru()
        col_c1, col_c2 = st.columns([3, 1])
        with col_c1:
            st.caption(f"🕒 Hora oficial de planta (Perú UTC-5): **{tiempo_peru.strftime('%H:%M:%S')}**")
        with col_c2:
            if st.button("🔄 Actualizar Cronograma", key="btn_actualizar_cronograma_v43", use_container_width=True):
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
                        if h_sal and h_ini:
                            partes_ini = h_ini.strip().split(":")
                            partes_sal = h_sal.strip().split(":")
                            minutos_inicio = int(partes_ini[0]) * 60 + int(partes_ini[1])
                            minutos_salida = int(partes_sal[0]) * 60 + int(partes_sal[1])
                            
                            if minutos_salida < minutos_inicio:
                                minutos_salida += 24 * 60
                            
                            min_act_calc = minutos_actuales_dia
                            if min_act_calc < minutos_inicio:
                                min_act_calc += 24 * 60
                                
                            if min_act_calc >= minutos_salida:
                                minutos_retraso = min_act_calc - minutos_salida
                                h_ret_h = minutos_retraso // 60
                                h_ret_m = minutos_retraso % 60
                                tiempo_ret_str = f"{h_ret_h}h {h_ret_m:02d}m" if h_ret_h > 0 else f"{h_ret_m} min"
                                situacion_txt = f"🔴 ¡CICLO CUMPLIDO!<br><span style='color: #d9534f; font-size: 13px;'>⏱️ Retraso sin bajar: <b>{tiempo_ret_str}</b></span>"
                    except:
                        pass
                    
                    tabla_consolidada.append({
                        "EQUIPO": eq,
                        "HORA INICIO": h_ini,
                        "HORA SALIDA": h_sal,
                        "PRODUCTO": lista_prods,
                        "SITUACION": situacion_txt,
                        "ids": r_dat["ids"]
                    })
                else:
                    tabla_consolidada.append({
                        "EQUIPO": eq,
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
                    st.markdown(f"**{row['EQUIPO']}**")
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
                        if st.button("🔓 Liberar", key=f"lib_fix_sel_v27_{row['EQUIPO']}_{idx}"):
                            try:
                                ws_env = get_env_sheet("ingreso_plaqueros")
                                all_vals = ws_env.get_all_values()
                                
                                ids_a_liberar = set(row['ids'])
                                for f_idx, f_vals in enumerate(all_vals):
                                    if len(f_vals) > 0 and f_vals[0].strip() in ids_a_liberar:
                                        ws_env.update_cell(f_idx + 1, 11, "Finalizado")
                                        
                                fecha_reg_prod = all_vals[f_idx][1] if len(all_vals[f_idx]) > 1 else ""
                                if fecha_reg_prod:
                                    actualizar_rendimientos_para_fecha(fecha_reg_prod)
                                
                                st.success(f"✅ ¡Equipo **{row['EQUIPO']}** liberado!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error al liberar: {e}")
                    else:
                        st.markdown("<span style='color: gray; font-size: 13px;'>Libre</span>", unsafe_allow_html=True)
                st.markdown("<hr style='margin: 6px 0px; border-color: #eee;'>", unsafe_allow_html=True)

        except Exception as e:
            st.warning(f"Error cargando tabla: {e}")

    # =========================================================================
    # ITEM 3: MODIFICACIÓN O ELIMINACIÓN DE REGISTROS
    # =========================================================================
    with st.expander("✏️ 3. Modificación o Eliminación de Registros", expanded=False):
        st.caption("Seleccione una fecha para filtrar los registros y editar o eliminar el que necesite.")
        
        try:
            df_all_mod = cargar_datos_env("ingreso_plaqueros")
            if not df_all_mod.empty and "fecha" in df_all_mod.columns:
                filtro_fecha_mod_obj = st.date_input("📅 Seleccionar Día a Gestionar:", obtener_hora_peru(), key="filtro_fecha_mod_input_v17")
                filtro_fecha_mod_str = filtro_fecha_mod_obj.strftime("%Y-%m-%d")
                
                df_mod_filtrado = df_all_mod[df_all_mod["fecha"].astype(str).str.strip() == filtro_fecha_mod_str]
                
                if not df_mod_filtrado.empty:
                    st.dataframe(df_mod_filtrado[["id_produccion", "equipo", "hora_inicio", "presentacion", "calibre", "bandejas", "estado", "bachadas"]], use_container_width=True)
                    
                    id_a_editar = st.selectbox("Seleccione el ID del registro a editar/eliminar:", df_mod_filtrado["id_produccion"].tolist(), key="sel_id_mod_v37")
                    
                    fila_act = df_mod_filtrado[df_mod_filtrado["id_produccion"] == id_a_editar].iloc[0]
                    
                    pres_actual = str(fila_act.get('presentacion', '')).strip()
                    cal_actual = str(fila_act.get('calibre', '')).strip()
                    band_actual = int(fila_act['bandejas']) if str(fila_act.get('bandejas', '50')).isdigit() else 50
                    
                    idx_pres = lista_presentaciones.index(pres_actual) if pres_actual in lista_presentaciones else 0
                    idx_cal = lista_calibres.index(cal_actual) if cal_actual in lista_calibres else 0
                    
                    st.markdown(f"**Registro seleccionado:** `{id_a_editar}` (Fecha: {fila_act.get('fecha', '')} | Equipo: {fila_act.get('equipo', '')} - {fila_act.get('bachadas', '')})")
                    
                    col_m1, col_m2, col_m3 = st.columns(3)
                    with col_m1:
                        nueva_pres = st.selectbox("Presentación:", lista_presentaciones, index=idx_pres, key=f"mod_pres_{id_a_editar}")
                    with col_m2:
                        nuevo_cal = st.selectbox("Calibre:", lista_calibres, index=idx_cal, key=f"mod_cal_{id_a_editar}")
                    with col_m3:
                        nuevas_band = st.number_input("Cantidad de Bandejas:", min_value=1, step=1, value=band_actual, key=f"mod_band_{id_a_editar}")

                    col_btn1, col_btn2 = st.columns(2)
                    with col_btn1:
                        if st.button("💾 Guardar Cambios (Modificar)", type="primary", key="btn_guardar_mod_v37", use_container_width=True):
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
                                
                                mp_dia = obtener_mp_por_fecha(filtro_fecha_mod_str)
                                nuevo_rend = f"{(nuevo_total_kg / mp_dia * 100):.2f}%" if mp_dia > 0 else "0.00%"
                                
                                ws_env.update_cell(fila_tabla, 7, nueva_pres)
                                ws_env.update_cell(fila_tabla, 8, nuevo_cal)
                                ws_env.update_cell(fila_tabla, 9, str(nuevas_band))
                                ws_env.update_cell(fila_tabla, 10, str(nuevo_total_kg))
                                ws_env.update_cell(fila_tabla, 13, nuevo_codigo)
                                ws_env.update_cell(fila_tabla, 15, nuevo_rend)
                                
                                actualizar_rendimientos_para_fecha(filtro_fecha_mod_str)
                                
                                st.success(f"✅ ¡Registro **{id_a_editar}** actualizado correctamente!")
                                st.rerun()
                            else:
                                st.error("No se encontró la fila en Google Sheets.")
                    
                    with col_btn2:
                        if st.button("🗑️ Eliminar Registro", type="secondary", key="btn_eliminar_reg_v37", use_container_width=True):
                            ws_env = get_env_sheet("ingreso_plaqueros")
                            all_vals = ws_env.get_all_values()
                            fila_tabla = -1
                            for f_idx, f_vals in enumerate(all_vals):
                                if len(f_vals) > 0 and f_vals[0].strip() == id_a_editar.strip():
                                    fila_tabla = f_idx + 1
                                    break
                            
                            if fila_tabla != -1:
                                ws_env.delete_rows(fila_tabla)
                                actualizar_rendimientos_para_fecha(filtro_fecha_mod_str)
                                st.success(f"🗑️ ¡Registro **{id_a_editar}** eliminado exitosamente!")
                                st.rerun()
                            else:
                                st.error("No se encontró la fila para eliminar.")
                else:
                    st.info(f"ℹ️ No hay registros para la fecha {filtro_fecha_mod_str}.")
            else:
                st.info("ℹ️ No hay datos en la base de envasado.")
        except Exception as e:
            st.warning(f"Error en panel de gestión: {e}")

    # =========================================================================
    # ITEM 4: RESUMEN DE PRODUCCION Y GESTIÓN DE MATERIA PRIMA (MP)
    # =========================================================================
    with st.expander("📊 4. Resumen de Producción y Materia Prima (MP)", expanded=False):
        st.markdown("##### 🐟 Gestión de Materia Prima (Kilos por Fecha)")
        
        col_mp1, col_mp2, col_mp3 = st.columns(3)
        with col_mp1:
            fecha_mp_obj = st.date_input("Fecha MP:", obtener_hora_peru(), key="fecha_mp_input_v11")
            fecha_mp_str = fecha_mp_obj.strftime("%Y-%m-%d")
            
            mp_actual_guardada = obtener_mp_por_fecha(fecha_mp_str)
            
        with col_mp2:
            kilos_mp_input = st.number_input("Kilos de Materia Prima (MP):", min_value=0.0, step=100.0, value=mp_actual_guardada, key=f"kilos_mp_val_{fecha_mp_str}")
        with col_mp3:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("💾 Guardar / Actualizar MP", type="primary", use_container_width=True):
                try:
                    ws_mp = get_env_sheet("MP")
                    mp_rows = ws_mp.get_all_values()
                    
                    encontrado = False
                    fila_mp_idx = -1
                    
                    for idx, fila in enumerate(mp_rows):
                        if len(fila) > 0:
                            f_Hoja = str(fila[0]).strip()
                            try:
                                dt_h = pd.to_datetime(f_Hoja).strftime("%Y-%m-%d")
                                if dt_h == fecha_mp_str:
                                    encontrado = True
                                    fila_mp_idx = idx + 1
                                    break
                            except:
                                if f_Hoja == fecha_mp_str:
                                    encontrado = True
                                    fila_mp_idx = idx + 1
                                    break
                    
                    if encontrado and fila_mp_idx != -1:
                        ws_mp.update_cell(fila_mp_idx, 2, str(kilos_mp_input))
                        st.success(f"✅ Materia Prima actualizada para el {fecha_mp_str}: `{kilos_mp_input} kg`")
                    else:
                        ws_mp.append_row([fecha_mp_str, str(kilos_mp_input)])
                        st.success(f"✅ Materia Prima registrada para el {fecha_mp_str}: `{kilos_mp_input} kg`")
                    
                    actualizar_rendimientos_para_fecha(fecha_mp_str)
                    st.rerun()
                except Exception as e:
                    st.error(f"Error al guardar MP: {e}")

        st.markdown("---")
        st.markdown("##### 📈 Filtrar Historial de Producción y Rendimiento:")
        
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            filtro_fecha_obj = st.date_input("Filtrar por Fecha:", obtener_hora_peru(), key="filtro_fecha_hist_v52")
        with col_f2:
            try:
                df_all_lotes = cargar_datos_env("ingreso_plaqueros")
                lotes_disponibles = ["TODOS"]
                if not df_all_lotes.empty and "lote" in df_all_lotes.columns:
                    lotes_unicos = df_all_lotes["lote"].dropna().astype(str).str.strip().unique().tolist()
                    lotes_disponibles += [l for l in lotes_unicos if l != ""]
            except:
                lotes_disponibles = ["TODOS"]
                
            filtro_lote_sel = st.selectbox("Filtrar por Lote:", lotes_disponibles, key="filtro_lote_sel_v52")

        filtro_fecha_str = filtro_fecha_obj.strftime("%Y-%m-%d")

        try:
            kilos_mp_dia = obtener_mp_por_fecha(filtro_fecha_str)

            df_p_all = cargar_datos_env("ingreso_plaqueros")
            if not df_p_all.empty and "fecha" in df_p_all.columns:
                df_p_filtrado = df_p_all[df_p_all["fecha"].astype(str).str.strip() == filtro_fecha_str]
                
                if filtro_lote_sel != "TODOS" and "lote" in df_p_filtrado.columns:
                    df_p_filtrado = df_p_filtrado[df_p_filtrado["lote"].astype(str).str.strip() == filtro_lote_sel]
                
                if not df_p_filtrado.empty:
                    st.dataframe(df_p_filtrado, use_container_width=True)
                    
                    total_bandejas_dia = pd.to_numeric(df_p_filtrado["bandejas"], errors="coerce").sum()
                    total_kg_dia = pd.to_numeric(df_p_filtrado["total_kg"], errors="coerce").sum()
                    
                    rendimiento_pct = (total_kg_dia / kilos_mp_dia * 100) if kilos_mp_dia > 0 else 0.0
                    
                    st.markdown(f"""
                    * 📦 **Total Bandejas:** `{int(total_bandejas_dia)}`
                    * ⚖️ **Total Kilos Envasados:** `{total_kg_dia:,.2f} kg`
                    * 🐟 **Materia Prima (MP) Registrada:** `{kilos_mp_dia:,.2f} kg`
                    * 📊 **Rendimiento Global:** `{rendimiento_pct:.2f}%`
                    """)
                else:
                    st.info(f"ℹ️ No hay registros de envasado para la fecha {filtro_fecha_str} con el lote '{filtro_lote_sel}'. (MP registrada: {kilos_mp_dia:,.2f} kg)")
            else:
                st.info("ℹ️ Aún no hay datos guardados.")
        except Exception as e:
            st.warning(f"Error en resumen y rendimientos: {e}")

    # =========================================================================
    # ITEM 5: HISTOGRAMA DE PLAQUEROS DEL DÍA
    # =========================================================================
    with st.expander("🕒 5. Histograma de Plaqueros del Día", expanded=False):
        st.caption("Matriz horaria de ocupación de los equipos (Bachadas extendidas y Tiempos Muertos).")
        
        col_h1, col_h2 = st.columns(2)
        with col_h1:
            fecha_histo_obj = st.date_input("📅 Seleccionar Día de Histograma:", obtener_hora_peru(), key="fecha_histo_input_v8")
        fecha_histo_str = fecha_histo_obj.strftime("%Y-%m-%d")

        try:
            df_histo_all = cargar_datos_env("ingreso_plaqueros")
            
            horas_matriz = [f"{h:02d}:00" for h in range(24)]
            equipos_columnas = [f"P{i}" for i in range(1, 19)] + ["TÚNEL 1", "TÚNEL 2", "TÚNEL 3", "IQF 1", "IQF 2"]
            
            matriz_datos = {eq: ["⏰ Tiempo Muerto" for _ in range(24)] for eq in equipos_columnas}
            df_matriz = pd.DataFrame(matriz_datos, index=horas_matriz)

            if not df_histo_all.empty and "fecha" in df_histo_all.columns:
                df_h_dia = df_histo_all[df_histo_all["fecha"].astype(str).str.strip() == fecha_histo_str]
                
                for _, r in df_h_dia.iterrows():
                    eq = str(r.get("equipo", "")).strip().upper()
                    h_ini = str(r.get("hora_inicio", "")).strip()
                    h_sal = str(r.get("hora_salida", "")).strip()
                    bachada = str(r.get("bachadas", "B1")).strip()
                    pres = str(r.get("presentacion", "")).strip()
                    
                    if eq in df_matriz.columns and h_ini and h_sal:
                        try:
                            p_ini = h_ini.strip().split(":")
                            p_sal = h_sal.strip().split(":")
                            min_ini = int(p_ini[0]) * 60 + int(p_ini[1])
                            min_sal = int(p_sal[0]) * 60 + int(p_sal[1])
                            
                            if min_sal < min_ini:
                                min_sal += 24 * 60
                                
                            for m in range(min_ini, min_sal + 1, 60):
                                h_idx = (m // 60) % 24
                                h_key = f"{h_idx:02d}:00"
                                if h_key in df_matriz.index:
                                    val_actual = df_matriz.loc[h_key, eq]
                                    texto_bachada = f"{bachada}: {pres}"
                                    if "Tiempo Muerto" in val_actual:
                                        df_matriz.loc[h_key, eq] = f"🟢 {texto_bachada}"
                                    else:
                                        if texto_bachada not in val_actual:
                                            df_matriz.loc[h_key, eq] += f"<br>🟢 {texto_bachada}"
                        except:
                            pass

            st.markdown(f"##### Historial de Operación para el {fecha_histo_str}")
            st.dataframe(df_matriz, use_container_width=True)
        except Exception as e:
            st.warning(f"Error cargando histograma: {e}")

    # =========================================================================
    # ITEM 6: RENDIMIENTO POR PRESENTACIÓN Y CALIBRE
    # =========================================================================
    with st.expander("📊 6. Rendimiento por Presentación y Calibre", expanded=False):
        st.markdown("##### Resumen de Producción por Producto y Calibre")
        
        fecha_def_r6 = obtener_hora_peru()
        try:
            df_check_r6 = cargar_datos_env("ingreso_plaqueros")
            if not df_check_r6.empty and "fecha" in df_check_r6.columns:
                fechas_unicas = sorted(df_check_r6["fecha"].dropna().astype(str).str.strip().unique().tolist(), reverse=True)
                if fechas_unicas:
                    fecha_def_r6 = datetime.strptime(fechas_unicas[0], "%Y-%m-%d")
        except:
            pass

        col_r6_1, col_r6_2 = st.columns(2)
        with col_r6_1:
            fecha_r6_obj = st.date_input("📅 Seleccionar Fecha:", fecha_def_r6, key="fecha_r6_input_v9")
        fecha_r6_str = fecha_r6_obj.strftime("%Y-%m-%d")
        
        try:
            df_env_r6 = cargar_datos_env("ingreso_plaqueros")
            mp_r6 = obtener_mp_por_fecha(fecha_r6_str)
            
            if not df_env_r6.empty and "fecha" in df_env_r6.columns:
                df_r6_dia = df_env_r6[df_env_r6["fecha"].astype(str).str.strip() == fecha_r6_str].copy()
                
                if not df_r6_dia.empty:
                    df_r6_dia["total_kg_num"] = pd.to_numeric(df_r6_dia["total_kg"], errors="coerce").fillna(0.0)
                    df_r6_dia["bandejas_num"] = pd.to_numeric(df_r6_dia["bandejas"], errors="coerce").fillna(0)
                    
                    df_agrupado = df_r6_dia.groupby(["presentacion", "calibre"]).agg(
                        total_bandejas=("bandejas_num", "sum"),
                        total_kilos=("total_kg_num", "sum")
                    ).reset_index()
                    
                    if mp_r6 > 0:
                        df_agrupado["rendimiento_pct"] = (df_agrupado["total_kilos"] / mp_r6) * 100
                    else:
                        df_agrupado["rendimiento_pct"] = 0.0
                        
                    df_tabla_final = pd.DataFrame({
                        "PRODUCTO / PRESENTACIÓN": df_agrupado["presentacion"],
                        "CALIBRE": df_agrupado["calibre"],
                        "TOTAL BANDEJAS": df_agrupado["total_bandejas"].astype(int),
                        "TOTAL KILOS": df_agrupado["total_kilos"].apply(lambda x: f"{x:,.2f} kg"),
                        "RENDIMIENTO (%)": df_agrupado["rendimiento_pct"].apply(lambda x: f"{x:.2f}%")
                    })
                    
                    st.info(f"🐟 **Materia Prima Total del Día ({fecha_r6_str}):** `{mp_r6:,.2f} kg`")
                    st.dataframe(df_tabla_final, use_container_width=True, hide_index=True)
                    
                    suma_kilos_totales = df_agrupado["total_kilos"].sum()
                    suma_rend_totales = df_agrupado["rendimiento_pct"].sum()
                    st.success(f"📌 **Suma del Día:** `{suma_kilos_totales:,.2f} kg` (Rendimiento Acumulado: `{suma_rend_totales:.2f}%`)")
                else:
                    st.info(f"ℹ️ No hay registros de envasado para la fecha {fecha_r6_str}.")
            else:
                st.info("ℹ️ Aún no hay datos guardados en la base de envasado.")
        except Exception as e:
            st.warning(f"Error generando reporte por presentación: {e}")

    # =========================================================================
    # ITEM 7: RESUMEN POR SUBFAMILIA (PRESENTACIÓN)
    # =========================================================================
    with st.expander("📊 7. Resumen por Subfamilia (Presentación)", expanded=False):
        st.markdown("##### Resumen General por Producto (Sin desglosar Calibre)")
        
        fecha_def_r7 = obtener_hora_peru()
        try:
            df_check_r7 = cargar_datos_env("ingreso_plaqueros")
            if not df_check_r7.empty and "fecha" in df_check_r7.columns:
                fechas_unicas_7 = sorted(df_check_r7["fecha"].dropna().astype(str).str.strip().unique().tolist(), reverse=True)
                if fechas_unicas_7:
                    fecha_def_r7 = datetime.strptime(fechas_unicas_7[0], "%Y-%m-%d")
        except:
            pass

        col_r7_1, col_r7_2 = st.columns(2)
        with col_r7_1:
            fecha_r7_obj = st.date_input("📅 Seleccionar Fecha:", fecha_def_r7, key="fecha_r7_input_v8")
        fecha_r7_str = fecha_r7_obj.strftime("%Y-%m-%d")
        
        try:
            df_env_r7 = cargar_datos_env("ingreso_plaqueros")
            mp_r7 = obtener_mp_por_fecha(fecha_r7_str)
            
            if not df_env_r7.empty and "fecha" in df_env_r7.columns:
                df_r7_dia = df_env_r7[df_env_r7["fecha"].astype(str).str.strip() == fecha_r7_str].copy()
                
                if not df_r7_dia.empty:
                    df_r7_dia["total_kg_num"] = pd.to_numeric(df_r7_dia["total_kg"], errors="coerce").fillna(0.0)
                    df_r7_dia["bandejas_num"] = pd.to_numeric(df_r7_dia["bandejas"], errors="coerce").fillna(0)
                    
                    df_agrupado_r7 = df_r7_dia.groupby("presentacion").agg(
                        total_bandejas=("bandejas_num", "sum"),
                        total_kilos=("total_kg_num", "sum")
                    ).reset_index()
                    
                    if mp_r7 > 0:
                        df_agrupado_r7["rendimiento_pct"] = (df_agrupado_r7["total_kilos"] / mp_r7) * 100
                    else:
                        df_agrupado_r7["rendimiento_pct"] = 0.0
                        
                    df_tabla_r7 = pd.DataFrame({
                        "PRODUCTO / PRESENTACIÓN": df_agrupado_r7["presentacion"],
                        "TOTAL BANDEJAS": df_agrupado_r7["total_bandejas"].astype(int),
                        "TOTAL KILOS": df_agrupado_r7["total_kilos"].apply(lambda x: f"{x:,.2f} kg"),
                        "RENDIMIENTO (%)": df_agrupado_r7["rendimiento_pct"].apply(lambda x: f"{x:.2f}%")
                    })
                    
                    st.info(f"🐟 **Materia Prima Total del Día ({fecha_r7_str}):** `{mp_r7:,.2f} kg`")
                    st.dataframe(df_tabla_r7, use_container_width=True, hide_index=True)
                    
                    suma_kilos_r7 = df_agrupado_r7["total_kilos"].sum()
                    suma_rend_r7 = df_agrupado_r7["rendimiento_pct"].sum()
                    st.success(f"📌 **Suma Total del Día:** `{suma_kilos_r7:,.2f} kg` (Rendimiento Total: `{suma_rend_r7:.2f}%`)")
                else:
                    st.info(f"ℹ️ No hay registros de envasado para la fecha {fecha_r7_str}.")
            else:
                st.info("ℹ️ Aún no hay datos guardados en la base de envasado.")
        except Exception as e:
            st.warning(f"Error generando resumen por subfamilia: {e}")

    # =========================================================================
    # ITEM 8: CONTROL Y REGISTRO DE TIEMPOS MUERTOS / PARADAS
    # =========================================================================
    with st.expander("⏱️ 8. Control y Registro de Tiempos Muertos / Paradas", expanded=False):
        st.markdown("##### ⚠️ Registro de Incidencias y Paradas de Equipos")
        
        col_par1, col_par2 = st.columns(2)
        with col_par1:
            fecha_parada_obj = st.date_input("Fecha de Parada:", obtener_hora_peru(), key="fecha_parada_input_v3")
            fecha_parada_str = fecha_parada_obj.strftime("%Y-%m-%d")
            
            tipo_eq_par = st.selectbox("Equipo Afectado:", ["Plaquero (P1 - P18)", "Túnel (1, 2 y 3)", "Equipo IQF (1 y 2)"], key="tipo_eq_par_v3")
            if tipo_eq_par == "Plaquero (P1 - P18)":
                eq_par_sel = st.selectbox("Nº de Plaquero:", [f"P{i}" for i in range(1, 19)], key="eq_par_plaquero_v3")
            elif tipo_eq_par == "Túnel (1, 2 y 3)":
                eq_par_sel = st.selectbox("Nº de Túnel:", ["TÚNEL 1", "TÚNEL 2", "TÚNEL 3"], key="eq_par_tunel_v3")
            else:
                eq_par_sel = st.selectbox("Nº de IQF:", ["IQF 1", "IQF 2"], key="eq_par_iqf_v3")

        with col_par2:
            motivo_parada = st.selectbox("Motivo de Parada / Demora:", [
                "Mantenimiento Correctivo / Falla Mecánica",
                "Demora en Descarga / Sin Bandejas",
                "Falta de Materia Prima",
                "Limpieza / Sanitización",
                "Falta de Personal / Operativa",
                "Otro"
            ], key="motivo_parada_sel_v3")
            
            minutos_muertos = st.number_input("Tiempo Muerto (en Minutos):", min_value=1, step=10, value=30, key="min_muertos_input_v3")
            observaciones_parada = st.text_input("Observaciones / Comentarios:", "", key="obs_parada_input_v3")

        if st.button("💾 Registrar Parada / Tiempo Muerto", type="primary", use_container_width=True, key="btn_guardar_parada_v3"):
            if motivo_parada == "Otro" and not observaciones_parada.strip():
                st.error("⚠️ **Atención:** Si selecciona 'Otro', el campo de **Observaciones / Comentarios** es obligatorio.")
            else:
                try:
                    ws_paradas = get_env_sheet("PARADAS")
                    id_par = f"PAR-{datetime.now().strftime('%y%m%d%H%M%S')}"
                    
                    ws_paradas.append_row([
                        id_par, fecha_parada_str, eq_par_sel, motivo_parada, str(minutos_muertos), observaciones_parada
                    ])
                    st.success(f"✅ ¡Parada registrada para **{eq_par_sel}** ({minutos_muertos} min por `{motivo_parada}`)!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error al registrar parada: {e}")

        st.markdown("---")
        st.markdown("##### 📋 Historial de Paradas Registradas:")
        try:
            df_paradas = cargar_datos_env("PARADAS")
            if not df_paradas.empty:
                st.dataframe(df_paradas, use_container_width=True)
            else:
                st.info("ℹ️ No hay registros de paradas o tiempos muertos guardados.")
        except Exception as e:
            st.warning(f"Error cargando historial de paradas: {e}")
