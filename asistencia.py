import streamlit as st
import pandas as pd
from datetime import datetime

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
            horas_bolsa_dominical = horas_totales_trabajadas
            horas_extras_totales = horas_totales_trabajadas
    else:
        if modo_turno == "Con Producción":
            if horas_totales_trabajadas >= 12.0:
                horas_pagadas = 1.0
                horas_bolsa_general = horas_totales_trabajadas - 12.0
                horas_extras_totales = horas_pagadas + horas_bolsa_general
        elif modo_turno == "Sin Producción":
            if horas_totales_trabajadas > 8.0:
                horas_bolsa_general = horas_totales_trabajadas - 8.0
                horas_extras_totales = horas_bolsa_general

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
        saldo_general, saldo_dominical = 0.0, 0.0
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
    except Exception:
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

    st.markdown("---")
    
    if tipo_asistencia != "Asistencia Normal (Trabajó)":
        st.warning(f"⚠️ Ha seleccionado **{tipo_asistencia}** para la fecha {fecha_actual_str}.")
        motivo_excepcion = st.text_input("Detalle o motivo adicional (Opcional):", key="obs_excepcion_input")
        
        if st.button(f"💾 Registrar {tipo_asistencia}", use_container_width=True, key="btn_reg_excepcion"):
            try:
                ws_asist = get_sheet("Asistencia_Personal")
                id_reg = f"EXC-{datetime.now().strftime('%y%m%d%H%M%S')}"
                etiqueta = f"EXCEPCIÓN: {tipo_asistencia}" + (f" - {motivo_excepcion}" if motivo_excepcion else "")
                ws_asist.append_row([id_reg, codigo_per, fecha_actual_str, "00:00", "00:00", modo_turno, "0", "0", "0", etiqueta, "Completado"])
                st.success(f"✅ Excepción registrada correctamente.")
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")
    else:
        col_reg1, col_reg2 = st.columns(2)
        with col_reg1:
            st.markdown("#### 📥 Ingreso")
            hora_ingreso_input = st.text_input("Hora de Entrada (Ej: 20:00):", key="h_ingreso_val")
            if st.button("Registrar Ingreso", use_container_width=True, key="btn_reg_ingreso"):
                if not hora_ingreso_input.strip():
                    st.error("Ingrese hora de entrada.")
                else:
                    try:
                        ws_asist = get_sheet("Asistencia_Personal")
                        id_reg = f"REG-{datetime.now().strftime('%y%m%d%H%M%S')}"
                        ws_asist.append_row([id_reg, codigo_per, fecha_actual_str, hora_ingreso_input, "", modo_turno, "0", "0", "0", "Ingreso Registrado", "Pendiente"])
                        st.success("✅ Ingreso registrado exitosamente!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")

        with col_reg2:
            st.markdown("#### 📤 Salida y Cálculo")
            hora_salida_input = st.text_input("Hora de Salida (Ej: 08:00):", key="h_salida_val")
            he_tot, h_pag, h_bg, h_bd = 0.0, 0.0, 0.0, 0.0
            if hora_ingreso_input.strip() and hora_salida_input.strip():
                try:
                    h_in_dt = datetime.strptime(hora_ingreso_input.strip(), "%H:%M")
                    h_sal_dt = datetime.strptime(hora_salida_input.strip(), "%H:%M")
                    he_tot, h_pag, h_bg, h_bd = calcular_horas_extras(h_in_dt, h_sal_dt, modo_turno, es_domingo)
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
                        id_reg = f"REG-{datetime.now().strftime('%y%m%d%H%M%S')}"
                        val_bolsa = h_bd if h_bd > 0 else h_bg
                        ws_asist.append_row([id_reg, codigo_per, fecha_actual_str, hora_ingreso_input, hora_salida_input, modo_turno, str(he_tot), str(h_pag), str(val_bolsa), obs_input, "Completado"])
                        st.success("✅ Salida registrada correctamente!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")

    # =========================================================================
    # ZONA PRINCIPAL PARA TARIADORES / ADMIN: CONTROL DIARIO DE ASISTENCIAS
    # =========================================================================
    if rol in ["Administrador", "JEFE DE TURNO"]:
        st.markdown("---")
        st.subheader("📋 Control Diario de Asistencias (Vista de Turno)")
        st.caption("Monitoreo en tiempo real de los ingresos y salidas registrados por el personal.")
        
        try:
            df_asist_full = cargar_datos("Asistencia_Personal")
            df_users_ref = cargar_datos("Usuarios")
            
            dict_nombres = {}
            if not df_users_ref.empty and "codigo_personal" in df_users_ref.columns and "nombre_completo" in df_users_ref.columns:
                for _, u_row in df_users_ref.iterrows():
                    c_p = str(u_row.get("codigo_personal", "")).strip()
                    n_c = str(u_row.get("nombre_completo", "")).strip()
                    if c_p:
                        dict_nombres[c_p] = n_c

            if not df_asist_full.empty:
                # Mostramos los últimos registros de forma directa
                tabla_mostrada = []
                df_ultimos = df_asist_full.tail(25)
                for _, r in df_ultimos.iterrows():
                    c_code = str(r.get("codigo_personal", "")).strip()
                    n_real = dict_nombres.get(c_code, r.get("nombre_trabajador", f"Colaborador {c_code}"))
                    
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
            else:
                st.info("ℹ️ Aún no hay registros de asistencia guardados.")
        except Exception as e:
            st.warning(f"Error en control diario: {e}")

        # =========================================================================
        # PANEL RR.HH. - GESTIÓN Y COMPENSACIONES
        # =========================================================================
        st.markdown("---")
        st.subheader("🛠️ Panel de RR.HH. - Gestión y Compensaciones")
        try:
            df_bolsa_admin = cargar_datos("Bolsa_Horas_Compensacion")
            if not df_bolsa_admin.empty:
                st.markdown("#### 💼 Estado Actual de Bolsas de Horas")
                st.dataframe(df_bolsa_admin, use_container_width=True)
        except Exception:
            pass

        # =========================================================================
        # PANEL GERENCIAL / RESUMEN MENSUAL
        # =========================================================================
        st.markdown("---")
        st.subheader("📊 Resumen Mensual y Control de Asistencia (RR.HH.)")
        try:
            df_asist_hist = cargar_datos("Asistencia_Personal")
            if not df_asist_hist.empty and "fecha" in df_asist_hist.columns and "codigo_personal" in df_asist_hist.columns:
                col_m1, col_m2 = st.columns(2)
                with col_m1:
                    mes_sel = st.selectbox("Seleccione Mes:", ["01 - Enero", "02 - Febrero", "03 - Marzo", "04 - Abril", "05 - Mayo", "06 - Junio", "07 - Julio", "08 - Agosto", "09 - Setiembre", "10 - Octubre", "11 - Noviembre", "12 - Diciembre"], index=7, key="sel_mes_auditoria_gerencial")
                with col_m2:
                    anio_sel = st.selectbox("Seleccione Año:", ["2026", "2027", "2025"], index=0, key="sel_anio_auditoria_gerencial")
                
                mes_num = mes_sel.split(" - ")[0]
                df_asist_hist["mes"] = df_asist_hist["fecha"].astype(str).str.slice(5, 7)
                df_asist_hist["anio"] = df_asist_hist["fecha"].astype(str).str.slice(0, 4)
                df_filtrado = df_asist_hist[(df_asist_hist["mes"] == mes_num) & (df_asist_hist["anio"] == anio_sel)]
                
                if not df_filtrado.empty:
                    resumen_list = []
                    for cod_p, grupo in df_filtrado.groupby("codigo_personal"):
                        cod_p_clean = str(cod_p).strip()
                        nombre_trab = dict_nombres.get(cod_p_clean, grupo.iloc[0].get("nombre_trabajador", f"Colaborador {cod_p_clean}"))
                        dias_trab = len(grupo[grupo["estado_registro"] == "Completado"])
                        
                        resumen_list.append({
                            "Código": cod_p_clean,
                            "Colaborador": nombre_trab,
                            "Días Registrados": dias_trab
                        })
                    st.dataframe(pd.DataFrame(resumen_list), use_container_width=True)
        except Exception as e:
            st.warning(f"Error en resumen: {e}")
