"""
Generador de diccionario de datos - Proyecto Endocarditis
Curso: Analisis de Datos I - CRISP-DM Fase 2 (Data Understanding)

Requisitos:
    pip install pandas

IMPORTANTE: ajusta RUTA_CSV a donde tengas el archivo en tu carpeta local.
"""

import pandas as pd

RUTA_CSV = "BD_Endocarditis.csv"  # <-- ajusta si el archivo esta en otra carpeta
RUTA_SALIDA_CSV = "diccionario_datos.csv"


# ---------------------------------------------------------------------
# BLOQUE 1: Carga del archivo
# sep=";" porque el CSV usa punto y coma (formato Excel/Latam)
# encoding="utf-8-sig" porque el archivo trae BOM al inicio
# ---------------------------------------------------------------------
def cargar_datos(ruta: str) -> pd.DataFrame:
    df = pd.read_csv(ruta, sep=";", encoding="utf-8-sig")
    df.columns = [c.strip() for c in df.columns]  # quita espacios sobrantes en nombres
    return df


# ---------------------------------------------------------------------
# BLOQUE 2: Limpieza estructural minima antes de perfilar
# - Renombra las columnas duplicadas para que no se pierda el significado
#   (FEVI/Valvulopatia aparecen 2 veces: al ingreso y en el ecocardiograma
#   de seguimiento; pandas les puso sufijo ".1" automaticamente)
# - Convierte a numerico las columnas que usan coma decimal (formato CO)
# ---------------------------------------------------------------------
RENOMBRAR = {
    "FEVI.1": "FEVI_ecocardiograma",
    "Valvulopatia.1": "Valvulopatia_ecocardiograma",
}


def limpiar_estructura(df: pd.DataFrame) -> pd.DataFrame:
    # Solo renombramos columnas duplicadas para que el diccionario sea legible.
    # NO se modifica ningun valor de los datos aqui -- eso es Fase 3 (Data
    # Preparation), no Fase 2 (Data Understanding).
    df = df.rename(columns=RENOMBRAR)
    return df


def es_convertible_a_numero(serie: pd.Series) -> float:
    """Retorna el % de valores no nulos que se pueden interpretar como numero
    (reemplazando coma decimal por punto)."""
    vals = serie.dropna().astype(str).str.replace(",", ".", regex=False)
    convertidos = pd.to_numeric(vals, errors="coerce")
    if len(vals) == 0:
        return 0.0
    return convertidos.notna().mean()


# ---------------------------------------------------------------------
# BLOQUE 3: Clasificacion propuesta de cada variable
# IMPORTANTE: esta clasificacion NO modifica los datos. Solo prueba, en
# memoria, si los valores podrian ser numericos/fecha para PROPONER un tipo.
# La decision de limpiar (convertir de verdad) es de la Fase 3, no de aqui.
# ---------------------------------------------------------------------
def clasificar_tipo(nombre_col: str, serie: pd.Series) -> str:
    if "fecha" in nombre_col.lower():
        return "fecha (almacenada como texto)"

    if pd.api.types.is_numeric_dtype(serie):
        return "numerica"

    # probamos convertibilidad excluyendo el placeholder "No information",
    # solo para proponer el tipo -- no se guarda ninguna conversion
    vals = serie.dropna().astype(str)
    vals_sin_placeholder = vals[vals != "No information"]
    if len(vals_sin_placeholder) > 0:
        pct_numerico = es_convertible_a_numero(vals_sin_placeholder)
        if pct_numerico >= 0.95:
            return "numerica (con placeholder de texto)"

    n_unicos = serie.nunique(dropna=True)
    if n_unicos == 0:
        return "sin datos"
    if n_unicos == 2:
        return "categorica binaria"
    if n_unicos <= 15:
        return "categorica nominal"
    return "texto libre / otro"


def detectar_observaciones(nombre_col: str, serie: pd.Series) -> str:
    """Documenta problemas de calidad detectados, SIN corregirlos.
    Esto es insumo para la Fase 3 (Data Preparation), no una correccion."""
    obs = []
    if "fecha" in nombre_col.lower():
        obs.append("Convertir a tipo fecha en fase de preparacion de datos")
    if (serie.dropna().astype(str) == "No information").any():
        obs.append("Contiene 'No information' como texto; tratar como nulo en fase de preparacion")
    return "; ".join(obs)


