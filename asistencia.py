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
            # Domingo con producción: misma regla que cualquier día (12h base, 1h pagada, resto a bolsa general)
            if horas_totales_trabajadas >= 12.0:
                horas_pagadas = 1.0
                horas_bolsa_general = horas_totales_trabajadas - 12.0
                horas_extras_totales = horas_pagadas + horas_bolsa_general
            else:
                horas_pagadas = 0.0
                horas_bolsa_general = 0.0
                horas_extras_totales = 0.0
        else:
            # Domingo sin producción: Va exclusivo a la bolsa dominical para canjear por descanso
            horas_pagadas = 0.0
            horas_bolsa_dominical = horas_totales_trabajadas
            horas_extras_totales = horas_totales_trabajadas
    else:
        # Días regulares de semana
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
    
    # 1. VISUALIZADOR DE SALDOS (Bolsa General vs Bolsa Dominical)
    try:
        df_bolsa_check = cargar_datos("Bolsa_Horas_Compensacion")
        saldo_general = 0.0
        saldo_dominical = 0.0
        
        if not df_bolsa_check.empty and "codigo_personal" in df_bolsa_check.columns:
            fila_usu = df_bolsa_check[df_bolsa_check["codigo_personal"].astype(str).str.strip() == codigo_per.strip()]
            if not fila_usu.empty:
                saldo_general = float(fila_usu.iloc[0].get("saldo_actual", 0.0))
                # Si agregamos la columna de saldo dominical o la manejamos dinámicamente
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
        st.warning("📅 **Domingo detectado:** 'Sin Producción' acumulará las horas en tu **Bolsa Dominical** exclusiva para compensar por otro día libre.")

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
                            st.warning(f"⚠️ ¡Atención! Su registro de ingreso para la fecha **{fecha_actual_str}** ya ha sido registrado anteriormente.")
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
                            # Guardamos en la bolsa correspondiente (general o dominical en el campo de bolsa)
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
                                        # Actualizamos columna de saldo dominical (asumiendo columna 5 o creando lógica)
                                        actual_sald_dom = float(vals_fila[5]) if len(vals_fila) > 5 and vals_fila[5] != "" else 0.0
                                        ws_bolsa.update_cell(fila_idx, 6, str(actual_sald_dom + h_bolsa_d))
                                    else:
                                        actual_acum = float(vals_fila[2]) if len(vals_fila) > 2 and vals_fila[2] != "" else 0.0
                                        actual_saldo = float(vals_fila[4]) if len(vals_fila) > 4 and vals_fila[4] != "" else 0.0
                                        ws_bolsa.update_cell(fila_idx, 3, str(actual_acum + h_bolsa_g))
                                        ws_bolsa.update_cell(fila_idx, 5, str(actual_saldo + h_bolsa_g))
                                else:
                                    # Si no existe, creamos la fila inicial
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
                st.markdown("#### 💼 Estado Actual de Bolsas (General y Dominical)")
                st.dataframe(df_bolsa_admin, use_container_width=True)
        except:
            pass
