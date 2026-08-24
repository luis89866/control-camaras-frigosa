import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# --- CÁLCULO DE HORAS EXTRAS Y DOMINICALES (FRIGOSA) ---
def calcular_horas_extras(hora_entrada_dt, hora_salida_dt, modo_turno, es_domingo):
    horas_totales_trabajadas = 0.0
    
    minutos_entrada = hora_entrada_dt.hour * 60 + hora_entrada_dt.minute
    minutos_salida = hora_salida_dt.hour * 60 + hora_salida_dt.minute
    
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
                horas_pagadas = 0.0
                horas_bolsa_general = 0.0
                horas_extras_totales = 0.0
        else:
            horas_pagadas = 0.0
            horas_bolsa_dominical = horas_totales_trabajadas
            horas_extras_totales = horas_totales_trabajadas
    else:
        if modo_turno == "Con Producción":
            if horas_totales_trabajadas >= 12.0:
                horas_pagadas = 1.0
                horas_bolsa_general = horas_totales_trabajadas - 12.0
                horas_extras_totales = horas_pagadas + horas_bolsa_general
            else:
                horas_pagadas = 0.0
                horas_bolsa_general = 0.0
                horas_extras_totales = 0.0
        elif modo_turno == "Sin Producción":
            jornada_regular = 8.0 
            if horas_totales_trabajadas > jornada_regular:
                horas_bolsa_general = horas_totales_trabajadas - jornada_regular
                horas_extras_totales = horas_bolsa_general
            else:
                horas_bolsa_general = 0.0
                horas_extras_totales = 0.0
            horas_pagadas = 0.0

    return round(horas_extras_totales, 2), round(horas_pagadas, 2), round(horas_bolsa_general, 2), round(horas_bolsa_dominical, 2)

