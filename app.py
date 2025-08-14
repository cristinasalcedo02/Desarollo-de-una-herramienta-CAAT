import streamlit as st
import pandas as pd
import random
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
    columns_to_check = st.multiselect(
        "Selecciona las columnas para detectar duplicados:",
        combined_df.columns.tolist()
    )
    
    if columns_to_check:
        duplicados_df = combined_df[combined_df.duplicated(subset=columns_to_check, keep=False)]
        
        if not duplicados_df.empty:
            st.write(f"Facturas duplicadas detectadas por las columnas: {', '.join(columns_to_check)}:")
            st.dataframe(duplicados_df)
            
            # Visualización: Gráfico de barras de duplicados
            fig, ax = plt.subplots(figsize=(10, 6))
            duplicados_count = duplicados_df[columns_to_check[0]].value_counts()  # Contar duplicados por la primera columna seleccionada
            ax.bar(duplicados_count.index.astype(str), duplicados_count.values, color='orange', edgecolor='black')
            ax.set_xlabel(columns_to_check[0])
            ax.set_ylabel('Frecuencia')
            ax.set_title(f'Duplicados en {columns_to_check[0]}')
            st.pyplot(fig)
        else:
            st.write(f"No se detectaron duplicados por las columnas: {', '.join(columns_to_check)}.")
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
    sheet1 = st.selectbox("Selecciona la primera hoja para la conciliación:", sheet_names)
    sheet2 = st.selectbox("Selecciona la segunda hoja para la conciliación:", sheet_names)
    
    df1 = pd.read_excel(xls, sheet_name=sheet1)
    df2 = pd.read_excel(xls, sheet_name=sheet2)
    
    common_columns = df1.columns.intersection(df2.columns).tolist()
    if common_columns:
        conciliacion = pd.merge(df1, df2, on=common_columns, how='outer', indicator=True)
        diferencias = conciliacion[conciliacion['_merge'] != 'both']
        
        if not diferencias.empty:
            st.write(f"Diferencias encontradas entre {sheet1} y {sheet2}:")
            st.dataframe(diferencias)
            
            # Visualización: Gráfico de barras de las diferencias
            if 'Monto' in diferencias.columns:
                monto_diferencias = diferencias[['ID Factura', 'Monto_x', 'Monto_y']].dropna()
                monto_diferencias = monto_diferencias.set_index('ID Factura')

                fig, ax = plt.subplots(figsize=(10, 6))
                ax.bar(monto_diferencias.index, monto_diferencias['Monto_x'] - monto_diferencias['Monto_y'], color='orange', edgecolor='black')
                ax.set_xlabel('ID Factura')
                ax.set_ylabel('Diferencia en Montos')
                ax.set_title(f'Diferencias en Montos entre {sheet1} y {sheet2}')
                st.pyplot(fig)
                
            # Si se tienen fechas, podemos graficar las diferencias por fecha
            if 'Fecha' in diferencias.columns:
                diferencias['Fecha'] = pd.to_datetime(diferencias['Fecha'])
                diferencias_por_fecha = diferencias.groupby(diferencias['Fecha'].dt.date).size().reset_index(name='Diferencias por Fecha')

                fig, ax = plt.subplots(figsize=(10, 6))
                ax.plot(diferencias_por_fecha['Fecha'], diferencias_por_fecha['Diferencias por Fecha'], marker='o', color='blue')
                ax.set_xlabel('Fecha')
                ax.set_ylabel('Número de Diferencias')
                ax.set_title(f'Diferencias por Fecha entre {sheet1} y {sheet2}')
                st.pyplot(fig)
        else:
            st.write(f"Las hojas {sheet1} y {sheet2} están conciliadas correctamente.")
    else:
        st.write(f"No hay columnas comunes entre las hojas {sheet1} y {sheet2} para conciliación.")

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