"""
Limpieza de datos - Proyecto Endocarditis Infecciosa
Curso: Análisis de Datos I - CRISP-DM Fase 3 (Data Preparation)

Este script implementa las estrategias definidas para:
  1. Tratamiento de datos nulos
  2. Tratamiento de outliers
  3. Estandarización de tipos de datos

Requisitos:
    pip install pandas numpy
"""

import pandas as pd
import numpy as np
from copy import deepcopy

RUTA_CSV = "/mnt/user-data/uploads/BD_Endocarditis.csv"
RUTA_SALIDA = "/mnt/user-data/outputs/BD_Endocarditis_limpia.csv"
RUTA_LOG = "/mnt/user-data/outputs/log_limpieza.txt"

log_cambios = []

def log(msg: str):
    log_cambios.append(msg)
    print(msg)


# =====================================================================
# BLOQUE 1: CARGA Y ESTRUCTURA BÁSICA
# =====================================================================
def cargar_datos(ruta: str) -> pd.DataFrame:
    df = pd.read_csv(ruta, sep=";", encoding="utf-8-sig")
    df.columns = [c.strip() for c in df.columns]
    df = df.rename(columns={
        "FEVI.1": "FEVI_ecocardiograma",
        "Valvulopatia.1": "Valvulopatia_ecocardiograma",
    })
    log(f"[CARGA] Dimensiones originales: {df.shape[0]} filas x {df.shape[1]} columnas")
    return df


# =====================================================================
# BLOQUE 2: UNIFICAR "No information" COMO NaN
# Estrategia: "No information" es un placeholder de texto que
# representa un dato faltante. Convertirlo a NaN real permite que
# pandas lo maneje de forma consistente.
# =====================================================================
def unificar_nulos(df: pd.DataFrame) -> pd.DataFrame:
    placeholders = ["No information", "No Information", "no information",
                     "NO INFORMATION", "N/A", "n/a", ""]
    count_before = df.isnull().sum().sum()
    for col in df.columns:
        if df[col].dtype == object:
            df[col] = df[col].str.strip()
            df[col] = df[col].replace(placeholders, np.nan)
    count_after = df.isnull().sum().sum()
    log(f"[NULOS] 'No information' → NaN: {count_after - count_before} valores convertidos")
    return df


# =====================================================================
# BLOQUE 3: CORRECCIÓN DE ERRORES DE DIGITACIÓN
# Casos identificados en el diagnóstico exploratorio.
# Cada corrección se documenta con su justificación clínica.
# =====================================================================
def corregir_errores_digitacion(df: pd.DataFrame) -> pd.DataFrame:
    log("[ERRORES] Correcciones de digitación:")

    # --- 3a: IDs 37 y 77 — Sodio y Potasio intercambiados ---
    # Justificación: Potasio normal = 3.5-5.5 mEq/L, Sodio normal = 135-145 mEq/L.
    # ID 37 tiene K=130.9, Na=3.74 → claramente invertidos.
    # ID 77 tiene K=136.0, Na=4.45 → claramente invertidos.
    for pid in [37, 77]:
        mask = df["ID"] == pid
        if mask.any():
            # Leer valores actuales (pueden tener coma decimal)
            k_val = df.loc[mask, "Potasio"].values[0]
            na_val = df.loc[mask, "Sodio"].values[0]
            # Intercambiar
            df.loc[mask, "Potasio"] = na_val
            df.loc[mask, "Sodio"] = k_val
            log(f"  ID {pid}: Sodio↔Potasio intercambiados (K={k_val}→{na_val}, Na={na_val}→{k_val})")

    # --- 3b: ID 58 — Días de estancia = 517 ---
    # Justificación: verificado con fechas (ingreso 7/10/20, egreso 8/03/22).
    # Son ~517 días reales. Se mantiene como dato válido pero se marca.
    log("  ID 58: Días estancia=517 (verificado con fechas, es real → se conserva)")

    # --- 3c: ID 40 — Edad = 0, Peso = 3 kg, Talla = 50 cm ---
    # Justificación: es un neonato. Datos coherentes entre sí. Se conserva.
    log("  ID 40: Edad=0, Peso=3kg, Talla=50cm (neonato, datos coherentes → se conserva)")

    # --- 3d: Procalcitonina ID 118 = 63,700 ---
    # Justificación: valor extremadamente alto. Posible error de unidades o
    # digitación. Se convierte a NaN para no distorsionar análisis.
    mask_118 = df["ID"] == 118
    if mask_118.any():
        df.loc[mask_118, "Procalcitonina"] = np.nan
        log("  ID 118: Procalcitonina=63700 → NaN (valor fuera de rango clínico plausible)")

    return df


