import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
import numpy as np

# Configuración inicial de Streamlit
st.set_page_config(page_title="Análisis de Ventas", layout="wide")

st.markdown('<h3>Por favor, sube un archivo CSV desde la barra lateral.</h3>', unsafe_allow_html=True)

def mostrar_informacion_alumno():
    with st.container():
        st.markdown('**Legajo:** 59451')
        st.markdown('**Nombre:** Karen Florencia Urueña')
        st.markdown('**Comisión:** C2')

mostrar_informacion_alumno()

st.title("📊 Análisis de Ventas de Sucursales")

# Barra lateral para cargar archivo y seleccionar sucursal
st.sidebar.header("Cargar archivo de datos")
uploaded_file = st.sidebar.file_uploader("Sube un archivo CSV", type=["csv"])

# Verificar si se ha cargado un archivo
if uploaded_file:
    # Leer datos del CSV
    df = pd.read_csv(uploaded_file)

    # Validar columnas necesarias
    columnas_necesarias = ["Sucursal", "Producto", "Unidades_vendidas", "Ingreso_total", "Costo_total", "Año", "Mes"]
    if not all(col in df.columns for col in columnas_necesarias):
        st.error("El archivo cargado no tiene las columnas necesarias.")
        st.stop()

    # Convertir a tipo datetime y ordenar
    df["Fecha"] = pd.to_datetime(df["Año"].astype(str) + "-" + df["Mes"].astype(str))
    df = df.sort_values("Fecha")

    # Actualizar el selector de sucursales con las opciones del archivo
    sucursales = ["Todas"] + df["Sucursal"].unique().tolist()
    sucursal_seleccionada = st.sidebar.selectbox("Seleccionar Sucursal", sucursales)

    # Filtrar por sucursal si no se selecciona "Todas"
    if sucursal_seleccionada != "Todas":
        df = df[df["Sucursal"] == sucursal_seleccionada]

    # Calcular métricas por producto
    resumen = df.groupby("Producto").agg(
        Precio_promedio=("Ingreso_total", lambda x: x.sum() / df.loc[x.index, "Unidades_vendidas"].sum()),
        Margen_promedio=("Ingreso_total", lambda x: (x.sum() - df.loc[x.index, "Costo_total"].sum()) / x.sum()),
        Unidades_vendidas=("Unidades_vendidas", "sum")
    ).reset_index()

    # Añadir columnas de porcentaje de cambio (últimos valores vs. anteriores)
    for producto in resumen["Producto"]:
        datos_producto = df[df["Producto"] == producto]
        datos_producto["Precio_promedio"] = datos_producto["Ingreso_total"] / datos_producto["Unidades_vendidas"]
        datos_producto["Margen_promedio"] = (datos_producto["Ingreso_total"] - datos_producto["Costo_total"]) / datos_producto["Ingreso_total"]
        
        # Calcular los cambios porcentuales
        resumen.loc[resumen["Producto"] == producto, "Precio_cambio"] = datos_producto["Precio_promedio"].pct_change().iloc[-1]
        resumen.loc[resumen["Producto"] == producto, "Margen_cambio"] = datos_producto["Margen_promedio"].pct_change().iloc[-1]
        resumen.loc[resumen["Producto"] == producto, "Unidades_cambio"] = datos_producto["Unidades_vendidas"].pct_change().iloc[-1]

    # Mostrar el resumen por producto
    st.header(f"📍 Datos de {sucursal_seleccionada}")
    for _, row in resumen.iterrows():
        with st.container():
            st.subheader(row["Producto"])
        
        # Crear dos columnas, una para las métricas y otra para el gráfico
        col1, col2 = st.columns([1, 2])  # Ajustamos la proporción

        with col1:
            # Mostrar las métricas a la izquierda del gráfico
            st.metric("Precio Promedio", f"${row['Precio_promedio']:.2f}", f"{row['Precio_cambio']:.2%}")
            margen_color = "inverse" if row["Margen_promedio"] > 0 else "red"
            st.metric("Margen Promedio", f"{row['Margen_promedio']:.2%}", f"{row['Margen_cambio']:.2%}")
            st.metric("Unidades Vendidas", f"{row['Unidades_vendidas']:,}", f"{row['Unidades_cambio']:.2%}")

        with col2:
            # Generar gráfico de evolución de ventas
            data_producto = df[df["Producto"] == row["Producto"]]
            X = np.arange(len(data_producto)).reshape(-1, 1)
            y = data_producto["Unidades_vendidas"]
            
            # Crear modelo de tendencia lineal
            modelo = LinearRegression().fit(X, y)
            tendencia = modelo.predict(X)

            # Configuración del gráfico
            fig, ax = plt.subplots(figsize=(10, 5))
            ax.plot(data_producto["Fecha"], data_producto["Unidades_vendidas"], label="Unidades Vendidas")
            ax.plot(data_producto["Fecha"], tendencia, label="Tendencia", linestyle="--", color="red")
            ax.set_title(f"Evolución de Ventas Mensual - {row['Producto']}")
            ax.set_xlabel("Fecha")
            ax.set_ylabel("Unidades Vendidas")
            ax.legend()
            ax.grid(True, which='both', linestyle='--', color='gray', alpha=0.7)
            plt.xticks(rotation=45)
            
            # Mostrar gráfico en Streamlit
            st.pyplot(fig)
            plt.close(fig)

        # Añadir un separador visual entre productos
        st.markdown("---")

