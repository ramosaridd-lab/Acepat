from __future__ import annotations

import json
import sys
from datetime import datetime

import pandas as pd
from openpyxl import load_workbook
from openpyxl.styles import Alignment, Font, PatternFill
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    precision_score,
    recall_score,
)

from configuracion import (
    ANIO_ENTRENAMIENTO,
    ANIO_PRUEBA,
    CLASE_A_CODIGO,
    CODIGOS_CLASES,
    MODO_RAPIDO,
    PREDICTORES,
    RESULTADOS_DIR,
)
from funciones_datos import cargar_dataset, preparar_entrenamiento_prueba
from funciones_modelos import (
    NOMBRES_MODELOS,
    crear_folds_temporales,
    entrenar_busqueda,
)


SALIDA_DIR = RESULTADOS_DIR / "sensibilidad_enero"


def formatear_reporte_excel(ruta) -> None:
    libro = load_workbook(ruta)
    relleno_encabezado = PatternFill("solid", fgColor="1F4E78")
    fuente_encabezado = Font(color="FFFFFF", bold=True)

    for hoja in libro.worksheets:
        hoja.freeze_panes = "A2"
        hoja.auto_filter.ref = hoja.dimensions
        hoja.row_dimensions[1].height = 34

        for celda in hoja[1]:
            celda.fill = relleno_encabezado
            celda.font = fuente_encabezado
            celda.alignment = Alignment(
                horizontal="center", vertical="center", wrap_text=True
            )

        for columna in hoja.columns:
            letra = columna[0].column_letter
            longitud = max(
                len(str(celda.value)) if celda.value is not None else 0
                for celda in columna
            )
            hoja.column_dimensions[letra].width = min(max(longitud + 2, 12), 42)
            for celda in columna[1:]:
                if isinstance(celda.value, float):
                    celda.number_format = "0.0000"

    libro.save(ruta)


def calcular_metricas(y_real: pd.Series, prediccion) -> dict[str, float]:
    return {
        "accuracy": float(accuracy_score(y_real, prediccion)),
        "precision_macro": float(
            precision_score(
                y_real,
                prediccion,
                labels=CODIGOS_CLASES,
                average="macro",
                zero_division=0,
            )
        ),
        "recall_macro": float(
            recall_score(
                y_real,
                prediccion,
                labels=CODIGOS_CLASES,
                average="macro",
                zero_division=0,
            )
        ),
        "f1_macro": float(
            f1_score(
                y_real,
                prediccion,
                labels=CODIGOS_CLASES,
                average="macro",
                zero_division=0,
            )
        ),
    }


