import streamlit as st
import pandas as pd
from datetime import datetime

# --- CÁLCULO DE HORAS EXTRAS (REGLA DEFINITIVA FRIGOSA) ---
def calcular_horas_extras(hora_entrada_dt, hora_salida_dt, modo_turno):
    horas_totales_trabajadas = 0.0
    
    # Si la hora de salida es menor o igual a la de entrada, significa que cruzó la medianoche (Turno Noche)
    if hora_salida_dt <= hora_entrada_dt:
        delta = (datetime.combine(datetime.today() + timedelta(days=1), hora_salida_dt) - 
                 datetime.combine(datetime.today(), hora_entrada_dt))
        horas_totales_trabajadas = delta.seconds / 3600.0
    else:
        delta = hora_salida_dt - hora_entrada_dt
        horas_totales_trabajadas = delta.seconds / 3600.0

    horas_pagadas = 0.0
    horas_bolsa = 0.0
    horas_extras_totales = 0.0

    if modo_turno == "Con Producción":
        # Si el turno es de 20:00 a 11:00, son 15 horas trabajadas
        if horas_totales_trabajadas >= 12.0:
            horas_pagadas = 1.0  # 1 hora fija por cumplir las 12 horas de turno
            horas_bolsa = horas_totales_trabajadas - 12.0  # Exceso a la bolsa (ej: 15 - 12 = 3 horas)
            horas_extras_totales = horas_pagadas + horas_bolsa  # Total: 1 + 3 = 4 horas
        else:
            horas_pagadas = 0.0
            horas_bolsa = 0.0
            horas_extras_totales = 0.0
            
    elif modo_turno == "Sin Producción":
        jornada_regular = 8.0 
        if horas_totales_trabajadas > jornada_regular:
            horas_bolsa = horas_totales_trabajadas - jornada_regular
            horas_extras_totales = horas_bolsa
        else:
            horas_bolsa = 0.0
            horas_extras_totales = 0.0
        horas_pagadas = 0.0

    return round(horas_extras_totales, 2), round(horas_pagadas, 2), round(horas_bolsa, 2)
