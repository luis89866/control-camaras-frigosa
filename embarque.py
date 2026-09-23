def guardar_o_actualizar_contenedor(get_gspread_client, datos_fila, forzar_nuevo=False):
    try:
        ws = obtener_hoja_distribuciones(get_gspread_client)
        # Obtenemos todos los valores de la columna B (CONTENEDOR)
        col_b_vals = ws.col_values(2)
        num_cont = str(datos_fila[1]).strip().upper()

        fila_idx = None
        for idx, c_val in enumerate(col_b_vals):
            if str(c_val).strip().upper() == num_cont and idx > 0:
                fila_idx = idx + 1
                break

        # Limpiar datos asegurando que no haya objetos raros
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

        # Asegurar longitud exacta de 49 columnas (A hasta AW)
        while len(datos_limpios) < 49:
            datos_limpios.append("")
        datos_limpios = datos_limpios[:49]

        if fila_idx:
            # Caso 1: Actualización de un contenedor existente
            rango_exacto = f"A{fila_idx}:AW{fila_idx}"
            try:
                ws.update(range_name=rango_exacto, values=[datos_limpios])
            except Exception:
                ws.update(rango_exacto, [datos_limpios])
            return True, f"Contenedor '{num_cont}' actualizado exitosamente en la fila {fila_idx}."
        else:
            # Caso 2: Nuevo contenedor -> Calculamos la fila real debajo del último registro
            # Usamos el largo de la columna B para saber cuál es la siguiente fila libre
            siguiente_fila = len(col_b_vals) + 1
            rango_nuevo = f"A{siguiente_fila}:AW{siguiente_fila}"
            
            try:
                ws.update(range_name=rango_nuevo, values=[datos_limpios])
            except Exception:
                ws.update(rango_nuevo, [datos_limpios])
                
            return True, f"Contenedor '{num_cont}' registrado exitosamente en la fila {siguiente_fila}."

    except Exception as e:
        return False, f"Error en Google Sheets: {str(e)}"