def main() -> int:
    print("\nACEPAT ML - ANÁLISIS DE SENSIBILIDAD DE ENERO 2025")
    print("=" * 61)
    print(f"Modo de búsqueda: {'RÁPIDO' if MODO_RAPIDO else 'COMPLETO'}")

    SALIDA_DIR.mkdir(parents=True, exist_ok=True)
    df, ruta_excel = cargar_dataset()
    entrenamiento_completo, prueba, q1, q2 = preparar_entrenamiento_prueba(df)

    X_test = prueba[PREDICTORES].copy()
    y_test = prueba["nivel_produccion"].map(CLASE_A_CODIGO).astype("int64")

    escenarios = {
        "con_enero": {
            "datos": entrenamiento_completo.copy(),
            "meses_excluidos": None,
        },
        "sin_enero": {
            "datos": entrenamiento_completo.loc[
                entrenamiento_completo["mes"] != 1
            ].reset_index(drop=True),
            "meses_excluidos": {1},
        },
    }

    resultados_validacion: list[dict] = []
    resultados_prueba: list[dict] = []
    folds_resumen: list[dict] = []

    for escenario, definicion in escenarios.items():
        datos = definicion["datos"]
        X_train = datos[PREDICTORES].copy()
        y_train = datos["nivel_produccion"].map(CLASE_A_CODIGO).astype("int64")
        folds = crear_folds_temporales(
            datos,
            meses_excluidos_entrenamiento=definicion["meses_excluidos"],
        )

        print("\n" + "#" * 72)
        print(f"Escenario: {escenario.replace('_', ' ').upper()}")
        print(f"Registros de entrenamiento: {len(datos):,}")

        for numero_fold, (idx_train, idx_val) in enumerate(folds, start=1):
            folds_resumen.append(
                {
                    "escenario": escenario,
                    "fold": numero_fold,
                    "registros_entrenamiento": int(len(idx_train)),
                    "registros_validacion": int(len(idx_val)),
                }
            )

        for clave, nombre in NOMBRES_MODELOS.items():
            print("\n" + "-" * 72)
            print(f"Entrenando: {nombre}")
            busqueda = entrenar_busqueda(clave, X_train, y_train, folds)
            indice_mejor = int(busqueda.best_index_)
            f1_train = float(
                busqueda.cv_results_["mean_train_score"][indice_mejor]
            )
            f1_validacion = float(busqueda.best_score_)

            resultados_validacion.append(
                {
                    "escenario": escenario,
                    "modelo_clave": clave,
                    "modelo": nombre,
                    "registros_entrenamiento_final": int(len(datos)),
                    "f1_macro_entrenamiento": f1_train,
                    "f1_macro_validacion": f1_validacion,
                    "brecha_entrenamiento_validacion": f1_train
                    - f1_validacion,
                    "desviacion_f1_validacion": float(
                        busqueda.cv_results_["std_test_score"][indice_mejor]
                    ),
                    "mejores_parametros": json.dumps(
                        busqueda.best_params_, ensure_ascii=False
                    ),
                }
            )

            detalle_cv = pd.DataFrame(busqueda.cv_results_).sort_values(
                "rank_test_score"
            )
            detalle_cv.to_csv(
                SALIDA_DIR / f"gridsearch_{escenario}_{clave}.csv",
                index=False,
                encoding="utf-8-sig",
            )

            prediccion = busqueda.best_estimator_.predict(X_test)
            metricas = calcular_metricas(y_test, prediccion)
            resultados_prueba.append(
                {
                    "escenario": escenario,
                    "modelo_clave": clave,
                    "modelo": nombre,
                    "registros_prueba": int(len(prueba)),
                    **metricas,
                }
            )

            print(f"F1 entrenamiento: {f1_train:.4f}")
            print(f"F1 validación: {f1_validacion:.4f}")
            print(f"Brecha: {f1_train - f1_validacion:.4f}")
            print(f"F1 prueba {ANIO_PRUEBA}: {metricas['f1_macro']:.4f}")

    validacion = pd.DataFrame(resultados_validacion).sort_values(
        ["escenario", "f1_macro_validacion"], ascending=[True, False]
    )
    prueba_df = pd.DataFrame(resultados_prueba).sort_values(
        ["escenario", "f1_macro"], ascending=[True, False]
    )
    folds_df = pd.DataFrame(folds_resumen)

    comparacion = validacion.pivot(
        index=["modelo_clave", "modelo"],
        columns="escenario",
        values=[
            "f1_macro_entrenamiento",
            "f1_macro_validacion",
            "brecha_entrenamiento_validacion",
        ],
    )
    comparacion.columns = [f"{metrica}_{escenario}" for metrica, escenario in comparacion.columns]
    comparacion = comparacion.reset_index()

    prueba_pivot = prueba_df.pivot(
        index=["modelo_clave", "modelo"],
        columns="escenario",
        values=["accuracy", "precision_macro", "recall_macro", "f1_macro"],
    )
    prueba_pivot.columns = [f"{metrica}_{escenario}" for metrica, escenario in prueba_pivot.columns]
    prueba_pivot = prueba_pivot.reset_index()
    comparacion = comparacion.merge(
        prueba_pivot, on=["modelo_clave", "modelo"], how="left"
    )
    comparacion["delta_f1_validacion_sin_menos_con"] = (
        comparacion["f1_macro_validacion_sin_enero"]
        - comparacion["f1_macro_validacion_con_enero"]
    )
    comparacion["delta_f1_prueba_sin_menos_con"] = (
        comparacion["f1_macro_sin_enero"]
        - comparacion["f1_macro_con_enero"]
    )
    comparacion = comparacion.sort_values(
        "f1_macro_validacion_con_enero", ascending=False
    )

    ganadores_validacion = {
        escenario: grupo.sort_values("f1_macro_validacion", ascending=False)
        .iloc[0][["modelo_clave", "modelo", "f1_macro_validacion"]]
        .to_dict()
        for escenario, grupo in validacion.groupby("escenario")
    }
    ganadores_prueba = {
        escenario: grupo.sort_values("f1_macro", ascending=False)
        .iloc[0][["modelo_clave", "modelo", "f1_macro", "accuracy"]]
        .to_dict()
        for escenario, grupo in prueba_df.groupby("escenario")
    }

    resumen = {
        "fecha_ejecucion": datetime.now().isoformat(timespec="seconds"),
        "archivo_excel": ruta_excel.name,
        "anio_entrenamiento": ANIO_ENTRENAMIENTO,
        "anio_prueba": ANIO_PRUEBA,
        "registros_con_enero": int(len(escenarios["con_enero"]["datos"])),
        "registros_sin_enero": int(len(escenarios["sin_enero"]["datos"])),
        "registros_enero_excluidos": int(
            len(escenarios["con_enero"]["datos"])
            - len(escenarios["sin_enero"]["datos"])
        ),
        "tercil_1_fijo": q1,
        "tercil_2_fijo": q2,
        "criterio": (
            "Los terciles y las ventanas de validación se mantienen fijos; "
            "solo se excluyen los registros de enero del entrenamiento."
        ),
        "ganadores_validacion": ganadores_validacion,
        "ganadores_prueba": ganadores_prueba,
    }

    validacion.to_csv(
        SALIDA_DIR / "validacion_con_sin_enero.csv",
        index=False,
        encoding="utf-8-sig",
    )
    prueba_df.to_csv(
        SALIDA_DIR / "prueba_2026_con_sin_enero.csv",
        index=False,
        encoding="utf-8-sig",
    )
    comparacion.to_csv(
        SALIDA_DIR / "comparacion_directa_con_sin_enero.csv",
        index=False,
        encoding="utf-8-sig",
    )
    folds_df.to_csv(
        SALIDA_DIR / "folds_con_sin_enero.csv",
        index=False,
        encoding="utf-8-sig",
    )
    ruta_reporte = SALIDA_DIR / "reporte_sensibilidad_enero.xlsx"
    with pd.ExcelWriter(ruta_reporte, engine="openpyxl") as writer:
        comparacion.to_excel(writer, sheet_name="Comparacion directa", index=False)
        validacion.to_excel(writer, sheet_name="Validacion", index=False)
        prueba_df.to_excel(writer, sheet_name="Prueba 2026", index=False)
        folds_df.to_excel(writer, sheet_name="Folds", index=False)
    formatear_reporte_excel(ruta_reporte)
    (SALIDA_DIR / "resumen_sensibilidad_enero.json").write_text(
        json.dumps(resumen, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print("\nANÁLISIS DE SENSIBILIDAD COMPLETADO")
    print(f"Resultados: {SALIDA_DIR}")
    print(
        "Ganador de validación con enero: "
        f"{ganadores_validacion['con_enero']['modelo']}"
    )
    print(
        "Ganador de validación sin enero: "
        f"{ganadores_validacion['sin_enero']['modelo']}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
