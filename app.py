import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

# Mostrar la mini guía introductoria
st.markdown("""
# 🛠 Herramienta de Auditoría de Sistemas

### 🎯 **Objetivo**:
La aplicación realiza **auditorías automáticas** en archivos **Excel o CSV** para detectar problemas en **transacciones comerciales** y **registros laborales**.

### 🚀 **Cómo Usar**:

1. **Sube un archivo (Excel o CSV)** con tus datos.
2. La aplicación realiza las siguientes pruebas de auditoría:
   
   **1. Detección de Facturas Duplicadas**  
   ✔️ Verifica si **facturas** o **transacciones** se repiten.

   **2. Detección de Montos Inusuales**  
   ✔️ Identifica **transacciones** con **montos altos** que superen un umbral.

   **3. Conciliación de Reportes**  
   ✔️ Compara diferentes hojas o conjuntos de datos para encontrar **diferencias**.

   **4. Revisión de Registros Fuera de Horario**  
   ✔️ Detecta **registros** ingresados **fuera de horario laboral**.

   **5. Revisión de Horas Extras**  
   ✔️ Compara **horas trabajadas** con el **límite legal** de horas extras.

3. **Visualiza los resultados** en **gráficos** y **tablas**.
4. **Descarga los resultados** en **CSV**.
""")

# Cargar archivo (con múltiples hojas)
uploaded_file = st.file_uploader("Cargar archivo (CSV/Excel)", type=["csv", "xlsx"])

