#realiza una verificacion previa antes de entrenar los modelos
from __future__ import annotations

import sys
import traceback

from funciones_datos import cargar_dataset, guardar_verificacion, verificar_dataset


def main() -> int:
    print("\nACEPAT ML - VERIFICACIÓN DEL DATASET", flush=True)
    print("=" * 42, flush=True)

    try:
        print("[1/4] Cargando el archivo Excel...", flush=True)
        df, ruta = cargar_dataset()

        print(f"[2/4] Excel cargado correctamente: {ruta}", flush=True)
        print(f"      Dimensiones detectadas: {df.shape[0]:,} filas x {df.shape[1]} columnas", flush=True)

        print("[3/4] Verificando calidad, duplicados y campos obligatorios...", flush=True)
        resultado = verificar_dataset(df)

        print("[4/4] Guardando el reporte de verificación...", flush=True)
        guardar_verificacion(resultado)

    except BaseException as exc:
        print("\nERROR DURANTE LA VERIFICACIÓN", flush=True)
        print(f"Tipo de error: {type(exc).__name__}", flush=True)
        print(f"Detalle: {exc}", flush=True)
        print("\nRastreo técnico:", flush=True)
        traceback.print_exc()
        return 1

    print("\nRESUMEN DE LA VERIFICACIÓN", flush=True)
    print(f"Excel analizado: {ruta}", flush=True)
    print(f"Filas encontradas: {resultado['filas_en_excel']:,}", flush=True)
    print(f"Socios anónimos: {resultado['socios_anonimos']}", flush=True)
    print(f"Registros por año: {resultado['registros_por_anio']}", flush=True)
    print(
        "Resultado: "
        + ("APTO PARA MODELADO" if resultado["apto_para_modelado"] else "NO APTO"),
        flush=True,
    )

    if resultado["problemas_bloqueantes"]:
        print("\nProblemas bloqueantes:", flush=True)
        for problema in resultado["problemas_bloqueantes"]:
            print(f"- {problema}", flush=True)

    if resultado["advertencias"]:
        print("\nAdvertencias controladas por el pipeline:", flush=True)
        for advertencia in resultado["advertencias"]:
            print(f"- {advertencia}", flush=True)

    print("\nReporte guardado en resultados/verificacion_dataset.txt", flush=True)
    return 0 if resultado["apto_para_modelado"] else 2


if __name__ == "__main__":
    sys.exit(main())