# ---------------------------------------------------------------------
# BLOQUE 4: Construccion del diccionario de datos
# ---------------------------------------------------------------------
def construir_diccionario(df: pd.DataFrame) -> pd.DataFrame:
    filas = []
    for col in df.columns:
        serie = df[col]
        n_no_nulos = serie.notna().sum()
        pct_nulos = round((serie.isna().sum() / len(serie)) * 100, 1)
        n_unicos = serie.nunique(dropna=True)
        tipo = clasificar_tipo(col, serie)
        observaciones = detectar_observaciones(col, serie)

        ejemplos = ", ".join([str(x) for x in serie.dropna().unique()[:5]])

        filas.append({
            "variable": col,
            "tipo_propuesto": tipo,
            "n_no_nulos": n_no_nulos,
            "pct_nulos": pct_nulos,
            "n_valores_unicos": n_unicos,
            "ejemplos_valores": ejemplos,
            "observaciones_calidad": observaciones,
            "descripcion": "",       # <- la llenas tu con criterio clinico
            "revisar_manual": tipo in ("texto libre / otro", "sin datos"),
        })
    return pd.DataFrame(filas)


# ---------------------------------------------------------------------
# BLOQUE 5: Ejecucion
# ---------------------------------------------------------------------
if __name__ == "__main__":
    df = cargar_datos(RUTA_CSV)
    df = limpiar_estructura(df)
    # OJO: df no se modifica mas alla de renombrar columnas duplicadas.
    # Ningun valor de los datos se limpia ni se convierte en este script.

    diccionario = construir_diccionario(df)

    diccionario.to_csv(RUTA_SALIDA_CSV, index=False, encoding="utf-8-sig")

    print(f"Filas: {df.shape[0]} | Columnas: {df.shape[1]}")
    print("\nDistribucion de tipos propuestos:")
    print(diccionario["tipo_propuesto"].value_counts())
    print(f"\nVariables con mas de 30% de nulos: {(diccionario['pct_nulos'] > 30).sum()}")
    print(f"Variables con observaciones de calidad: {(diccionario['observaciones_calidad'] != '').sum()}")
    print(f"Variables marcadas para revision manual: {diccionario['revisar_manual'].sum()}")
    print(f"\nArchivo generado: {RUTA_SALIDA_CSV}")

    # -------------------------------------------------------------
    # BLOQUE 6 (opcional): grafico de barras con la distribucion de
    # tipos de variable -- util como evidencia visual para el informe.
    # Requiere: pip install matplotlib
    # -------------------------------------------------------------
    import matplotlib.pyplot as plt

    conteo = diccionario["tipo_propuesto"].value_counts()
    plt.figure(figsize=(8, 5))
    conteo.plot(kind="barh")
    plt.xlabel("Numero de variables")
    plt.title("Distribucion de tipos de variable - Base Endocarditis")
    plt.tight_layout()
    plt.savefig("distribucion_tipos_variable.png", dpi=150)
    print("Grafico guardado: distribucion_tipos_variable.png")

    # -------------------------------------------------------------
    # BLOQUE 7: version en Markdown para lectura humana en GitHub
    # Se genera a partir del MISMO DataFrame que el CSV -- no se
    # escribe a mano, asi que nunca queda desincronizado.
    # Requiere: pip install tabulate
    # -------------------------------------------------------------
    columnas_para_md = [
        "variable", "tipo_propuesto", "pct_nulos",
        "n_valores_unicos", "ejemplos_valores", "observaciones_calidad",
    ]
    diccionario_md = diccionario[columnas_para_md].copy()
    diccionario_md["ejemplos_valores"] = diccionario_md["ejemplos_valores"].str.slice(0, 60)

    with open("diccionario_datos.md", "w", encoding="utf-8") as f:
        f.write("# Diccionario de datos - Base Endocarditis\n\n")
        f.write(f"Filas: {df.shape[0]} | Columnas: {df.shape[1]}\n\n")
        f.write(diccionario_md.to_markdown(index=False))

    print("Version legible guardada: diccionario_datos.md")