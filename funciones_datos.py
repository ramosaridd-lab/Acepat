from __future__ import annotations

import json
import math
import re
import unicodedata
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from configuracion import (
    ANIO_ENTRENAMIENTO,
    ANIO_PRUEBA,
    CLASES,
    COLUMNAS_OBLIGATORIAS,
    DATA_DIR,
    EVIDENCIA_DIR,
    HOJA_DATOS,
    MUESTRA_ESPERADA,
    NOMBRE_EXCEL_ESPERADO,
    POBLACION_DECLARADA,
    PREDICTORES,
    RESULTADOS_DIR,
)


ALIASES_COLUMNAS = {
    # Encabezados técnicos originales
    "id_registro": "id_registro",
    "id_socio_anonimo": "id_socio_anonimo",
    # Posibles encabezados descriptivos usados en versiones editadas
    "codigo_del_registro": "id_registro",
    "codigo_registro": "id_registro",
    "codigo_del_socio": "id_socio_anonimo",
    "codigo_socio": "id_socio_anonimo",
    "ano": "anio",
    "ano_del_registro": "anio",
    "fecha_del_periodo": "fecha_periodo",
    "hectareas_en_produccion": "hectareas_produccion",
    "area_instalada": "area_instalada_ha",
    "numero_de_parcelas_en_produccion": "numero_parcelas_produccion",
    "produccion_toneladas": "produccion_tn",
    "produccion_en_toneladas": "produccion_tn",
    "rendimiento_toneladas_por_hectarea": "rendimiento_tn_ha",
}

COLUMNAS_NUMERICAS_BASE = [
    "anio",
    "mes",
    "hectareas_produccion",
    "area_instalada_ha",
    "numero_parcelas_produccion",
    "edad_plantacion_anios",
    "produccion_tn",
    "rendimiento_tn_ha",
    "produccion_mes_anterior_tn",
    "rendimiento_mes_anterior_tn_ha",
    "precipitacion_mes_anterior_mm",
    "precipitacion_acumulada_3_meses_mm",
    "movimientos_fertilizante_mes_anterior",
    "unidades_fertilizante_mes_anterior",
    "monto_fertilizante_mes_anterior",
    "tipos_fertilizante_mes_anterior",
    "numero_fumigaciones_mes_anterior",
    "horas_maquina_mes_anterior",
    "tanques_mes_anterior",
    "numero_plagas_mes_anterior",
]

COLUMNAS_CATEGORICAS_BASE = [
    "id_registro",
    "id_socio_anonimo",
    "comite_sectorial",
    "sexo",
    "datos_fertilizantes_mes_anterior_disponibles",
    "datos_fumigacion_mes_anterior_disponibles",
]


def normalizar_texto_columna(texto: Any) -> str:
    texto = "" if texto is None else str(texto).strip().lower()
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    texto = re.sub(r"[^a-z0-9]+", "_", texto)
    return texto.strip("_")


def normalizar_encabezados(df: pd.DataFrame) -> pd.DataFrame:
    columnas = []
    for columna in df.columns:
        limpia = normalizar_texto_columna(columna)
        columnas.append(ALIASES_COLUMNAS.get(limpia, limpia))
    df = df.copy()
    df.columns = columnas
    return df


def localizar_excel(ruta: str | Path | None = None) -> Path:
    if ruta:
        ruta_resuelta = Path(ruta).expanduser().resolve()
        if not ruta_resuelta.exists():
            raise FileNotFoundError(f"No se encontró el Excel: {ruta_resuelta}")
        return ruta_resuelta

    esperado = EVIDENCIA_DIR / NOMBRE_EXCEL_ESPERADO
    if esperado.exists():
        return esperado

    candidatos = sorted(
        p for p in EVIDENCIA_DIR.glob("*.xlsx") if not p.name.startswith("~$")
    )
    if len(candidatos) == 1:
        return candidatos[0]
    if not candidatos:
        raise FileNotFoundError(
            "No se encontró el dataset anonimizado de evidencia metodológica. "
            f"Debe existir evidencia_metodologica/{NOMBRE_EXCEL_ESPERADO}."
        )
    nombres = "\n - ".join(p.name for p in candidatos)
    raise RuntimeError(
        "Hay varios Excel en evidencia_metodologica y no se puede decidir cuál usar:\n"
        f" - {nombres}\n"
        f"Conserve el archivo esperado: {NOMBRE_EXCEL_ESPERADO}."
    )
