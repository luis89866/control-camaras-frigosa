# =========================================================================
# HOJA DISTRIBUCIONES (GUARDADO POR ID_EMBARQUE Y HASTA COLUMNA AX: 50 COLS)
# =========================================================================
def obtener_hoja_distribuciones(get_gspread_client):
    client = get_gspread_client()
    try:
        sh = client.open_by_key(ID_SPREADSHEET_PRODUCCION)
    except Exception:
        sh = client.open("BD_PRODUCCION_ARCHI_001")
    return sh.worksheet("DISTRIBUCIONES")

def guardar_o_actualizar_contenedor(get_gspread_client, datos_fila, forzar_nuevo=False):
    try:
        ws = obtener_hoja_distribuciones(get_gspread_client)
        col_a_ids = ws.col_values(1)       # Columna A: ID_EMBARQUE
        col_b_conts = ws.col_values(2)     # Columna B: CONTENEDOR
        
        target_id = str(datos_fila[0]).strip().upper()
        target_cont = str(datos_fila[1]).strip().upper()

        fila_idx = None

        if not forzar_nuevo and target_id:
            for idx, id_val in enumerate(col_a_ids):
                if str(id_val).strip().upper() == target_id and idx > 0:
                    fila_idx = idx + 1
                    break

        if fila_idx is None:
            for idx, c_val in enumerate(col_b_conts):
                if str(c_val).strip().upper() == target_cont and idx > 0:
                    fila_idx = idx + 1
                    break

        datos_limpios = []
        for val in datos_fila:
            if isinstance(val, (date, datetime)):
                datos_limpios.append(str(val))
            elif isinstance(val, (int, float)):
                datos_limpios.append(val)
            elif val is None:
                datos_limpios.append("")
            else:
                datos_limpios.append(str(val))

        while len(datos_limpios) < 50:
            datos_limpios.append("")
        datos_limpios = datos_limpios[:50]

        if fila_idx:
            rango_exacto = f"A{fila_idx}:AX{fila_idx}"
            try:
                ws.update(range_name=rango_exacto, values=[datos_limpios])
            except Exception:
                ws.update(rango_exacto, [datos_limpios])
            return True, f"Contenedor '{target_cont}' actualizado exitosamente en la fila {fila_idx}."
        else:
            siguiente_fila = max(len(col_a_ids), len(col_b_conts)) + 1
            rango_nuevo = f"A{siguiente_fila}:AX{siguiente_fila}"
            try:
                ws.update(range_name=rango_nuevo, values=[datos_limpios])
            except Exception:
                ws.update(rango_nuevo, [datos_limpios])
            return True, f"Contenedor '{target_cont}' registrado exitosamente en la fila {siguiente_fila}."

    except Exception as e:
        return False, f"Error en Google Sheets: {str(e)}"

