from __future__ import annotations

from collections.abc import Iterable
from typing import Any

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GridSearchCV
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier

from configuracion import (
    MODO_RAPIDO,
    PREDICTORES_CATEGORICOS,
    PREDICTORES_NUMERICOS,
    SEMILLA,
)
###define los clasificadores, el preprocesamiento y la validacion temporal expansiva 
#1 #####
NOMBRES_MODELOS = {
    "regresion_logistica": "Regresión logística",
    "arbol_decision": "Árbol de decisiones",
    "random_forest": "Random Forest",
    "svm": "SVM",
    "gradient_boosting": "Gradient Boosting",
    "knn": "KNN",
}

#2 ### el pipeline garantiza transformaciones consistentes dentro de las etapas de entramiento y validacion 
def crear_preprocesador(con_escalado: bool) -> ColumnTransformer:
    pasos_numericos: list[tuple[str, Any]] = [
        ("imputador", SimpleImputer(strategy="median", add_indicator=True))
    ]
    if con_escalado:
        pasos_numericos.append(("escalador", StandardScaler()))

    transformador_numerico = Pipeline(pasos_numericos)
    transformador_categorico = Pipeline(
        [
            ("imputador", SimpleImputer(strategy="most_frequent")),
            (
                "onehot",
                OneHotEncoder(handle_unknown="ignore", sparse_output=False),
            ),
        ]
    )

    return ColumnTransformer(
        transformers=[
            ("numericas", transformador_numerico, PREDICTORES_NUMERICOS),
            ("categoricas", transformador_categorico, PREDICTORES_CATEGORICOS),
        ],
        remainder="drop",
        sparse_threshold=0.0,
        verbose_feature_names_out=False,
    )


def especificaciones_modelos() -> dict[str, dict[str, Any]]:
    if MODO_RAPIDO:
        grids = {
            "regresion_logistica": {
                "modelo__C": [0.5, 2.0],
                "modelo__class_weight": [None, "balanced"],
            },
            "arbol_decision": {
                "modelo__max_depth": [6, None],
                "modelo__min_samples_leaf": [4],
                "modelo__class_weight": [None, "balanced"],
            },
            "random_forest": {
                "modelo__max_depth": [12, None],
                "modelo__min_samples_leaf": [2],
                "modelo__class_weight": [None, "balanced_subsample"],
            },
            "svm": {
                "modelo__C": [1.0, 3.0],
                "modelo__gamma": ["scale"],
                "modelo__class_weight": [None, "balanced"],
            },
            "gradient_boosting": {
                "modelo__n_estimators": [100, 180],
                "modelo__learning_rate": [0.05],
                "modelo__max_depth": [2],
            },
            "knn": {
                "modelo__n_neighbors": [9, 21],
                "modelo__weights": ["distance"],
                "modelo__p": [1, 2],
            },
        }
    else:
        grids = {
            "regresion_logistica": {
                "modelo__C": [0.01, 0.1, 1.0, 10.0, 100.0],
                "modelo__class_weight": [None, "balanced"],
            },
            "arbol_decision": {
                "modelo__max_depth": [3, 5, 8, 12, None],
                "modelo__min_samples_split": [2, 10, 20],
                "modelo__min_samples_leaf": [1, 3, 8, 15],
                "modelo__class_weight": [None, "balanced"],
            },
            "random_forest": {
                "modelo__n_estimators": [250, 500],
                "modelo__max_depth": [8, 15, None],
                "modelo__min_samples_leaf": [1, 3, 8],
                "modelo__max_features": ["sqrt", 0.7],
                "modelo__class_weight": [None, "balanced_subsample"],
            },
            "svm": {
                "modelo__C": [0.1, 0.5, 1.0, 5.0, 10.0],
                "modelo__gamma": ["scale", "auto", 0.01, 0.1],
                "modelo__class_weight": [None, "balanced"],
            },
            "gradient_boosting": {
                "modelo__n_estimators": [100, 200, 350],
                "modelo__learning_rate": [0.03, 0.05, 0.1],
                "modelo__max_depth": [2, 3],
                "modelo__min_samples_leaf": [1, 5, 10],
            },
            "knn": {
                "modelo__n_neighbors": [5, 9, 15, 25, 35],
                "modelo__weights": ["uniform", "distance"],
                "modelo__p": [1, 2],
            },
        }

    return {
        "regresion_logistica": {
            "escalado": True,
            "estimador": LogisticRegression(
                max_iter=4000,
                solver="lbfgs",
                random_state=SEMILLA,
            ),
            "parametros": grids["regresion_logistica"],
        },
        "arbol_decision": {
            "escalado": False,
            "estimador": DecisionTreeClassifier(random_state=SEMILLA),
            "parametros": grids["arbol_decision"],
        },
        "random_forest": {
            "escalado": False,
            "estimador": RandomForestClassifier(
                random_state=SEMILLA,
                n_jobs=1,
            ),
            "parametros": grids["random_forest"],
        },
        "svm": {
            "escalado": True,
            "estimador": SVC(
                kernel="rbf",
                probability=True,
                cache_size=1024,
                random_state=SEMILLA,
            ),
            "parametros": grids["svm"],
        },
        "gradient_boosting": {
            "escalado": False,
            "estimador": GradientBoostingClassifier(random_state=SEMILLA),
            "parametros": grids["gradient_boosting"],
        },
        "knn": {
            "escalado": True,
            "estimador": KNeighborsClassifier(),
            "parametros": grids["knn"],
        },
    }