##1
#lee el excel anonimizado y comprueba sus columnas 
def cargar_dataset(ruta: str | Path | None = None) -> tuple[pd.DataFrame, Path]:
    ruta_excel = localizar_excel(ruta)
    try:
        df = pd.read_excel(ruta_excel, sheet_name=HOJA_DATOS, engine="openpyxl")
    except ValueError as exc:
        raise ValueError(
            f"El archivo no contiene la hoja '{HOJA_DATOS}'. "
            "El programa no debe usar Dataset_Maestro ni hojas con nombres o DNI."
        ) from exc

    df = normalizar_encabezados(df)
    columnas_faltantes = [c for c in COLUMNAS_OBLIGATORIAS if c not in df.columns]
    if columnas_faltantes:
        raise ValueError(
            "El Excel no contiene todas las columnas requeridas. Faltan: "
            + ", ".join(columnas_faltantes)
        )

    for columna in COLUMNAS_NUMERICAS_BASE:
        df[columna] = pd.to_numeric(df[columna], errors="coerce")

    for columna in COLUMNAS_CATEGORICAS_BASE:
        df[columna] = (
            df[columna]
            .astype("string")
            .str.strip()
            .str.upper()
            .replace({"<NA>": pd.NA, "NAN": pd.NA, "NONE": pd.NA, "": pd.NA})
        )

    # La fecha se reconstruye con año y mes para evitar problemas de serial Excel.
    df["fecha_periodo"] = pd.to_datetime(
        dict(year=df["anio"], month=df["mes"], day=1), errors="coerce"
    )
    # Sexo desconocido, no se considera relevante para esta investigación.
    df["sexo"] = df["sexo"].fillna("DESCONOCIDO")
    df["comite_sectorial"] = df["comite_sectorial"].fillna("DESCONOCIDO")

    for indicador in [
        "datos_fertilizantes_mes_anterior_disponibles",
        "datos_fumigacion_mes_anterior_disponibles",
    ]:
        df[indicador] = df[indicador].fillna("NO").replace({"SÍ": "SI"})
    return df, ruta_excel