# =========================================================================
# FUNCIÓN PRINCIPAL DE ENTRADA (NIVEL RAÍZ)
# =========================================================================
def render_module(user, get_gspread_client):
    st.subheader("🚢 Módulo de Despachos, Estiba y Embarques")

    if "form_version" not in st.session_state:
        st.session_state.form_version = 0

    if "emb_id" not in st.session_state:
        st.session_state.emb_id = f"EMB-{datetime.now().strftime('%y%m%d%H%M%S')}"
    if "cont_val" not in st.session_state:
        st.session_state.cont_val = ""
    if "fec_val" not in st.session_state:
        st.session_state.fec_val = date.today()
    if "mes_val" not in st.session_state:
        st.session_state.mes_val = MESES_ESP.get(date.today().month, "SETIEMBRE")
    if "pi_val" not in st.session_state:
        st.session_state.pi_val = ""
    if "bk_val" not in st.session_state:
        st.session_state.bk_val = ""
    if "cli_val" not in st.session_state:
        st.session_state.cli_val = "Shandong sheenier"
    if "dest_val" not in st.session_state:
        st.session_state.dest_val = "Yantai china"
    if "pais_val" not in st.session_state:
        st.session_state.pais_val = "CHINA"
    if "pay_val" not in st.session_state:
        st.session_state.pay_val = 30400.0

    if "nfil_val" not in st.session_state:
        st.session_state.nfil_val = 18
    if "capg_val" not in st.session_state:
        st.session_state.capg_val = 75
    if "capf1_val" not in st.session_state:
        st.session_state.capf1_val = 75
    if "capfu_val" not in st.session_state:
        st.session_state.capfu_val = 75
    if "wstd_val" not in st.session_state:
        st.session_state.wstd_val = 20.00

    if "modalidad_cap_selector" not in st.session_state:
        st.session_state["modalidad_cap_selector"] = "Modo Estándar (Fila 1, Centro y Puerta)"

    if "tipo_envase_val" not in st.session_state:
        st.session_state.tipo_envase_val = "Saco"
    if "tara_insumos_val" not in st.session_state:
        st.session_state.tara_insumos_val = 0.15
    if "bloques_bulto_val" not in st.session_state:
        st.session_state.bloques_bulto_val = 2

    if "peso_saco_hist" not in st.session_state:
        st.session_state.peso_saco_hist = 0.0
    if "peso_block_hist" not in st.session_state:
        st.session_state.peso_block_hist = 0.0
    if "plus_hist" not in st.session_state:
        st.session_state.plus_hist = 0.0

    if "pres_items" not in st.session_state:
        st.session_state.pres_items = [
            {"nombre": "FF C/M C/T 2000 g/pza - 4000 g/pza MANTO ", "bultos": 800, "peso": 20.00},
            {"nombre": "FF C/M C/T 2000 g/pza - 4000 g/pza CORTADO ", "bultos": 550, "peso": 20.00}
        ]
    if "lotes_items" not in st.session_state:
        st.session_state.lotes_items = [
            {"fecha": date.today(), "lote": generar_lote_juliano(date.today()), "bultos": 650},
            {"fecha": date.today(), "lote": generar_lote_juliano(date.today()), "bultos": 700}
        ]
    if "txt_pesos_mem" not in st.session_state:
        st.session_state.txt_pesos_mem = {}

    if "fotos_contenedor_db" not in st.session_state:
        st.session_state.fotos_contenedor_db = {}

    v = st.session_state.form_version

    # =========================================================================
    # BARRA SUPERIOR DE SELECCIÓN Y CONTROLES
    # =========================================================================
    c_btn_c2 = None
    col_sel1, col_sel2 = st.columns([3, 1])
    with col_sel1:
        try:
            ws_d = obtener_hoja_distribuciones(get_gspread_client)
            registros = ws_d.get_all_values()
        except Exception:
            registros = []

        modo_operacion = st.radio(
            "Modo de Trabajo:",
            ["Nuevo Contenedor", "Cargar / Editar Contenedor Existente"],
            horizontal=True
        )

        if modo_operacion == "Cargar / Editar Contenedor Existente" and len(registros) > 1:
            st.markdown("##### 🔍 Buscar Contenedor Registrado")
            c_f1, c_f2 = st.columns([1.5, 2])
            with c_f1:
                ver_todos = st.checkbox("Ver todo el histórico", value=False)
                if not ver_todos:
                    fecha_filtro = st.date_input("Filtrar por Fecha:", value=date.today(), key="f_filtro_cont")
            
            opciones_conts = []
            for r in registros[1:]:
                if len(r) > 3 and r[1].strip():
                    c_num = r[1].strip()
                    c_fec = r[3].strip()
                    c_cli = r[6].strip() if len(r) > 6 else ""
                    if ver_todos or c_fec == str(fecha_filtro):
                        opciones_conts.append((c_num, f"{c_num} | {c_fec} | {c_cli}"))

            with c_f2:
                if opciones_conts:
                    map_display = {disp: c_id for c_id, disp in opciones_conts}
                    sel_display = st.selectbox("Seleccionar Contenedor:", list(map_display.keys()))
                    cont_seleccionado = map_display[sel_display]
                else:
                    st.info("No hay contenedores en la fecha seleccionada.")
                    cont_seleccionado = None

            c_btn_c1, c_btn_c2 = st.columns([1.5, 2])
            with c_btn_c1:
                btn_cargar_datos = st.button("📥 Cargar en Pantalla", use_container_width=True) if cont_seleccionado else False
            with c_btn_c2:
                btn_refrescar_datos = st.button("🔄 Refrescar Datos del Contenedor", use_container_width=True) if cont_seleccionado else False

            if btn_cargar_datos or btn_refrescar_datos:
                fila_encontrada = None
                for r in registros[1:]:
                    if len(r) > 1 and r[1].strip() == cont_seleccionado:
                        fila_encontrada = r
                        break

                if fila_encontrada:
                    st.session_state.emb_id = fila_encontrada[0]
                    num_c_cargado = fila_encontrada[1].strip()
                    st.session_state.cont_val = num_c_cargado
                    st.session_state.mes_val = fila_encontrada[2].strip() if len(fila_encontrada) > 2 and fila_encontrada[2].strip() else "SETIEMBRE"
                    
                    try:
                        st.session_state.fec_val = datetime.strptime(fila_encontrada[3].strip(), "%Y-%m-%d").date()
                    except Exception:
                        st.session_state.fec_val = date.today()

                    st.session_state.pi_val = fila_encontrada[4].strip() if len(fila_encontrada) > 4 else ""
                    st.session_state.bk_val = fila_encontrada[5].strip() if len(fila_encontrada) > 5 else ""
                    st.session_state.cli_val = fila_encontrada[6].strip() if len(fila_encontrada) > 6 else ""
                    st.session_state.dest_val = fila_encontrada[7].strip() if len(fila_encontrada) > 7 else ""
                    st.session_state.pais_val = fila_encontrada[8].strip() if len(fila_encontrada) > 8 else "CHINA"

                    try:
                        st.session_state.pay_val = float(fila_encontrada[26]) if len(fila_encontrada) > 26 and fila_encontrada[26].strip() else 30400.0
                    except Exception:
                        st.session_state.pay_val = 30400.0

                    try:
                        if len(fila_encontrada) > 35 and fila_encontrada[35].strip():
                            st.session_state.nfil_val = int(fila_encontrada[35].strip())
                        if len(fila_encontrada) > 36 and fila_encontrada[36].strip():
                            st.session_state.capg_val = int(fila_encontrada[36].strip())
                        if len(fila_encontrada) > 37 and fila_encontrada[37].strip():
                            st.session_state.capf1_val = int(fila_encontrada[37].strip())
                        if len(fila_encontrada) > 38 and fila_encontrada[38].strip():
                            st.session_state.capfu_val = int(fila_encontrada[38].strip())
                        if len(fila_encontrada) > 39 and fila_encontrada[39].strip():
                            st.session_state.wstd_val = float(fila_encontrada[39].strip())

                        target_filas_cargadas = int(st.session_state.nfil_val)

                        # EVALUACIÓN DUAL INTELIGENTE:
                        tiene_ax = len(fila_encontrada) > 49 and bool(fila_encontrada[49].strip())

                        if tiene_ax:
                            raw_caps_ax = fila_encontrada[49].strip().split(",")
                            st.session_state.caps_filas_override = [int(x) for x in raw_caps_ax if x.strip().isdigit()][:target_filas_cargadas]
                            while len(st.session_state.caps_filas_override) < target_filas_cargadas:
                                st.session_state.caps_filas_override.append(int(st.session_state.capg_val))
                            st.session_state["modalidad_cap_selector"] = "Digitar Cada Fila Manualmente (Sacos/Cajas)"
                        else:
                            def_caps = [int(st.session_state.capg_val)] * target_filas_cargadas
                            def_caps[0] = int(st.session_state.capf1_val)
                            def_caps[-1] = int(st.session_state.capfu_val)
                            st.session_state.caps_filas_override = def_caps
                            st.session_state["modalidad_cap_selector"] = "Modo Estándar (Fila 1, Centro y Puerta)"
                    except Exception:
                        pass

                    cargadas_pres = []
                    for p_i in range(10, 26, 2):
                        if len(fila_encontrada) > p_i + 1:
                            nom_p = fila_encontrada[p_i].strip()
                            cant_str = fila_encontrada[p_i + 1].strip()
                            if nom_p and cant_str:
                                try:
                                    peso_sug = obtener_peso_sugerido_presentacion(nom_p)
                                    cargadas_pres.append({"nombre": nom_p, "bultos": int(cant_str), "peso": peso_sug})
                                except Exception:
                                    pass
                    if cargadas_pres:
                        st.session_state.pres_items = cargadas_pres

                    if len(fila_encontrada) > 34 and fila_encontrada[34].strip():
                        det_lotes_str = fila_encontrada[34].strip()
                        partes_l = det_lotes_str.split(" | ")
                        nuevos_lotes = []
                        for pl in partes_l:
                            try:
                                cod_lote = pl.split(" (")[0].strip()
                                rest = pl.split(" (")[1]
                                fec_str = rest.split("): ")[0].strip()
                                b_val = int(rest.split("): ")[1].replace("b", "").strip())
                                f_obj = datetime.strptime(fec_str, "%d/%m/%Y").date()
                                nuevos_lotes.append({"fecha": f_obj, "lote": cod_lote, "bultos": b_val})
                            except Exception:
                                pass
                        if nuevos_lotes:
                            st.session_state.lotes_items = nuevos_lotes

                    if len(fila_encontrada) > 40 and fila_encontrada[40].strip():
                        raw_pesos = fila_encontrada[40].strip().split(" ;; ")
                        st.session_state.txt_pesos_mem = {}
                        for item_p in raw_pesos:
                            if "::" in item_p:
                                p_idx, p_vals = item_p.split("::", 1)
                                st.session_state.txt_pesos_mem[p_idx.strip()] = p_vals.strip()

                    try:
                        st.session_state.peso_saco_hist = float(fila_encontrada[46].strip()) if len(fila_encontrada) > 46 and fila_encontrada[46].strip() else 0.0
                        st.session_state.peso_block_hist = float(fila_encontrada[47].strip()) if len(fila_encontrada) > 47 and fila_encontrada[47].strip() else 0.0
                        st.session_state.plus_hist = float(fila_encontrada[48].strip()) if len(fila_encontrada) > 48 and fila_encontrada[48].strip() else 0.0
                    except Exception:
                        pass

                    with st.spinner("Sincronizando fotos y reportes guardados desde la base de datos..."):
                        fotos_recuperadas = recuperar_fotos_de_sheets(get_gspread_client, num_c_cargado)
                        if num_c_cargado not in st.session_state.fotos_contenedor_db:
                            st.session_state.fotos_contenedor_db[num_c_cargado] = {}
                        
                        db_c = st.session_state.fotos_contenedor_db[num_c_cargado]
                        db_c["bytes_ir"] = fotos_recuperadas.get("IR")
                        db_c["bytes_temp"] = fotos_recuperadas.get("TEMP")
                        db_c["bytes_pack"] = fotos_recuperadas.get("PACK")
                        db_c["bytes_invol"] = fotos_recuperadas.get("INVOLUCRADO")

                    if "df_congelado_edit" in st.session_state:
                        del st.session_state["df_congelado_edit"]

                    st.session_state.form_version += 1
                    st.success(f"✅ ¡Contenedor {num_c_cargado} cargado con éxito!")
                    st.rerun()

    with col_sel2:
        if st.button("🧹 Nuevo / Limpiar Formulario"):
            st.session_state.emb_id = f"EMB-{datetime.now().strftime('%y%m%d%H%M%S')}"
            st.session_state.cont_val = ""
            st.session_state.fec_val = date.today()
            st.session_state.mes_val = MESES_ESP.get(date.today().month, "SETIEMBRE")
            st.session_state.pi_val = ""
            st.session_state.bk_val = ""
            st.session_state.cli_val = ""
            st.session_state.dest_val = ""
            st.session_state.pais_val = ""
            st.session_state.pay_val = 30400.0
            st.session_state.nfil_val = 18
            st.session_state.capg_val = 75
            st.session_state.capf1_val = 75
            st.session_state.capfu_val = 75
            st.session_state.wstd_val = 20.00
            st.session_state.peso_saco_hist = 0.0
            st.session_state.peso_block_hist = 0.0
            st.session_state.plus_hist = 0.0
            st.session_state["modalidad_cap_selector"] = "Modo Estándar (Fila 1, Centro y Puerta)"
            st.session_state.pres_items = [{"nombre": LISTA_PRESENTACIONES_FRIGOSA[0], "bultos": 0, "peso": 20.0}]
            st.session_state.lotes_items = [{"fecha": date.today(), "lote": generar_lote_juliano(date.today()), "bultos": 0}]
            st.session_state.txt_pesos_mem = {}
            if "df_congelado_edit" in st.session_state:
                del st.session_state["df_congelado_edit"]
            if "caps_filas_override" in st.session_state:
                del st.session_state["caps_filas_override"]
            st.session_state.form_version += 1
            st.rerun()

    with st.expander("⚙️ Datos Principales del Contenedor", expanded=True):
        cp1, cp2, cp3, cp4 = st.columns(4)
        with cp1:
            st.session_state.fec_val = st.date_input("Fecha:", value=st.session_state.fec_val, key=f"fec_emb_{v}")
            st.session_state.cont_val = st.text_input("N° Contenedor:", value=st.session_state.cont_val, key=f"cont_emb_{v}").upper().strip()
            mes_idx = list(MESES_ESP.values()).index(st.session_state.mes_val) if st.session_state.mes_val in MESES_ESP.values() else 8
            st.session_state.mes_val = st.selectbox("Mes:", list(MESES_ESP.values()), index=mes_idx, key=f"mes_emb_{v}")
        with cp2:
            st.session_state.bk_val = st.text_input("Booking:", value=st.session_state.bk_val, key=f"bk_emb_{v}").strip()
            st.session_state.pi_val = st.text_input("N° P.I. (Pedido):", value=st.session_state.pi_val, key=f"pi_emb_{v}").strip()
        with cp3:
            st.session_state.cli_val = st.text_input("Cliente:", value=st.session_state.cli_val, key=f"cli_emb_{v}").strip()
            st.session_state.dest_val = st.text_input("Destino (Puerto):", value=st.session_state.dest_val, key=f"dest_emb_{v}").strip()
        with cp4:
            st.session_state.pais_val = st.text_input("País:", value=st.session_state.pais_val, key=f"pais_emb_{v}").strip().upper()
            st.session_state.pay_val = st.number_input("Payload Máx (kg):", min_value=15000.0, max_value=34000.0, value=float(st.session_state.pay_val), step=100.0, key=f"pay_emb_{v}")

    # =========================================================================
    # CONFIGURACIÓN DINÁMICA DE FILAS Y CAPACIDADES (PROTEGIDO)
    # =========================================================================
    target_nfil = int(st.session_state.nfil_val)
    if "caps_filas_override" not in st.session_state:
        st.session_state.caps_filas_override = [75] * target_nfil
    else:
        while len(st.session_state.caps_filas_override) < target_nfil:
            st.session_state.caps_filas_override.append(int(st.session_state.capg_val))
        if len(st.session_state.caps_filas_override) > target_nfil:
            st.session_state.caps_filas_override = st.session_state.caps_filas_override[:target_nfil]

    caps_reales_actuales = [int(x) for x in st.session_state.caps_filas_override]

    # CÁLCULO DE PRESENTACIONES CON PESOS INDIVIDUALES POR CORTE (10 kg Botones vs 20 kg Sacos)
    lista_pres_mem = [
        {
            "nombre": p["nombre"],
            "cantidad": int(p["bultos"]),
            "peso_unit": float(p.get("peso", obtener_peso_sugerido_presentacion(p["nombre"])))
        }
        for p in st.session_state.pres_items
    ]
    matriz_pres_auto = calcular_matriz_estiba(caps_reales_actuales, lista_pres_mem)
    headers_pres = [f"{p['nombre']} (P{idx+1})" for idx, p in enumerate(lista_pres_mem)]
    data_pres_tabla = []
    pesos_totales_por_fila = []
    for f_idx in range(len(caps_reales_actuales)):
        b_f = sum(matriz_pres_auto[f_idx])
        # Tonelaje exacto calculado según el peso unitario de cada producto en la fila
        tm_f = sum(matriz_pres_auto[f_idx][p_i] * lista_pres_mem[p_i]['peso_unit'] for p_i in range(len(lista_pres_mem))) / 1000.0
        pesos_totales_por_fila.append(tm_f)
        r_d = {"N° FILA": f_idx + 1, "TM ESTIMADO": round(tm_f, 4), "TOTAL BULTOS": b_f}
        for p_i in range(len(lista_pres_mem)):
            r_d[headers_pres[p_i]] = matriz_pres_auto[f_idx][p_i]
        data_pres_tabla.append(r_d)
    df_pres_global = pd.DataFrame(data_pres_tabla)

    # MATRIZ DE LOTES: TOMA EL TONELAJE REAL DE LA FILA (NO ASUME 20 KG A TODO)
    lista_lotes_mem = [{"idx": idx + 1, "fecha_txt": l["fecha"].strftime('%d/%m/%Y'), "lote_txt": l["lote"].strip(), "cantidad": int(l["bultos"])} for idx, l in enumerate(st.session_state.lotes_items)]
    headers_l = [f"L{l['idx']}: {l['fecha_txt']} | {l['lote_txt']}" for l in lista_lotes_mem]
    matriz_lotes_auto = calcular_matriz_estiba(caps_reales_actuales, lista_lotes_mem)

    data_filas_tabla = []
    for f_idx in range(target_nfil):
        b_f = caps_reales_actuales[f_idx]
        tm_f_real = pesos_totales_por_fila[f_idx] if f_idx < len(pesos_totales_por_fila) and sum(p['cantidad'] for p in lista_pres_mem) > 0 else round((b_f * float(st.session_state.wstd_val)) / 1000.0, 4)
        r_dict = {"N° FILA": f_idx + 1, "TM": round(tm_f_real, 4), "CANT/FILA": b_f}
        for l_i in range(len(lista_lotes_mem)):
            r_dict[headers_l[l_i]] = matriz_lotes_auto[f_idx][l_i]
        data_filas_tabla.append(r_dict)
    df_lotes_global = pd.DataFrame(data_filas_tabla)

    # ------------------ INICIALIZACIÓN TABLA CONGELADO ------------------
    if "df_congelado_edit" not in st.session_state or len(st.session_state.df_congelado_edit) != len(caps_reales_actuales):
        filas_sist_init = []
        for f_idx in range(len(caps_reales_actuales)):
            cap_f = caps_reales_actuales[f_idx]
            tm_f_sist = pesos_totales_por_fila[f_idx] if f_idx < len(pesos_totales_por_fila) else round((cap_f * float(st.session_state.wstd_val)) / 1000.0, 4)
            filas_sist_init.append({
                "N° FILA": f_idx + 1,
                "TM": round(tm_f_sist, 4),
                "PLACAS": cap_f,
                "TUNEL": 0,
                "IQF": 0,
                "TOTAL": cap_f
            })
        st.session_state.df_congelado_edit = pd.DataFrame(filas_sist_init)

    presentaciones_data_global = []
    for i, p_item in enumerate(lista_pres_mem):
        val_mem = st.session_state.txt_pesos_mem.get(str(i), "20.00, 20.05, 19.98")
        pesos_clean = []
        for p in val_mem.replace("\n", ",").split(","):
            try:
                val_num = float(p.strip())
                if val_num > 0:
                    pesos_clean.append(val_num)
            except Exception:
                pass
        pesos_clean = pesos_clean[:20]
        prom_u = (sum(pesos_clean) / len(pesos_clean)) if pesos_clean else float(p_item["peso_unit"])
        tot_k = prom_u * p_item["cantidad"]
        presentaciones_data_global.append({
            "nombre": p_item["nombre"],
            "bultos": p_item["cantidad"],
            "pesos": pesos_clean,
            "promedio": prom_u,
            "total_kg": tot_k
        })

    tot_b_gral = sum(p['bultos'] for p in presentaciones_data_global)
    peso_tot_gral = sum(p['total_kg'] for p in presentaciones_data_global)
    prom_global = (peso_tot_gral / tot_b_gral) if tot_b_gral > 0 else 0.0
    peso_a_favor = float(st.session_state.pay_val) - peso_tot_gral

    tipo_env_act = st.session_state.tipo_envase_val
    tara_act = float(st.session_state.tara_insumos_val)
    bloques_act = int(st.session_state.bloques_bulto_val)

    if prom_global > tara_act and bloques_act > 0:
        peso_block_planta = (prom_global - tara_act) / float(bloques_act)
        plus_planta = ((peso_block_planta - 10.0) / 10.0) * 100.0
    else:
        peso_block_planta = 0.0
        plus_planta = 0.0

    curr_c_id = st.session_state.cont_val.strip()
    if curr_c_id and curr_c_id not in st.session_state.fotos_contenedor_db:
        st.session_state.fotos_contenedor_db[curr_c_id] = {}

    db_actual = st.session_state.fotos_contenedor_db.get(curr_c_id, {})
    bytes_ir_actual = db_actual.get("bytes_ir")
    bytes_temp_actual = db_actual.get("bytes_temp")
    bytes_pack_actual = db_actual.get("bytes_pack")
    bytes_invol_actual = db_actual.get("bytes_invol")

    cabecera_pdf_maestra = {
        "fecha": str(st.session_state.fec_val),
        "contenedor": st.session_state.cont_val,
        "payload": float(st.session_state.pay_val),
        "pi": st.session_state.pi_val,
        "booking": st.session_state.bk_val,
        "cliente": st.session_state.cli_val,
        "destino": st.session_state.dest_val
    }
    resumen_pdf_maestro = {
        "total_bultos": tot_b_gral,
        "peso_total": peso_tot_gral,
        "promedio_global": prom_global,
        "peso_a_favor": peso_a_favor,
        "peso_block_planta": peso_block_planta,
        "porcentaje_plus_planta": plus_planta,
        "tipo_envase": tipo_env_act,
        "tara_descuento": tara_act,
        "bloques_x_bulto": bloques_act
    }

    pdf_dossier_bytes_cache = None
    if st.session_state.cont_val:
        try:
            pdf_dossier_bytes_cache = generar_dossier_unificado(
                cabecera_pdf_maestra,
                df_lotes_global,
                df_pres_global,
                st.session_state.df_congelado_edit,
                presentaciones_data_global,
                resumen_pdf_maestro,
                bytes_ir_actual,
                bytes_temp_actual,
                bytes_pack_actual,
                bytes_invol_actual
            ).getvalue()
        except Exception:
            pdf_dossier_bytes_cache = None

    if c_btn_c2 is not None and st.session_state.cont_val and pdf_dossier_bytes_cache:
        with c_btn_c2:
            st.download_button(
                label=f"📦 Descargar Reporte ({st.session_state.cont_val})",
                data=pdf_dossier_bytes_cache,
                file_name=f"Reporte_Embarque_{st.session_state.cont_val}.pdf",
                mime="application/pdf",
                use_container_width=True
            )

    # =========================================================================
    # PESTAÑAS
    # =========================================================================
    tab_estiba_lotes, tab_estiba_pres, tab_placa_tunel, tab_pesos, tab_adjuntos, tab_visor = st.tabs([
        "📅 1. Plano Estiba (Lotes)",
        "📦 2. Plano Estiba (Presentaciones)",
        "❄️ 3. Placas / Túnel / IQF",
        "⚖️ 4. Control de Pesos (Balanza)",
        "📸 5. IR (PDF/Foto), Temp, Packing & Involucrado",
        "🔎 6. Visor Documental y Estado"
    ])

    # ------------------ TAB 1: PLANO ESTIBA (FORMULARIO BATCH SIN BUCLES) ------------------
    with tab_estiba_lotes:
        st.markdown("#### Configuración de Filas y Capacidad")
        
        c_top1, c_top2 = st.columns([1.5, 3])
        with c_top1:
            st.session_state.nfil_val = int(st.number_input("Total Filas del Contenedor:", min_value=10, max_value=30, value=int(st.session_state.nfil_val), key=f"nfil_{v}"))
        
        default_idx_m = 1 if st.session_state.get("modalidad_cap_selector") == "Digitar Cada Fila Manualmente (Sacos/Cajas)" else 0
        with c_top2:
            modo_cap_fila = st.radio(
                "Modalidad de Capacidad por Fila:",
                ["Modo Estándar (Fila 1, Centro y Puerta)", "Digitar Cada Fila Manualmente (Sacos/Cajas)"],
                index=default_idx_m,
                horizontal=True,
                key=f"m_cap_fila_{v}"
            )

        if modo_cap_fila == "Modo Estándar (Fila 1, Centro y Puerta)":
            cf1, cf2, cf3, cf4 = st.columns(4)
            with cf1:
                st.session_state.capg_val = int(st.number_input("Capacidad Estándar Fila:", min_value=20, max_value=120, value=int(st.session_state.capg_val), key=f"capg_{v}"))
            with cf2:
                st.session_state.capf1_val = int(st.number_input("Capacidad Fila 1:", min_value=20, max_value=120, value=int(st.session_state.capf1_val), key=f"capf1_{v}"))
            with cf3:
                st.session_state.capfu_val = int(st.number_input(f"Capacidad Fila {target_nfil}:", min_value=20, max_value=120, value=int(st.session_state.capfu_val), key=f"capfu_{v}"))
            with cf4:
                st.session_state.wstd_val = float(st.number_input("Peso Estándar Bulto (kg):", value=float(st.session_state.wstd_val), step=0.1, key=f"wstd_{v}"))
            
            for i in range(target_nfil):
                if i == 0:
                    st.session_state.caps_filas_override[i] = int(st.session_state.capf1_val)
                elif i == target_nfil - 1:
                    st.session_state.caps_filas_override[i] = int(st.session_state.capfu_val)
                else:
                    st.session_state.caps_filas_override[i] = int(st.session_state.capg_val)
        
        else:
            st.info("✍️ **Modo Manual Batch:** Digita directamente los bultos por fila. Al finalizar, presiona el botón verde de abajo para confirmar.")
            
            with st.form(f"form_filas_manuales_{v}"):
                c_pstd, _ = st.columns([2, 2])
                with c_pstd:
                    w_man_tmp = st.number_input("Peso Estándar Bulto (kg):", value=float(st.session_state.wstd_val), step=0.1)

                cols_per_row = 6
                grid_cols_f = st.columns(cols_per_row)
                nuevos_valores_buffer = []

                for f_i in range(target_nfil):
                    with grid_cols_f[f_i % cols_per_row]:
                        val_actual_f = int(st.session_state.caps_filas_override[f_i]) if f_i < len(st.session_state.caps_filas_override) else 75
                        v_inp = st.number_input(
                            f"Fila {f_i + 1}:", 
                            min_value=0, 
                            max_value=150, 
                            value=val_actual_f, 
                            step=1, 
                            key=f"manual_f_inp_{f_i}_{v}"
                        )
                        nuevos_valores_buffer.append(int(v_inp))
                
                btn_aplicar_filas = st.form_submit_button(
                    "🔄 Confirmar y Aplicar Capacidades de Filas", 
                    type="primary", 
                    use_container_width=True
                )

                if btn_aplicar_filas:
                    st.session_state.wstd_val = float(w_man_tmp)
                    st.session_state.caps_filas_override = nuevos_valores_buffer
                    st.session_state["modalidad_cap_selector"] = "Digitar Cada Fila Manualmente (Sacos/Cajas)"
                    st.success("✅ ¡Capacidades de filas actualizadas y aplicadas correctamente!")
                    st.rerun()

        with st.expander("⚡ Asignación Rápida por Rangos de Filas (Ej: Fila 2 a 14 = 63, Fila 15 a 19 = 78)", expanded=False):
            cr1, cr2, cr3, cr4 = st.columns([1.5, 1.5, 2, 2])
            with cr1:
                r_ini = st.number_input("Desde Fila:", min_value=1, max_value=target_nfil, value=1, key=f"r_ini_{v}")
            with cr2:
                r_fin = st.number_input("Hasta Fila:", min_value=1, max_value=target_nfil, value=target_nfil, key=f"r_fin_{v}")
            with cr3:
                r_cant = st.number_input("Cantidad Bultos por Fila:", min_value=0, max_value=150, value=63, key=f"r_cant_{v}")
            with cr4:
                st.markdown("<br/>", unsafe_allow_html=True)
                if st.button("Aplicar Rango a Filas", use_container_width=True, key=f"btn_rango_{v}"):
                    if r_ini <= r_fin:
                        for idx_f in range(int(r_ini) - 1, int(r_fin)):
                            st.session_state.caps_filas_override[idx_f] = int(r_cant)
                        st.session_state["modalidad_cap_selector"] = "Digitar Cada Fila Manualmente (Sacos/Cajas)"
                        st.success(f"Filas de {r_ini} a {r_fin} fijadas en {r_cant} bultos.")
                        st.rerun()
                    else:
                        st.error("La fila inicial debe ser menor o igual a la final.")

        st.markdown("---")
        n_lotes = st.number_input("Cantidad de Lotes:", min_value=1, max_value=100, value=max(len(st.session_state.lotes_items), 1), key=f"nlot_c_{v}")
        while len(st.session_state.lotes_items) < n_lotes:
            st.session_state.lotes_items.append({"fecha": date.today(), "lote": generar_lote_juliano(date.today()), "bultos": 0})
        while len(st.session_state.lotes_items) > n_lotes:
            st.session_state.lotes_items.pop()

        cols_l = st.columns(min(int(n_lotes), 4))
        lista_lotes_calc = []
        for i in range(int(n_lotes)):
            col_target = cols_l[i % 4]
            item_l = st.session_state.lotes_items[i]
            with col_target:
                fl = st.date_input(f"Fecha {i+1}:", value=item_l["fecha"], key=f"fl_{i}_{v}")
                
                if fl != item_l["fecha"]:
                    item_l["fecha"] = fl
                    item_l["lote"] = generar_lote_juliano(fl)
                    st.session_state[f"cl_{i}_{v}"] = item_l["lote"]

                lot_txt = st.text_input(f"Lote {i+1}:", value=item_l["lote"], key=f"cl_{i}_{v}").strip().upper()
                bl = st.number_input(f"Bultos {i+1}:", min_value=0, value=int(item_l["bultos"]), step=10, key=f"bl_{i}_{v}")
                
                item_l["fecha"] = fl
                item_l["lote"] = lot_txt
                item_l["bultos"] = int(bl)
                lista_lotes_calc.append({"idx": i + 1, "fecha_txt": fl.strftime('%d/%m/%Y'), "lote_txt": lot_txt, "cantidad": int(bl)})

        # TABLA DE ESTIBA LIMPIA (SIN RERUN CÍCLICO Y SIN DUPLICACIÓN)
        st.markdown("##### 📊 Plano de Distribución Calculado (Lotes)")
        st.dataframe(
            df_lotes_global,
            hide_index=True,
            use_container_width=True,
            height=320
        )

        tot_b_cargados = sum(caps_reales_actuales)
        tot_tm_cargados_real = sum(pesos_totales_por_fila) if sum(p['cantidad'] for p in lista_pres_mem) > 0 else (tot_b_cargados * float(st.session_state.wstd_val)) / 1000.0

        m1, m2 = st.columns(2)
        m1.metric("Total Bultos Cargados (Lotes)", f"{tot_b_cargados:,} bultos")
        m1_tm = f"{tot_tm_cargados_real:.3f} TM"
        m2.metric("Tonelaje Total Real", m1_tm)

    # ------------------ TAB 2: PRESENTACIONES (CON DESCARGA DE PDF INDIVIDUAL) ------------------
    with tab_estiba_pres:
        st.markdown("#### Presentaciones a Embarcar (Hasta 8 según la hoja)")
        st.caption("Configura el kilaje unitario exacto por presentación (ej. 10 kg para Botones/Cajas, 20 kg para Sacos).")

        np_m = st.number_input("Número de Presentaciones:", min_value=1, max_value=8, value=max(len(st.session_state.pres_items), 1), key=f"npres_c_{v}")
        while len(st.session_state.pres_items) < np_m:
            st.session_state.pres_items.append({"nombre": LISTA_PRESENTACIONES_FRIGOSA[0], "bultos": 0, "peso": 20.0})
        while len(st.session_state.pres_items) > np_m:
            st.session_state.pres_items.pop()

        cols_p = st.columns(min(int(np_m), 4))
        for i in range(int(np_m)):
            col_target_p = cols_p[i % 4]
            p_item = st.session_state.pres_items[i]
            with col_target_p:
                st.markdown(f"**Presentación {i+1}**")
                idx_p_sel = LISTA_PRESENTACIONES_FRIGOSA.index(p_item["nombre"]) if p_item["nombre"] in LISTA_PRESENTACIONES_FRIGOSA else 0
                sel_nom = st.selectbox(f"Corte {i+1}:", LISTA_PRESENTACIONES_FRIGOSA, index=idx_p_sel, key=f"sp_{i}_{v}")
                
                # Asignación automática de kilaje según corte
                peso_default_sug = obtener_peso_sugerido_presentacion(sel_nom)
                val_peso_actual = float(p_item.get("peso", peso_default_sug))
                if p_item.get("nombre") != sel_nom:
                    val_peso_actual = peso_default_sug

                cant_b = st.number_input(f"Bultos {i+1}:", min_value=0, value=int(p_item["bultos"]), step=10, key=f"bp_{i}_{v}")
                p_peso = st.number_input(f"Peso Unit (kg) {i+1}:", min_value=1.0, max_value=50.0, value=val_peso_actual, step=0.5, key=f"w_pres_{i}_{v}")

                p_item["nombre"] = sel_nom
                p_item["bultos"] = int(cant_b)
                p_item["peso"] = float(p_peso)

        st.dataframe(df_pres_global, hide_index=True, use_container_width=True, height=280)

        # BOTÓN INDIVIDUAL DE DESCARGA: SOLO EL PLANO DE ESTIBA POR PRESENTACIONES
        st.markdown("---")
        try:
            pdf_pres_solo_bytes = generar_pdf_estiba_presentaciones_solo(cabecera_pdf_maestra, df_pres_global)
            st.download_button(
                label="📄 Descargar Plano de Estiba (Presentaciones) - PDF",
                data=pdf_pres_solo_bytes,
                file_name=f"Plano_Estiba_Presentaciones_{st.session_state.cont_val or 'Contenedor'}.pdf",
                mime="application/pdf",
                use_container_width=True
            )
        except Exception as e_pres_pdf:
            st.caption(f"Nota en generación de PDF de presentaciones: {e_pres_pdf}")

    # ------------------ TAB 3: PLACAS / TÚNEL / IQF ------------------
    with tab_placa_tunel:
        st.markdown("#### Configuración de Sistema de Congelación")

        def on_change_modo_cong():
            opc = st.session_state.get(f"rad_cong_{v}")
            num_f = len(caps_reales_actuales)
            if opc == "Mixto (Ingreso Manual Fila por Fila)":
                filas_clean = []
                for f_idx in range(num_f):
                    filas_clean.append({
                        "N° FILA": f_idx + 1, "TM": 0.0, "PLACAS": 0, "TUNEL": 0, "IQF": 0, "TOTAL": 0
                    })
                st.session_state.df_congelado_edit = pd.DataFrame(filas_clean)

        modo_cong_opc = st.radio(
            "Carga predominante:",
            ["Solo Placas (100% de la carga)", "Solo Túnel (100% de la carga)", "Mixto (Ingreso Manual Fila por Fila)"],
            horizontal=True,
            key=f"rad_cong_{v}",
            on_change=on_change_modo_cong
        )

        num_filas_actual = len(caps_reales_actuales)
        df_editor_source = st.session_state.df_congelado_edit.copy()

        if modo_cong_opc == "Solo Placas (100% de la carga)":
            for idx in range(num_filas_actual):
                cap_f = caps_reales_actuales[idx]
                tm_f_sist = pesos_totales_por_fila[idx] if idx < len(pesos_totales_por_fila) else round((cap_f * float(st.session_state.wstd_val)) / 1000.0, 4)
                df_editor_source.at[idx, "PLACAS"] = cap_f
                df_editor_source.at[idx, "TUNEL"] = 0
                df_editor_source.at[idx, "IQF"] = 0
                df_editor_source.at[idx, "TOTAL"] = cap_f
                df_editor_source.at[idx, "TM"] = round(tm_f_sist, 4)
            st.session_state.df_congelado_edit = df_editor_source

            st.dataframe(
                df_editor_source,
                hide_index=True,
                use_container_width=True,
                height=320
            )

        elif modo_cong_opc == "Solo Túnel (100% de la carga)":
            for idx in range(num_filas_actual):
                cap_f = caps_reales_actuales[idx]
                tm_f_sist = pesos_totales_por_fila[idx] if idx < len(pesos_totales_por_fila) else round((cap_f * float(st.session_state.wstd_val)) / 1000.0, 4)
                df_editor_source.at[idx, "PLACAS"] = 0
                df_editor_source.at[idx, "TUNEL"] = cap_f
                df_editor_source.at[idx, "IQF"] = 0
                df_editor_source.at[idx, "TOTAL"] = cap_f
                df_editor_source.at[idx, "TM"] = round(tm_f_sist, 4)
            st.session_state.df_congelado_edit = df_editor_source

            st.dataframe(
                df_editor_source,
                hide_index=True,
                use_container_width=True,
                height=320
            )

        else:
            st.info("✍️ **Modo Mixto Activo:** Digita libremente las cantidades de Placas, Túnel e IQF fila por fila. Al finalizar, presiona el botón **'🔄 Actualizar y Calcular Distribución Mixta'** para consolidar los cálculos.")

            with st.form("form_mixto_congelado"):
                df_grid_ingreso = st.data_editor(
                    df_editor_source,
                    disabled=["N° FILA", "TM", "TOTAL"],
                    hide_index=True,
                    use_container_width=True,
                    height=320,
                    key=f"grid_cong_batch_{v}_{num_filas_actual}"
                )
                
                btn_actualizar_mixto = st.form_submit_button(
                    "🔄 Actualizar y Calcular Distribución Mixta",
                    type="secondary",
                    use_container_width=True
                )

                if btn_actualizar_mixto:
                    df_grid_ingreso["TOTAL"] = df_grid_ingreso["PLACAS"] + df_grid_ingreso["TUNEL"] + df_grid_ingreso["IQF"]
                    df_grid_ingreso["TM"] = round((df_grid_ingreso["TOTAL"] * float(st.session_state.wstd_val)) / 1000.0, 4)
                    st.session_state.df_congelado_edit = df_grid_ingreso
                    st.success("✅ ¡Distribución mixta consolidada y calculada correctamente!")
                    st.rerun()

        df_congelado_resultado = st.session_state.df_congelado_edit
        tot_placas_sum = int(df_congelado_resultado["PLACAS"].sum())
        tot_tunel_sum = int(df_congelado_resultado["TUNEL"].sum())
        tot_iqf_sum = int(df_congelado_resultado["IQF"].sum())

        s1, s2, s3, s4 = st.columns(4)
        s1.metric("Total Placas", f"{tot_placas_sum:,} b")
        s2.metric("Total Túnel", f"{tot_tunel_sum:,} b")
        s3.metric("Total IQF", f"{tot_iqf_sum:,} b")
        s4.metric("Total Congelado", f"{tot_placas_sum + tot_tunel_sum + tot_iqf_sum:,} b")

    # ------------------ TAB 4: CONTROL DE PESOS (CON DESCARGA DE PDF INDIVIDUAL) ------------------
    with tab_pesos:
        st.markdown("#### 1. Muestreo de Control de Pesos en Balanza")
        cols_w = st.columns(max(len(lista_pres_mem), 1))

        for i, col in enumerate(cols_w):
            with col:
                nom_completo = lista_pres_mem[i]['nombre'].strip()
                st.markdown(f"**{nom_completo}**")
                val_mem = st.session_state.txt_pesos_mem.get(str(i), "20.00, 20.05, 19.98")
                txt_p = st.text_area(f"Pesos balanza ({i+1}):", value=val_mem, height=90, key=f"pw_box_{i}_{v}")
                st.session_state.txt_pesos_mem[str(i)] = txt_p

        if peso_a_favor < 0:
            estilo_box = "background-color: #FED7D7; border: 1px solid #E53E3E; padding: 12px; border-radius: 8px; color: #9B2C2C;"
            label_margen = f"🚨 Margen en Contra (Exceso de Payload): {abs(peso_a_favor):,.2f} kg"
        elif peso_a_favor <= 500:
            estilo_box = "background-color: #EBF8FF; border: 1px solid #3182CE; padding: 12px; border-radius: 8px; color: #2B6CB0;"
            label_margen = f"ℹ️ Margen al Límite del Payload: {peso_a_favor:,.2f} kg"
        else:
            estilo_box = "background-color: #C6F6D5; border: 1px solid #38A169; padding: 12px; border-radius: 8px; color: #22543D;"
            label_margen = f"✅ Margen a Favor Holgado: {peso_a_favor:,.2f} kg"

        st.markdown(f"<div style='{estilo_box} font-weight: bold; margin-bottom: 12px;'>{label_margen}</div>", unsafe_allow_html=True)

        r1, r2, r3, r4 = st.columns(4)
        r1.metric("Bultos Totales", f"{tot_b_gral:,}")
        r2.metric("Promedio Global", f"{prom_global:.3f} kg")
        r3.metric("Peso Bruto Total", f"{peso_tot_gral:,.2f} kg")
        r4.metric("Margen Restante", f"{peso_a_favor:,.2f} kg")

        st.markdown("---")
        st.markdown("#### ⚖️ 2. Liquidación Técnica del Muestreo (Block, Tara y Plus)")
        st.caption("Visibilidad interna de supervisión: El plus y el peso block se controlan aquí y se respaldan en Sheets, pero se omiten del PDF.")

        col_cfg1, col_cfg2, col_cfg3 = st.columns(3)
        with col_cfg1:
            idx_env = 0 if st.session_state.tipo_envase_val == "Saco" else 1
            env_sel = st.selectbox("Envase Empleado:", ["Saco", "Caja"], index=idx_env, key=f"env_sel_{v}")
            st.session_state.tipo_envase_val = env_sel
            tara_sugerida = 0.15 if env_sel == "Saco" else 0.59
            bloques_sugeridos = 2 if env_sel == "Saco" else 1

        with col_cfg2:
            st.session_state.tara_insumos_val = st.number_input(
                f"Tara / Insumos ({env_sel} en kg):",
                min_value=0.0,
                max_value=2.0,
                value=tara_sugerida,
                step=0.01,
                format="%.2f",
                key=f"tara_inp_{v}"
            )

        with col_cfg3:
            st.session_state.bloques_bulto_val = st.selectbox(
                f"Bloques por {env_sel}:",
                [1, 2, 4],
                index=[1, 2, 4].index(bloques_sugeridos),
                key=f"blq_inp_{v}"
            )

        t_d = float(st.session_state.tara_insumos_val)
        n_b = int(st.session_state.bloques_bulto_val)
        
        if prom_global > t_d and n_b > 0:
            p_block_disp = (prom_global - t_d) / float(n_b)
            p_plus_disp = ((p_block_disp - 10.0) / 10.0) * 100.0
        else:
            p_block_disp = 0.0
            p_plus_disp = 0.0

        m_res1, m_res2, m_res3 = st.columns(3)
        m_res1.metric(f"Promedio {env_sel} (Muestreo)", f"{prom_global:.3f} kg")
        m_res2.metric("⚖️ Peso Block Neto", f"{p_block_disp:.3f} kg")
        m_res3.metric("📈 Plus Real (%)", f"{p_plus_disp:+.2f} %", help="Control interno exclusivo de supervisión (no figura en el PDF final)")

        st.markdown("---")
        try:
            pdf_pesos_bytes = generar_pdf_pesos_solos(cabecera_pdf_maestra, presentaciones_data_global, resumen_pdf_maestro)
            st.download_button(
                "📄 Descargar Reporte de Control de Pesos y Balanza (Sin Plus)",
                data=pdf_pesos_bytes,
                file_name=f"Pesos_{st.session_state.cont_val}.pdf",
                mime="application/pdf",
                use_container_width=True
            )
        except Exception as e_pesos:
            st.caption(f"Generando reporte de pesos: {e_pesos}")

    # ------------------ TAB 5: PANEL DOCUMENTAL (IR EN PDF O FOTO) ------------------
    with tab_adjuntos:
        st.markdown("#### 📸 Panel Documental del Contenedor")
        st.caption("El Reporte de Inspección (IR) puede subirse como archivo **PDF nativo** desde PC o en imagen JPG/PNG. Al guardar en Sheets se conservará y se cargará en cualquier momento.")

        c_f1, c_f2 = st.columns(2)
        with c_f1:
            st.markdown("##### 📄 1. Reporte de Inspección (IR / EIR)")
            foto_ir = st.file_uploader(
                "Subir / Reemplazar Reporte IR (PDF o Imagen):", 
                type=["pdf", "jpg", "jpeg", "png"], 
                key=f"up_ir_{v}"
            )
            if foto_ir:
                raw_bytes = foto_ir.getvalue()
                if foto_ir.name.lower().endswith(".pdf") or raw_bytes.startswith(b'%PDF'):
                    db_actual["bytes_ir"] = raw_bytes
                    st.success(f"📄 Archivo PDF cargado con éxito: **{foto_ir.name}** (Listo para guardar)")
                else:
                    b_opt = optimizar_bytes_imagen(raw_bytes)
                    db_actual["bytes_ir"] = b_opt
                    st.image(b_opt, caption="Foto IR Cargada (Lista para guardar)", use_container_width=True)
            elif db_actual.get("bytes_ir"):
                b_ir_exist = db_actual["bytes_ir"]
                if isinstance(b_ir_exist, (bytes, bytearray)) and b_ir_exist.startswith(b'%PDF'):
                    st.success("📄 **Documento PDF del IR actualmente activo y respaldado.**")
                    st.download_button(
                        "👁️ Descargar / Abrir IR (PDF)",
                        data=b_ir_exist,
                        file_name=f"IR_{st.session_state.cont_val or 'Contenedor'}.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
                else:
                    st.image(b_ir_exist, caption="Foto IR Activa", use_container_width=True)
                
                if st.button("🗑️ Quitar / Eliminar Documento IR", key=f"del_ir_{v}"):
                    db_actual["bytes_ir"] = None
                    if curr_c_id:
                        eliminar_foto_de_sheets(get_gspread_client, curr_c_id, "IR")
                    st.success("Reporte IR eliminado.")
                    st.rerun()

        with c_f2:
            st.markdown("##### ❄️ 2. Foto de Temperatura")
            foto_temp = st.file_uploader("Subir / Reemplazar foto Termoking:", type=["jpg", "jpeg", "png"], key=f"up_temp_{v}")
            if foto_temp:
                b_opt_t = optimizar_bytes_imagen(foto_temp.getvalue())
                db_actual["bytes_temp"] = b_opt_t
                st.image(b_opt_t, caption="Display Termoking Cargado", use_container_width=True)
            elif db_actual.get("bytes_temp"):
                st.image(db_actual["bytes_temp"], caption="Display Termoking Activo", use_container_width=True)
                if st.button("🗑️ Quitar / Eliminar Foto Temp", key=f"del_temp_{v}"):
                    db_actual["bytes_temp"] = None
                    if curr_c_id:
                        eliminar_foto_de_sheets(get_gspread_client, curr_c_id, "TEMP")
                    st.success("Foto de temperatura eliminada.")
                    st.rerun()

        st.markdown("---")
        c_f3, c_f4 = st.columns(2)
        with c_f3:
            st.markdown("##### 📋 3. Foto de Lista de Empaque")
            foto_pack = st.file_uploader("Subir / Reemplazar foto Packing List:", type=["jpg", "jpeg", "png"], key=f"up_pack_{v}")
            if foto_pack:
                b_opt_p = optimizar_bytes_imagen(foto_pack.getvalue())
                db_actual["bytes_pack"] = b_opt_p
                st.image(b_opt_p, caption="Packing List Cargado", use_container_width=True)
            elif db_actual.get("bytes_pack"):
                st.image(db_actual["bytes_pack"], caption="Packing List Activo", use_container_width=True)
                if st.button("🗑️ Quitar / Eliminar Packing List", key=f"del_pack_{v}"):
                    db_actual["bytes_pack"] = None
                    if curr_c_id:
                        eliminar_foto_de_sheets(get_gspread_client, curr_c_id, "PACK")
                    st.success("Foto de packing list eliminada.")
                    st.rerun()

        with c_f4:
            st.markdown("##### 👤 4. Foto de Involucrado / Supervisor en Planta")
            foto_invol = st.file_uploader("Subir / Reemplazar foto Involucrado:", type=["jpg", "jpeg", "png"], key=f"up_invol_{v}")
            if foto_invol:
                b_opt_i = optimizar_bytes_imagen(foto_invol.getvalue())
                db_actual["bytes_invol"] = b_opt_i
                st.image(b_opt_i, caption="Foto Involucrado Cargada", use_container_width=True)
            elif db_actual.get("bytes_invol"):
                st.image(db_actual["bytes_invol"], caption="Foto Involucrado Activa", use_container_width=True)
                if st.button("🗑️ Quitar / Eliminar Foto Involucrado", key=f"del_invol_{v}"):
                    db_actual["bytes_invol"] = None
                    if curr_c_id:
                        eliminar_foto_de_sheets(get_gspread_client, curr_c_id, "INVOLUCRADO")
                    st.success("Foto de involucrado eliminada.")
                    st.rerun()

    # ------------------ TAB 6: VISOR DOCUMENTAL Y ESTADO ------------------
    with tab_visor:
        st.markdown("#### 🔎 Centro de Visualización de Documentos y Evidencias")
        st.caption(f"Inspección directa de los archivos del contenedor: **{st.session_state.cont_val or 'Sin Contenedor Asignado'}**")

        v_c1, v_c2, v_c3, v_c4 = st.columns(4)
        has_ir = bool(db_actual.get("bytes_ir"))
        has_temp = bool(db_actual.get("bytes_temp"))
        has_pack = bool(db_actual.get("bytes_pack"))
        has_invol = bool(db_actual.get("bytes_invol"))

        v_c1.markdown(f"**Reporte IR:** {'🟢 Cargado' if has_ir else '🔴 Pendiente'}")
        v_c2.markdown(f"**Temperatura:** {'🟢 Cargado' if has_temp else '🔴 Pendiente'}")
        v_c3.markdown(f"**Packing List:** {'🟢 Cargado' if has_pack else '🔴 Pendiente'}")
        v_c4.markdown(f"**Involucrado:** {'🟢 Cargado' if has_invol else '🔴 Pendiente'}")

        st.markdown("---")

        opciones_visor = [
            "📄 1. Reporte de Inspección (IR / EIR)",
            "❄️ 2. Foto de Temperatura (Termoking)",
            "📋 3. Foto de Packing List",
            "👤 4. Foto de Supervisor en Planta",
            "📦 5. Reporte Consolidado de Embarque (PDF Completo)"
        ]

        doc_elegido = st.selectbox("Seleccione el Documento a Inspeccionar:", opciones_visor)

        if "1. Reporte de Inspección" in doc_elegido:
            b_ir_view = db_actual.get("bytes_ir")
            if not b_ir_view:
                st.warning("⚠️ Aún no se ha cargado el Reporte de Inspección (IR) para este contenedor.")
            else:
                if isinstance(b_ir_view, (bytes, bytearray)) and b_ir_view.startswith(b'%PDF'):
                    c_act1, c_act2 = st.columns([1.5, 3])
                    with c_act1:
                        st.download_button(
                            "📥 Descargar Archivo IR (PDF)",
                            data=b_ir_view,
                            file_name=f"IR_{st.session_state.cont_val or 'Contenedor'}.pdf",
                            mime="application/pdf",
                            use_container_width=True
                        )
                    with c_act2:
                        b64_ir_direct = base64.b64encode(b_ir_view).decode('utf-8')
                        st.markdown(f'<a href="data:application/pdf;base64,{b64_ir_direct}" target="_blank" style="display:inline-block; padding:8px 16px; background-color:#2B6CB0; color:white; border-radius:5px; text-decoration:none; font-weight:bold;">🚀 Abrir IR en Pestaña Completa</a>', unsafe_allow_html=True)
                    
                    try:
                        reader = pypdf.PdfReader(io.BytesIO(b_ir_view))
                        imagenes_encontradas = []
                        for page in reader.pages:
                            for img_obj in page.images:
                                imagenes_encontradas.append(img_obj.data)
                        
                        if imagenes_encontradas:
                            st.info(f"Visualizando {len(imagenes_encontradas)} página(s) del documento IR:")
                            for idx_img, b_pg in enumerate(imagenes_encontradas):
                                st.image(b_pg, caption=f"Página {idx_img+1} - Reporte IR", use_container_width=True)
                        else:
                            st.info("ℹ️ El archivo PDF contiene texto vectorial. Presiona el botón azul arriba para abrirlo en pantalla completa o descargarlo.")
                    except Exception:
                        st.info("Utilice el botón superior para abrir o descargar el documento PDF con nitidez.")
                else:
                    st.image(b_ir_view, caption=f"Reporte IR - Contenedor {st.session_state.cont_val}", use_container_width=True)

        elif "2. Foto de Temperatura" in doc_elegido:
            b_temp_view = db_actual.get("bytes_temp")
            if not b_temp_view:
                st.warning("⚠️ No hay registro fotográfico de temperatura para este contenedor.")
            else:
                st.image(b_temp_view, caption=f"Display de Temperatura - Contenedor {st.session_state.cont_val}", use_container_width=True)

        elif "3. Foto de Packing List" in doc_elegido:
            b_pack_view = db_actual.get("bytes_pack")
            if not b_pack_view:
                st.warning("⚠️ No hay fotografía de Packing List cargada.")
            else:
                st.image(b_pack_view, caption=f"Packing List Oficial - Contenedor {st.session_state.cont_val}", use_container_width=True)

        elif "4. Foto de Supervisor" in doc_elegido:
            b_invol_view = db_actual.get("bytes_invol")
            if not b_invol_view:
                st.warning("⚠️ No hay fotografía de supervisión en planta cargada.")
            else:
                st.image(b_invol_view, caption=f"Supervisión en Planta - Luis Enrique Fiestas Eca", use_container_width=True)

        elif "5. Reporte Consolidado" in doc_elegido:
            if not pdf_dossier_bytes_cache:
                st.info("ℹ️ Ingrese el N° de Contenedor y los datos básicos para previsualizar el dossier completo.")
            else:
                c_d1, c_d2 = st.columns([1.5, 3])
                with c_d1:
                    st.download_button(
                        "📥 Descargar Reporte de Embarque Oficial (PDF)",
                        data=pdf_dossier_bytes_cache,
                        file_name=f"Reporte_Embarque_{st.session_state.cont_val}.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
                with c_d2:
                    b64_dos_link = base64.b64encode(pdf_dossier_bytes_cache).decode('utf-8')
                    st.markdown(f'<a href="data:application/pdf;base64,{b64_dos_link}" target="_blank" style="display:inline-block; padding:8px 16px; background-color:#2F855A; color:white; border-radius:5px; text-decoration:none; font-weight:bold;">🚀 Abrir Reporte Completo en Pestaña Nueva</a>', unsafe_allow_html=True)

    # =========================================================================
    # GUARDADO CENTRALIZADO (DESDE A HASTA AX - 50 COLUMNAS)
    # =========================================================================
    st.markdown("---")
    btn_label = f"💾 Guardar / Actualizar Información de {st.session_state.cont_val or 'Contenedor'} en Sheets"
    if st.button(btn_label, type="primary", use_container_width=True):
        if not st.session_state.cont_val.strip():
            st.warning("⚠️ Debe ingresar el N° de Contenedor antes de guardar.")
        else:
            try:
                num_c_guardar = st.session_state.cont_val.strip().upper()
                db_c_guardar = st.session_state.fotos_contenedor_db.get(num_c_guardar, {})

                with st.spinner("Guardando archivos y fotos en la base de datos..."):
                    if db_c_guardar.get("bytes_ir"):
                        guardar_foto_en_sheets(get_gspread_client, num_c_guardar, "IR", db_c_guardar["bytes_ir"])
                    if db_c_guardar.get("bytes_temp"):
                        guardar_foto_en_sheets(get_gspread_client, num_c_guardar, "TEMP", db_c_guardar["bytes_temp"])
                    if db_c_guardar.get("bytes_pack"):
                        guardar_foto_en_sheets(get_gspread_client, num_c_guardar, "PACK", db_c_guardar["bytes_pack"])
                    if db_c_guardar.get("bytes_invol"):
                        guardar_foto_en_sheets(get_gspread_client, num_c_guardar, "INVOLUCRADO", db_c_guardar["bytes_invol"])

                pres_cols = []
                for idx in range(8):
                    if idx < len(lista_pres_mem):
                        pres_cols.extend([lista_pres_mem[idx]["nombre"], int(lista_pres_mem[idx]["cantidad"])])
                    else:
                        pres_cols.extend(["", ""])

                detalle_lotes_str = " | ".join([f"{l['lote_txt']} ({l['fecha_txt']}): {l['cantidad']}b" for l in lista_lotes_mem if l['cantidad'] > 0])

                serial_pesos = []
                for k_p, v_p in st.session_state.txt_pesos_mem.items():
                    clean_v = v_p.replace("\n", " ").strip()
                    if clean_v:
                        serial_pesos.append(f"{k_p}::{clean_v}")
                detalle_pesos_str = " ;; ".join(serial_pesos)

                link_ir_final = "REGISTRADO_EN_SHEETS" if db_c_guardar.get("bytes_ir") else ""
                link_temp_final = "REGISTRADO_EN_SHEETS" if db_c_guardar.get("bytes_temp") else ""
                link_pack_final = "REGISTRADO_EN_SHEETS" if db_c_guardar.get("bytes_pack") else ""
                link_invol_final = "REGISTRADO_EN_SHEETS" if db_c_guardar.get("bytes_invol") else ""

                val_prom_saco_planta = round(prom_global, 3)
                val_block_planta = round(peso_block_planta, 3)
                val_plus_planta = round(plus_planta, 2)

                id_embarque_final = st.session_state.emb_id if st.session_state.emb_id else f"EMB-{datetime.now().strftime('%y%m%d%H%M%S')}"

                serial_caps_filas_ax = ",".join([str(int(x)) for x in caps_reales_actuales])

                fila_maestra = [
                    id_embarque_final,                             # A: ID_EMBARQUE
                    num_c_guardar,                                 # B: CONTENEDOR
                    str(st.session_state.mes_val),                 # C: MES
                    str(st.session_state.fec_val),                 # D: FECHA
                    str(st.session_state.pi_val).strip(),          # E: N°_PI
                    str(st.session_state.bk_val).strip(),          # F: BOOKING
                    str(st.session_state.cli_val).strip(),         # G: CLIENTE
                    str(st.session_state.dest_val).strip(),        # H: Destino
                    str(st.session_state.pais_val).strip(),        # I: PAIS
                    "LUIS ENRIQUE FIESTAS ECA",                    # J: supervisor
                    *pres_cols,                                    # K a Z: PRESENTACION 1 a 8 y BULTOS 1 a 8
                    float(st.session_state.pay_val),               # AA: payload_contenedor
                    int(tot_b_gral),                               # AB: total_bultos
                    float(round(peso_tot_gral, 2)),                # AC: peso_bruto
                    float(round(peso_a_favor, 2)),                 # AD: margen_a_favor
                    float(round(prom_global, 3)),                  # AE: promedio_global
                    int(tot_placas_sum),                           # AF: placas
                    int(tot_tunel_sum),                            # AG: tunel
                    int(tot_iqf_sum),                              # AH: iqf
                    detalle_lotes_str,                             # AI: detalle_lotes_fechas
                    int(st.session_state.nfil_val),                # AJ: total_filas
                    int(caps_reales_actuales[1]) if len(caps_reales_actuales) > 1 else int(st.session_state.capg_val), # AK: cap_estandar_fila
                    int(caps_reales_actuales[0]),                  # AL: cap_fila_1
                    int(caps_reales_actuales[-1]),                 # AM: cap_fila_puerta
                    float(st.session_state.wstd_val),              # AN: peso_std_bulto
                    detalle_pesos_str,                             # AO: detalle_pesos_balanza
                    link_ir_final,                                 # AP: link_foto_ir
                    link_temp_final,                               # AQ: link_foto_temperatura
                    link_pack_final,                               # AR: link_foto_packing
                    link_invol_final,                              # AS: link_foto_involucrado
                    0.0,                                           # AT: pesos_wincha
                    val_prom_saco_planta,                          # AU: peso_saco_wincha
                    val_block_planta,                              # AV: peso_block real
                    val_plus_planta,                               # AW: porcentaje_plus_planta
                    serial_caps_filas_ax                           # AX: CAPACIDADES_POR_FILA_SERIAL (Columna 50)
                ]

                es_modo_nuevo = (modo_operacion == "Nuevo Contenedor")
                ok, res_msg = guardar_o_actualizar_contenedor(get_gspread_client, fila_maestra, forzar_nuevo=es_modo_nuevo)

                if ok:
                    st.success(f"🎉 {res_msg}")
                    st.session_state.emb_id = f"EMB-{datetime.now().strftime('%y%m%d%H%M%S')}"
                else:
                    st.error(f"🚫 {res_msg}")
            except Exception as e:
                st.error(f"Error al guardar en Sheets: {e}")
