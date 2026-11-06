from __future__ import annotations

from pathlib import Path

######
# 1 Rutas del proyecto

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
EVIDENCIA_DIR = BASE_DIR / "evidencia_metodologica"
MODELOS_DIR = BASE_DIR / "modelos"
RESULTADOS_DIR = BASE_DIR / "resultados"
MATRICES_DIR = RESULTADOS_DIR / "matrices_confusion"
LOGS_DIR = BASE_DIR / "logs"

NOMBRE_EXCEL_ESPERADO = "Dataset_ACEPAT_ML_Anonimizado_7150.xlsx"
HOJA_DATOS = "Muestra_7150"

#####
# 2 Parámetros metodológicos aprobados para la tesis
POBLACION_DECLARADA = 10_000
MUESTRA_ESPERADA = 7_150
ANIO_ENTRENAMIENTO = 2025
ANIO_PRUEBA = 2026
SEMILLA = 2026

# True: rejilla pequeña para ejecutar más rápido durante el desarrollo.
# False: rejilla más amplia para la ejecución final de la tesis.
MODO_RAPIDO = False

CLASES = ["BAJA", "MEDIA", "ALTA"]

# Los algoritmos trabajan internamente con códigos numéricos. Esto evita
# incompatibilidades del backend optimizado de KNN con etiquetas de texto.
# En los reportes y archivos de salida se conservan BAJA, MEDIA y ALTA.
CLASE_A_CODIGO = {clase: indice for indice, clase in enumerate(CLASES)}
CODIGO_A_CLASE = {indice: clase for clase, indice in CLASE_A_CODIGO.items()}
CODIGOS_CLASES = list(range(len(CLASES)))

#####
# 3 No se incluyen produccion_tn ni rendimiento_tn_ha porque construyen la
# respuesta real del mes actual y producirían fuga de información.
PREDICTORES_NUMERICOS = [
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
    "mes_seno",
    "mes_coseno",
]

PREDICTORES_CATEGORICOS = [
    "comite_sectorial",
    "sexo",
    "datos_fertilizantes_mes_anterior_disponibles",
    "datos_fumigacion_mes_anterior_disponibles",
    "historial_mes_anterior_disponible",
]

PREDICTORES = PREDICTORES_NUMERICOS + PREDICTORES_CATEGORICOS

COLUMNAS_OBLIGATORIAS = [
    "id_registro",
    "id_socio_anonimo",
    "anio",
    "mes",
    "comite_sectorial",
    "sexo",
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
    "datos_fertilizantes_mes_anterior_disponibles",
    "movimientos_fertilizante_mes_anterior",
    "unidades_fertilizante_mes_anterior",
    "monto_fertilizante_mes_anterior",
    "tipos_fertilizante_mes_anterior",
    "datos_fumigacion_mes_anterior_disponibles",
    "numero_fumigaciones_mes_anterior",
    "horas_maquina_mes_anterior",
    "tanques_mes_anterior",
    "numero_plagas_mes_anterior",
]

for carpeta in (DATA_DIR, EVIDENCIA_DIR, MODELOS_DIR, RESULTADOS_DIR, MATRICES_DIR, LOGS_DIR):
    carpeta.mkdir(parents=True, exist_ok=True)
