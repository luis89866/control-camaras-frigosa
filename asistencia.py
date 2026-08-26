import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

def calcular_horas_extras(hora_entrada_dt, hora_salida_dt, modo_turno, es_domingo, es_sabado):
    minutos_salida = hora_salida_dt.hour * 60 + hora_salida_dt.minute
    minutos_entrada = hora_entrada_dt.hour * 60 + hora_entrada_dt.minute
    
    if minutos_salida <= minutos_entrada:
        minutos_totales = (1440 - minutos_entrada) + minutos_salida
    else:
        minutos_totales = minutos_salida - minutos_entrada
    horas_totales_trabajadas = minutos_totales / 60.0

    horas_pagadas = 0.0
    horas_bolsa_general = 0.0
    horas_bolsa_dominical = 0.0
    horas_extras_totales = 0.0

    if es_domingo:
        if modo_turno == "Con Producción":
            if horas_totales_trabajadas >= 12.0:
                horas_pagadas = 1.0
                horas_bolsa_general = horas_totales_trabajadas - 12.0
                horas_extras_totales = horas_pagadas + horas_bolsa_general
        else:
            horas_bolsa_dominical = horas_totales_trabajadas
            horas_extras_totales = horas_totales_trabajadas
    else:
        if modo_turno == "Con Producción":
            if horas_totales_trabajadas >= 12.0:
                horas_pagadas = 1.0
                horas_bolsa_general = horas_totales_trabajadas - 12.0
                horas_extras_totales = horas_pagadas + horas_bolsa_general
        elif modo_turno == "Sin Producción":
            # Lunes a Viernes: límite normal 18:00 (18 * 60)
            # Sábados: límite normal 15:00 (15 * 60)
            limite_normal_minutos = (15 * 60) if es_sabado else (18 * 60)
            
            if minutos_salida > limite_normal_minutos:
                minutos_extras = minutos_salida - limite_normal_minutos
                horas_bolsa_general = minutos_extras / 60.0
                horas_extras_totales = horas_bolsa_general

    return round(horas_extras_totales, 2), round(horas_pagadas, 2), round(horas_bolsa_general, 2), round(horas_bolsa_dominical, 2)

