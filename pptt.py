import streamlit as st
import pandas as pd
from datetime import datetime 

# Listas maestras para selección rápida
LISTA_PRODUCTOS = [
    "Aleta Fresca",
    "Tubo de Pota",
    "Tentáculo / Rejo",
    "Pota Entera",
    "Filete de Pota",
    "Anillas / Rabas",
    "Aleta Congelada",
    "Bloque de Pota",
    "Otro (Escribir)"
]

LISTA_CALIBRES = [
    "0-300 gr",
    "300-500 gr",
    "500-1000 gr",
    "1000 UP",
    "1000-2000 gr",
    "2000-3000 gr",
    "3000 UP",
    "S/C (Sin Calibre)",
    "Otro (Escribir)"
]

def render_module(user, get_sheet, cargar_datos, registrar_log):
    nombre = user.get("nombre_completo", user.get("usuario"))
    rol = user.get("rol", "Visualizador")
    
    st.subheader("📥 Módulo 2: Ingreso de Productos Terminados (PPTT)")
    st.markdown(f"Operador: **{nombre}** | Rol: `{rol}`")
    st.markdown("---")

    camaras_disponibles = ["Camara 01", "Camara 02", "Camara 03"]

    with st.form("form_ingreso_pptt", clear_on_submit=True):
        ci1, ci2 = st.columns(2)
        with ci1:
            in_camara = st.selectbox("Cámara de Destino", camaras_disponibles)
            
            col_pos1, col_pos2 = st.columns(2)
            with col_pos1:
                nivel_sel = st.selectbox("Nivel", ["Nivel A (Piso)", "Nivel B (Medio)", "Nivel C (Alto)"])
            with col_pos2:
                columna_sel = st.selectbox("Columna", [f"Col {i}" for i in range(1, 21)])
            
            n_letra = nivel_sel.split()[1]
            c_num = columna_sel.split()[1]
            cam_n = in_camara.split()[-1].replace("0", "")
            pos_calculada = f"{n_letra}{c_num}-C{cam_n}"
            
            in_posicion = st.text_input("Código de Posición Asignado:", value=pos_calculada)
            in_codigo_palet = st.text_input("Código de Palet / Lote (Ej: PAL-2026-001)").strip()

        with ci2:
            prod_sel = st.selectbox("Producto:", LISTA_PRODUCTOS)
            in_producto = st.text_input("Especifique el Producto:").strip() if prod_sel == "Otro (Escribir)" else prod_sel

            cal_sel = st.selectbox("Calibre / Especificación:", LISTA_CALIBRES)
            in_calibre = st.text_input("Especifique el Calibre:").strip() if cal_sel == "Otro (Escribir)" else cal_sel

            in_cajas = st.number_input("Cantidad de Cajas / Sacos", min_value=1, step=1, value=40)
            in_peso = st.number_input("Peso Total (kg)", min_value=0.0, step=0.5, value=1000.0)
        
        btn_guardar_ingreso = st.form_submit_button("📥 Confirmar Ingreso de PPTT y Guardar", use_container_width=True)

        if btn_guardar_ingreso:
            if not in_posicion or not in_codigo_palet or not in_producto:
                st.error("Completa la posición, código de palet y producto para guardar.")
            else:
                try:
                    ws_inv = get_sheet("Inventario")
                    fecha_hoy = datetime.now().strftime("%Y-%m-%d %H:%M")
                    ws_inv.append_row([
                        in_camara, in_posicion, str(in_codigo_palet), in_producto,
                        in_calibre, str(in_cajas), str(in_peso), fecha_hoy, nombre, "Ocupado"
                    ])
                    registrar_log("INGRESO", in_camara, in_posicion, in_codigo_palet, in_producto, in_cajas, nombre)
                    st.success(f"✅ ¡Palet {in_codigo_palet} registrado con éxito en {in_posicion}!")
                except Exception as e:
                    st.error(f"Error al guardar el ingreso: {e}")