# =====================================================================
# BLOQUE 4: CONVERSIÓN DE TIPOS DE DATOS
# =====================================================================
def convertir_tipos(df: pd.DataFrame) -> pd.DataFrame:
    log("[TIPOS] Conversión de tipos de datos:")

    # --- 4a: Columnas numéricas con coma decimal ---
    cols_numericas_coma = [
        "Peso", "Talla", "IMC",
        "Presion arterial sistolica", "Presion arterial diastolica",
        "Presion arterial media", "Frecuencia cardiaca", "Frecuencia respiratoria",
        "Leucocitos", "Linfocitos", "Neutrofilos", "Hemoglobina",
        "Velocidad eritrosedimentacion", "Proteina C reactiva",
        "Factor reumatoideo", "Creatinina", "Nitrogeno ureico",
        "NT proBNP BNP", "Troponina I ultrasensible", "Troponina T",
        "Procalcitonina", "Potasio", "Sodio", "AST", "ALT",
        "FEVI_ecocardiograma",
    ]
    converted = 0
    for col in cols_numericas_coma:
        if col in df.columns and df[col].dtype == object:
            df[col] = df[col].astype(str).str.replace(",", ".", regex=False)
            df[col] = pd.to_numeric(df[col], errors="coerce")
            converted += 1
    log(f"  {converted} columnas: coma decimal → punto, convertidas a float")

    # --- 4b: Fechas ---
    cols_fecha = [c for c in df.columns if "fecha" in c.lower()]
    for col in cols_fecha:
        df[col] = pd.to_datetime(df[col], dayfirst=True, errors="coerce")
    log(f"  {len(cols_fecha)} columnas de fecha convertidas: {cols_fecha}")

    return df


# =====================================================================
# BLOQUE 5: ESTRATEGIA DE NULOS — POR GRUPO DE VARIABLES
# =====================================================================
def tratar_nulos(df: pd.DataFrame) -> pd.DataFrame:
    log("[NULOS] Estrategias de tratamiento:")
    n = len(df)

    # --- 5a: Eliminar columnas con >70% de nulos ---
    # Justificación: con >70% faltante no hay suficiente información
    # para imputar confiablemente. Se documentan pero se descartan.
    pct_nulos = df.isnull().mean() * 100
    cols_eliminar = pct_nulos[pct_nulos > 70].index.tolist()

    # Proteger la variable "Causa de muerte" (útil para análisis descriptivo)
    cols_eliminar_final = [c for c in cols_eliminar if c != "Causa de muerte"]
    df = df.drop(columns=cols_eliminar_final)
    log(f"  ELIMINADAS {len(cols_eliminar_final)} columnas con >70% nulos:")
    for c in cols_eliminar_final:
        log(f"    - {c} ({pct_nulos[c]:.1f}% nulos)")

    # --- 5b: Variables categóricas binarias — imputar con la MODA ---
    # Justificación: para variables Sí/No con pocos faltantes (<10%),
    # la moda es la estrategia más conservadora.
    cols_bin = df.select_dtypes(include="object").columns
    for col in cols_bin:
        n_unicos = df[col].nunique(dropna=True)
        pct_null = df[col].isnull().mean() * 100
        if n_unicos == 2 and 0 < pct_null <= 10:
            moda = df[col].mode()[0]
            n_imp = df[col].isnull().sum()
            df[col] = df[col].fillna(moda)
            log(f"  {col}: {n_imp} nulos → moda ('{moda}')")

    # --- 5c: Variables numéricas con <30% nulos — imputar con MEDIANA ---
    # Justificación: la mediana es robusta a outliers y no asume normalidad.
    cols_num = df.select_dtypes(include=[np.number]).columns
    for col in cols_num:
        pct_null = df[col].isnull().mean() * 100
        if 0 < pct_null <= 30:
            mediana = df[col].median()
            n_imp = df[col].isnull().sum()
            df[col] = df[col].fillna(mediana)
            log(f"  {col}: {n_imp} nulos → mediana ({mediana:.2f})")

    # --- 5d: FEVI (73% nulos → ya eliminada en 5a) ---
    # Nota: FEVI tiene 73% nulos. Fue eliminada en el paso 5a.
    # Para el modelo, se puede usar FEVI_ecocardiograma si está disponible,
    # o Falla cardiaca como proxy de disfunción cardíaca.
    if "FEVI" in df.columns:
        log("  FEVI: 73% nulos — conservada pero NO imputada (decisión del grupo)")
    else:
        log("  FEVI: eliminada por >70% nulos. Usar 'Falla cardiaca' como proxy en modelo")

    # --- 5e: Variables categóricas nominales con 30-70% nulos ---
    # Se conservan sin imputar. Imputar categorías con alta ausencia
    # introduce sesgo. Se manejan como categoría "Desconocido" si se
    # requieren en análisis futuros.
    cols_cat_alto_nulo = []
    for col in df.select_dtypes(include="object").columns:
        pct_null = df[col].isnull().mean() * 100
        if 30 < pct_null <= 70:
            cols_cat_alto_nulo.append((col, pct_null))
    if cols_cat_alto_nulo:
        log(f"  {len(cols_cat_alto_nulo)} variables categóricas con 30-70% nulos → sin imputar:")
        for c, p in cols_cat_alto_nulo:
            log(f"    - {c} ({p:.1f}%)")

    return df