def render_module(user, get_sheet, cargar_datos):
    nombre = user.get("nombre_completo", user.get("usuario"))
    codigo_per = user.get("codigo_personal", "P000")
    rol = user.get("rol", "Visualizador")

    st.subheader("⏱️ Control de Asistencia y Bolsa de Horas")
    st.markdown(f"Colaborador: **{nombre}** | Código: `{codigo_per}` | Rol: `{rol}`")
    
    # 1. VISUALIZADOR DE SALDOS
    try:
        df_bolsa_check = cargar_datos("Bolsa_Horas_Compensacion")
        saldo_general = 0.0
        saldo_dominical = 0.0
        
        if not df_bolsa_check.empty and "codigo_personal" in df_bolsa_check.columns:
            fila_usu = df_bolsa_check[df_bolsa_check["codigo_personal"].astype(str).str.strip() == codigo_per.strip()]
            if not fila_usu.empty:
                saldo_general = float(fila_usu.iloc[0].get("saldo_actual", 0.0))
                saldo_dominical = float(fila_usu.iloc[0].get("saldo_dominical", 0.0) if "saldo_dominical" in fila_usu.columns else 0.0)
        
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            st.info(f"💼 **Bolsa de Horas Extras:** `{saldo_general} hrs` disponibles.")
        with col_s2:
            st.success(f"📅 **Bolsa Dominical (Compensación):** `{saldo_dominical} hrs` disponibles.")

        df_hist_comp = cargar_datos("Historial_Compensaciones")
        if not df_hist_comp.empty and "codigo_personal" in df_hist_comp.columns:
            df_hist_usu = df_hist_comp[df_hist_comp["codigo_personal"].astype(str).str.strip() == codigo_per.strip()]
            if not df_hist_usu.empty:
                with st.expander("📜 Ver mi Historial de Descansos / Horas Compensadas"):
                    st.dataframe(df_hist_usu, use_container_width=True)
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
    with col_t3:
        tipo_asistencia = st.selectbox(
            "Estado del Día:", 
            ["Asistencia Normal (Trabajó)", "Feriado", "Licencia", "Compensación", "Vacaciones", "Descanso Médico", "Inasistencia / Falta"],
            key="asist_tipo_dia"
        )

    if es_domingo:
        st.warning("📅 **Domingo detectado:** 'Sin Producción' acumulará las horas en tu **Bolsa Dominical** exclusiva.")

    st.markdown("---")
    
    if tipo_asistencia != "Asistencia Normal (Trabajó)":
        st.warning(f"⚠️ Ha seleccionado **{tipo_asistencia}** para la fecha {fecha_actual_str}.")
        motivo_excepcion = st.text_input("Detalle o motivo adicional (Opcional):", key="obs_excepcion_input")
        
        if st.button(f"💾 Registrar {tipo_asistencia}", use_container_width=True, key="btn_reg_excepcion"):
            try:
                ws_asist = get_sheet("Asistencia_Personal")
                registros_existentes = ws_asist.get_all_values()
                
                ya_registrado = False
                if len(registros_existentes) > 1:
                    for fila in registros_existentes[1:]:
                        if len(fila) >= 3 and fila[1].strip() == codigo_per.strip() and fila[2].strip() == fecha_actual_str:
                            ya_registrado = True
                            break
                
                if ya_registrado:
                    st.warning(f"⚠️ Ya existe un registro para esta fecha ({fecha_actual_str}).")
                else:
                    id_registro = f"EXC-{datetime.now().strftime('%y%m%d%H%M%S')}"
                    etiqueta_estado = f"EXCEPCIÓN: {tipo_asistencia}" + (f" - {motivo_excepcion}" if motivo_excepcion else "")
                    
                    ws_asist.append_row([
                        id_registro, codigo_per, fecha_actual_str, "00:00", "00:00", modo_turno, "0", "0", "0", etiqueta_estado, "Completado"
                    ])
                    st.success(f"✅ Se registró correctamente la excepción: **{tipo_asistencia}**.")
                    st.rerun()
            except Exception as e:
                st.error(f"Error al registrar excepción: {e}")
    else:
        col_reg1, col_reg2 = st.columns(2)
        
        with col_reg1:
            st.markdown("#### 📥 Ingreso")
            hora_ingreso_input = st.text_input("Hora de Entrada (Ej: 20:00):", placeholder="Ej: 20:00", key="h_ingreso_val")
            
            if st.button("Registrar Ingreso", use_container_width=True, key="btn_reg_ingreso"):
                if not hora_ingreso_input.strip():
                    st.error("❌ Por favor ingrese la hora de entrada.")
                else:
                    try:
                        ws_asist = get_sheet("Asistencia_Personal")
                        registros_existentes = ws_asist.get_all_values()
                        
                        ya_registrado = False
                        if len(registros_existentes) > 1:
                            for fila in registros_existentes[1:]:
                                if len(fila) >= 3 and fila[1].strip() == codigo_per.strip() and fila[2].strip() == fecha_actual_str:
                                    ya_registrado = True
                                    break
                        
                        if ya_registrado:
                            st.warning(f"⚠️ ¡Atención! Su registro de ingreso para la fecha **{fecha_actual_str}** ya ha sido registrado.")
                        else:
                            id_registro = f"REG-{datetime.now().strftime('%y%m%d%H%M%S')}"
                            ws_asist.append_row([
                                id_registro, codigo_per, fecha_actual_str, hora_ingreso_input, "", modo_turno, "0", "0", "0", "Ingreso Registrado", "Pendiente"
                            ])
                            st.success(f"✅ ¡Se registró su ingreso exitosamente a las {hora_ingreso_input}!")
                            st.rerun()
                    except Exception as e:
                        st.error(f"Error al registrar ingreso: {e}")

        with col_reg2:
            st.markdown("#### 📤 Salida y Cálculo")
            hora_salida_input = st.text_input("Hora de Salida (Ej: 08:00):", placeholder="Ej: 08:00", key="h_salida_val")
            
            he_tot, h_pag, h_bolsa_g, h_bolsa_d = 0.0, 0.0, 0.0, 0.0
            if hora_ingreso_input.strip() and hora_salida_input.strip():
                try:
                    h_in_dt = datetime.strptime(hora_ingreso_input.strip(), "%H:%M")
                    h_sal_dt = datetime.strptime(hora_salida_input.strip(), "%H:%M")
                    he_tot, h_pag, h_bolsa_g, h_bolsa_d = calcular_horas_extras(h_in_dt, h_sal_dt, modo_turno, es_domingo)
                except:
                    pass

            if he_tot > 0:
                if h_bolsa_d > 0:
                    st.warning(f"⚠️ Domingo sin producción: **{h_bolsa_d} hrs** asignadas directo a la **Bolsa Dominical**.")
                else:
                    st.warning(f"⚠️ Se detectaron **{he_tot} hrs** (Pagadas: {h_pag}h | Bolsa General: {h_bolsa_g}h).")
                obs_input = st.text_input("Motivo u observación operativa:", key="obs_extra_val", placeholder="Ej: Apoyo en cámaras")
            else:
                if hora_salida_input.strip():
                    st.info("ℹ️ Jornada regular.")
                obs_input = "Jornada Regular"

            if es_domingo:
                obs_input = f"[DOMINICAL] {obs_input}"

            if st.button("Registrar Salida y Actualizar Bolsa", use_container_width=True, key="btn_reg_salida"):
                if not hora_salida_input.strip():
                    st.error("❌ Por favor ingrese la hora de salida.")
                else:
                    try:
                        ws_asist = get_sheet("Asistencia_Personal")
                        registros_existentes = ws_asist.get_all_values()
                        
                        salida_registrada = False
                        if len(registros_existentes) > 1:
                            for fila in registros_existentes[1:]:
                                if len(fila) >= 11 and fila[1].strip() == codigo_per.strip() and fila[2].strip() == fecha_actual_str and fila[10].strip() == "Completado":
                                    salida_registrada = True
                                    break
                        
                        if salida_registrada:
                            st.warning(f"⚠️ ¡Atención! Su registro de salida ya fue procesado anteriormente.")
                        else:
                            id_registro = f"REG-{datetime.now().strftime('%y%m%d%H%M%S')}"
                            val_bolsa_guardar = h_bolsa_d if h_bolsa_d > 0 else h_bolsa_g
                            ws_asist.append_row([
                                id_registro, codigo_per, fecha_actual_str, hora_ingreso_input, hora_salida_input, 
                                modo_turno, str(he_tot), str(h_pag), str(val_bolsa_guardar), obs_input, "Completado"
                            ])
                            
                            if val_bolsa_guardar > 0:
                                ws_bolsa = get_sheet("Bolsa_Horas_Compensacion")
                                try:
                                    celda_codigo = ws_bolsa.find(codigo_per.strip())
                                except:
                                    celda_codigo = None
                                    
                                if celda_codigo:
                                    fila_idx = celda_codigo.row
                                    vals_fila = ws_bolsa.row_values(fila_idx)
                                    
                                    if h_bolsa_d > 0:
                                        actual_sald_dom = float(vals_fila[5]) if len(vals_fila) > 5 and vals_fila[5] != "" else 0.0
                                        ws_bolsa.update_cell(fila_idx, 6, str(actual_sald_dom + h_bolsa_d))
                                    else:
                                        actual_acum = float(vals_fila[2]) if len(vals_fila) > 2 and vals_fila[2] != "" else 0.0
                                        actual_saldo = float(vals_fila[4]) if len(vals_fila) > 4 and vals_fila[4] != "" else 0.0
                                        ws_bolsa.update_cell(fila_idx, 3, str(actual_acum + h_bolsa_g))
                                        ws_bolsa.update_cell(fila_idx, 5, str(actual_saldo + h_bolsa_g))
                                else:
                                    if h_bolsa_d > 0:
                                        ws_bolsa.append_row([codigo_per, nombre, "0", "0", "0", str(h_bolsa_d), "", "Activo"])
                                    else:
                                        ws_bolsa.append_row([codigo_per, nombre, str(h_bolsa_g), "0", str(h_bolsa_g), "0", "", "Activo"])
                                    
                            st.success("✅ ¡Salida registrada y bolsa correspondiente actualizada correctamente!")
                            st.rerun()
                    except Exception as e:
                        st.error(f"Error al registrar salida: {e}")

    # =========================================================================
    # PANEL RR.HH. - GESTIÓN Y COMPENSACIONES
    # =========================================================================
    if rol in ["Administrador", "JEFE DE TURNO"]:
        st.markdown("---")
        st.subheader("🛠️ Panel de RR.HH. - Gestión y Compensaciones")
        try:
            df_bolsa_admin = cargar_datos("Bolsa_Horas_Compensacion")
            if not df_bolsa_admin.empty:
                st.markdown("#### 💼 Estado Actual de Bolsas de Horas")
                st.dataframe(df_bolsa_admin, use_container_width=True)
                
                lista_personal_bolsa = [f"{r.get('codigo_personal','').strip()} - {r.get('nombre_trabajador','').strip()}" for _, r in df_bolsa_admin.iterrows()]
                
                accion_rrhh = st.radio("Seleccione acción de RR.HH.:", ["Registrar Compensación (Descontar)", "Revertir Compensación (Devolver Horas)"], horizontal=True, key="radio_accion_rrhh")
                
                if accion_rrhh == "Registrar Compensación (Descontar)":
                    if lista_personal_bolsa:
                        col_l1, col_l2, col_l3, col_l4 = st.columns([1.5, 1, 1, 1])
                        with col_l1:
                            sel_col = st.selectbox("Colaborador:", lista_personal_bolsa, key="s_c_desc")
                            cod_comp = sel_col.split(" - ")[0].strip()
                        with col_l2:
                            hrs_ret = st.number_input("Horas a descontar:", min_value=0.5, step=0.5, value=1.0, key="i_h_c")
                        with col_l3:
                            fec_lib = st.date_input("Fecha:", datetime.now(), key="i_f_c").strftime("%Y-%m-%d")
                        with col_l4:
                            st.markdown("<br>", unsafe_allow_html=True)
                            btn_comp = st.button("Descontar Horas", use_container_width=True, key="btn_desc_horas")

                        if btn_comp:
                            ws_h = get_sheet("Historial_Compensaciones")
                            regs_h = ws_h.get_all_values()
                            ya_comp = any(len(f) >= 5 and f[1].strip() == cod_comp and f[4].strip() == fec_lib for f in regs_h[1:])
                            
                            if ya_comp:
                                st.error(f"❌ **Restricción:** El colaborador ya cuenta con una compensación para el **{fec_lib}**.")
                            else:
                                ws_b = get_sheet("Bolsa_Horas_Compensacion")
                                c_lib = ws_b.find(cod_comp)
                                if c_lib:
                                    f_idx = c_lib.row
                                    v_lib = ws_b.row_values(f_idx)
                                    nom_afec = v_lib[1] if len(v_lib) > 1 else ""
                                    a_sald = float(v_lib[4]) if len(v_lib) > 4 and v_lib[4] != "" else 0.0
                                    
                                    if hrs_ret > a_sald:
                                        st.error(f"❌ Saldo insuficiente ({a_sald} hrs disponibles).")
                                    else:
                                        ws_b.update_cell(f_idx, 5, str(a_sald - hrs_ret))
                                        ws_h.append_row([f"COMP-{datetime.now().strftime('%y%m%d%H%M%S')}", cod_comp, nom_afec, str(hrs_ret), fec_lib, nombre])
                                        st.success(f"✅ Se descontaron {hrs_ret} horas a **{nom_afec}**.")
                                        st.rerun()

                elif accion_rrhh == "Revertir Compensación (Devolver Horas)":
                    if lista_personal_bolsa:
                        col_r1, col_r2, col_r3 = st.columns([2, 1, 1])
                        with col_r1:
                            sel_rev = st.selectbox("Colaborador a Revertir:", lista_personal_bolsa, key="s_c_rev")
                            cod_rev = sel_rev.split(" - ")[0].strip()
                        with col_r2:
                            hrs_dev = st.number_input("Horas a devolver:", min_value=0.5, step=0.5, value=1.0, key="i_h_r")
                        with col_r3:
                            st.markdown("<br>", unsafe_allow_html=True)
                            btn_rev = st.button("🔄 Devolver", use_container_width=True, key="btn_rev_horas")
                            
                        if btn_rev:
                            ws_b = get_sheet("Bolsa_Horas_Compensacion")
                            c_rev = ws_b.find(cod_rev)
                            if c_rev:
                                f_r = c_rev.row
                                v_r = ws_b.row_values(f_r)
                                nom_r = v_r[1] if len(v_r) > 1 else ""
                                a_sald = float(v_r[4]) if len(v_r) > 4 and v_r[4] != "" else 0.0
                                
                                ws_b.update_cell(f_r, 5, str(a_sald + hrs_dev))
                                get_sheet("Historial_Compensaciones").append_row([f"REV-{datetime.now().strftime('%y%m%d%H%M%S')}", cod_rev, nom_r, f"-{hrs_dev}", datetime.now().strftime("%Y-%m-%d"), f"REVERSIÓN BY {nombre}"])
                                st.success(f"✅ Se devolvieron {hrs_dev} horas al saldo de **{nom_r}**.")
                                st.rerun()
        except Exception as e:
            st.error(f"Error en panel RR.HH.: {e}")

    # =========================================================================
    # PANEL GERENCIAL / RESUMEN MENSUAL Y CONTROL DE ASISTENCIA (RR.HH.)
    # =========================================================================
    if rol in ["Administrador", "JEFE DE TURNO"]:
        st.markdown("---")
        st.subheader("📊 Resumen Mensual y Control de Asistencia (RR.HH.)")
        st.caption("Panel ejecutivo avanzado: días trabajados, feriados, dominicales, inasistencias, licencias, tardanzas y horas calculadas.")
        
        try:
            df_asist_hist = cargar_datos("Asistencia_Personal")
            df_bolsa_hist = cargar_datos("Bolsa_Horas_Compensacion")
            df_users_ref = cargar_datos("Usuarios") # Cargamos la tabla de usuarios para extraer los nombres reales
            
            # Diccionario de respaldo código -> nombre real
            dict_nombres = {}
            if not df_users_ref.empty and "codigo_personal" in df_users_ref.columns and "nombre_completo" in df_users_ref.columns:
                for _, u_row in df_users_ref.iterrows():
                    c_p = str(u_row.get("codigo_personal", "")).strip()
                    n_c = str(u_row.get("nombre_completo", "")).strip()
                    if c_p:
                        dict_nombres[c_p] = n_c
            
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
                            # Obtenemos el nombre real desde el diccionario de usuarios, si no existe usamos el guardado en el grupo
                            nombre_trab = dict_nombres.get(cod_p_clean, grupo.iloc[0].get("nombre_trabajador", f"Colaborador {cod_p_clean}"))
                            
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
                            permisos = obs_serie.str.contains("permiso", case=False, na=False).sum()
                            
                            horas_inasistencia = inasistencias_cnt * 12.0
                            horas_feriados = feriados_cnt * 12.0
                            
                            sald_general = 0.0
                            sald_dominical = 0.0
                            if not df_bolsa_hist.empty and "codigo_personal" in df_bolsa_hist.columns:
                                match_b = df_bolsa_hist[df_bolsa_hist["codigo_personal"].astype(str).str.strip() == cod_p_clean]
                                if not match_b.empty:
                                    sald_general = float(match_b.iloc[0].get("saldo_actual", 0.0))
                                    sald_dominical = float(match_b.iloc[0].get("saldo_dominical", 0.0) if "saldo_dominical" in match_b.columns else 0.0)

                            resumen_list.append({
                                "Código": cod_p_clean,
                                "Colaborador": nombre_trab,
                                "Días Trabajados": dias_trabajados,
                                "Feriados": int(feriados_cnt),
                                "Días Dominicales": int(dominicales_cnt),
                                "Inasistencias": int(inasistencias_cnt),
                                "Días Licencia": int(licencias_cnt),
                                "Compensación": int(compensacion_cnt),
                                "Vacaciones": int(vacaciones),
                                "Tardanzas": int(tardanzas),
                                "Permisos": int(permisos),
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
            st.warning(f"Nota: El módulo de resumen mensual se calibrará con los datos de las columnas. Detalle: {e}")
