import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# Cargar archivo (con múltiples hojas)
uploaded_file = st.file_uploader("Cargar archivo (CSV/Excel)", type=["csv", "xlsx"])

if uploaded_file is not None:
    # Si es un archivo Excel, leer las hojas disponibles
    if uploaded_file.name.endswith('.xlsx'):
        xls = pd.ExcelFile(uploaded_file)
        sheet_names = xls.sheet_names
        selected_sheets = st.multiselect("Selecciona las hojas para el análisis cruzado:", sheet_names)

        # Leer las hojas seleccionadas
        dfs = [pd.read_excel(xls, sheet_name=sheet) for sheet in selected_sheets]
        
        # Combinar las hojas seleccionadas en un solo DataFrame
        combined_df = pd.concat(dfs, ignore_index=True)

        # Mostrar las primeras filas del DataFrame combinado
        st.write("Datos combinados de las hojas seleccionadas:")
        st.dataframe(combined_df.head())
    
    # Si es un archivo CSV
    else:
        df = pd.read_csv(uploaded_file)
        st.write("Datos cargados:")
        st.dataframe(df.head())

    # **1️⃣ Detección de Facturas Duplicadas**
    st.subheader("Prueba de Facturas Duplicadas")
    # Detecta duplicados de cualquier tipo de transacción (facturas, registros, etc.)
    facturas_df = combined_df[combined_df.duplicated(subset=[col for col in combined_df.columns if 'factura' in col.lower()], keep=False)]
    if not facturas_df.empty:
        st.write("Facturas duplicadas detectadas:")
        st.dataframe(facturas_df)

    # **2️⃣ Detección de Montos Inusuales**
    st.subheader("Prueba de Montos Inusuales")
    threshold = st.number_input("Establece el umbral de monto ($)", min_value=0, value=10000, step=1000)
    
    # Filtrar montos mayores al umbral en columnas numéricas
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
    # Selección dinámica de hojas para conciliación
    sheet1 = st.selectbox("Selecciona la primera hoja para la conciliación:", sheet_names)
    sheet2 = st.selectbox("Selecciona la segunda hoja para la conciliación:", sheet_names)
    
    df1 = pd.read_excel(xls, sheet_name=sheet1)
    df2 = pd.read_excel(xls, sheet_name=sheet2)
    
    # Buscar columnas comunes entre ambas hojas
    common_columns = df1.columns.intersection(df2.columns).tolist()
    if common_columns:
        conciliacion = pd.merge(df1, df2, on=common_columns, how='outer', indicator=True)
        diferencias = conciliacion[conciliacion['_merge'] != 'both']
        
        if not diferencias.empty:
            st.write(f"Diferencias encontradas entre {sheet1} y {sheet2}:")
            st.dataframe(diferencias)
        else:
            st.write(f"Las hojas {sheet1} y {sheet2} están conciliadas correctamente.")
    else:
        st.write(f"No hay columnas comunes entre las hojas {sheet1} y {sheet2} para conciliación.")

    # **4️⃣ Revisar Horarios de Registro**
    st.subheader("Prueba de Registros Fuera de Horario")
    # Detección de registros fuera del horario
    fecha_columns = combined_df.select_dtypes(include='datetime').columns
    if fecha_columns:
        for col in fecha_columns:
            registros_fuera_horario = combined_df[combined_df[col].dt.hour > 18]  # Filtrar registros fuera de horario laboral
            if not registros_fuera_horario.empty:
                st.write(f"Registros fuera de horario en {col}:")
                st.dataframe(registros_fuera_horario)
                
                # Visualización: Gráfico de líneas de registros fuera de horario
                registros_fuera_horario_by_date = registros_fuera_horario.groupby(registros_fuera_horario[col].dt.date).size().reset_index(name='Registros Fuera de Horario')
                fig, ax = plt.subplots(figsize=(10, 6))
                ax.plot(registros_fuera_horario_by_date[col], registros_fuera_horario_by_date['Registros Fuera de Horario'], marker='o', color='red')
                ax.set_xlabel('Fecha')
                ax.set_ylabel('Registros Fuera de Horario')
                ax.set_title(f'Registros Fuera de Horario por Día en {col}')
                st.pyplot(fig)
    else:
        st.write("No se encontraron columnas de fecha para analizar registros fuera de horario.")

    # **5️⃣ Revisión de Horas Extras**
    st.subheader("Prueba de Horas Extras")
    # Cálculo de horas extras en columnas numéricas
    numeric_columns = combined_df.select_dtypes(include='number').columns
    limite_horas = st.number_input("Límite de horas extras (horas)", min_value=0, value=8, step=1)
    
    if "Horas Trabajadas" in numeric_columns:
        combined_df['Horas Extras'] = combined_df['Horas Trabajadas'] - limite_horas
        empleados_extras = combined_df[combined_df['Horas Extras'] > 0]  # Filtrar empleados con horas extras
        if not empleados_extras.empty:
            st.write("Empleados con horas extras detectados:")
            st.dataframe(empleados_extras)
        else:
            st.write("No se detectaron empleados con horas extras.")
