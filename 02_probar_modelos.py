from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

import joblib
import matplotlib.pyplot as plt
import pandas as pd
from sklearn.metrics import (
    ConfusionMatrixDisplay,
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)

from configuracion import (
    ANIO_PRUEBA,
    CLASES,
    CLASE_A_CODIGO,
    CODIGO_A_CLASE,
    CODIGOS_CLASES,
    MATRICES_DIR,
    MODELOS_DIR,
    PREDICTORES,
    RESULTADOS_DIR,
)
from funciones_datos import cargar_dataset, preparar_entrenamiento_prueba
from funciones_modelos import NOMBRES_MODELOS
#evalua las clases predichas contra el conjunto de pruebas y define el ganador operativo

def cargar_metadatos() -> dict:
    ruta = MODELOS_DIR / "metadatos_entrenamiento.json"
    if not ruta.exists():
        raise FileNotFoundError(
            "No existe modelos/metadatos_entrenamiento.json. "
            "Primero ejecute 01_entrenar_modelos.py."
        )
    return json.loads(ruta.read_text(encoding="utf-8"))


def main() -> int:
    print("\nACEPAT ML - PRUEBA FINAL CON REGISTROS 2026")
    print("=" * 50)

    metadatos = cargar_metadatos()
    df, ruta_excel = cargar_dataset()
    _, prueba, q1_actual, q2_actual = preparar_entrenamiento_prueba(df)

    q1_guardado = float(metadatos["tercil_1"])
    q2_guardado = float(metadatos["tercil_2"])
    if abs(q1_actual - q1_guardado) > 1e-12 or abs(q2_actual - q2_guardado) > 1e-12:
        raise RuntimeError(
            "Los terciles actuales no coinciden con los del entrenamiento. "
            "El Excel cambió después de entrenar; vuelva a ejecutar el entrenamiento."
        )

    X_test = prueba[PREDICTORES].copy()
    y_test_texto = prueba["nivel_produccion"].copy()
    y_test = y_test_texto.map(CLASE_A_CODIGO)
    if y_test.isna().any():
        valores_invalidos = sorted(
            y_test_texto[y_test.isna()].dropna().unique().tolist()
        )
        raise ValueError(
            "Se encontraron niveles de producción no reconocidos en prueba: "
            + ", ".join(map(str, valores_invalidos))
        )
    y_test = y_test.astype("int64")

    print(f"Excel: {ruta_excel.name}")
    print(f"Registros de prueba {ANIO_PRUEBA}: {len(prueba):,}")
    print(f"Distribución real: {y_test_texto.value_counts().to_dict()}")

    resumen: list[dict] = []
    reportes: dict[str, pd.DataFrame] = {}

    #1###
    for clave, nombre in NOMBRES_MODELOS.items():
        ruta_modelo = MODELOS_DIR / f"modelo_{clave}.joblib"
        if not ruta_modelo.exists():
            raise FileNotFoundError(
                f"Falta {ruta_modelo.name}. Ejecute nuevamente 01_entrenar_modelos.py."
            )

        modelo = joblib.load(ruta_modelo)
        prediccion = modelo.predict(X_test)

        metricas = {
            "modelo_clave": clave,
            "modelo": nombre,
            "accuracy": accuracy_score(y_test, prediccion),
            "precision_macro": precision_score(
                y_test, prediccion, labels=CODIGOS_CLASES, average="macro", zero_division=0
            ),
            "recall_macro": recall_score(
                y_test, prediccion, labels=CODIGOS_CLASES, average="macro", zero_division=0
            ),
            "f1_macro": f1_score(
                y_test, prediccion, labels=CODIGOS_CLASES, average="macro", zero_division=0
            ),
            "precision_ponderada": precision_score(
                y_test, prediccion, labels=CODIGOS_CLASES, average="weighted", zero_division=0
            ),
            "recall_ponderado": recall_score(
                y_test, prediccion, labels=CODIGOS_CLASES, average="weighted", zero_division=0
            ),
            "f1_ponderado": f1_score(
                y_test, prediccion, labels=CODIGOS_CLASES, average="weighted", zero_division=0
            ),
        }
        resumen.append(metricas)

        reporte_dict = classification_report(
            y_test,
            prediccion,
            labels=CODIGOS_CLASES,
            target_names=CLASES,
            output_dict=True,
            zero_division=0,
        )
        reportes[clave] = pd.DataFrame(reporte_dict).transpose()

        predicciones = prueba[
            [
                "id_registro",
                "id_socio_anonimo",
                "anio",
                "mes",
                "fecha_periodo",
                "produccion_tn",
                "rendimiento_tn_ha",
                "nivel_produccion",
            ]
        ].copy()
        predicciones = predicciones.rename(
            columns={"nivel_produccion": "nivel_real"}
        )
        prediccion_texto = pd.Series(prediccion, index=prueba.index).map(
            CODIGO_A_CLASE
        )
        predicciones["nivel_predicho"] = prediccion_texto.to_numpy()
        predicciones["acierto"] = (
            predicciones["nivel_real"] == predicciones["nivel_predicho"]
        )

        if hasattr(modelo, "predict_proba"):
            probabilidades = modelo.predict_proba(X_test)
            clases_modelo = [int(codigo) for codigo in modelo.classes_]
            for codigo, clase in CODIGO_A_CLASE.items():
                if codigo in clases_modelo:
                    indice = clases_modelo.index(codigo)
                    predicciones[f"probabilidad_{clase.lower()}"] = (
                        probabilidades[:, indice]
                    )
            columnas_prob = [
                c for c in predicciones.columns if c.startswith("probabilidad_")
            ]
            if columnas_prob:
                predicciones["confianza_prediccion"] = predicciones[columnas_prob].max(
                    axis=1
                )

        predicciones.to_csv(
            RESULTADOS_DIR / f"predicciones_prueba_{clave}.csv",
            index=False,
            encoding="utf-8-sig",
        )

        matriz = confusion_matrix(
            y_test, prediccion, labels=CODIGOS_CLASES
        )
        figura, eje = plt.subplots(figsize=(7, 6))
        visual = ConfusionMatrixDisplay(confusion_matrix=matriz, display_labels=CLASES)
        visual.plot(ax=eje, values_format="d")
        eje.set_title(f"Matriz de confusión - {nombre}")
        figura.tight_layout()
        figura.savefig(MATRICES_DIR / f"matriz_{clave}.png", dpi=160)
        plt.close(figura)

        print(
            f"{nombre}: Accuracy={metricas['accuracy']:.4f} | "
            f"Precision={metricas['precision_macro']:.4f} | "
            f"Recall={metricas['recall_macro']:.4f} | "
            f"F1={metricas['f1_macro']:.4f}"
        )

        #2##### El sistema selecciona el fayor F1 macro y usa Accuracy y Recall macro como desempates
    comparacion = pd.DataFrame(resumen).sort_values(
        ["f1_macro", "accuracy", "recall_macro"], ascending=False
    )
    comparacion.insert(0, "posicion", range(1, len(comparacion) + 1))
    ganador = comparacion.iloc[0]

    ruta_ganador_origen = MODELOS_DIR / f"modelo_{ganador['modelo_clave']}.joblib"
    ruta_ganador = MODELOS_DIR / "modelo_ganador.joblib"
    shutil.copy2(ruta_ganador_origen, ruta_ganador)

    with pd.ExcelWriter(
        RESULTADOS_DIR / "reporte_prueba_modelos.xlsx", engine="openpyxl"
    ) as writer:
        comparacion.to_excel(writer, sheet_name="Comparacion", index=False)
        for clave, reporte in reportes.items():
            reporte.to_excel(writer, sheet_name=clave[:31])

    comparacion.to_csv(
        RESULTADOS_DIR / "comparacion_prueba_2026.csv",
        index=False,
        encoding="utf-8-sig",
    )

    resumen_ganador = {
        "modelo_clave": ganador["modelo_clave"],
        "modelo": ganador["modelo"],
        "accuracy": float(ganador["accuracy"]),
        "precision_macro": float(ganador["precision_macro"]),
        "recall_macro": float(ganador["recall_macro"]),
        "f1_macro": float(ganador["f1_macro"]),
        "criterio_seleccion": "Mayor F1 macro; desempate por Accuracy y Recall macro",
        "archivo_modelo": ruta_ganador.name,
    }
    (MODELOS_DIR / "modelo_ganador.json").write_text(
        json.dumps(resumen_ganador, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print("\nPRUEBA FINAL COMPLETADA")
    print(f"Modelo ganador: {ganador['modelo']}")
    print(f"F1 macro: {ganador['f1_macro']:.4f}")
    print(f"Accuracy: {ganador['accuracy']:.4f}")
    print("Reporte: resultados/reporte_prueba_modelos.xlsx")
    print("Modelo ganador: modelos/modelo_ganador.joblib")
    return 0


if __name__ == "__main__":
    sys.exit(main())
