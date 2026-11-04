from __future__ import annotations

import json
import platform
import sys
from datetime import datetime

import joblib
import numpy as np
import pandas as pd
import sklearn

from configuracion import (
    ANIO_ENTRENAMIENTO,
    ANIO_PRUEBA,
    CLASES,
    CLASE_A_CODIGO,
    MODELOS_DIR,
    MODO_RAPIDO,
    PREDICTORES,
    PREDICTORES_CATEGORICOS,
    PREDICTORES_NUMERICOS,
    RESULTADOS_DIR,
)
from funciones_datos import (
    cargar_dataset,
    guardar_dataset_separado,
    guardar_verificacion,
    preparar_entrenamiento_prueba,
    verificar_dataset,
)
from funciones_modelos import (
    NOMBRES_MODELOS,
    crear_folds_temporales,
    entrenar_busqueda,
)


def main() -> int:
    print("\nACEPAT ML - ENTRENAMIENTO DE LOS SEIS ALGORITMOS")
    print("=" * 55)
    print(f"Modo de búsqueda: {'RÁPIDO' if MODO_RAPIDO else 'COMPLETO'}")

    try:
        df, ruta_excel = cargar_dataset()
        verificacion = verificar_dataset(df)
        guardar_verificacion(verificacion)
        if not verificacion["apto_para_modelado"]:
            print("El dataset tiene problemas bloqueantes. Ejecute 00_verificar_dataset.py.")
            for problema in verificacion["problemas_bloqueantes"]:
                print(f"- {problema}")
            return 2

        entrenamiento, prueba, q1, q2 = preparar_entrenamiento_prueba(df)
        ruta_separacion = guardar_dataset_separado(entrenamiento, prueba, q1, q2)

        X_train = entrenamiento[PREDICTORES].copy()

        # Las clases se convierten a códigos numéricos únicamente para el
        # entrenamiento interno: BAJA=0, MEDIA=1 y ALTA=2.
        y_train_texto = entrenamiento["nivel_produccion"].copy()
        y_train = y_train_texto.map(CLASE_A_CODIGO)
        if y_train.isna().any():
            valores_invalidos = sorted(
                y_train_texto[y_train.isna()].dropna().unique().tolist()
            )
            raise ValueError(
                "Se encontraron niveles de producción no reconocidos: "
                + ", ".join(map(str, valores_invalidos))
            )
        y_train = y_train.astype("int64")
        folds = crear_folds_temporales(entrenamiento)

        print(f"Excel: {ruta_excel.name}")
        print(f"Entrenamiento {ANIO_ENTRENAMIENTO}: {len(entrenamiento):,} registros")
        print(f"Prueba reservada {ANIO_PRUEBA}: {len(prueba):,} registros")
        print(f"Tercil 1: {q1:.6f} t/ha")
        print(f"Tercil 2: {q2:.6f} t/ha")
        print(f"Clases de entrenamiento: {y_train_texto.value_counts().to_dict()}")
        print(f"Codificación interna: {CLASE_A_CODIGO}")
        print(f"Separación guardada en: {ruta_separacion}")

        resumen_validacion: list[dict] = []
        for clave, nombre in NOMBRES_MODELOS.items():
            print("\n" + "-" * 70)
            print(f"Entrenando: {nombre}")
            busqueda = entrenar_busqueda(clave, X_train, y_train, folds)

            ruta_modelo = MODELOS_DIR / f"modelo_{clave}.joblib"
            joblib.dump(busqueda.best_estimator_, ruta_modelo, compress=3)

            resultados_cv = pd.DataFrame(busqueda.cv_results_).sort_values(
                "rank_test_score"
            )
            resultados_cv.to_csv(
                RESULTADOS_DIR / f"validacion_{clave}.csv",
                index=False,
                encoding="utf-8-sig",
            )

            indice_mejor = int(busqueda.best_index_)
            f1_entrenamiento = float(
                busqueda.cv_results_["mean_train_score"][indice_mejor]
            )
            brecha_sobreajuste = f1_entrenamiento - float(busqueda.best_score_)

            fila = {
                "modelo_clave": clave,
                "modelo": nombre,
                "f1_macro_entrenamiento": f1_entrenamiento,
                "f1_macro_validacion": float(busqueda.best_score_),
                "brecha_entrenamiento_validacion": brecha_sobreajuste,
                "mejores_parametros": json.dumps(
                    busqueda.best_params_, ensure_ascii=False
                ),
                "archivo_modelo": ruta_modelo.name,
            }
            resumen_validacion.append(fila)
            print(f"F1 macro de entrenamiento: {f1_entrenamiento:.4f}")
            print(f"Mejor F1 macro de validación: {busqueda.best_score_:.4f}")
            print(f"Brecha entrenamiento-validación: {brecha_sobreajuste:.4f}")
            print(f"Mejores parámetros: {busqueda.best_params_}")
            print(f"Modelo guardado: {ruta_modelo.name}")

        df_resumen = pd.DataFrame(resumen_validacion).sort_values(
            "f1_macro_validacion", ascending=False
        )
        df_resumen.to_csv(
            RESULTADOS_DIR / "comparacion_validacion_2025.csv",
            index=False,
            encoding="utf-8-sig",
        )

        metadatos = {
            "fecha_entrenamiento": datetime.now().isoformat(timespec="seconds"),
            "archivo_excel": ruta_excel.name,
            "hoja": "Muestra_7150",
            "anio_entrenamiento": ANIO_ENTRENAMIENTO,
            "anio_prueba_reservada": ANIO_PRUEBA,
            "registros_entrenamiento": int(len(entrenamiento)),
            "registros_prueba_reservada": int(len(prueba)),
            "tercil_1": q1,
            "tercil_2": q2,
            "clases": CLASES,
            "codificacion_clases": CLASE_A_CODIGO,
            "predictores": PREDICTORES,
            "predictores_numericos": PREDICTORES_NUMERICOS,
            "predictores_categoricos": PREDICTORES_CATEGORICOS,
            "modo_rapido": MODO_RAPIDO,
            "version_python": platform.python_version(),
            "version_numpy": np.__version__,
            "version_pandas": pd.__version__,
            "version_scikit_learn": sklearn.__version__,
            "resultados_validacion": resumen_validacion,
        }
        (MODELOS_DIR / "metadatos_entrenamiento.json").write_text(
            json.dumps(metadatos, ensure_ascii=False, indent=2), encoding="utf-8"
        )

        print("\nENTRENAMIENTO COMPLETADO")
        print("La prueba 2026 no fue usada para ajustar los modelos.")
        print("Siguiente paso: ejecute 02_probar_modelos.py")
        return 0

    except KeyboardInterrupt:
        print("\nEntrenamiento cancelado por el usuario.")
        return 130
    except Exception as exc:
        print(f"\nERROR DURANTE EL ENTRENAMIENTO: {exc}")
        raise


if __name__ == "__main__":
    sys.exit(main())
