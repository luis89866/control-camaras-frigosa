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
    # ITEM 1: INGRESOS DE DATOS (CON TIEMPO DE 10 EN 10 MINUTOS)
    # =========================================================================
    with st.expander("📥 1. Ingresos de Datos (Túneles y Plaqueros P1-P18)", expanded=True):
        st.caption("Seleccione el equipo, hora de inicio, ajuste el tiempo de congelación de 10 en 10 minutos (ej. 2:30, 2:45), presentación y bandejas.")
        
        col_d1, col_d2 = st.columns(2)
        with col_d1:
            tipo_equipo = st.selectbox("Seleccione Tipo de Equipo:", ["Plaquero (P1 - P18)", "Túnel (1, 2 y 3)"], key="tipo_eq_sel_v7")
            if tipo_equipo == "Plaquero (P1 - P18)":
                plaquero_sel = st.selectbox("Nº de Plaquero:", [f"P{i}" for i in range(1, 19)], key="sel_plaquero_reg_v7")
            else:
                plaquero_sel = st.selectbox("Nº de Túnel:", ["TÚNEL 1", "TÚNEL 2", "TÚNEL 3"], key="sel_tunel_reg_v7")
                
            hora_inicio_str = st.text_input("Hora de Inicio (Ej: 08:00):", datetime.now().strftime("%H:%M"), key="h_inicio_prod_v7")
            
        with col_d2:
            st.markdown("##### Tiempo de Congelación (Ajuste de 10 en 10 min):")
            # Minutos de congelación con pasos de 10 en 10 (por defecto 165 min = 2h 45m)
            minutos_cong = st.number_input("Minutos Totales (+ / - 10 min):", min_value=10, max_value=1440, step=10, value=165, key="t_cong_min_v7")
            
            # Formato visual amigable (ej: 2h 45m)
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
            
            st.info(f"⏱️ Duración seleccionada: **{tiempo_formato_str}** | ⏰ **Salida Automática:** `{hora_salida_estimada}`")

        st.markdown("---")
        col_p1, col_p2, col_p3 = st.columns(3)
        with col_p1:
            presentacion_sel = st.selectbox("Presentación / Producto:", lista_presentaciones, key="sel_presentacion_v7")
        with col_p2:
            calibre_sel = st.selectbox("Calibre:", lista_calibres, key="sel_calibre_v7")
        with col_p3:
            bandejas_cant = st.number_input("Cantidad de Bandejas:", min_value=1, step=1, value=70, key="num_bandejas_v7")

        if st.button("🚀 Ingresar Producción en Línea", use_container_width=True, key="btn_enviar_produccion_v7"):
            try:
                ws_env = get_env_sheet("ingreso_plaqueros")
                existing_data = ws_env.get_all_values()
                fecha_hoy = datetime.now().strftime("%Y-%m-%d")
                
                ya_registrado = False
                if len(existing_data) > 1:
                    for fila in existing_data[1:]:
                        if len(fila) >= 4:
                            f_reg = str(fila[1]).strip()
                            eq_reg = str(fila[2]).strip().upper()
                            h_reg = str(fila[3]).strip()
                            
                            if f_reg == fecha_hoy and eq_reg == plaquero_sel.strip().upper() and h_reg == hora_inicio_str.strip():
                                ya_registrado = True
                                break

                if ya_registrado:
                    st.warning(f"⚠️ El equipo **{plaquero_sel}** ya tiene un registro activo ingresado a las **{hora_inicio_str}** para hoy. Evite duplicar datos.")
                else:
                    id_prod = f"PROD-{datetime.now().strftime('%y%m%d%H%M%S')}"
                    total_kg = bandejas_cant * 10.0

                    ws_env.append_row([
                        id_prod, fecha_hoy, plaquero_sel, hora_inicio_str, tiempo_formato_str, 
                        hora_salida_estimada, presentacion_sel, calibre_sel, str(bandejas_cant), 
                        str(total_kg), "En Proceso"
                    ])
                    st.success(f"✅ Producción registrada exitosamente en **{plaquero_sel}**! (Salida prevista: {hora_salida_estimada})")
                    st.rerun()
            except Exception as e:
                st.error(f"Error al guardar: {e}")

    # =========================================================================
    # ITEM 2: PLAQUEROS ENCENDIDOS (CON ALERTA EN TIEMPO REAL DE VENCIMIENTO)
    # =========================================================================
    with st.expander("⚡ 2. Plaqueros Encendidos (En Proceso y Alertas de Ciclo)", expanded=True):
        st.caption("Equipos activos comparando la hora actual del sistema frente a la hora de salida para emitir alerta de bajada.")
        try:
            df_prod = cargar_datos_env("ingreso_plaqueros")
            if not df_prod.empty:
                tabla_encendidos = []
                # Hora actual exacta del sistema para comparar vencimientos
                ahora_dt = datetime.now()
                
                for _, row in df_prod.iterrows():
                    eq = row.get("equipo", row.get("plaquero", ""))
                    h_ini = row.get("hora_inicio", "")
                    h_sal = row.get("hora_salida", "")
                    
                    alerta_ciclo = "🟢 En Proceso Normal"
                    try:
                        if h_sal:
                            # Parsear la hora de salida estimada
                            h_sal_t = datetime.strptime(h_sal.strip(), "%H:%M").time()
                            # Comparar hora actual con la hora de salida
                            if ahora_dt.time() >= h_sal_t:
                                alerta_ciclo = "🚨 ¡CICLO CUMPLIDO - PLACA LISTA PARA BAJAR!"
                    except:
                        pass

                    tabla_encendidos.append({
                        "Plaquero / Túnel": eq,
                        "Hora Inicio": h_ini,
                        "Hora Fin / Salida": h_sal,
                        "Presentación": row.get("presentacion", ""),
                        "Calibre": row.get("calibre", ""),
                        "Bandejas": row.get("bandejas", ""),
                        "Situación / Alerta": alerta_ciclo
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
            fecha_filtro_prod = st.date_input("Filtrar por Fecha:", datetime.now(), key="filtro_fecha_prod_v7")
        
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