def crear_folds_temporales(
    df_entrenamiento: pd.DataFrame,
    meses_excluidos_entrenamiento: Iterable[int] | None = None,
) -> list[tuple[np.ndarray, np.ndarray]]:
    """Crea cuatro validaciones expansivas sin mezclar meses futuros en el pasado.

    ``meses_excluidos_entrenamiento`` permite realizar análisis de sensibilidad
    sin alterar las ventanas de validación. Su uso no modifica el flujo normal.
    """
    fechas = pd.to_datetime(df_entrenamiento["fecha_periodo"], errors="coerce")
    anios = sorted(int(anio) for anio in fechas.dropna().dt.year.unique())
    if len(anios) != 1:
        raise ValueError(
            "Los folds temporales deben construirse con un único año de entrenamiento."
        )

    excluidos = {int(mes) for mes in (meses_excluidos_entrenamiento or [])}
    if any(mes < 1 or mes > 12 for mes in excluidos):
        raise ValueError("Los meses excluidos deben estar entre 1 y 12.")

    periodos = list(pd.date_range(f"{anios[0]}-01-01", periods=12, freq="MS"))
    meses_presentes = set(fechas.dropna().dt.month.astype(int).unique())
    meses_requeridos = set(range(1, 13)) - excluidos
    meses_faltantes = sorted(meses_requeridos - meses_presentes)
    if meses_faltantes:
        raise ValueError(
            "Faltan meses requeridos para construir los folds temporales: "
            + ", ".join(map(str, meses_faltantes))
        )
###3 
    planes = [
        (periodos[:4], periodos[4:6]),
        (periodos[:6], periodos[6:8]),
        (periodos[:8], periodos[8:10]),
        (periodos[:10], periodos[10:12]),
    ]

    folds: list[tuple[np.ndarray, np.ndarray]] = []
    for meses_train, meses_val in planes:
        idx_train = np.flatnonzero(
            (
                df_entrenamiento["fecha_periodo"].isin(meses_train)
                & ~fechas.dt.month.isin(excluidos)
            ).to_numpy()
        )
        idx_val = np.flatnonzero(
            df_entrenamiento["fecha_periodo"].isin(meses_val).to_numpy()
        )
        if len(idx_train) == 0 or len(idx_val) == 0:
            raise ValueError("Se generó un fold temporal vacío.")
        folds.append((idx_train, idx_val))
    return folds


def entrenar_busqueda(
    clave_modelo: str,
    X: pd.DataFrame,
    y: pd.Series,
    folds: Iterable[tuple[np.ndarray, np.ndarray]],
) -> GridSearchCV:
    especificaciones = especificaciones_modelos()
    if clave_modelo not in especificaciones:
        raise KeyError(f"Modelo no reconocido: {clave_modelo}")

    spec = especificaciones[clave_modelo]

    #4
    pipeline = Pipeline(
        [
            ("preprocesador", crear_preprocesador(spec["escalado"])),
            ("modelo", spec["estimador"]),
        ]
    )
    busqueda = GridSearchCV(
        estimator=pipeline,
        param_grid=spec["parametros"],
        scoring="f1_macro",
        cv=list(folds),
        refit=True,
        n_jobs=-1,
        verbose=1,
        return_train_score=True,
        error_score="raise",
    )
    busqueda.fit(X, y)
    return busqueda