#el uso de seno y coseno evita representar diciembre y enero como meses distantes en un eje lineal
def agregar_variables_derivadas(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["mes_seno"] = np.sin(2 * np.pi * df["mes"] / 12.0)
    df["mes_coseno"] = np.cos(2 * np.pi * df["mes"] / 12.0)
    df["historial_mes_anterior_disponible"] = np.where(
        df["produccion_mes_anterior_tn"].notna()
        & df["rendimiento_mes_anterior_tn_ha"].notna(),
        "SI",
        "NO",
    )
    return df

#2 clasificacion por terciles
#Los cuantiles 1/3 y 2/3 se calculan unicamente sobre rendimiento de 2025 y definen BAJA, MEDIA y ALTA. 
def calcular_terciles(rendimientos_entrenamiento: pd.Series) -> tuple[float, float]:
    serie = pd.to_numeric(rendimientos_entrenamiento, errors="coerce").dropna()
    if serie.empty:
        raise ValueError("No hay rendimientos válidos para calcular los terciles.")
    q1 = float(serie.quantile(1 / 3))
    q2 = float(serie.quantile(2 / 3))
    if not math.isfinite(q1) or not math.isfinite(q2) or q1 >= q2:
        raise ValueError(f"Terciles inválidos: q1={q1}, q2={q2}")
    return q1, q2
def asignar_nivel_produccion(
    rendimiento: pd.Series, q1: float, q2: float
) -> pd.Series:
    valores = pd.to_numeric(rendimiento, errors="coerce")
    niveles = np.select(
        [valores <= q1, (valores > q1) & (valores <= q2), valores > q2],
        CLASES,
        default=None,
    )
    return pd.Series(niveles, index=rendimiento.index, dtype="string")

#3#### Se selecciona registros de 2025/2026, ordenada por fecha y aplica a ambos las clases con umbrales del entrenamiento
def preparar_entrenamiento_prueba(
    df: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, float, float]:
    df = agregar_variables_derivadas(df)
    entrenamiento = (
        df.loc[df["anio"] == ANIO_ENTRENAMIENTO]
        .sort_values(["fecha_periodo", "id_socio_anonimo"])
        .reset_index(drop=True)
    )
    prueba = (
        df.loc[df["anio"] == ANIO_PRUEBA]
        .sort_values(["fecha_periodo", "id_socio_anonimo"])
        .reset_index(drop=True)
    )
    if entrenamiento.empty or prueba.empty:
        raise ValueError(
            f"Se necesitan registros de {ANIO_ENTRENAMIENTO} para entrenar y "
            f"de {ANIO_PRUEBA} para probar."
        )

    q1, q2 = calcular_terciles(entrenamiento["rendimiento_tn_ha"])
    entrenamiento["nivel_produccion"] = asignar_nivel_produccion(
        entrenamiento["rendimiento_tn_ha"], q1, q2
    )
    prueba["nivel_produccion"] = asignar_nivel_produccion(
        prueba["rendimiento_tn_ha"], q1, q2
    )
    return entrenamiento, prueba, q1, q2

#mide tamaño, duplicados por registro/socio-periodo, valores imposibles y faltantes
# con distincion entre bloqueantes y advertencias 
def verificar_dataset(df: pd.DataFrame) -> dict[str, Any]:
    problemas: list[str] = []
    advertencias: list[str] = []

    if len(df) != MUESTRA_ESPERADA:
        problemas.append(
            f"La hoja tiene {len(df):,} filas y la muestra aprobada debe tener "
            f"{MUESTRA_ESPERADA:,}."
        )

    duplicados_id = int(df["id_registro"].duplicated().sum())
    duplicados_socio_mes = int(
        df.duplicated(["id_socio_anonimo", "anio", "mes"]).sum()
    )
    if duplicados_id:
        problemas.append(f"Hay {duplicados_id} id_registro duplicados.")
    if duplicados_socio_mes:
        problemas.append(
            f"Hay {duplicados_socio_mes} combinaciones socio-año-mes duplicadas."
        )

    if df["hectareas_produccion"].isna().any() or (
        df["hectareas_produccion"] <= 0
    ).any():
        problemas.append("Existen hectáreas en producción vacías, iguales a cero o negativas.")

    if df["rendimiento_tn_ha"].isna().any() or (df["rendimiento_tn_ha"] <= 0).any():
        problemas.append("Existen rendimientos vacíos, iguales a cero o negativos.")

    if df["produccion_tn"].isna().any() or (df["produccion_tn"] <= 0).any():
        problemas.append("Existen producciones vacías, iguales a cero o negativas.")

    anios = sorted(int(a) for a in df["anio"].dropna().unique())
    if ANIO_ENTRENAMIENTO not in anios or ANIO_PRUEBA not in anios:
        problemas.append(
            f"Los años disponibles son {anios}; se requieren "
            f"{ANIO_ENTRENAMIENTO} y {ANIO_PRUEBA}."
        )

    faltantes = {
        columna: int(df[columna].isna().sum())
        for columna in PREDICTORES
        if columna in df.columns and df[columna].isna().any()
    }
    if faltantes:
        advertencias.append(
            "Hay valores faltantes en predictores. El pipeline los tratará "
            "mediante imputación y categorías de disponibilidad."
        )

    conteo_anios = {
        str(int(anio)): int(cantidad)
        for anio, cantidad in df["anio"].value_counts().sort_index().items()
    }

    resultado = {
        "fecha_verificacion": datetime.now().isoformat(timespec="seconds"),
        "poblacion_declarada": POBLACION_DECLARADA,
        "muestra_esperada": MUESTRA_ESPERADA,
        "filas_en_excel": int(len(df)),
        "columnas_en_excel": int(len(df.columns)),
        "socios_anonimos": int(df["id_socio_anonimo"].nunique()),
        "registros_por_anio": conteo_anios,
        "duplicados_id_registro": duplicados_id,
        "duplicados_socio_anio_mes": duplicados_socio_mes,
        "faltantes_predictores": faltantes,
        "problemas_bloqueantes": problemas,
        "advertencias": advertencias,
        "apto_para_modelado": len(problemas) == 0,
    }
    return resultado


def guardar_verificacion(resultado: dict[str, Any]) -> None:
    ruta_json = RESULTADOS_DIR / "verificacion_dataset.json"
    ruta_txt = RESULTADOS_DIR / "verificacion_dataset.txt"
    ruta_json.write_text(
        json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    lineas = [
        "VERIFICACIÓN DEL DATASET ACEPAT",
        "=" * 38,
        f"Población declarada: {resultado['poblacion_declarada']:,}",
        f"Muestra esperada: {resultado['muestra_esperada']:,}",
        f"Filas encontradas: {resultado['filas_en_excel']:,}",
        f"Columnas: {resultado['columnas_en_excel']}",
        f"Socios anónimos: {resultado['socios_anonimos']}",
        f"Registros por año: {resultado['registros_por_anio']}",
        f"Apto para modelado: {'SÍ' if resultado['apto_para_modelado'] else 'NO'}",
        "",
        "Problemas bloqueantes:",
    ]
    lineas.extend(
        [f"- {p}" for p in resultado["problemas_bloqueantes"]] or ["- Ninguno"]
    )
    lineas.append("")
    lineas.append("Advertencias:")
    lineas.extend([f"- {a}" for a in resultado["advertencias"]] or ["- Ninguna"])
    lineas.append("")
    lineas.append("Faltantes por predictor:")
    if resultado["faltantes_predictores"]:
        for campo, cantidad in resultado["faltantes_predictores"].items():
            lineas.append(f"- {campo}: {cantidad}")
    else:
        lineas.append("- Ninguno")
    ruta_txt.write_text("\n".join(lineas), encoding="utf-8")


def guardar_dataset_separado(
    entrenamiento: pd.DataFrame,
    prueba: pd.DataFrame,
    q1: float,
    q2: float,
) -> Path:
    ruta = RESULTADOS_DIR / "dataset_separado_clasificado.xlsx"
    resumen = pd.DataFrame(
        [
            ["Población declarada", POBLACION_DECLARADA],
            ["Muestra total", len(entrenamiento) + len(prueba)],
            [f"Entrenamiento ({ANIO_ENTRENAMIENTO})", len(entrenamiento)],
            [f"Prueba ({ANIO_PRUEBA})", len(prueba)],
            ["Límite tercil 1 (BAJA/MEDIA)", q1],
            ["Límite tercil 2 (MEDIA/ALTA)", q2],
            ["Criterio", "Terciles calculados solo con entrenamiento 2025"],
        ],
        columns=["concepto", "valor"],
    )
    columnas_salida = [
        "id_registro",
        "id_socio_anonimo",
        "anio",
        "mes",
        "fecha_periodo",
        *PREDICTORES,
        "produccion_tn",
        "rendimiento_tn_ha",
        "nivel_produccion",
    ]
    columnas_salida = list(dict.fromkeys(columnas_salida))
    with pd.ExcelWriter(ruta, engine="openpyxl") as writer:
        resumen.to_excel(writer, sheet_name="Resumen", index=False)
        entrenamiento[columnas_salida].to_excel(
            writer, sheet_name=f"Entrenamiento_{ANIO_ENTRENAMIENTO}", index=False
        )
        prueba[columnas_salida].to_excel(
            writer, sheet_name=f"Prueba_{ANIO_PRUEBA}", index=False
        )
    return ruta
