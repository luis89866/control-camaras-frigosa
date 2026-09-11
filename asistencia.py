import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

def formatear_horas_minutos_texto(minutos_totales):
    """Retorna formato legible 'Xh Ym' (ej: 103 min -> '1h 43m')."""
    if minutos_totales <= 0:
        return "0h 00m"
    h = int(minutos_totales // 60)
    m = int(round(minutos_totales % 60))
    if m >= 60:
        h += m // 60
        m = m % 60
    return f"{h}h {m:02d}m"

def minutos_a_formato_punto(minutos_totales):
    """
    Convierte minutos a formato numérico H.MM:
    103 minutos -> 1 hora y 43 minutos -> 1.43
    256 minutos -> 4 horas y 16 minutos -> 4.16
    """
    if minutos_totales <= 0:
        return 0.0
    h = int(minutos_totales // 60)
    m = int(round(minutos_totales % 60))
    if m >= 60:
        h += m // 60
        m = m % 60
    return round(h + (m / 100.0), 2)

def formato_punto_a_minutos(val_hmm):
    """
    Convierte formato numérico H.MM a minutos netos:
    2.42 -> 2 horas y 42 minutos -> 162 minutos
    1.34 -> 1 hora y 34 minutos -> 94 minutos
    """
    try:
        val = float(val_hmm or 0.0)
    except Exception:
        return 0
    if val <= 0:
        return 0
    h = int(val)
    m = int(round((val - h) * 100))
    return (h * 60) + m

def sumar_horas_minutos_formato(serie_o_lista):
    """Suma múltiples valores en formato H.MM respetando base 60."""
    total_min = 0
    for v in serie_o_lista:
        total_min += formato_punto_a_minutos(v)
    return minutos_a_formato_punto(total_min)

def calcular_horas_extras(hora_entrada_dt, hora_salida_dt, modo_turno, es_domingo, es_sabado):
    minutos_salida = hora_salida_dt.hour * 60 + hora_salida_dt.minute
    minutos_entrada = hora_entrada_dt.hour * 60 + hora_entrada_dt.minute
    
    # Manejo de amanecida / cambio de día
    if minutos_salida <= minutos_entrada:
        minutos_trabajados = (1440 - minutos_entrada) + minutos_salida
    else:
        minutos_trabajados = minutos_salida - minutos_entrada

    minutos_pagados = 0
    minutos_bolsa_general = 0
    minutos_bolsa_dominical = 0

    if es_domingo:
        if modo_turno == "Con Producción":
            if minutos_trabajados >= 720:  # 12 horas base
                minutos_pagados = 60       # 1 hora fija pagada
                minutos_bolsa_general = minutos_trabajados - 720
        else:
            minutos_bolsa_dominical = minutos_trabajados
    else:
        if modo_turno == "Con Producción":
            if minutos_trabajados >= 720:  # 12 horas base
                minutos_pagados = 60       # 1 hora fija pagada
                minutos_bolsa_general = minutos_trabajados - 720
        elif modo_turno == "Sin Producción":
            limite_normal_minutos = (15 * 60) if es_sabado else (18 * 60)
            if minutos_salida > limite_normal_minutos:
                minutos_bolsa_general = minutos_salida - limite_normal_minutos
        elif modo_turno == "Sin Producción - Renganche":
            jornada_minutos = 9 * 60
            if minutos_trabajados > jornada_minutos:
                minutos_bolsa_general = minutos_trabajados - jornada_minutos

    minutos_extras_totales = minutos_pagados + minutos_bolsa_general + minutos_bolsa_dominical

    he_tot_val = minutos_a_formato_punto(minutos_extras_totales)
    h_pag_val = minutos_a_formato_punto(minutos_pagados)
    h_bg_val = minutos_a_formato_punto(minutos_bolsa_general)
    h_bd_val = minutos_a_formato_punto(minutos_bolsa_dominical)
    
    texto_h_m = formatear_horas_minutos_texto(minutos_extras_totales)

    return he_tot_val, h_pag_val, h_bg_val, h_bd_val, texto_h_m

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
    # CALCULADORA RÁPIDA DE SALIDA (RENGANCHE 9 HRS)
    # =========================================================================
    with st.expander("🧮 Calculadora Rápida de Salida (Turnos Especiales / Renganche)"):
        st.caption("Calcula la hora exacta de salida sumando las horas de jornada.")
        c_calc1, c_calc2, c_calc3 = st.columns(3)
        with c_calc1:
            hora_ing_calc = st.text_input("Hora de Ingreso (Ej: 12:00):", "12:00", key="calc_h_ing")
        with c_calc2:
            horas_a_cubrir = st.number_input("Horas a Cubrir:", min_value=4.0, max_value=14.0, step=0.5, value=9.0, key="calc_hrs_cubrir")
        with c_calc3:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Calcular Hora de Salida", key="btn_ejecutar_calc"):
                try:
                    dt_ing_calc = datetime.strptime(hora_ing_calc.strip(), "%H:%M")
                    dt_sal_calc = dt_ing_calc + timedelta(hours=float(horas_a_cubrir))
                    st.success(f"🎯 Hora de Salida Sugerida: **{dt_sal_calc.strftime('%H:%M')}**")
                except Exception:
                    st.error("Formato de hora inválido. Use HH:MM.")

    # 1. VISUALIZADOR DE SALDOS (Lee las fórmulas automáticas de Sheets)
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
        
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            st.info(f"💼 **Bolsa de Horas Extras ({nombre}):** `{saldo_general}` hrs disponibles.")
        with col_s2:
            st.success(f"📅 **Bolsa Dominical:** `{saldo_dominical}` hrs disponibles.")
    except Exception:
        pass

    st.markdown("---")
    
    col_t1, col_t2, col_t3 = st.columns(3)
    with col_t1:
        modo_turno = st.selectbox("Modalidad del Turno:", ["Con Producción", "Sin Producción", "Sin Producción - Renganche"], key="asist_modo_turno")
    with col_t2:
        fecha_obj = st.date_input("Fecha de Registro:", datetime.now(), key="asist_fecha_reg")
        fecha_actual_str = fecha_obj.strftime("%Y-%m-%d")
        es_domingo = (fecha_obj.weekday() == 6)
        es_sabado = (fecha_obj.weekday() == 5)
        
        dia_semana_nombres = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
        nombre_dia_actual = dia_semana_nombres[fecha_obj.weekday()]
        st.caption(f"📅 Día: **{nombre_dia_actual}**")
    with col_t3:
        tipo_asistencia = st.selectbox(
            "Estado del Día:", 
            ["Asistencia Normal (Trabajó)", "Feriado", "Licencia", "Permiso", "Compensación", "Vacaciones", "Descanso Médico", "Inasistencia / Falta"],
            key="asist_tipo_dia"
        )

    st.markdown("---")
    
    if tipo_asistencia != "Asistencia Normal (Trabajó)":
        st.warning(f"⚠️ Ha seleccionado **{tipo_asistencia}** para **{nombre}** en la fecha {fecha_actual_str}.")
        motivo_excepcion = st.text_input("Detalle o motivo adicional (Opcional):", key="obs_excepcion_input")
        
        es_tardanza = st.checkbox("¿Registrar con tardanza?", key="chk_es_tardanza")
        minutos_tardanza = st.number_input("Tiempo de tardanza (minutos):", min_value=1, step=5, value=15, key="num_min_tardanza") if es_tardanza else 0

        if st.button(f"💾 Registrar {tipo_asistencia}", use_container_width=True, key="btn_reg_excepcion"):
            try:
                ws_asist = get_sheet("Asistencia_Personal")
                id_reg = f"EXC-{datetime.now().strftime('%y%m%d%H%M%S')}"
                etiqueta = f"EXCEPCIÓN: {tipo_asistencia}" + (f" - Tardanza: {minutos_tardanza} min" if es_tardanza else "") + (f" - {motivo_excepcion}" if motivo_excepcion else "")
                
                ws_asist.append_row([
                    id_reg, codigo_per, nombre, fecha_actual_str, 
                    "00:00", "00:00", modo_turno, 
                    0.0, 0.0, 0.0, 
                    etiqueta, "Completado"
                ])
                st.success(f"✅ Excepción registrada correctamente para {nombre}.")
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")
    else:
        col_reg1, col_reg2 = st.columns(2)
        with col_reg1:
            st.markdown(f"#### 📥 Ingreso ({nombre})")
            hora_ingreso_input = st.text_input("Hora de Entrada (Ej: 08:00):", key="h_ingreso_val")
            
            es_tardanza_ing = st.checkbox("¿Ingreso con tardanza?", key="chk_ing_tardanza")
            min_tard_ing = st.number_input("Minutos de tardanza:", min_value=1, step=5, value=15, key="num_tard_ing_val") if es_tardanza_ing else 0

            if st.button("Registrar Ingreso", use_container_width=True, key="btn_reg_ingreso"):
                if not hora_ingreso_input.strip():
                    st.error("Ingrese hora de entrada.")
                else:
                    try:
                        ws_asist = get_sheet("Asistencia_Personal")
                        id_reg = f"REG-{datetime.now().strftime('%y%m%d%H%M%S')}"
                        obs_ing = "Ingreso Registrado" + (f" - Tardanza: {min_tard_ing} min" if es_tardanza_ing else "")
                        
                        ws_asist.append_row([
                            id_reg, codigo_per, nombre, fecha_actual_str, 
                            hora_ingreso_input.strip(), "", modo_turno, 
                            0.0, 0.0, 0.0, 
                            obs_ing, "Pendiente"
                        ])
                        st.success(f"✅ Ingreso registrado exitosamente para {nombre}!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")

        with col_reg2:
            st.markdown(f"#### 📤 Salida y Cálculo ({nombre})")
            hora_salida_input = st.text_input("Hora de Salida (Ej: 21:43):", key="h_salida_val")
            he_tot, h_pag, h_bg, h_bd = 0.0, 0.0, 0.0, 0.0
            texto_extra_fmt = "0h 00m"
            
            if hora_ingreso_input.strip() and hora_salida_input.strip():
                try:
                    h_in_dt = datetime.strptime(hora_ingreso_input.strip(), "%H:%M")
                    h_sal_dt = datetime.strptime(hora_salida_input.strip(), "%H:%M")
                    he_tot, h_pag, h_bg, h_bd, texto_extra_fmt = calcular_horas_extras(h_in_dt, h_sal_dt, modo_turno, es_domingo, es_sabado)
                    if he_tot > 0:
                        st.info(f"⏱️ Tiempo extra: **{texto_extra_fmt}** (Registra: `{he_tot}`)")
                except Exception:
                    pass

            obs_input = st.text_input("Motivo u observación operativa:", key="obs_extra_val", placeholder="Ej: Apoyo en cámaras") if he_tot > 0 else "Jornada Regular"
            if es_domingo:
                obs_input = f"[DOMINICAL] {obs_input}"

            if st.button("Registrar Salida y Guardar", use_container_width=True, key="btn_reg_salida"):
                if not hora_salida_input.strip():
                    st.error("Ingrese hora de salida.")
                else:
                    try:
                        ws_asist = get_sheet("Asistencia_Personal")
                        val_bolsa = h_bd if h_bd > 0 else h_bg
                        id_reg = f"REG-{datetime.now().strftime('%y%m%d%H%M%S')}"

                        fila_datos = [
                            id_reg,                             # A: id_registro
                            str(codigo_per).strip(),            # B: codigo_personal
                            str(nombre).strip(),                # C: nombre_personal
                            str(fecha_actual_str).strip(),      # D: fecha
                            str(hora_ingreso_input).strip(),    # E: hora_entrada
                            str(hora_salida_input).strip(),     # F: hora_salida
                            str(modo_turno).strip(),            # G: modo_turno
                            float(he_tot),                      # H: horas_extras_totales
                            float(h_pag),                       # I: horas_pagadas
                            float(val_bolsa),                   # J: horas_bolsa
                            str(obs_input).strip(),             # K: observacion
                            "Completado"                        # L: estado_registro
                        ]
                        
                        # Solo se escribe en Asistencia_Personal
                        ws_asist.append_row(fila_datos)

                        st.success(f"✅ Salida registrada para {nombre}: {he_tot} (Total) | {val_bolsa} (Bolsa)!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")

    # =========================================================================
    # 1. ZONA: CONTROL DIARIO PARA EL TARIADOR
    # =========================================================================
    st.markdown("---")
    st.subheader("📋 Control Diario de Asistencias (Vista de Turno)")
    
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
                        "H. Extras": r.get("horas_extras_totales"),
                        "H. Pagadas": r.get("horas_pagadas"),
                        "H. Bolsa": r.get("horas_bolsa"),
                        "Estado": r.get("estado_registro"),
                        "Observación": r.get("observacion")
                    })
                st.dataframe(pd.DataFrame(tabla_mostrada), use_container_width=True)
            else:
                st.info(f"ℹ️ No hay registros para {fecha_filtro_str}.")
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
                st.dataframe(df_bolsa_admin, use_container_width=True)
            
            if lista_personal_opciones:
                tab_v, tab_l, tab_c, tab_reg = st.tabs(["🌴 Vacaciones por Rango", "📜 Licencias por Rango", "⚖️ Compensación con Bolsa", "⚙️ Regularizar Bolsa"])
                
                with tab_v:
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
                        if fec_fin_v >= fec_ini_v:
                            try:
                                ws_asist = get_sheet("Asistencia_Personal")
                                delta_dias = (fec_fin_v - fec_ini_v).days + 1
                                current_d = fec_ini_v
                                for c_idx in range(delta_dias):
                                    f_str = current_d.strftime("%Y-%m-%d")
                                    id_reg = f"VAC-{datetime.now().strftime('%y%m%d%H%M%S')}-{c_idx}"
                                    ws_asist.append_row([
                                        id_reg, cod_vac, nom_vac, f_str, "00:00", "00:00", "Sin Producción", 0.0, 0.0, 0.0, "EXCEPCIÓN: Vacaciones", "Completado"
                                    ])
                                    current_d += timedelta(days=1)
                                st.success("✅ Vacaciones registradas.")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error: {e}")

                with tab_l:
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
                        motivo_lic = st.text_input("Motivo:", key="motivo_lic_txt")
                    
                    if st.button("💾 Guardar Licencia por Rango", key="btn_guardar_licencia"):
                        if fec_fin_l >= fec_ini_l:
                            try:
                                ws_asist = get_sheet("Asistencia_Personal")
                                delta_dias_l = (fec_fin_l - fec_ini_l).days + 1
                                current_dl = fec_ini_l
                                for c_idx in range(delta_dias_l):
                                    f_str_l = current_dl.strftime("%Y-%m-%d")
                                    id_reg_l = f"LIC-{datetime.now().strftime('%y%m%d%H%M%S')}-{c_idx}"
                                    detalle_lic = f"EXCEPCIÓN: Licencia - {motivo_lic}" if motivo_lic else "EXCEPCIÓN: Licencia"
                                    ws_asist.append_row([
                                        id_reg_l, cod_lic, nom_lic, f_str_l, "00:00", "00:00", "Sin Producción", 0.0, 0.0, 0.0, detalle_lic, "Completado"
                                    ])
                                    current_dl += timedelta(days=1)
                                st.success("✅ Licencia registrada.")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error: {e}")

                with tab_c:
                    col_c1, col_c2, col_c3, col_c4, col_c5 = st.columns([1.5, 1, 1, 1, 1])
                    with col_c1:
                        sel_col_comp = st.selectbox("Colaborador:", lista_personal_opciones, key="s_col_comp")
                        cod_comp = sel_col_comp.split(" - ")[0].strip()
                        nom_comp = sel_col_comp.split(" - ")[1].strip()
                    with col_c2:
                        hrs_ret = st.number_input("Horas a descontar (ej: 1.30 = 1h 30m):", min_value=0.01, step=0.5, value=8.0, key="i_h_c")
                    with col_c3:
                        fec_ini_c = st.date_input("Fecha Inicio:", datetime.now(), key="i_f_ini_c")
                    with col_c4:
                        fec_fin_c = st.date_input("Fecha Fin:", datetime.now(), key="i_f_fin_c")
                    with col_c5:
                        st.markdown("<br>", unsafe_allow_html=True)
                        btn_comp = st.button("⚖️ Descontar Bolsa", use_container_width=True, key="btn_desc_horas")

                    if btn_comp and fec_fin_c >= fec_ini_c:
                        try:
                            # Solo registra en el historial y asistencia; la bolsa se calcula sola en Sheets
                            ws_h = get_sheet("Historial_Compensaciones")
                            ws_h.append_row([
                                f"COMP-{datetime.now().strftime('%y%m%d%H%M%S')}", cod_comp, nom_comp, float(hrs_ret), f"{fec_ini_c} al {fec_fin_c}", f"AUTORIZADO BY {nombre_sesion}"
                            ])
                            
                            ws_asist = get_sheet("Asistencia_Personal")
                            delta_c = (fec_fin_c - fec_ini_c).days + 1
                            curr_c = fec_ini_c
                            for c_i in range(delta_c):
                                f_str_c = curr_c.strftime("%Y-%m-%d")
                                id_reg_c = f"COMPD-{datetime.now().strftime('%y%m%d%H%M%S')}-{c_i}"
                                ws_asist.append_row([
                                    id_reg_c, cod_comp, nom_comp, f_str_c, 
                                    "00:00", "00:00", "Sin Producción", 
                                    0.0, 0.0, 0.0, 
                                    "EXCEPCIÓN: Compensación de Horas", "Completado"
                                ])
                                curr_c += timedelta(days=1)

                            st.success(f"✅ Se registraron {hrs_ret} hrs compensadas para {nom_comp}.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")

                with tab_reg:
                    col_r1, col_r2, col_r3, col_r4 = st.columns([1.5, 1, 1, 1.5])
                    with col_r1:
                        sel_col_reg = st.selectbox("Colaborador:", lista_personal_opciones, key="s_col_reg")
                        cod_reg = sel_col_reg.split(" - ")[0].strip()
                        nom_reg = sel_col_reg.split(" - ")[1].strip()
                    with col_r2:
                        tipo_ajuste = st.selectbox("Acción:", ["Sumar Horas (+)", "Restar Horas (-)"], key="sel_tipo_ajuste")
                    with col_r3:
                        cant_horas_reg = st.number_input("Cantidad:", min_value=0.01, step=0.5, value=1.0, key="num_horas_reg")
                    with col_r4:
                        motivo_reg = st.text_input("Motivo:", key="txt_motivo_reg")
                    
                    if st.button("⚙️ Aplicar Regularización", key="btn_aplicar_regularizacion"):
                        try:
                            # Solo registra en el historial; no toca celdas en Bolsa_Horas_Compensacion
                            signo_str = f"+{cant_horas_reg}" if tipo_ajuste == "Sumar Horas (+)" else f"-{cant_horas_reg}"
                            ws_h = get_sheet("Historial_Compensaciones")
                            ws_h.append_row([
                                f"REGUL-{datetime.now().strftime('%y%m%d%H%M%S')}", 
                                cod_reg, 
                                nom_reg, 
                                signo_str, 
                                datetime.now().strftime("%Y-%m-%d"), 
                                f"REGULARIZACIÓN: {motivo_reg} (By {nombre_sesion})"
                            ])
                            st.success(f"✅ Regularización guardada en historial para {nom_reg}.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")

        except Exception as e:
            st.warning(f"Nota en panel RR.HH.: {e}")

        # =========================================================================
        # 3. PANEL GERENCIAL / RESUMEN MENSUAL COMPLETO
        # =========================================================================
        st.markdown("---")
        st.subheader("📊 Resumen Mensual y Control de Asistencia (RR.HH.)")
        
        try:
            df_asist_hist = cargar_datos("Asistencia_Personal")
            df_bolsa_hist = cargar_datos("Bolsa_Horas_Compensacion")
            
            if not df_asist_hist.empty:
                col_f1, col_f2 = st.columns(2)
                with col_f1:
                    mes_sel = st.selectbox("Mes de Auditoría:", ["01 - Enero", "02 - Febrero", "03 - Marzo", "04 - Abril", "05 - Mayo", "06 - Junio", "07 - Julio", "08 - Agosto", "09 - Setiembre", "10 - Octubre", "11 - Noviembre", "12 - Diciembre"], index=8, key="sel_mes_auditoria_gerencial")
                with col_f2:
                    anio_sel = st.selectbox("Año:", ["2026", "2027", "2025"], index=0, key="sel_anio_auditoria_gerencial")
                
                mes_num = mes_sel.split(" - ")[0]
                
                if "fecha" in df_asist_hist.columns and "codigo_personal" in df_asist_hist.columns:
                    df_asist_hist["mes"] = df_asist_hist["fecha"].astype(str).str.slice(5, 7)
                    df_asist_hist["anio"] = df_asist_hist["fecha"].astype(str).str.slice(0, 4)
                    
                    df_filtrado = df_asist_hist[(df_asist_hist["mes"] == mes_num) & (df_asist_hist["anio"] == anio_sel)]
                    
                    if not df_filtrado.empty:
                        resumen_list = []
                        for cod_p, grupo in df_filtrado.groupby("codigo_personal"):
                            cod_p_clean = str(cod_p).strip()
                            nombre_trab = dict_nombres.get(cod_p_clean, grupo.iloc[0].get("nombre_personal", f"Colaborador {cod_p_clean}"))
                            obs_serie = grupo["observacion"].astype(str)
                            
                            dias_trabajados = len(grupo[(grupo["estado_registro"] == "Completado") & (~obs_serie.str.contains("EXCEPCIÓN:", case=False, na=False))])
                            
                            # Suma sexagesimal correcta en base a minutos
                            horas_bolsa_acum = sumar_horas_minutos_formato(grupo["horas_bolsa"])
                            horas_pagadas_acum = sumar_horas_minutos_formato(grupo["horas_pagadas"])
                            
                            resumen_list.append({
                                "Código": cod_p_clean,
                                "Colaborador": nombre_trab,
                                "Días Trabajados": dias_trabajados,
                                "H. Pagadas (25%)": horas_pagadas_acum,
                                "H. Compensación (35%)": horas_bolsa_acum
                            })
                        
                        st.dataframe(pd.DataFrame(resumen_list), use_container_width=True)
        except Exception as e:
            st.warning(f"Nota en resumen mensual: {e}")
