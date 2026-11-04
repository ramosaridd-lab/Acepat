from __future__ import annotations

import json
import math
import os
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import joblib
import numpy as np
import pandas as pd

from configuracion import BASE_DIR, DATA_DIR, MODELOS_DIR


CLASES = ["BAJA", "MEDIA", "ALTA"]
CODIGO_A_CLASE = {0: "BAJA", 1: "MEDIA", 2: "ALTA"}
PERIODO_MINIMO = (2026, 5)
HISTORIAL_PATH = DATA_DIR / "historial_predicciones.csv"

MESES = {
    1: "Enero",
    2: "Febrero",
    3: "Marzo",
    4: "Abril",
    5: "Mayo",
    6: "Junio",
    7: "Julio",
    8: "Agosto",
    9: "Septiembre",
    10: "Octubre",
    11: "Noviembre",
    12: "Diciembre",
}

CAMPOS_NUMERICOS = [
    "hectareas_produccion",
    "area_instalada_ha",
    "numero_parcelas_produccion",
    "edad_plantacion_anios",
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


class ErrorPrediccion(ValueError):
    """Error controlado que puede mostrarse directamente en la interfaz."""


def cargar_json(ruta: Path) -> dict[str, Any]:
    if not ruta.exists():
        raise FileNotFoundError(f"No se encontró el archivo requerido: {ruta}")
    return json.loads(ruta.read_text(encoding="utf-8"))


def cargar_recursos_modelo(
    base_dir: Path | None = None,
) -> tuple[Any, dict[str, Any], dict[str, Any], dict[str, Any]]:
    raiz = Path(base_dir) if base_dir else BASE_DIR
    modelos_dir = raiz / "modelos"

    ruta_modelo = modelos_dir / "modelo_ganador.joblib"
    if not ruta_modelo.exists():
        raise FileNotFoundError(
            "No se encontró modelos/modelo_ganador.joblib. "
            "Ejecute primero 01_entrenar_modelos.py y 02_probar_modelos.py."
        )

    try:
        modelo = joblib.load(ruta_modelo)
    except Exception as exc:  # pragma: no cover - depende del entorno instalado
        raise RuntimeError(
            "No fue posible abrir el modelo ganador. Compruebe que instaló "
            "las versiones indicadas en requirements.txt."
        ) from exc

    metadatos = cargar_json(modelos_dir / "metadatos_entrenamiento.json")
    ganador = cargar_json(modelos_dir / "modelo_ganador.json")
    perfil = cargar_json(modelos_dir / "perfil_interfaz.json")
    return modelo, metadatos, ganador, perfil


def periodo_anterior(anio: int, mes: int) -> tuple[int, int]:
    if mes == 1:
        return anio - 1, 12
    return anio, mes - 1


def formatear_periodo(anio: int, mes: int) -> str:
    return f"{MESES[int(mes)]} de {int(anio)}"


def periodo_es_valido(anio: int, mes: int) -> bool:
    return (int(anio), int(mes)) >= PERIODO_MINIMO


def _a_float(valor: Any, campo: str, permitir_vacio: bool = False) -> float:
    if valor is None or (isinstance(valor, str) and not valor.strip()):
        if permitir_vacio:
            return float("nan")
        raise ErrorPrediccion(f"Complete el campo: {campo}.")
    try:
        numero = float(valor)
    except (TypeError, ValueError) as exc:
        raise ErrorPrediccion(f"El campo {campo} debe ser numérico.") from exc
    if not math.isfinite(numero):
        if permitir_vacio:
            return float("nan")
        raise ErrorPrediccion(f"El campo {campo} no contiene un valor válido.")
    return numero


def validar_datos(datos: dict[str, Any], anio: int, mes: int) -> list[str]:
    errores: list[str] = []

    if not str(datos.get("nombre_socio", "")).strip():
        errores.append("Seleccione un socio o productor.")
    if not str(datos.get("comite_sectorial", "")).strip():
        errores.append("Seleccione el comité sectorial.")
    if not periodo_es_valido(anio, mes):
        errores.append(
            "El primer periodo posterior a los datos disponibles es mayo de 2026."
        )

    nombres = {
        "hectareas_produccion": "Hectáreas en producción",
        "area_instalada_ha": "Área instalada",
        "numero_parcelas_produccion": "Número de parcelas",
        "edad_plantacion_anios": "Edad de la plantación",
        "produccion_mes_anterior_tn": "Producción del mes anterior",
        "rendimiento_mes_anterior_tn_ha": "Rendimiento del mes anterior",
        "precipitacion_mes_anterior_mm": "Precipitación del mes anterior",
        "precipitacion_acumulada_3_meses_mm": "Precipitación acumulada de tres meses",
    }

    valores: dict[str, float] = {}
    for campo, etiqueta in nombres.items():
        try:
            valores[campo] = _a_float(datos.get(campo), etiqueta)
        except ErrorPrediccion as exc:
            errores.append(str(exc))

    for campo in [
        "hectareas_produccion",
        "area_instalada_ha",
        "numero_parcelas_produccion",
        "edad_plantacion_anios",
        "produccion_mes_anterior_tn",
        "rendimiento_mes_anterior_tn_ha",
    ]:
        if campo in valores and valores[campo] <= 0:
            errores.append(f"{nombres[campo]} debe ser mayor que cero.")

    for campo in [
        "precipitacion_mes_anterior_mm",
        "precipitacion_acumulada_3_meses_mm",
    ]:
        if campo in valores and valores[campo] < 0:
            errores.append(f"{nombres[campo]} no puede ser negativo.")

    if (
        "area_instalada_ha" in valores
        and "hectareas_produccion" in valores
        and valores["area_instalada_ha"] < valores["hectareas_produccion"]
    ):
        errores.append(
            "El área instalada no puede ser menor que las hectáreas en producción."
        )

    campos_no_negativos = [
        "movimientos_fertilizante_mes_anterior",
        "unidades_fertilizante_mes_anterior",
        "monto_fertilizante_mes_anterior",
        "tipos_fertilizante_mes_anterior",
        "numero_fumigaciones_mes_anterior",
        "horas_maquina_mes_anterior",
        "tanques_mes_anterior",
        "numero_plagas_mes_anterior",
    ]
    for campo in campos_no_negativos:
        valor = datos.get(campo)
        if valor is None:
            continue
        try:
            if float(valor) < 0:
                errores.append(f"{campo.replace('_', ' ').capitalize()} no puede ser negativo.")
        except (TypeError, ValueError):
            errores.append(f"{campo.replace('_', ' ').capitalize()} debe ser numérico.")

    return list(dict.fromkeys(errores))


def advertencias_fuera_de_rango(
    datos: dict[str, Any], perfil: dict[str, Any]
) -> list[str]:
    advertencias: list[str] = []
    rangos = perfil.get("rangos_entrenamiento", {})
    etiquetas = perfil.get("etiquetas", {})

    for campo, limites in rangos.items():
        valor = datos.get(campo)
        if valor is None:
            continue
        try:
            numero = float(valor)
        except (TypeError, ValueError):
            continue
        minimo = limites.get("min")
        maximo = limites.get("max")
        if minimo is None or maximo is None:
            continue
        if numero < float(minimo) or numero > float(maximo):
            etiqueta = etiquetas.get(campo, campo.replace("_", " "))
            advertencias.append(
                f"{etiqueta}: {numero:g} está fuera del rango observado durante "
                f"el entrenamiento ({float(minimo):g} a {float(maximo):g})."
            )
    return advertencias


def construir_entrada_modelo(
    datos: dict[str, Any],
    anio_objetivo: int,
    mes_objetivo: int,
    predictores: list[str],
) -> pd.DataFrame:
    errores = validar_datos(datos, anio_objetivo, mes_objetivo)
    if errores:
        raise ErrorPrediccion("\n".join(errores))

    fertilizantes_disponibles = (
        str(datos.get("datos_fertilizantes_mes_anterior_disponibles", "NO"))
        .strip()
        .upper()
        .replace("SÍ", "SI")
    )
    fumigacion_disponible = (
        str(datos.get("datos_fumigacion_mes_anterior_disponibles", "NO"))
        .strip()
        .upper()
        .replace("SÍ", "SI")
    )

    fila: dict[str, Any] = {
        "hectareas_produccion": _a_float(
            datos.get("hectareas_produccion"), "Hectáreas en producción"
        ),
        "area_instalada_ha": _a_float(
            datos.get("area_instalada_ha"), "Área instalada"
        ),
        "numero_parcelas_produccion": _a_float(
            datos.get("numero_parcelas_produccion"), "Número de parcelas"
        ),
        "edad_plantacion_anios": _a_float(
            datos.get("edad_plantacion_anios"), "Edad de la plantación"
        ),
        "produccion_mes_anterior_tn": _a_float(
            datos.get("produccion_mes_anterior_tn"),
            "Producción del mes anterior",
        ),
        "rendimiento_mes_anterior_tn_ha": _a_float(
            datos.get("rendimiento_mes_anterior_tn_ha"),
            "Rendimiento del mes anterior",
        ),
        "precipitacion_mes_anterior_mm": _a_float(
            datos.get("precipitacion_mes_anterior_mm"),
            "Precipitación del mes anterior",
        ),
        "precipitacion_acumulada_3_meses_mm": _a_float(
            datos.get("precipitacion_acumulada_3_meses_mm"),
            "Precipitación acumulada de tres meses",
        ),
        "datos_fertilizantes_mes_anterior_disponibles": fertilizantes_disponibles,
        "datos_fumigacion_mes_anterior_disponibles": fumigacion_disponible,
        "comite_sectorial": str(datos.get("comite_sectorial", "DESCONOCIDO"))
        .strip()
        .upper(),
        "sexo": str(datos.get("sexo", "DESCONOCIDO")).strip().upper(),
        "mes_seno": math.sin(2 * math.pi * int(mes_objetivo) / 12.0),
        "mes_coseno": math.cos(2 * math.pi * int(mes_objetivo) / 12.0),
        "historial_mes_anterior_disponible": "SI",
    }

    campos_fertilizantes = [
        "movimientos_fertilizante_mes_anterior",
        "unidades_fertilizante_mes_anterior",
        "monto_fertilizante_mes_anterior",
        "tipos_fertilizante_mes_anterior",
    ]
    campos_fumigacion = [
        "numero_fumigaciones_mes_anterior",
        "horas_maquina_mes_anterior",
        "tanques_mes_anterior",
        "numero_plagas_mes_anterior",
    ]

    for campo in campos_fertilizantes:
        fila[campo] = (
            _a_float(datos.get(campo, 0), campo, permitir_vacio=True)
            if fertilizantes_disponibles == "SI"
            else float("nan")
        )
    for campo in campos_fumigacion:
        fila[campo] = (
            _a_float(datos.get(campo, 0), campo, permitir_vacio=True)
            if fumigacion_disponible == "SI"
            else float("nan")
        )

    faltantes = [campo for campo in predictores if campo not in fila]
    if faltantes:
        raise ErrorPrediccion(
            "No se pudieron construir todos los predictores: " + ", ".join(faltantes)
        )

    return pd.DataFrame([{campo: fila[campo] for campo in predictores}])


def _etiqueta_clase(valor: Any) -> str:
    if isinstance(valor, (np.integer, int)):
        return CODIGO_A_CLASE.get(int(valor), str(valor))
    texto = str(valor).strip().upper()
    if texto.isdigit():
        return CODIGO_A_CLASE.get(int(texto), texto)
    return texto


def ejecutar_prediccion(
    modelo: Any,
    entrada: pd.DataFrame,
) -> tuple[str, dict[str, float]]:
    prediccion_cruda = modelo.predict(entrada)[0]
    nivel = _etiqueta_clase(prediccion_cruda)
    if nivel not in CLASES:
        raise ErrorPrediccion(f"El modelo devolvió una clase desconocida: {nivel}")

    probabilidades = {clase: 0.0 for clase in CLASES}
    if hasattr(modelo, "predict_proba"):
        valores = modelo.predict_proba(entrada)[0]
        clases_modelo = getattr(modelo, "classes_", range(len(valores)))
        for clase_modelo, probabilidad in zip(clases_modelo, valores, strict=False):
            etiqueta = _etiqueta_clase(clase_modelo)
            if etiqueta in probabilidades:
                probabilidades[etiqueta] = float(probabilidad)
    else:  # pragma: no cover - el modelo ganador actual sí implementa predict_proba
        probabilidades[nivel] = 1.0

    total = sum(probabilidades.values())
    if total > 0:
        probabilidades = {
            clase: probabilidad / total
            for clase, probabilidad in probabilidades.items()
        }
    return nivel, probabilidades


def construir_registro_resultado(
    datos: dict[str, Any],
    anio_objetivo: int,
    mes_objetivo: int,
    nivel: str,
    probabilidades: dict[str, float],
    ganador: dict[str, Any],
) -> dict[str, Any]:
    anio_base, mes_base = periodo_anterior(anio_objetivo, mes_objetivo)
    ahora = datetime.now(ZoneInfo("America/Lima"))
    return {
        "fecha_hora_prediccion": ahora.isoformat(timespec="seconds"),
        "codigo_socio": str(datos.get("codigo_socio", "")).strip(),
        "nombre_socio": str(datos.get("nombre_socio", "")).strip(),
        "dni": str(datos.get("dni", "")).strip(),
        "comite_sectorial": str(datos.get("comite_sectorial", "")).strip(),
        "periodo_base": formatear_periodo(anio_base, mes_base),
        "periodo_predicho": formatear_periodo(anio_objetivo, mes_objetivo),
        "nivel_predicho": nivel,
        "probabilidad_baja": probabilidades.get("BAJA", 0.0),
        "probabilidad_media": probabilidades.get("MEDIA", 0.0),
        "probabilidad_alta": probabilidades.get("ALTA", 0.0),
        "modelo": ganador.get("modelo", "Modelo ganador"),
        "f1_macro_prueba": ganador.get("f1_macro"),
        "accuracy_prueba": ganador.get("accuracy"),
    }


def guardar_historial(
    registro: dict[str, Any], ruta: Path | None = None
) -> Path:
    destino = Path(ruta) if ruta else HISTORIAL_PATH
    destino.parent.mkdir(parents=True, exist_ok=True)

    nuevo = pd.DataFrame([registro])
    if destino.exists():
        try:
            actual = pd.read_csv(destino, encoding="utf-8-sig")
        except pd.errors.EmptyDataError:
            actual = pd.DataFrame()
        historial = pd.concat([actual, nuevo], ignore_index=True)
    else:
        historial = nuevo

    temporal = destino.with_suffix(destino.suffix + ".tmp")
    historial.to_csv(temporal, index=False, encoding="utf-8-sig")
    os.replace(temporal, destino)
    return destino


def leer_historial(ruta: Path | None = None) -> pd.DataFrame:
    origen = Path(ruta) if ruta else HISTORIAL_PATH
    if not origen.exists():
        return pd.DataFrame()
    try:
        return pd.read_csv(origen, encoding="utf-8-sig")
    except pd.errors.EmptyDataError:
        return pd.DataFrame()


def generar_excel_resultado(
    registro: dict[str, Any], datos_entrada: dict[str, Any]
) -> bytes:
    resumen = pd.DataFrame(
        [
            ["Socio", registro.get("nombre_socio", "")],
            ["DNI", registro.get("dni", "")],
            ["Comité sectorial", registro["comite_sectorial"]],
            ["Periodo base", registro["periodo_base"]],
            ["Periodo predicho", registro["periodo_predicho"]],
            ["Nivel predicho", registro["nivel_predicho"]],
            ["Modelo utilizado", registro["modelo"]],
            ["Fecha y hora", registro["fecha_hora_prediccion"]],
        ],
        columns=["Campo", "Valor"],
    )
    probabilidades = pd.DataFrame(
        {
            "Nivel": ["BAJA", "MEDIA", "ALTA"],
            "Probabilidad": [
                registro["probabilidad_baja"],
                registro["probabilidad_media"],
                registro["probabilidad_alta"],
            ],
        }
    )
    entradas = pd.DataFrame(
        [
            [clave.replace("_", " ").capitalize(), valor]
            for clave, valor in datos_entrada.items()
            if clave not in {"codigo_socio", "nombre_socio", "dni"}
        ],
        columns=["Dato ingresado", "Valor"],
    )

    salida = BytesIO()
    with pd.ExcelWriter(salida, engine="openpyxl") as escritor:
        resumen.to_excel(escritor, sheet_name="Resultado", index=False)
        probabilidades.to_excel(escritor, sheet_name="Probabilidades", index=False)
        entradas.to_excel(escritor, sheet_name="Datos ingresados", index=False)

        for hoja in escritor.book.worksheets:
            hoja.freeze_panes = "A2"
            hoja.auto_filter.ref = hoja.dimensions
            for celda in hoja[1]:
                celda.font = celda.font.copy(bold=True)
            for columna in hoja.columns:
                ancho = min(
                    max(len(str(celda.value)) if celda.value is not None else 0 for celda in columna)
                    + 2,
                    45,
                )
                hoja.column_dimensions[columna[0].column_letter].width = max(ancho, 12)

        hoja_prob = escritor.book["Probabilidades"]
        for celda in hoja_prob["B"][1:]:
            celda.number_format = "0.00%"

    return salida.getvalue()