def render_module(user, get_sheet, cargar_datos):
    nombre_sesion = user.get("nombre_completo", user.get("usuario"))
    codigo_sesion = user.get("codigo_personal", "P000")
    rol = user.get("rol", "Visualizador")

    st.subheader("⏱️ Control de Asistencia y Bolsa de Horas")
    st.markdown(f"Usuario: **{nombre_sesion}** | Código: `{codigo_sesion}` | Rol: `{rol}`")
    
    col_ref1, col_ref2 = st.columns([3, 1])
    with col_ref2:
        if st.button("🔄 Refrescar Datos", use_container_width=True):
            st.cache_data.clear()
            st.success("¡Datos actualizados!")
            st.rerun()

    df_users_ref = cargar_datos("Usuarios")
    dict_nombres = {}
    lista_personal_opciones = []
    
    if not df_users_ref.empty and "codigo_personal" in df_users_ref.columns and "nombre_completo" in df_users_ref.columns:
        for _, u_row in df_users_ref.iterrows():
            c_p = str(u_row.get("codigo_personal", "")).strip()
            n_c = str(u_row.get("nombre_completo", "")).strip()
            if c_p:
                dict_nombres[c_p] = n_c
                lista_personal_opciones.append(f"{c_p} - {n_c}")

    if rol in ["Administrador", "JEFE DE TURNO"] and lista_personal_opciones:
        st.markdown("#### 👤 Selección de Colaborador (Modo Operativo)")
        sel_col_op = st.selectbox("Operar asistencia para:", lista_personal_opciones, key="sel_col_operativo_general")
        codigo_per = sel_col_op.split(" - ")[0].strip()
        nombre = sel_col_op.split(" - ")[1].strip()
    else:
        codigo_per = codigo_sesion
        nombre = nombre_sesion

    # =========================================================================
    # CALCULADORA RÁPIDA DE HORARIOS EXCEPCIONALES (NUEVO)
    # =========================================================================
    with st.expander("🧮 Calculadora Rápida de Salida (Turnos Especiales / Almuerzo)"):
        st.caption("Calcula a qué hora exacta debe salir el personal si ingresó en un horario excepcional (ej. desde el mediodía).")
        c_calc1, c_calc2, c_calc3 = st.columns(3)
        with c_calc1:
            hora_ing_calc = st.text_input("Hora de Ingreso (Ej: 12:00):", "12:00", key="calc_h_ing")
        with c_calc2:
            horas_a_cubrir = st.number_input("Horas de Jornada + Almuerzo:", min_value=4.0, max_value=14.0, step=0.5, value=9.0, key="calc_hrs_cubrir", help="Ej: 8 horas de labor + 1 hora de refrigerio = 9 horas en total.")
        with c_calc3:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Calcular Hora de Salida", key="btn_ejecutar_calc"):
                try:
                    dt_ing_calc = datetime.strptime(hora_ing_calc.strip(), "%H:%M")
                    dt_sal_calc = dt_ing_calc + timedelta(hours=float(horas_a_cubrir))
                    st.success(f"🎯 Hora de Salida Exacta: **{dt_sal_calc.strftime('%H:%M')}**")
                except Exception:
                    st.error("Formato de hora inválido. Use HH:MM (Ej: 12:00).")

    # 1. VISUALIZADOR DE SALDOS
    try:
        df_bolsa_check = cargar_datos("Bolsa_Horas_Compensacion")
        saldo_general, saldo_dominical = 0.0, 0.0
        if not df_bolsa_check.empty and "codigo_personal" in df_bolsa_check.columns:
            fila_usu = df_bolsa_check[df_bolsa_check["codigo_personal"].astype(str).str.strip() == codigo_per.strip()]
            if not fila_usu.empty:
                cols_b = df_bolsa_check.columns.tolist()
                s_act_col = [c for c in cols_b if "saldo" in c.lower() and "dom" not in c.lower()]
                s_dom_col = [c for c in cols_b if "dom" in c.lower() or "dominical" in c.lower()]
                
                if s_act_col:
                    saldo_general = float(fila_usu.iloc[0].get(s_act_col[0], 0.0) or 0.0)
                if s_dom_col:
                    saldo_dominical = float(fila_usu.iloc[0].get(s_dom_col[0], 0.0) or 0.0)
                else:
                    vals_f = fila_usu.iloc[0].tolist()
                    if len(vals_f) > 5:
                        saldo_dominical = float(vals_f[5] or 0.0)
        
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            st.info(f"💼 **Bolsa de Horas Extras ({nombre}):** `{saldo_general} hrs` disponibles.")
        with col_s2:
            st.success(f"📅 **Bolsa Dominical:** `{saldo_dominical} hrs` disponibles.")
    except Exception as e:
        pass

    st.markdown("---")
    
    col_t1, col_t2, col_t3 = st.columns(3)
    with col_t1:
        modo_turno = st.selectbox("Modalidad del Turno:", ["Con Producción", "Sin Producción"], key="asist_modo_turno")
    with col_t2:
        fecha_obj = st.date_input("Fecha de Registro:", datetime.now(), key="asist_fecha_reg")
        fecha_actual_str = fecha_obj.strftime("%Y-%m-%d")
        es_domingo = (fecha_obj.weekday() == 6)
        es_sabado = (fecha_obj.weekday() == 5)
        
        dia_semana_nombres = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
        nombre_dia_actual = dia_semana_nombres[fecha_obj.weekday()]
        st.caption((f"📅 Día: **{nombre_dia_actual}**" + (" (Sábado: Salida normal 15:00)" if es_sabado else " (L-V: Salida normal 18:00)" if not es_domingo else " (Domingo)")))
    with col_t3:
        tipo_asistencia = st.selectbox(
            "Estado del Día:", 
            ["Asistencia Normal (Trabajó)", "Feriado", "Licencia", "Permiso", "Compensación", "Vacaciones", "Descanso Médico", "Inasistencia / Falta"],
            key="asist_tipo_dia"
        )

    try:
        df_val_bloqueo = cargar_datos("Asistencia_Personal")
        bloqueado_msg = ""
        if not df_val_bloqueo.empty and "codigo_personal" in df_val_bloqueo.columns and "fecha" in df_val_bloqueo.columns:
            match_bloq = df_val_bloqueo[
                (df_val_bloqueo["codigo_personal"].astype(str).str.strip() == codigo_per.strip()) & 
                (df_val_bloqueo["fecha"].astype(str).str.strip() == fecha_actual_str)
            ]
            if not match_bloq.empty:
                for _, b_row in match_bloq.iterrows():
                    obs_reg = str(b_row.get("observacion", ""))
                    if any(x in obs_reg for x in ["Vacaciones", "Licencia", "Compensación"]):
                        bloqueado_msg = f"⚠️ El colaborador **{nombre}** registra **{obs_reg}** en la fecha {fecha_actual_str}. No se le puede dar asistencia normal."
                        break
    except Exception:
        bloqueado_msg = ""

    st.markdown("---")
    
    if bloqueado_msg:
        st.error(bloqueado_msg)
    elif tipo_asistencia != "Asistencia Normal (Trabajó)":
        st.warning(f"⚠️ Ha seleccionado **{tipo_asistencia}** para **{nombre}** en la fecha {fecha_actual_str}.")
        motivo_excepcion = st.text_input("Detalle o motivo adicional (Opcional):", key="obs_excepcion_input")
        
        es_tardanza = st.checkbox("¿Registrar con tardanza?", key="chk_es_tardanza")
        minutos_tardanza = st.number_input("Tiempo de tardanza (minutos):", min_value=1, step=5, value=15, key="num_min_tardanza") if es_tardanza else 0

        if st.button(f"💾 Registrar {tipo_asistencia}", use_container_width=True, key="btn_reg_excepcion"):
            try:
                ws_asist = get_sheet("Asistencia_Personal")
                recs = ws_asist.get_all_values()
                ya_existe = False
                if len(recs) > 1:
                    for fila_ex in recs[1:]:
                        if len(fila_ex) >= 4 and fila_ex[1].strip() == codigo_per.strip() and fila_ex[3].strip() == fecha_actual_str:
                            ya_existe = True
                            break
                
                if ya_existe:
                    st.warning(f"⚠️ Ya existe un registro para **{nombre}** en la fecha {fecha_actual_str}. No se puede duplicar.")
                else:
                    id_reg = f"EXC-{datetime.now().strftime('%y%m%d%H%M%S')}"
                    etiqueta = f"EXCEPCIÓN: {tipo_asistencia}" + (f" - Tardanza: {minutos_tardanza} min" if es_tardanza else "") + (f" - {motivo_excepcion}" if motivo_excepcion else "")
                    ws_asist.append_row([id_reg, codigo_per, nombre, fecha_actual_str, "00:00", "00:00", modo_turno, "0", "0", "0", etiqueta, "Completado"])
                    st.success(f"✅ Excepción registrada correctamente para {nombre}.")
                    st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")
    else:
        col_reg1, col_reg2 = st.columns(2)
        with col_reg1:
            st.markdown(f"#### 📥 Ingreso ({nombre})")
            hora_ingreso_input = st.text_input("Hora de Entrada (Ej: 20:00):", key="h_ingreso_val")
            
            es_tardanza_ing = st.checkbox("¿Ingreso con tardanza?", key="chk_ing_tardanza")
            min_tard_ing = st.number_input("Minutos de tardanza:", min_value=1, step=5, value=15, key="num_tard_ing_val") if es_tardanza_ing else 0

            if st.button("Registrar Ingreso", use_container_width=True, key="btn_reg_ingreso"):
                if not hora_ingreso_input.strip():
                    st.error("Ingrese hora de entrada.")
                else:
                    try:
                        ws_asist = get_sheet("Asistencia_Personal")
                        registros_actuales = ws_asist.get_all_values()
                        ya_ingresado = False
                        
                        if len(registros_actuales) > 1:
                            for f_ila in registros_actuales[1:]:
                                if len(f_ila) >= 12 and f_ila[1].strip() == codigo_per.strip() and f_ila[3].strip() == fecha_actual_str and f_ila[11].strip() == "Pendiente":
                                    ya_ingresado = True
                                    break
                        
                        if ya_ingresado:
                            st.warning(f"⚠️ El colaborador **{nombre}** ya tiene un ingreso pendiente registrado para hoy. Evite hacer doble clic.")
                        else:
                            id_reg = f"REG-{datetime.now().strftime('%y%m%d%H%M%S')}"
                            obs_ing = "Ingreso Registrado" + (f" - Tardanza: {min_tard_ing} min" if es_tardanza_ing else "")
                            ws_asist.append_row([id_reg, codigo_per, nombre, fecha_actual_str, hora_ingreso_input, "", modo_turno, "0", "0", "0", obs_ing, "Pendiente"])
                            st.success(f"✅ Ingreso registrado exitosamente para {nombre}!")
                            st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")

        with col_reg2:
            st.markdown(f"#### 📤 Salida y Cálculo ({nombre})")
            hora_salida_input = st.text_input("Hora de Salida (Ej: 08:00):", key="h_salida_val")
            he_tot, h_pag, h_bg, h_bd = 0.0, 0.0, 0.0, 0.0
            if hora_ingreso_input.strip() and hora_salida_input.strip():
                try:
                    h_in_dt = datetime.strptime(hora_ingreso_input.strip(), "%H:%M")
                    h_sal_dt = datetime.strptime(hora_salida_input.strip(), "%H:%M")
                    he_tot, h_pag, h_bg, h_bd = calcular_horas_extras(h_in_dt, h_sal_dt, modo_turno, es_domingo, es_sabado)
                except:
                    pass

            obs_input = st.text_input("Motivo u observación operativa:", key="obs_extra_val", placeholder="Ej: Apoyo en cámaras") if he_tot > 0 else "Jornada Regular"
            if es_domingo:
                obs_input = f"[DOMINICAL] {obs_input}"

            if st.button("Registrar Salida y Actualizar Bolsa", use_container_width=True, key="btn_reg_salida"):
                if not hora_salida_input.strip():
                    st.error("Ingrese hora de salida.")
                else:
                    try:
                        ws_asist = get_sheet("Asistencia_Personal")
                        registros_actuales = ws_asist.get_all_values()
                        ya_salida = False
                        if len(registros_actuales) > 1:
                            for f_ila in registros_actuales[1:]:
                                if len(f_ila) >= 12 and f_ila[1].strip() == codigo_per.strip() and f_ila[3].strip() == fecha_actual_str and f_ila[5].strip() == hora_salida_input.strip():
                                    ya_salida = True
                                    break
                        
                        if ya_salida:
                            st.warning("⚠️ Este registro de salida ya fue procesado. Evite hacer doble clic.")
                        else:
                            id_reg = f"REG-{datetime.now().strftime('%y%m%d%H%M%S')}"
                            val_bolsa = h_bd if h_bd > 0 else h_bg
                            
                            ws_asist.append_row([id_reg, codigo_per, nombre, fecha_actual_str, hora_ingreso_input, hora_salida_input, modo_turno, str(he_tot), str(h_pag), str(val_bolsa), obs_input, "Completado"])
                            
                            if val_bolsa > 0 or h_pag > 0:
                                ws_bolsa = get_sheet("Bolsa_Horas_Compensacion")
                                try:
                                    celda_c = ws_bolsa.find(codigo_per.strip())
                                except:
                                    celda_c = None
                                    
                                if celda_c:
                                    f_idx = celda_c.row
                                    v_fila = ws_bolsa.row_values(f_idx)
                                    if h_bd > 0:
                                        act_dom = float(v_fila[5]) if len(v_fila) > 5 and v_fila[5] != "" else 0.0
                                        ws_bolsa.update_cell(f_idx, 6, str(act_dom + h_bd))
                                    else:
                                        act_acum = float(v_fila[2]) if len(v_fila) > 2 and v_fila[2] != "" else 0.0
                                        act_sald = float(v_fila[4]) if len(v_fila) > 4 and v_fila[4] != "" else 0.0
                                        ws_bolsa.update_cell(f_idx, 3, str(act_acum + h_bg))
                                        ws_bolsa.update_cell(f_idx, 5, str(act_sald + h_bg))
                                else:
                                    if h_bd > 0:
                                        ws_bolsa.append_row([codigo_per, nombre, "0", "0", "0", str(h_bd), "", "Activo"])
                                    else:
                                        ws_bolsa.append_row([codigo_per, nombre, str(h_bg), "0", str(h_bg), "0", "", "Activo"])

                            st.success(f"✅ Salida registrada correctamente para {nombre}!")
                            st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")

    # =========================================================================
    # 1. ZONA: CONTROL DIARIO PARA EL TARIADOR
    # =========================================================================
    st.markdown("---")
    st.subheader("📋 Control Diario de Asistencias (Vista de Turno)")
    st.caption("Monitoreo en tiempo real de los ingresos y salidas registrados por el personal.")
    
    try:
        df_asist_full = cargar_datos("Asistencia_Personal")
        
        if not df_asist_full.empty and "fecha" in df_asist_full.columns:
            col_f_f1, _ = st.columns([1, 2])
            with col_f_f1:
                fecha_filtro_obj = st.date_input("Filtrar por Fecha de Turno:", datetime.now(), key="filtro_fecha_diaria_tariador")
            
            fecha_filtro_str = fecha_filtro_obj.strftime("%Y-%m-%d")
            df_dia_actual = df_asist_full[df_asist_full["fecha"].astype(str).str.strip() == fecha_filtro_str].copy()
            
            if not df_dia_actual.empty:
                tabla_mostrada = []
                for _, r in df_dia_actual.iterrows():
                    c_code = str(r.get("codigo_personal", "")).strip()
                    n_real = r.get("nombre_personal", "")
                    if not n_real or pd.isna(n_real):
                        n_real = dict_nombres.get(c_code, f"Colaborador {c_code}")
                    
                    tabla_mostrada.append({
                        "Código": c_code,
                        "Colaborador": n_real,
                        "Fecha": r.get("fecha"),
                        "Hora Entrada": r.get("hora_entrada"),
                        "Hora Salida": r.get("hora_salida"),
                        "Modalidad": r.get("modo_turno"),
                        "Estado": r.get("estado_registro"),
                        "Observación": r.get("observacion")
                    })
                st.dataframe(pd.DataFrame(tabla_mostrada), use_container_width=True)
                st.success(f"📊 Se encontraron **{len(tabla_mostrada)} registros** para el {fecha_filtro_str}.")
            else:
                st.info(f"ℹ️ No hay registros de asistencia para la fecha seleccionada ({fecha_filtro_str}).")
        else:
            st.info("ℹ️ Aún no hay registros de asistencia guardados.")
    except Exception as e:
        st.warning(f"Error en control diario: {e}")

    # =========================================================================
    # 2. PANEL RR.HH.
    # =========================================================================
    if rol in ["Administrador", "JEFE DE TURNO"]:
        st.markdown("---")
        st.subheader("🛠️ Panel de RR.HH. - Vacaciones, Licencias y Compensaciones")
        
        try:
            df_bolsa_admin = cargar_datos("Bolsa_Horas_Compensacion")
            if not df_bolsa_admin.empty:
                st.markdown("#### 💼 Estado Actual de Bolsas de Horas")
                st.dataframe(df_bolsa_admin, use_container_width=True)
            
            if lista_personal_opciones:
                st.markdown("---")
                tab_v, tab_l, tab_c, tab_reg = st.tabs(["🌴 Vacaciones por Rango", "📜 Licencias por Rango", "⚖️ Compensación con Bolsa", "⚙️ Regularizar Bolsa"])
                
                with tab_v:
                    st.caption("Registra vacaciones masivas por rango de fechas.")
                    col_v1, col_v2, col_v3 = st.columns([2, 1, 1])
                    with col_v1:
                        sel_col_vac = st.selectbox("Colaborador:", lista_personal_opciones, key="s_col_vac")
                        cod_vac = sel_col_vac.split(" - ")[0].strip()
                        nom_vac = sel_col_vac.split(" - ")[1].strip()
                    with col_v2:
                        fec_ini_v = st.date_input("Fecha Inicio:", datetime.now(), key="f_ini_vac")
                    with col_v3:
                        fec_fin_v = st.date_input("Fecha Fin:", datetime.now(), key="f_fin_vac")
                    
                    if st.button("💾 Guardar Vacaciones por Rango", key="btn_guardar_vacaciones"):
                        if fec_fin_v < fec_ini_v:
                            st.error("❌ La fecha fin no puede ser anterior a la fecha inicio.")
                        else:
                            try:
                                ws_asist = get_sheet("Asistencia_Personal")
                                existing_recs = ws_asist.get_all_values()
                                
                                delta_dias = (fec_fin_v - fec_ini_v).days + 1
                                current_d = fec_ini_v
                                count_registrados = 0
                                count_omitidos = 0
                                
                                for _ in range(delta_dias):
                                    f_str = current_d.strftime("%Y-%m-%d")
                                    ya_registrado_fecha = False
                                    if len(existing_recs) > 1:
                                        for f_ex in existing_recs[1:]:
                                            if len(f_ex) >= 4 and f_ex[1].strip() == cod_vac.strip() and f_ex[3].strip() == f_str:
                                                ya_registrado_fecha = True
                                                break
                                    
                                    if ya_registrado_fecha:
                                        count_omitidos += 1
                                    else:
                                        id_reg = f"VAC-{datetime.now().strftime('%y%m%d%H%M%S')}-{count_registrados}"
                                        ws_asist.append_row([
                                            id_reg, cod_vac, nom_vac, f_str, "00:00", "00:00", "Sin Producción", "0", "0", "0", "EXCEPCIÓN: Vacaciones", "Completado"
                                        ])
                                        count_registrados += 1
                                    current_d += timedelta(days=1)
                                
                                st.success(f"✅ Vacaciones guardadas para **{nom_vac}**: {count_registrados} días nuevos ({count_omitidos} omitidos por ya existir).")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error al registrar vacaciones: {e}")

                with tab_l:
                    st.caption("Registra licencias por rango de fechas.")
                    col_l1, col_l2, col_l3, col_l4 = st.columns([1.5, 1, 1, 1])
                    with col_l1:
                        sel_col_lic = st.selectbox("Colaborador:", lista_personal_opciones, key="s_col_lic")
                        cod_lic = sel_col_lic.split(" - ")[0].strip()
                        nom_lic = sel_col_lic.split(" - ")[1].strip()
                    with col_l2:
                        fec_ini_l = st.date_input("Fecha Inicio:", datetime.now(), key="f_ini_lic")
                    with col_l3:
                        fec_fin_l = st.date_input("Fecha Fin:", datetime.now(), key="f_fin_lic")
                    with col_l4:
                        motivo_lic = st.text_input("Motivo:", placeholder="Ej: Paternidad", key="motivo_lic_txt")
                    
                    if st.button("💾 Guardar Licencia por Rango", key="btn_guardar_licencia"):
                        if fec_fin_l < fec_ini_l:
                            st.error("❌ La fecha fin no puede ser anterior a la fecha inicio.")
                        else:
                            try:
                                ws_asist = get_sheet("Asistencia_Personal")
                                existing_recs = ws_asist.get_all_values()
                                
                                delta_dias_l = (fec_fin_l - fec_ini_l).days + 1
                                current_dl = fec_ini_l
                                count_l = 0
                                count_omitidos_l = 0
                                
                                for _ in range(delta_dias_l):
                                    f_str_l = current_dl.strftime("%Y-%m-%d")
                                    ya_reg_l = False
                                    if len(existing_recs) > 1:
                                        for f_ex in existing_recs[1:]:
                                            if len(f_ex) >= 4 and f_ex[1].strip() == cod_lic.strip() and f_ex[3].strip() == f_str_l:
                                                ya_reg_l = True
                                                break
                                    
                                    if ya_reg_l:
                                        count_omitidos_l += 1
                                    else:
                                        id_reg_l = f"LIC-{datetime.now().strftime('%y%m%d%H%M%S')}-{count_l}"
                                        detalle_lic = f"EXCEPCIÓN: Licencia" + (f" - {motivo_lic}" if motivo_lic else "")
                                        ws_asist.append_row([
                                            id_reg_l, cod_lic, nom_lic, f_str_l, "00:00", "00:00", "Sin Producción", "0", "0", "0", detalle_lic, "Completado"
                                        ])
                                        count_l += 1
                                    current_dl += timedelta(days=1)
                                
                                st.success(f"✅ Licencia guardada para **{nom_lic}**: {count_l} días nuevos ({count_omitidos_l} omitidos por duplicidad).")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error al registrar licencia: {e}")

                with tab_c:
                    st.caption("Descuenta horas de la bolsa por permisos o compensaciones.")
                    col_c1, col_c2, col_c3, col_c4, col_c5 = st.columns([1.5, 1, 1, 1, 1])
                    with col_c1:
                        sel_col_comp = st.selectbox("Colaborador:", lista_personal_opciones, key="s_col_comp")
                        cod_comp = sel_col_comp.split(" - ")[0].strip()
                        nom_comp = sel_col_comp.split(" - ")[1].strip()
                    with col_c2:
                        hrs_ret = st.number_input("Horas a descontar:", min_value=0.5, step=0.5, value=8.0, key="i_h_c")
                    with col_c3:
                        fec_ini_c = st.date_input("Fecha Inicio:", datetime.now(), key="i_f_ini_c")
                    with col_c4:
                        fec_fin_c = st.date_input("Fecha Fin:", datetime.now(), key="i_f_fin_c")
                    with col_c5:
                        st.markdown("<br>", unsafe_allow_html=True)
                        btn_comp = st.button("⚖️ Descontar Bolsa", use_container_width=True, key="btn_desc_horas")

                    if btn_comp:
                        if fec_fin_c < fec_ini_c:
                            st.error("❌ La fecha fin no puede ser anterior a la fecha inicio.")
                        else:
                            try:
                                ws_b = get_sheet("Bolsa_Horas_Compensacion")
                                c_lib = ws_b.find(cod_comp)
                                if c_lib:
                                    f_idx = c_lib.row
                                    v_lib = ws_b.row_values(f_idx)
                                    a_sald = float(v_lib[4]) if len(v_lib) > 4 and v_lib[4] != "" else 0.0
                                    
                                    if hrs_ret > a_sald:
                                        st.error(f"❌ Saldo insuficiente en la bolsa de **{nom_comp}** ({a_sald} hrs disponibles).")
                                    else:
                                        hrs_comp_ant = float(v_lib[3]) if len(v_lib) > 3 and v_lib[3] != "" else 0.0
                                        ws_b.update_cell(f_idx, 4, str(hrs_comp_ant + hrs_ret))
                                        ws_b.update_cell(f_idx, 5, str(a_sald - hrs_ret))
                                        
                                        ws_h = get_sheet("Historial_Compensaciones")
                                        fec_str_comp = f"{fec_ini_c} al {fec_fin_c}"
                                        ws_h.append_row([f"COMP-{datetime.now().strftime('%y%m%d%H%M%S')}", cod_comp, nom_comp, str(hrs_ret), fec_str_comp, f"AUTORIZADO BY {nombre_sesion}"])
                                        
                                        ws_asist = get_sheet("Asistencia_Personal")
                                        existing_recs = ws_asist.get_all_values()
                                        
                                        delta_c = (fec_fin_c - fec_ini_c).days + 1
                                        curr_c = fec_ini_c
                                        for c_i in range(delta_c):
                                            f_str_c = curr_c.strftime("%Y-%m-%d")
                                            ya_reg_c = False
                                            if len(existing_recs) > 1:
                                                for f_ex in existing_recs[1:]:
                                                    if len(f_ex) >= 4 and f_ex[1].strip() == cod_comp.strip() and f_ex[3].strip() == f_str_c:
                                                        ya_reg_c = True
                                                        break
                                            if not ya_reg_c:
                                                id_reg_c = f"COMPD-{datetime.now().strftime('%y%m%d%H%M%S')}-{c_i}"
                                                ws_asist.append_row([id_reg_c, cod_comp, nom_comp, f_str_c, "00:00", "00:00", "Sin Producción", "0", "0", str(hrs_ret), "EXCEPCIÓN: Compensación de Horas", "Completado"])
                                            curr_c += timedelta(days=1)

                                        st.success(f"✅ Se descontaron {hrs_ret} hrs y se procesó la compensación para **{nom_comp}**.")
                                        st.rerun()
                                else:
                                    st.error("❌ El colaborador no registra bolsa de horas activa.")
                            except Exception as e:
                                st.error(f"Error al procesar compensación: {e}")

                with tab_reg:
                    st.caption("Permite sumar o restar horas a la bolsa de un colaborador por correcciones operativas.")
                    col_r1, col_r2, col_r3, col_r4 = st.columns([1.5, 1, 1, 1.5])
                    with col_r1:
                        sel_col_reg = st.selectbox("Colaborador:", lista_personal_opciones, key="s_col_reg")
                        cod_reg = sel_col_reg.split(" - ")[0].strip()
                        nom_reg = sel_col_reg.split(" - ")[1].strip()
                    with col_r2:
                        tipo_ajuste = st.selectbox("Acción:", ["Sumar Horas (+)", "Restar Horas (-)"], key="sel_tipo_ajuste")
                    with col_r3:
                        cant_horas_reg = st.number_input("Cantidad de horas:", min_value=0.5, step=0.5, value=1.0, key="num_horas_reg")
                    with col_r4:
                        motivo_reg = st.text_input("Motivo / Justificación:", placeholder="Ej: Error de cálculo salida", key="txt_motivo_reg")
                    
                    if st.button("⚙️ Aplicar Regularización", key="btn_aplicar_regularizacion"):
                        try:
                            ws_b = get_sheet("Bolsa_Horas_Compensacion")
                            c_reg = ws_b.find(cod_reg)
                            if c_reg:
                                f_idx_r = c_reg.row
                                v_fila_r = ws_b.row_values(f_idx_r)
                                saldo_actual_r = float(v_fila_r[4]) if len(v_fila_r) > 4 and v_fila_r[4] != "" else 0.0
                                acum_general_r = float(v_fila_r[2]) if len(v_fila_r) > 2 and v_fila_r[2] != "" else 0.0
                                
                                if tipo_ajuste == "Sumar Horas (+)":
                                    nuevo_saldo = saldo_actual_r + cant_horas_reg
                                    nuevo_acum = acum_general_r + cant_horas_reg
                                    signo_str = f"+{cant_horas_reg}"
                                else:
                                    if cant_horas_reg > saldo_actual_r:
                                        st.error(f"❌ No se pueden restar {cant_horas_reg} hrs porque el saldo actual es de solo {saldo_actual_r} hrs.")
                                        st.stop()
                                    nuevo_saldo = saldo_actual_r - cant_horas_reg
                                    nuevo_acum = acum_general_r
                                    signo_str = f"-{cant_horas_reg}"

                                ws_b.update_cell(f_idx_r, 3, str(nuevo_acum))
                                ws_b.update_cell(f_idx_r, 5, str(nuevo_saldo))
                                
                                ws_h = get_sheet("Historial_Compensaciones")
                                ws_h.append_row([f"REGUL-{datetime.now().strftime('%y%m%d%H%M%S')}", cod_reg, nom_reg, signo_str, datetime.now().strftime("%Y-%m-%d"), f"REGULARIZACIÓN: {motivo_reg} (By {nombre_sesion})"])
                                
                                st.success(f"✅ Regularización aplicada a **{nom_reg}**. Nuevo saldo en bolsa: **{nuevo_saldo} hrs**.")
                                st.rerun()
                            else:
                                st.error("❌ El colaborador no registra bolsa de horas activa.")
                        except Exception as e:
                            st.error(f"Error al regularizar: {e}")

        except Exception as e:
            st.warning(f"Nota en panel RR.HH.: {e}")

        # =========================================================================
        # 3. PANEL GERENCIAL / RESUMEN MENSUAL COMPLETO
        # =========================================================================
        st.markdown("---")
        st.subheader("📊 Resumen Mensual y Control de Asistencia (RR.HH.)")
        st.caption("Panel ejecutivo avanzado: días trabajados, feriados, dominicales, inasistencias, licencias, tardanzas y horas calculadas.")
        
        try:
            df_asist_hist = cargar_datos("Asistencia_Personal")
            df_bolsa_hist = cargar_datos("Bolsa_Horas_Compensacion")
            
            if not df_asist_hist.empty:
                col_f1, col_f2 = st.columns(2)
                with col_f1:
                    mes_sel = st.selectbox("Seleccione Mes de Auditoría:", ["01 - Enero", "02 - Febrero", "03 - Marzo", "04 - Abril", "05 - Mayo", "06 - Junio", "07 - Julio", "08 - Agosto", "09 - Setiembre", "10 - Octubre", "11 - Noviembre", "12 - Diciembre"], index=7, key="sel_mes_auditoria_gerencial")
                with col_f2:
                    anio_sel = st.selectbox("Seleccione Año:", ["2026", "2027", "2025"], index=0, key="sel_anio_auditoria_gerencial")
                
                mes_num = mes_sel.split(" - ")[0]
                
                if "fecha" in df_asist_hist.columns and "codigo_personal" in df_asist_hist.columns:
                    df_asist_hist["mes"] = df_asist_hist["fecha"].astype(str).str.slice(5, 7)
                    df_asist_hist["anio"] = df_asist_hist["fecha"].astype(str).str.slice(0, 4)
                    
                    df_filtrado = df_asist_hist[(df_asist_hist["mes"] == mes_num) & (df_asist_hist["anio"] == anio_sel)]
                    
                    if not df_filtrado.empty:
                        st.markdown(f"#### 📋 Consolidado Operativo - Período: {mes_sel} {anio_sel}")
                        
                        resumen_list = []
                        for cod_p, grupo in df_filtrado.groupby("codigo_personal"):
                            cod_p_clean = str(cod_p).strip()
                            nombre_trab = dict_nombres.get(cod_p_clean, grupo.iloc[0].get("nombre_personal", grupo.iloc[0].get("nombre_trabajador", f"Colaborador {cod_p_clean}")))
                            
                            obs_serie = grupo["observacion"].astype(str)
                            
                            dias_trabajados = len(grupo[(grupo["estado_registro"] == "Completado") & (~obs_serie.str.contains("EXCEPCIÓN:", case=False, na=False))])
                            
                            horas_bolsa_acum = pd.to_numeric(grupo["horas_bolsa"], errors="coerce").sum()
                            horas_pagadas_acum = pd.to_numeric(grupo["horas_pagadas"], errors="coerce").sum()
                            
                            feriados_cnt = obs_serie.str.contains("Feriado", case=False, na=False).sum()
                            dominicales_cnt = obs_serie.str.contains("DOMINICAL", case=False, na=False).sum()
                            descanso_medico = obs_serie.str.contains("Descanso Médico", case=False, na=False).sum()
                            licencias_cnt = obs_serie.str.contains("Licencia", case=False, na=False).sum()
                            inasistencias_cnt = obs_serie.str.contains("Inasistencia|Falta", case=False, na=False).sum()
                            vacaciones = obs_serie.str.contains("Vacaciones", case=False, na=False).sum()
                            compensacion_cnt = obs_serie.str.contains("Compensación", case=False, na=False).sum()
                            
                            tardanzas = obs_serie.str.contains("tardanza|tarde", case=False, na=False).sum()
                            permisos = obs_serie.str.contains("Permiso|permiso", case=False, na=False).sum()
                            
                            horas_inasistencia = inasistencias_cnt * 12.0
                            horas_feriados = feriados_cnt * 12.0
                            
                            sald_general = 0.0
                            sald_dominical = 0.0
                            if not df_bolsa_hist.empty and "codigo_personal" in df_bolsa_hist.columns:
                                match_b = df_bolsa_hist[df_bolsa_hist["codigo_personal"].astype(str).str.strip() == cod_p_clean]
                                if not match_b.empty:
                                    sald_general = float(match_b.iloc[0].get("saldo_actual", 0.0) or 0.0)
                                    sald_dom_cols = [c for c in match_b.columns if "dom" in c.lower()]
                                    if sald_dom_cols:
                                        sald_dominical = float(match_b.iloc[0].get(sald_dom_cols[0], 0.0) or 0.0)

                            resumen_list.append({
                                "Código": cod_p_clean,
                                "Colaborador": nombre_trab,
                                "Días Trabajados": dias_trabajados,
                                "Feriados": int(feriados_cnt),
                                "Días Dominicales": int(dominicales_cnt),
                                "Inasistencias": int(inasistencias_cnt),
                                "Días Licencia": int(licencias_cnt),
                                "Permisos": int(permisos),
                                "Compensación": int(compensacion_cnt),
                                "Vacaciones": int(vacaciones),
                                "Tardanzas": int(tardanzas),
                                "Descanso Médico": int(descanso_medico),
                                "H. Inasistencias": round(horas_inasistencia, 2),
                                "H. Feriados Trabajados": round(horas_feriados, 2),
                                "H. Pagadas (25%)": round(horas_pagadas_acum, 2),
                                "H. Compensación (35%)": round(horas_bolsa_acum, 2),
                                "Saldo Bolsa General": round(sald_general, 2),
                                "Saldo Bolsa Dominical": round(sald_dominical, 2)
                            })
                        
                        df_resumen_final = pd.DataFrame(resumen_list)
                        st.dataframe(df_resumen_final, use_container_width=True)
                        
                        st.download_button(
                            label="📥 Descargar Reporte Mensual de Asistencia a CSV",
                            data=df_resumen_final.to_csv(index=False).encode("utf-8"),
                            file_name=f"Resumen_Asistencia_Frigosa_{mes_num}_{anio_sel}.csv",
                            mime="text/csv",
                            key="btn_descarga_csv_resumen_final"
                        )
                    else:
                        st.info(f"No hay registros de asistencia para el período {mes_sel} {anio_sel}.")
            else:
                st.info("Aún no hay datos históricos suficientes en la tabla de asistencia.")
        except Exception as e:
            st.warning(f"Nota en resumen mensual: {e}")