if uploaded_file is not None:
    # Si es un archivo Excel, leer las hojas disponibles
    if uploaded_file.name.endswith('.xlsx'):
        xls = pd.ExcelFile(uploaded_file)
        sheet_names = xls.sheet_names
        
        # Verificar si hay hojas en el archivo
        if len(sheet_names) == 0:
            st.error("El archivo Excel no contiene hojas.")
        else:
            selected_sheets = st.multiselect("Selecciona las hojas para el análisis cruzado:", sheet_names)

            # Verificar que al menos se haya seleccionado una hoja
            if not selected_sheets:
                st.warning("Por favor selecciona al menos una hoja para el análisis.")
            else:
                # Leer las hojas seleccionadas
                dfs = [pd.read_excel(xls, sheet_name=sheet) for sheet in selected_sheets]
                
                # Combinar las hojas seleccionadas en un solo DataFrame
                combined_df = pd.concat(dfs, ignore_index=True)

                # Mostrar las primeras filas del DataFrame combinado
                st.write("Datos combinados de las hojas seleccionadas:")
                st.dataframe(combined_df.head())
    
    # Si es un archivo CSV
    else:
        st.error("El archivo debe ser un archivo Excel.")
    
    # **1️⃣ Detección de Facturas Duplicadas**
    st.subheader("Prueba de Facturas Duplicadas")
    
    # Leer automáticamente todas las columnas del archivo Excel
    columns_to_check = combined_df.columns.tolist()
    
    # Permitir al usuario seleccionar las columnas para detectar duplicados
    selected_columns = st.multiselect("Selecciona las columnas para detectar duplicados:", columns_to_check)

    if selected_columns:
        # Permitir que el usuario aplique filtros por las columnas seleccionadas
        filtered_df = combined_df
        for column in selected_columns:
            filter_value = st.text_input(f"Filtra por {column}:", key=f"filter_{column}")
            if filter_value:
                filtered_df = filtered_df[filtered_df[column].astype(str).str.contains(filter_value, case=False, na=False)]
        
        # Detectar duplicados
        duplicados_df = filtered_df[filtered_df.duplicated(subset=selected_columns, keep=False)]
        
        if not duplicados_df.empty:
            st.write(f"Facturas duplicadas detectadas por las columnas: {', '.join(selected_columns)}:")
            st.dataframe(duplicados_df)
            
            # Visualización: Gráfico de barras de duplicados
            fig, ax = plt.subplots(figsize=(10, 6))
            duplicados_count = duplicados_df[selected_columns[0]].value_counts()  # Contar duplicados por la primera columna seleccionada
            ax.bar(duplicados_count.index.astype(str), duplicados_count.values, color='orange', edgecolor='black')
            ax.set_xlabel(selected_columns[0])
            ax.set_ylabel('Frecuencia')
            ax.set_title(f'Duplicados en {selected_columns[0]}')
            st.pyplot(fig)
            
            # Análisis, alerta y conclusión
            st.write(f"**Análisis**: Se han encontrado duplicados en las facturas o transacciones seleccionadas. Esto puede ser indicativo de errores en el registro o posible fraude.")
            st.warning(f"**Alerta**: Es recomendable revisar las transacciones duplicadas para evitar pagos duplicados o registros erróneos.")
            st.success(f"**Conclusión**: Se recomienda realizar una revisión detallada de las transacciones detectadas como duplicadas.")
        else:
            st.write(f"No se detectaron duplicados por las columnas: {', '.join(selected_columns)}.")
    else:
        st.write("Por favor, selecciona las columnas para detectar duplicados.")

    # **2️⃣ Detección de Montos Inusuales**
    st.subheader("Prueba de Montos Inusuales")
    threshold = st.number_input("Establece el umbral de monto ($)", min_value=0, value=10000, step=1000)
    
    numeric_columns = combined_df.select_dtypes(include='number').columns
    for col in numeric_columns:
        montos_inusuales = combined_df[combined_df[col] > threshold]  # Detectar montos
        if not montos_inusuales.empty:
            st.write(f"Montos inusuales en la columna {col}:")
            st.dataframe(montos_inusuales)
            
            # Análisis, alerta y conclusión
            st.write(f"**Análisis**: Se han detectado montos que superan el umbral establecido. Esto podría indicar transacciones irregulares o fraudulentas.")
            st.warning(f"**Alerta**: Es importante investigar las transacciones con montos fuera del umbral para verificar su legitimidad.")
            st.success(f"**Conclusión**: Se recomienda una revisión exhaustiva de las transacciones con montos inusuales para prevenir fraudes.")

    # **3️⃣ Conciliación de Reportes**
    st.subheader("Prueba de Conciliación de Reportes")
    
    # Selección de las hojas para la conciliación
    selected_sheets_for_conciliation = st.multiselect("Selecciona las hojas para comparar:", xls.sheet_names)
    
    if len(selected_sheets_for_conciliation) == 2:
        # Leer las dos hojas seleccionadas
        df1 = pd.read_excel(xls, sheet_name=selected_sheets_for_conciliation[0])
        df2 = pd.read_excel(xls, sheet_name=selected_sheets_for_conciliation[1])

        # Mostrar las primeras filas de ambas hojas
        st.write(f"Datos de la hoja {selected_sheets_for_conciliation[0]}:")
        st.dataframe(df1.head())
        
        st.write(f"Datos de la hoja {selected_sheets_for_conciliation[1]}:")
        st.dataframe(df2.head())

        # Permitir al usuario seleccionar una columna para comparar
        common_columns = list(set(df1.columns).intersection(set(df2.columns)))
        selected_column = st.selectbox("Selecciona la columna para comparar:", common_columns)
        
        # Selección de rango de fechas para comparar
        if selected_column:
            start_date = st.date_input("Fecha de inicio", value=datetime.today() - timedelta(days=30))
            end_date = st.date_input("Fecha de fin", value=datetime.today())
            
            # Filtrar los datos por el rango de fechas seleccionado
            df1['Fecha'] = pd.to_datetime(df1[selected_column], errors='coerce')
            df2['Fecha'] = pd.to_datetime(df2[selected_column], errors='coerce')
            df1_filtered = df1[(df1['Fecha'] >= pd.to_datetime(start_date)) & (df1['Fecha'] <= pd.to_datetime(end_date))]
            df2_filtered = df2[(df2['Fecha'] >= pd.to_datetime(start_date)) & (df2['Fecha'] <= pd.to_datetime(end_date))]
            
            # Comparar los valores en la columna seleccionada
            differences = pd.merge(df1_filtered, df2_filtered, on=selected_column, how='outer', indicator=True)
            
            # Agregar una nueva columna de "Estado de Conciliación"
            differences['Estado de Conciliación'] = differences['_merge'].apply(lambda x: 'Conciliado' if x == 'both' else 'No Conciliado')
            
            # Calcular la diferencia si es numérica
            if pd.api.types.is_numeric_dtype(differences[selected_column]):
                differences['Diferencia'] = differences.apply(lambda row: row[f'{selected_column}_x'] - row[f'{selected_column}_y'] 
                                                              if pd.notnull(row[f'{selected_column}_x']) and pd.notnull(row[f'{selected_column}_y']) else None, axis=1)
            
            # Mostrar las diferencias
            st.write("Diferencias encontradas en la columna seleccionada:")
            st.dataframe(differences[differences['_merge'] != 'both'])

            # Visualización: Diferencias
            show_graph = st.checkbox("Mostrar gráfico de diferencias", value=True)
            if show_graph:
                differences_by_value = differences[selected_column].value_counts()
                fig, ax = plt.subplots(figsize=(10, 6))
                ax.bar(differences_by_value.index.astype(str), differences_by_value.values, color='green', edgecolor='black')
                ax.set_xlabel(selected_column)
                ax.set_ylabel('Frecuencia')
                ax.set_title(f'Diferencias en {selected_column}')
                st.pyplot(fig)

            # Análisis, alerta y conclusión
            st.write(f"**Análisis**: Se han encontrado diferencias entre las hojas seleccionadas, lo que indica posibles errores en los registros o información desactualizada.")
            st.warning(f"**Alerta**: Es necesario investigar y corregir las diferencias encontradas entre los reportes.")
            st.success(f"**Conclusión**: Se recomienda realizar una reconciliación exhaustiva de los datos para asegurar la consistencia entre los reportes.")

    # **4️⃣ Revisar Horarios de Registro**
    st.subheader("Prueba de Registros Fuera de Horario")
    
    # Intentar convertir las columnas de fecha a tipo datetime
    try:
        fecha_columns = combined_df.select_dtypes(include='datetime').columns.tolist()
        
        if not fecha_columns:
            for col in combined_df.columns:
                try:
                    combined_df[col] = pd.to_datetime(combined_df[col], errors='coerce')
                    if combined_df[col].isnull().sum() < len(combined_df):
                        fecha_columns.append(col)
                except Exception as e:
                    pass

        if fecha_columns:
            for col in fecha_columns:
                # Verificar si la fecha es fuera del horario de trabajo
                hora_inicio_extras = st.time_input("Hora de inicio para horas extras", value=datetime.strptime("18:00", "%H:%M").time())
                registros_fuera_horario = combined_df[(combined_df[col].dt.hour < hora_inicio_extras.hour)]  # Filtro por hora

                if not registros_fuera_horario.empty:
                    st.write(f"Registros fuera de horario en {col}:")
                    st.dataframe(registros_fuera_horario)
                    
                    # Análisis, alerta y conclusión
                    st.write(f"**Análisis**: Se han detectado registros fuera de horario laboral, lo que podría ser un indicador de irregularidades.")
                    st.warning(f"**Alerta**: Es importante revisar estos registros para verificar si son autorizados.")
                    st.success(f"**Conclusión**: Se recomienda realizar una revisión de los registros fuera de horario para tomar acciones correctivas.")

    except Exception as e:
        st.write(f"Hubo un error al procesar las fechas: {e}")

    # **5️⃣ Revisión de Horas Extras**
    st.subheader("Prueba de Horas Extras")

    limite_horas = st.number_input("Límite de horas extras (horas)", min_value=0, value=8, step=1)
    
    # Parámetro: Hora de inicio para horas extras (hora de corte)
    hora_inicio_extras = st.time_input("Hora de inicio para horas extras", value=datetime.strptime("18:00", "%H:%M").time())
    
    # Parámetro: Feriados (se pueden ingresar múltiples fechas)
    feriados_input = st.text_area("Ingresa los feriados (separados por comas, formato: YYYY-MM-DD)", 
                                  value="2022-12-25,2022-01-01")
    feriados = [datetime.strptime(f, "%Y-%m-%d").date() for f in feriados_input.split(",")]
    
    if "Hora de Entrada" in combined_df.columns and "Hora de Salida" in combined_df.columns:
        # Convertir las columnas de hora a datetime
        combined_df['Hora de Entrada'] = pd.to_datetime(combined_df['Hora de Entrada'], errors='coerce')
        combined_df['Hora de Salida'] = pd.to_datetime(combined_df['Hora de Salida'], errors='coerce')
        
        # Calcular las horas trabajadas
        combined_df['Horas Trabajadas'] = (combined_df['Hora de Salida'] - combined_df['Hora de Entrada']).dt.total_seconds() / 3600
        
        # Calcular las horas extras
        combined_df['Horas Extras'] = combined_df['Horas Trabajadas'] - limite_horas
        empleados_extras = combined_df[combined_df['Horas Extras'] > 0]

        # Verificar si las horas extras fueron aprobadas
        if "Autorizado por" in combined_df.columns:
            empleados_extras_no_aprobados = empleados_extras[empleados_extras['Autorizado por'].isnull()]

            # Mostrar empleados con horas extras no aprobadas
            if not empleados_extras_no_aprobados.empty:
                st.write("Empleados con horas extras no aprobadas detectados:")
                st.dataframe(empleados_extras_no_aprobados)

            # Mostrar empleados con horas extras aprobadas
            empleados_extras_aprobados = empleados_extras[empleados_extras['Autorizado por'].notnull()]
            if not empleados_extras_aprobados.empty:
                st.write("Empleados con horas extras aprobadas detectados:")
                st.dataframe(empleados_extras_aprobados)

            # Identificar empleados con horas extras en feriados
            empleados_extras_feriados = empleados_extras[empleados_extras['Fecha'].dt.date.isin(feriados)]
            if not empleados_extras_feriados.empty:
                st.write("Empleados con horas extras en feriados detectados:")
                st.dataframe(empleados_extras_feriados)

            # Visualización de horas extras
            show_graph = st.checkbox("Mostrar gráfico de horas extras", value=True)
            if show_graph:
                fig, ax = plt.subplots(figsize=(10, 6))
                ax.bar(empleados_extras['ID Cliente'], empleados_extras['Horas Extras'], color='orange', edgecolor='black')
                ax.set_xlabel('ID Cliente')
                ax.set_ylabel('Horas Extras')
                ax.set_title('Horas Extras por Empleado')
                st.pyplot(fig)

            # Análisis, alerta y conclusión
            st.write(f"**Análisis**: Se han identificado empleados con horas extras. Es importante verificar si fueron aprobadas y si se registraron correctamente.")
            st.warning(f"**Alerta**: Los registros de horas extras no aprobadas o en feriados deben ser revisados cuidadosamente.")
            st.success(f"**Conclusión**: Se recomienda auditar las horas extras para asegurar que cumplan con las políticas y la legalidad.")

    else:
        st.write("Las columnas 'Hora de Entrada' o 'Hora de Salida' no están presentes en los datos.")

    # **Descargar los resultados**
    if st.button("Descargar Resultados"):
        resultados_df = combined_df  # Puedes ajustar esto para exportar los resultados relevantes
        resultado_file_path = "/mnt/data/resultados_auditoria.xlsx"
        resultados_df.to_excel(resultado_file_path, index=False)
        st.success(f"Resultados descargados exitosamente: {resultado_file_path}")