# =====================================================================
# BLOQUE 6: TRATAMIENTO DE OUTLIERS
# =====================================================================
def tratar_outliers(df: pd.DataFrame) -> pd.DataFrame:
    log("[OUTLIERS] Estrategia: Winsorización (capping) al percentil 1-99")
    log("  Justificación: conserva la observación reemplazando el valor")
    log("  extremo por el límite del percentil. Apropiado para variables")
    log("  clínicas donde los extremos pueden ser reales pero distorsionan.")

    # Variables clínicas a winsorizar (excluir ID, Edad, Días)
    cols_winsorizar = [
        "Peso", "Talla", "IMC",
        "Presion arterial sistolica", "Presion arterial diastolica",
        "Presion arterial media", "Frecuencia cardiaca", "Frecuencia respiratoria",
        "Leucocitos", "Linfocitos", "Neutrofilos", "Hemoglobina",
        "Creatinina", "Nitrogeno ureico",
        "Proteina C reactiva", "Potasio", "Sodio", "AST", "ALT",
    ]

    for col in cols_winsorizar:
        if col not in df.columns or not pd.api.types.is_numeric_dtype(df[col]):
            continue
        valid = df[col].dropna()
        if len(valid) < 10:
            continue

        p1 = valid.quantile(0.01)
        p99 = valid.quantile(0.99)
        n_low = (df[col] < p1).sum()
        n_high = (df[col] > p99).sum()

        if n_low + n_high > 0:
            df[col] = df[col].clip(lower=p1, upper=p99)
            log(f"  {col}: {n_low} bajos (→{p1:.1f}), {n_high} altos (→{p99:.1f})")

    # --- Outliers que NO se tocan ---
    log("\n  Variables con outliers conservados (justificación clínica):")
    log("    - Edad: rango 0-89, incluye neonatos (legítimo)")
    log("    - Dias estancia: ID 58=517 días (verificado con fechas)")
    log("    - Dias antibiotico: tratamientos prolongados son clínicamente posibles")
    log("    - Dias de estancia en UCI: variabilidad esperada en UCI")

    return df


# =====================================================================
# BLOQUE 7: LIMPIEZA DE LA VARIABLE OBJETIVO
# =====================================================================
def limpiar_variable_objetivo(df: pd.DataFrame) -> pd.DataFrame:
    target = "Estado vital al  finalizar hospitalizacion"
    log(f"\n[OBJETIVO] Variable: '{target}'")
    log(f"  Distribución original: {df[target].value_counts().to_dict()}")

    # Los 12 pacientes "Remitido" se excluyen del análisis de mortalidad
    # porque su desenlace final es desconocido.
    n_remitidos = (df[target] == "Remitido").sum()
    df = df[df[target] != "Remitido"].copy()
    log(f"  Excluidos {n_remitidos} pacientes 'Remitido' (desenlace desconocido)")

    # Codificación binaria para el modelo
    df["Mortalidad"] = (df[target] == "Muerto").astype(int)
    log(f"  Nueva columna 'Mortalidad': 1=Muerto, 0=Vivo")
    log(f"  Distribución final: {df['Mortalidad'].value_counts().to_dict()}")

    return df


# =====================================================================
# BLOQUE 8: RESUMEN FINAL
# =====================================================================
def resumen_final(df: pd.DataFrame):
    log(f"\n{'=' * 60}")
    log("RESUMEN POST-LIMPIEZA")
    log(f"{'=' * 60}")
    log(f"  Dimensiones: {df.shape[0]} filas x {df.shape[1]} columnas")
    log(f"  Nulos restantes: {df.isnull().sum().sum()} ({(df.isnull().mean().mean()*100):.1f}% promedio)")
    log(f"  Variable objetivo — Mortalidad: {df['Mortalidad'].value_counts().to_dict()}")

    # Variables clave para las hipótesis
    log(f"\n  Estado de variables para hipótesis:")
    for v in ["Falla cardiaca", "FEVI", "Staphylococcus aureus", "Edad", "Mortalidad"]:
        if v in df.columns:
            nulos = df[v].isnull().sum()
            log(f"    ✓ {v}: presente, {nulos} nulos")
        else:
            log(f"    ✗ {v}: NO presente (eliminada o renombrada)")


# =====================================================================
# EJECUCIÓN
# =====================================================================
if __name__ == "__main__":
    df = cargar_datos(RUTA_CSV)
    df = unificar_nulos(df)
    df = corregir_errores_digitacion(df)
    df = convertir_tipos(df)
    df = tratar_nulos(df)
    df = tratar_outliers(df)
    df = limpiar_variable_objetivo(df)
    resumen_final(df)

    # Guardar
    df.to_csv(RUTA_SALIDA, index=False, encoding="utf-8-sig")
    log(f"\n[GUARDADO] {RUTA_SALIDA}")

    # Guardar log
    with open(RUTA_LOG, "w", encoding="utf-8") as f:
        f.write("\n".join(log_cambios))
    log(f"[LOG] {RUTA_LOG}")
