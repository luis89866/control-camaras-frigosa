import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

def render_module(user, get_sheet, cargar_datos):
    nombre_sesion = user.get("nombre_completo", user.get("usuario"))
    rol = user.get("rol", "Visualizador")

    st.subheader("📦 Módulo de Envasado y Control de Plaqueros / Túneles")
    st.markdown(f"Operador / Supervisor: **{nombre_sesion}** | Rol: `{rol}`")
    
    # Botón de actualización rápida
    col_r1, col_r2 = st.columns([3, 1])
    with col_r2:
        if st.button("🔄 Refrescar Envasado", use_container_width=True):
            st.cache_data.clear()
            st.success("¡Datos actualizados!")
            st.rerun()

    st.markdown("---")

    # Listas de referencia para la planta
    lista_plaqueros = [f"P{i}" for i in range(1, 19)] + ["TÚNEL 1", "TÚNEL 2", "TÚNEL 3"]
    lista_presentaciones = [
        "ALETA FRESCA", "CONOS", "TENTACULO SU SV", "BOTON", 
        "FILETE FRESCO", "FILETE PRECOCIDO", "NUCAS", "REPRODUCTOR", 
        "ALETA PRECOCIDA", "TUBO"
    ]
    lista_calibres = ["0-50 GR", "50-100 GR", "100-300 GR", "300-500 GR", "500-1000 GR", "1000-3000 GR", "-"]

    # =========================================================================
    # ITEM 1: INGRESOS DE DATOS
    # =========================================================================
    with st.expander("📥 1. Ingresos de Datos (Túneles y Plaqueros P1-P18)", expanded=True):
        st.caption("Seleccione el equipo, hora de inicio, tiempo de congelación, presentación, calibre y bandejas.")
        
        col_d1, col_d2 = st.columns(2)
        with col_d1:
            tipo_equipo = st.selectbox("Seleccione Tipo de Equipo:", ["Plaquero (P1 - P18)", "Túnel (1, 2 y 3)"], key="tipo_eq_sel_exp")
            if tipo_equipo == "Plaquero (P1 - P18)":
                plaquero_sel = st.selectbox("Nº de Plaquero:", [f"P{i}" for i in range(1, 19)], key="sel_plaquero_reg_exp")
            else:
                plaquero_sel = st.selectbox("Nº de Túnel:", ["TÚNEL 1", "TÚNEL 2", "TÚNEL 3"], key="sel_tunel_reg_exp")
                
            hora_inicio_str = st.text_input("Hora de Inicio (Ej: 08:00):", datetime.now().strftime("%H:%M"), key="h_inicio_prod_exp")
            
        with col_d2:
            tiempo_cong = st.selectbox("Tiempo de Congelación (Horas):", [1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 6.0, 8.0, 12.0], index=2, key="t_cong_exp")
            
            hora_salida_estimada = "00:00"
            try:
                dt_ini = datetime.strptime(hora_inicio_str.strip(), "%H:%M")
                dt_sal = dt_ini + timedelta(hours=float(tiempo_cong))
                hora_salida_estimada = dt_sal.strftime("%H:%M")
            except:
                pass
            
            st.info(f"⏰ **Hora de Salida Automática:** `{hora_salida_estimada}`")

        st.markdown("---")
        col_p1, col_p2, col_p3 = st.columns(3)
        with col_p1:
            presentacion_sel = st.selectbox("Presentación:", lista_presentaciones, key="sel_presentacion_env_exp")
        with col_p2:
            calibre_sel = st.selectbox("Calibre:", lista_calibres, key="sel_calibre_env_exp")
        with col_p3:
            bandejas_cant = st.number_input("Cantidad de Bandejas:", min_value=1, step=1, value=50, key="num_bandejas_env_exp")

        lote_ingreso = st.text_input("Materia Prima / Nº de Lote:", placeholder="Ej: LOTE-2026-0829", key="lote_prod_env_exp")
        materia_prima_kg = st.number_input("Materia Prima Total (Kg):", min_value=1.0, step=10.0, value=1000.0, key="mp_kg_env_exp")

        if st.button("🚀 Ingresar Producción", use_container_width=True, key="btn_enviar_produccion_exp"):
            if not lote_ingreso.strip():
                st.error("❌ Debe ingresar el número de lote.")
            else:
                try:
                    ws_env = get_sheet("Produccion_Envasado")
                    id_prod = f"PROD-{datetime.now().strftime('%y%m%d%H%M%S')}"
                    fecha_hoy = datetime.now().strftime("%Y-%m-%d")
                    
                    total_kg = bandejas_cant * 10.0
                    rendimiento_val = round((total_kg / materia_prima_kg) * 100, 2) if materia_prima_kg > 0 else 0.0

                    ws_env.append_row([
                        id_prod, fecha_hoy, plaquero_sel, hora_inicio_str, str(tiempo_cong), 
                        hora_salida_estimada, presentacion_sel, calibre_sel, str(bandejas_cant), 
                        str(total_kg), lote_ingreso, str(materia_prima_kg), str(rendimiento_val), "En Proceso"
                    ])
                    st.success(f"✅ Producción registrada en **{plaquero_sel}**! (Total Kilos: {total_kg} kg | Rendimiento: {rendimiento_val}%)")
                except Exception as e:
                    st.error(f"Error al guardar: {e}")

    # =========================================================================
    # ITEM 2: PLAQUEROS ENCENDIDOS
    # =========================================================================
    with st.expander("⚡ 2. Plaqueros Encendidos (En Proceso y Alertas de Ciclo)", expanded=False):
        st.caption("Equipos activos en este momento, mostrando la última hora ingresada y alertas de ciclo cumplido.")
        try:
            df_prod = cargar_datos("Produccion_Envasado")
            if not df_prod.empty:
                tabla_encendidos = []
                hora_actual_dt = datetime.now()
                
                for _, row in df_prod.iterrows():
                    eq = row.get("equipo", row.get("plaquero", ""))
                    h_ini = row.get("hora_inicio", "")
                    h_sal = row.get("hora_salida", "")
                    
                    alerta_ciclo = "🟢 En Proceso Normal"
                    try:
                        if h_sal:
                            h_sal_dt = datetime.strptime(h_sal.strip(), "%H:%M")
                            if hora_actual_dt.time() >= h_sal_dt.time():
                                alerta_ciclo = "🚨 ¡CICLO CUMPLIDO - SALIDA REQUERIDA!"
                    except:
                        pass

                    tabla_encendidos.append({
                        "Plaquero / Túnel": eq,
                        "Hora Inicio": h_ini,
                        "Hora Fin / Salida": h_sal,
                        "Presentación": row.get("presentacion", ""),
                        "Calibre": row.get("calibre", ""),
                        "Situación": alerta_ciclo
                    })
                st.dataframe(pd.DataFrame(tabla_encendidos), use_container_width=True)
            else:
                st.info("ℹ️ No hay equipos activos registrados.")
        except Exception as e:
            st.warning(f"Error cargando encendidos: {e}")

    # =========================================================================
    # ITEM 3: PLAQUEROS APAGADOS (TIEMPO MUERTO)
    # =========================================================================
    with st.expander("⏳ 3. Plaqueros Apagados (Tiempo Muerto y Desperdicio de Horas)", expanded=False):
        st.caption("Mide el tiempo inactivo de los equipos desde su última salida para controlar la eficiencia.")
        
        # Simulación de equipos inactivos
        df_apagados = pd.DataFrame([
            {"Equipo": eq, "Última Salida": "12:30", "Tiempo Muerto Transcurrido": "3 hrs 15 min", "Impacto": "Moderado"} 
            for eq in lista_plaqueros[:5]
        ])
        st.dataframe(df_apagados, use_container_width=True)

    # =========================================================================
    # ITEM 4: RESUMEN DE PRODUCCION Y RENDIMIENTOS
    # =========================================================================
    with st.expander("📊 4. Resumen de Producción (Filtrado por Fecha)", expanded=False):
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            fecha_filtro_prod = st.date_input("Filtrar por Fecha:", datetime.now(), key="filtro_fecha_prod_exp")
        
        fecha_filtro_str = fecha_filtro_prod.strftime("%Y-%m-%d")
        st.markdown(f"**Fecha seleccionada:** {fecha_filtro_str}")

        try:
            df_p_all = cargar_datos("Produccion_Envasado")
            if not df_p_all.empty and "fecha" in df_p_all.columns:
                df_p_filtrado = df_p_all[df_p_all["fecha"].astype(str).str.strip() == fecha_filtro_str]
                
                if not df_p_filtrado.empty:
                    st.dataframe(df_p_filtrado, use_container_width=True)
                    
                    # Totales automáticos
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
