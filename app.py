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
        filtered_df = combined_df
        
        # Iterar sobre las columnas seleccionadas para aplicar los filtros correspondientes
        for col in selected_columns:
            column_type = combined_df[col].dtype
            
            # Filtros por Fecha (si la columna es de tipo fecha)
            if pd.api.types.is_datetime64_any_dtype(column_type):
                st.write(f"Filtrando por {col} (Fecha)")
                start_date = st.date_input(f"Fecha de inicio para {col}", value=datetime.today() - timedelta(days=30))
                end_date = st.date_input(f"Fecha de fin para {col}", value=datetime.today())
                filtered_df = filtered_df[filtered_df[col] >= pd.to_datetime(start_date)]
                filtered_df = filtered_df[filtered_df[col] <= pd.to_datetime(end_date)]
                st.write(f"Datos entre {start_date} y {end_date}:")
                st.dataframe(filtered_df)
            
            # Filtros por Proveedor u otro tipo de texto (si la columna es de tipo objeto, que es texto)
            elif pd.api.types.is_object_dtype(column_type):
                st.write(f"Filtrando por {col} (Texto)")
                unique_values = filtered_df[col].unique()
                selected_value = st.selectbox(f"Selecciona un valor para {col}:", unique_values)
                filtered_df = filtered_df[filtered_df[col] == selected_value]
                st.write(f"Datos para el valor '{selected_value}' en {col}:")
                st.dataframe(filtered_df)
            
            # Filtros por Monto u otro tipo numérico (si la columna es de tipo numérico)
            elif pd.api.types.is_numeric_dtype(column_type):
                st.write(f"Filtrando por {col} (Numérico)")
                min_value = st.number_input(f"{col} mínimo", min_value=0, value=int(filtered_df[col].min()))
                max_value = st.number_input(f"{col} máximo", min_value=0, value=int(filtered_df[col].max()))
                filtered_df = filtered_df[(filtered_df[col] >= min_value) & (filtered_df[col] <= max_value)]
                st.write(f"Datos con {col} entre {min_value} y {max_value}:")
                st.dataframe(filtered_df)

        # Detección de duplicados en las columnas seleccionadas
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
            
            # Visualización: Histograma
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.hist(montos_inusuales[col], bins=10, color='orange', edgecolor='black')
            ax.set_xlabel('Monto')
            ax.set_ylabel('Frecuencia')
            ax.set_title(f'Distribución de Montos Fuera de Umbral en {col}')
            st.pyplot(fig)

    # **3️⃣ Conciliación de Reportes**
    st.subheader("Prueba de Conciliación de Reportes")
    
    # Selección de fechas para el análisis
    date_column = st.selectbox("Selecciona la columna de fecha para la conciliación:", combined_df.columns)
    
    start_date = st.date_input("Fecha de inicio", value=datetime.today() - timedelta(days=30))
    end_date = st.date_input("Fecha de fin", value=datetime.today())
    
    # Filtrar los datos por el rango de fechas seleccionado
    combined_df['Fecha'] = pd.to_datetime(combined_df[date_column], errors='coerce')
    filtered_data = combined_df[(combined_df['Fecha'] >= pd.to_datetime(start_date)) & (combined_df['Fecha'] <= pd.to_datetime(end_date))]
    
    st.write(f"Datos entre {start_date} y {end_date}:")
    st.dataframe(filtered_data)

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
                registros_fuera_horario = combined_df[combined_df[col].dt.hour > 18]
                if not registros_fuera_horario.empty:
                    st.write(f"Registros fuera de horario en {col}:")
                    st.dataframe(registros_fuera_horario)

                    registros_fuera_horario_by_date = registros_fuera_horario.groupby(registros_fuera_horario[col].dt.date).size().reset_index(name='Registros Fuera de Horario')
                    fig, ax = plt.subplots(figsize=(10, 6))
                    ax.plot(registros_fuera_horario_by_date[col], registros_fuera_horario_by_date['Registros Fuera de Horario'], marker='o', color='red')
                    ax.set_xlabel('Fecha')
                    ax.set_ylabel('Registros Fuera de Horario')
                    ax.set_title(f'Registros Fuera de Horario por Día en {col}')
                    st.pyplot(fig)
    except Exception as e:
        st.write(f"Hubo un error al procesar las fechas: {e}")

    # **5️⃣ Revisión de Horas Extras**
    st.subheader("Prueba de Horas Extras")

    limite_horas = st.number_input("Límite de horas extras (horas)", min_value=0, value=8, step=1)
    
    if "Horas Trabajadas" in combined_df.columns:
        combined_df['Horas Extras'] = combined_df['Horas Trabajadas'] - limite_horas
        empleados_extras = combined_df[combined_df['Horas Extras'] > 0]

        if not empleados_extras.empty:
            st.write("Empleados con horas extras detectados:")
            st.dataframe(empleados_extras)
            
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.bar(empleados_extras['ID Cliente'], empleados_extras['Horas Extras'], color='orange', edgecolor='black')
            ax.set_xlabel('ID Cliente')
            ax.set_ylabel('Horas Extras')
            ax.set_title('Horas Extras por Empleado')
            st.pyplot(fig)
        else:
            st.write("No se detectaron empleados con horas extras.")
    else:
        st.write("La columna 'Horas Trabajadas' no está presente en los datos.")

    # **Descargar los resultados**
    if st.button("Descargar Resultados"):
        resultados_df = combined_df  # Puedes ajustar esto para exportar los resultados relevantes
        resultado_file_path = "/mnt/data/resultados_auditoria.xlsx"
        resultados_df.to_excel(resultado_file_path, index=False)
        st.success(f"Resultados descargados exitosamente: {resultado_file_path}")