def render_module(user, get_sheet, cargar_datos):
    nombre = user.get("nombre_completo", user.get("usuario"))
    codigo_per = user.get("codigo_personal", "P000")
    rol = user.get("rol", "Visualizador")

    st.subheader("⏱️ Control de Asistencia y Bolsa de Horas")
    st.markdown(f"Colaborador: **{nombre}** | Código: `{codigo_per}` | Rol: `{rol}`")
    
    # 1. VISUALIZADOR DE SALDO Y LISTADO DE HISTORIAL
    try:
        df_bolsa_check = cargar_datos("Bolsa_Horas_Compensacion")
        saldo_usuario = 0.0
        if not df_bolsa_check.empty and "codigo_personal" in df_bolsa_check.columns:
            fila_usu = df_bolsa_check[df_bolsa_check["codigo_personal"].astype(str).str.strip() == codigo_per.strip()]
            if not fila_usu.empty:
                saldo_usuario = float(fila_usu.iloc[0].get("saldo_actual", 0.0))
        
        st.info(f"💼 **Mi Bolsa de Horas Actual:** `{saldo_usuario} horas` disponibles para compensación.")

        df_hist_comp = cargar_datos("Historial_Compensaciones")
        if not df_hist_comp.empty and "codigo_personal" in df_hist_comp.columns:
            df_hist_usu = df_hist_comp[df_hist_comp["codigo_personal"].astype(str).str.strip() == codigo_per.strip()]
            if not df_hist_usu.empty:
                with st.expander("📜 Ver mi Historial de Descansos / Horas Compensadas"):
                    st.dataframe(df_hist_usu, use_container_width=True)
    except Exception as e:
        pass

    st.markdown("---")
    
    col_t1, col_t2 = st.columns(2)
    with col_t1:
        modo_turno = st.selectbox("Modalidad del Turno de Hoy:", ["Sin Producción", "Con Producción"], key="asist_modo_turno")
    with col_t2:
        fecha_actual_str = st.date_input("Fecha de Registro:", datetime.now()).strftime("%Y-%m-%d")
        
    st.markdown("---")
    
    col_reg1, col_reg2 = st.columns(2)
    
    # INGRESO
    with col_reg1:
        st.markdown("#### 📥 Ingreso")
        hora_ingreso_input = st.text_input("Hora de Entrada:", value="20:00", key="h_ingreso_val")
        
        if st.button("Registrar Ingreso", use_container_width=True):
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
            except Exception as e:
                st.error(f"Error al registrar ingreso: {e}")

    # SALIDA
    with col_reg2:
        st.markdown("#### 📤 Salida y Cálculo de Extras")
        hora_salida_input = st.text_input("Hora de Salida:", value="08:00", key="h_salida_val")
        
        try:
            h_in_dt = datetime.strptime(hora_ingreso_input.strip(), "%H:%M")
            h_sal_dt = datetime.strptime(hora_salida_input.strip(), "%H:%M")
            he_tot, h_pag, h_bolsa = calcular_horas_extras(h_in_dt, h_sal_dt, modo_turno)
        except:
            he_tot, h_pag, h_bolsa = 0.0, 0.0, 0.0

        if he_tot > 0:
            st.warning(f"⚠️ Se detectaron **{he_tot} hrs extras** (Pagadas: {h_pag}h | Bolsa: {h_bolsa}h).")
            obs_input = st.text_input("Observación obligatoria del sobretiempo:", key="obs_extra_val")
        else:
            st.info("ℹ️ Jornada regular (Sin horas extras).")
            obs_input = "Jornada Regular"

        if st.button("Registrar Salida y Actualizar Bolsa", use_container_width=True):
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
                    st.warning(f"⚠️ ¡Atención! Su registro de salida para la fecha **{fecha_actual_str}** ya fue procesado y completado anteriormente.")
                elif he_tot > 0 and not obs_input.strip():
                    st.error("❌ La observación es obligatoria cuando se generan horas extras.")
                else:
                    id_registro = f"REG-{datetime.now().strftime('%y%m%d%H%M%S')}"
                    ws_asist.append_row([
                        id_registro, codigo_per, fecha_actual_str, hora_ingreso_input, hora_salida_input, 
                        modo_turno, str(he_tot), str(h_pag), str(h_bolsa), obs_input, "Completado"
                    ])
                    
                    if h_bolsa > 0:
                        ws_bolsa = get_sheet("Bolsa_Horas_Compensacion")
                        try:
                            celda_codigo = ws_bolsa.find(codigo_per.strip())
                        except:
                            celda_codigo = None
                            
                        if celda_codigo:
                            fila_idx = celda_codigo.row
                            vals_fila = ws_bolsa.row_values(fila_idx)
                            actual_acum = float(vals_fila[2]) if len(vals_fila) > 2 and vals_fila[2] != "" else 0.0
                            actual_saldo = float(vals_fila[4]) if len(vals_fila) > 4 and vals_fila[4] != "" else 0.0
                            
                            ws_bolsa.update_cell(fila_idx, 3, str(actual_acum + h_bolsa))
                            ws_bolsa.update_cell(fila_idx, 5, str(actual_saldo + h_bolsa))
                        else:
                            ws_bolsa.append_row([
                                codigo_per, nombre, str(h_bolsa), "0", str(h_bolsa), "", "", "Activo"
                            ])
                            
                    st.success("✅ ¡Salida registrada y bolsa de horas actualizada correctamente!")
            except Exception as e:
                st.error(f"Error al registrar salida: {e}")

    # PANEL RR.HH.
    if rol in ["Administrador", "JEFE DE TURNO"]:
        st.markdown("---")
        st.subheader("🛠️ Panel de RR.HH. - Liberación y Reversión de Horas")
        try:
            df_bolsa_admin = cargar_datos("Bolsa_Horas_Compensacion")
            if not df_bolsa_admin.empty:
                st.markdown("#### 💼 Estado Actual de Bolsas")
                st.dataframe(df_bolsa_admin, use_container_width=True)
                
                lista_personal_bolsa = [f"{r.get('codigo_personal','').strip()} - {r.get('nombre_trabajador','').strip()} (Saldo: {r.get('saldo_actual','0')} hrs)" for _, r in df_bolsa_admin.iterrows()]
                
                accion_rrhh = st.radio("Seleccione acción de RR.HH.:", ["Registrar Compensación (Descontar)", "Revertir Compensación (Devolver Horas por Error)"], horizontal=True)
                
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
                            btn_comp = st.button("Descontar Horas", use_container_width=True)

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
                                    a_comp = float(v_lib[3]) if len(v_lib) > 3 and v_lib[3] != "" else 0.0
                                    a_sald = float(v_lib[4]) if len(v_lib) > 4 and v_lib[4] != "" else 0.0
                                    
                                    if hrs_ret > a_sald:
                                        st.error(f"❌ Saldo insuficiente ({a_sald} hrs disponibles).")
                                    else:
                                        ws_b.update_cell(f_idx, 4, str(a_comp + hrs_ret))
                                        ws_b.update_cell(f_idx, 5, str(a_sald - hrs_ret))
                                        ws_b.update_cell(f_idx, 6, fec_lib)
                                        ws_b.update_cell(f_idx, 7, nombre)
                                        ws_h.append_row([f"COMP-{datetime.now().strftime('%y%m%d%H%M%S')}", cod_comp, nom_afec, str(hrs_ret), fec_lib, nombre])
                                        st.success(f"✅ Se descontaron {hrs_ret} horas a **{nom_afec}**.")
                                        st.rerun()

                elif accion_rrhh == "Revertir Compensación (Devolver Horas por Error)":
                    if lista_personal_bolsa:
                        col_r1, col_r2, col_r3 = st.columns([2, 1, 1])
                        with col_r1:
                            sel_rev = st.selectbox("Colaborador a Revertir:", lista_personal_bolsa, key="s_c_rev")
                            cod_rev = sel_rev.split(" - ")[0].strip()
                        with col_r2:
                            hrs_dev = st.number_input("Horas a devolver:", min_value=0.5, step=0.5, value=1.0, key="i_h_r")
                        with col_r3:
                            st.markdown("<br>", unsafe_allow_html=True)
                            btn_rev = st.button("🔄 Devolver", use_container_width=True)
                            
                        if btn_rev:
                            ws_b = get_sheet("Bolsa_Horas_Compensacion")
                            c_rev = ws_b.find(cod_rev)
                            if c_rev:
                                f_r = c_rev.row
                                v_r = ws_b.row_values(f_r)
                                nom_r = v_r[1] if len(v_r) > 1 else ""
                                a_comp = float(v_r[3]) if len(v_r) > 3 and v_r[3] != "" else 0.0
                                a_sald = float(v_r[4]) if len(v_r) > 4 and v_r[4] != "" else 0.0
                                
                                ws_b.update_cell(f_r, 4, str(max(0.0, a_comp - hrs_dev)))
                                ws_b.update_cell(f_r, 5, str(a_sald + hrs_dev))
                                get_sheet("Historial_Compensaciones").append_row([f"REV-{datetime.now().strftime('%y%m%d%H%M%S')}", cod_rev, nom_r, f"-{hrs_dev}", datetime.now().strftime("%Y-%m-%d"), f"REVERSIÓN POR {nombre}"])
                                st.success(f"✅ Se devolvieron {hrs_dev} horas a **{nom_r}**.")
                                st.rerun()
        except Exception as e:
            st.error(f"Error en panel RR.HH.: {e}")
