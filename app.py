from __future__ import annotations

from datetime import datetime
from pathlib import Path
import base64

import pandas as pd
import streamlit as st

from funciones_prediccion import (
    CLASES,
    MESES,
    advertencias_fuera_de_rango,
    cargar_recursos_modelo,
    construir_entrada_modelo,
    construir_registro_resultado,
    ejecutar_prediccion,
    formatear_periodo,
    generar_excel_resultado,
    guardar_historial,
    leer_historial,
    periodo_anterior,
    periodo_es_valido,
)


st.set_page_config(
    page_title="ACEPAT | Predicción de producción",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="collapsed",
)


RUTA_APP = Path(__file__).resolve().parent
RUTA_MARCA = RUTA_APP / "assets" / "logo_acepat_oficial.png"
RUTA_BASE_ACEPAT = RUTA_APP / "data" / "ACEPAT_Dataset_Limpio_7150.xlsx"
HOJA_DATOS_ACEPAT = "Datos"


def imagen_base64(ruta: Path) -> str:
    """Convierte un recurso local en una URL de datos para usarlo sin internet."""
    if not ruta.exists():
        return ""
    contenido = base64.b64encode(ruta.read_bytes()).decode("ascii")
    mime = "image/png" if ruta.suffix.lower() == ".png" else "image/svg+xml"
    return f"data:{mime};base64,{contenido}"


MARCA_ACEPAT = imagen_base64(RUTA_MARCA)

st.markdown(
    """
    <style>
    :root {
        --acepat-green: #14352A;
        --acepat-green-2: #1C493A;
        --acepat-green-3: #2D604E;
        --acepat-gold: #C8A43A;
        --acepat-gold-soft: #E7D8A4;
        --acepat-ivory: #F5F1E8;
        --acepat-paper: #FBF9F4;
        --acepat-white: #FFFFFF;
        --acepat-ink: #17372C;
        --acepat-muted: #66756D;
        --acepat-line: #D8DED7;
        --acepat-danger: #9E3F35;
        --acepat-warning: #9A6A16;
    }

    html, body, [class*="css"] {
        font-family: Inter, "Segoe UI", Arial, sans-serif;
        color: var(--acepat-ink);
    }

    .stApp {
        background: var(--acepat-ivory);
    }

    .block-container {
        max-width: 1240px;
        padding-top: 0;
        padding-bottom: 2.5rem;
    }

    header[data-testid="stHeader"] {
        background: transparent;
        height: 0;
    }

    [data-testid="stToolbar"], [data-testid="stDecoration"], #MainMenu {
        visibility: hidden;
    }

    section[data-testid="stSidebar"] {
        display: none;
    }

    /* Encabezado institucional inspirado en la web pública de ACEPAT */
    .acepat-site-header {
        background: var(--acepat-green);
        margin-left: calc(-50vw + 50%);
        margin-right: calc(-50vw + 50%);
        padding: 0 2rem;
        position: sticky;
        top: 0;
        z-index: 999;
        box-shadow: 0 1px 0 rgba(255,255,255,.08);
    }

    .acepat-nav {
        max-width: 1240px;
        min-height: 76px;
        margin: 0 auto;
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 2rem;
    }

    .acepat-logo img {
        display: block;
        width: 198px;
        max-width: 42vw;
        height: auto;
    }

    .acepat-navlinks {
        display: flex;
        align-items: center;
        gap: 1.55rem;
        color: rgba(255,255,255,.82);
        font-size: .78rem;
        font-weight: 700;
        letter-spacing: .06em;
        text-transform: uppercase;
        white-space: nowrap;
    }

    .acepat-navlinks a {
        color: rgba(255,255,255,.76);
        text-decoration: none;
        padding: .45rem 0;
        border-bottom: 2px solid transparent;
        transition: color .16s ease, border-color .16s ease;
    }

    .acepat-navlinks a:hover,
    .acepat-navlinks a.active {
        color: #FFFFFF;
        border-bottom-color: var(--acepat-gold);
    }

    .acepat-navpill {
        border: 1px solid rgba(200,164,58,.65);
        color: #F4E8BD;
        padding: .55rem .8rem;
        border-radius: 999px;
    }

    .acepat-hero {
        display: grid;
        grid-template-columns: minmax(0, 1.38fr) minmax(300px, .62fr);
        gap: 4rem;
        align-items: center;
        padding: 5.2rem 0 4.5rem;
        border-bottom: 1px solid #D6DACE;
    }

    .acepat-eyebrow {
        color: var(--acepat-green-3);
        font-size: .74rem;
        font-weight: 800;
        letter-spacing: .15em;
        text-transform: uppercase;
        margin-bottom: 1rem;
    }

    .acepat-hero h1 {
        margin: 0;
        max-width: 850px;
        color: var(--acepat-green);
        font-family: Georgia, "Times New Roman", serif;
        font-weight: 500;
        font-size: clamp(2.7rem, 5.6vw, 5.25rem);
        line-height: .98;
        letter-spacing: -.045em;
    }

    .acepat-hero p {
        max-width: 720px;
        margin: 1.45rem 0 0;
        color: #52665D;
        font-size: 1.02rem;
        line-height: 1.72;
    }

    .acepat-hero-note {
        border-left: 1px solid #B8C1B8;
        padding-left: 2rem;
    }

    .acepat-hero-note .note-kicker {
        color: var(--acepat-gold);
        font-size: .72rem;
        font-weight: 850;
        letter-spacing: .13em;
        text-transform: uppercase;
        margin-bottom: 1rem;
    }

    .acepat-hero-note strong {
        display: block;
        color: var(--acepat-green);
        font-family: Georgia, "Times New Roman", serif;
        font-size: 2rem;
        font-weight: 500;
        line-height: 1.08;
        margin-bottom: .8rem;
    }

    .acepat-hero-note p {
        margin: 0;
        font-size: .9rem;
        line-height: 1.6;
    }

    .acepat-stat-strip {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        background: var(--acepat-green);
        margin: 0 0 2.2rem;
    }

    .acepat-stat {
        min-height: 108px;
        padding: 1.45rem 1.55rem;
        border-right: 1px solid rgba(255,255,255,.13);
    }

    .acepat-stat:last-child {border-right: 0;}
    .acepat-stat span {
        display: block;
        color: rgba(255,255,255,.62);
        font-size: .68rem;
        font-weight: 800;
        letter-spacing: .12em;
        text-transform: uppercase;
        margin-bottom: .45rem;
    }
    .acepat-stat strong {
        color: #fff;
        font-family: Georgia, "Times New Roman", serif;
        font-weight: 500;
        font-size: 1.35rem;
    }

    .acepat-intro {
        display: grid;
        grid-template-columns: 1.3fr .7fr;
        gap: 2rem;
        margin: 0 0 1.3rem;
        align-items: start;
    }

    .acepat-intro h2 {
        font-family: Georgia, "Times New Roman", serif;
        color: var(--acepat-green);
        font-weight: 500;
        font-size: 2rem;
        margin: 0 0 .45rem;
    }

    .acepat-intro p {
        margin: 0;
        color: var(--acepat-muted);
        line-height: 1.65;
    }

    .acepat-rule {
        background: #EFE9D8;
        border-top: 2px solid var(--acepat-gold);
        padding: 1rem 1.1rem;
        color: #465A50;
        font-size: .9rem;
        line-height: 1.55;
    }

    /* Navegación interna */
    div[data-testid="stTabs"] > div:first-child {
        gap: .2rem;
        border-bottom: 1px solid #CDD4CD;
        margin-bottom: 1.2rem;
    }
    div[data-testid="stTabs"] button {
        color: #62736A;
        font-weight: 750;
        padding: .75rem 1.25rem;
    }
    div[data-testid="stTabs"] button[aria-selected="true"] {
        color: var(--acepat-green);
    }
    div[data-testid="stTabs"] [data-baseweb="tab-highlight"] {
        background-color: var(--acepat-gold);
        height: 3px;
    }

    h1, h2, h3 {color: var(--acepat-green);}
    h2, h3 {letter-spacing: -.02em;}
    h3 {font-family: Georgia, "Times New Roman", serif;}

    div[data-testid="stNumberInput"] input,
    div[data-testid="stTextInput"] input,
    div[data-baseweb="select"] > div {
        background: var(--acepat-paper);
        border-color: #C8D0C9;
        border-radius: 2px;
    }

    div[data-testid="stMetric"] {
        background: var(--acepat-paper);
        border-top: 2px solid var(--acepat-gold);
        border-left: 1px solid var(--acepat-line);
        border-right: 1px solid var(--acepat-line);
        border-bottom: 1px solid var(--acepat-line);
        padding: .9rem 1rem;
        border-radius: 0;
    }
    div[data-testid="stMetric"] label {
        color: var(--acepat-muted);
        font-weight: 700;
    }

    .stButton > button[kind="primary"],
    .stDownloadButton > button {
        border-radius: 2px;
        min-height: 3.15rem;
        font-weight: 850;
        letter-spacing: .02em;
    }
    .stButton > button[kind="primary"] {
        background: var(--acepat-gold);
        border-color: var(--acepat-gold);
        color: var(--acepat-green);
    }
    .stButton > button[kind="primary"]:hover {
        background: #D6B64D;
        border-color: #D6B64D;
        color: var(--acepat-green);
    }

    .result-card {
        border: 1px solid #CAD2CB;
        border-left: 7px solid var(--acepat-gold);
        background: var(--acepat-paper);
        padding: 1.55rem 1.7rem;
        margin-bottom: 1rem;
    }
    .result-level {
        font-family: Georgia, "Times New Roman", serif;
        font-size: 2.6rem;
        font-weight: 500;
        margin: .3rem 0;
        letter-spacing: -.035em;
    }
    .level-BAJA {color: var(--acepat-danger);}
    .level-MEDIA {color: var(--acepat-warning);}
    .level-ALTA {color: var(--acepat-green-3);}
    .small-muted {color: var(--acepat-muted); font-size: .9rem;}

    .acepat-footer {
        background: var(--acepat-green);
        margin: 3rem calc(-50vw + 50%) -2.5rem;
        padding: 2rem max(2rem, calc((100vw - 1240px)/2));
        display: flex;
        justify-content: space-between;
        gap: 1rem;
        color: rgba(255,255,255,.68);
        font-size: .82rem;
    }
    .acepat-footer strong {color:white;}
    .acepat-footer a {
        color: #E7D8A4;
        font-weight: 750;
        text-decoration: none;
    }

    @media (max-width: 900px) {
        .acepat-site-header {padding: 0 1rem;}
        .acepat-nav {flex-direction:column; align-items:flex-start; gap:.65rem; padding:.85rem 0;}
        .acepat-navlinks {display:flex; width:100%; gap:1rem; overflow-x:auto; padding-bottom:.2rem;}
        .acepat-navlinks a {font-size:.7rem;}
        .acepat-navpill {font-size:.68rem;}
        .acepat-hero {grid-template-columns:1fr; gap:2rem; padding:3.5rem 0;}
        .acepat-hero-note {border-left:0; border-top:1px solid #B8C1B8; padding:1.5rem 0 0;}
        .acepat-stat-strip {grid-template-columns:1fr;}
        .acepat-stat {border-right:0; border-bottom:1px solid rgba(255,255,255,.13);}
        .acepat-intro {grid-template-columns:1fr;}
        .acepat-footer {flex-direction:column;}
    }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_resource(show_spinner=False)
def recursos_modelo():
    return cargar_recursos_modelo()


@st.cache_data(show_spinner=False)
def cargar_base_socios() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Carga la única hoja operativa y deriva de ella el catálogo de socios."""
    if not RUTA_BASE_ACEPAT.exists():
        raise FileNotFoundError("No se encontró data/ACEPAT_Dataset_Limpio_7150.xlsx.")

    datos = pd.read_excel(
        RUTA_BASE_ACEPAT,
        sheet_name=HOJA_DATOS_ACEPAT,
        dtype={"codigo_socio": "string", "dni": "string"},
        engine="openpyxl",
    )

    columnas_requeridas = {
        "codigo_socio", "dni", "nombre_socio", "anio", "mes",
        "comite_sectorial", "sexo", "hectareas_produccion",
        "area_instalada_ha", "numero_parcelas_produccion",
        "anio_siembra_ponderado", "edad_plantacion_anios",
        "produccion_tn", "rendimiento_tn_ha",
    }
    faltantes = sorted(columnas_requeridas.difference(datos.columns))
    if faltantes:
        raise ValueError(
            "La hoja Datos no contiene las columnas obligatorias: " + ", ".join(faltantes)
        )

    datos["codigo_socio"] = datos["codigo_socio"].fillna("").astype(str).str.strip()
    datos["nombre_socio"] = datos["nombre_socio"].fillna("").astype(str).str.strip()
    datos["dni"] = (
        datos["dni"].fillna("").astype(str)
        .str.replace(r"\.0$", "", regex=True)
        .str.replace(r"\D", "", regex=True)
        .str.zfill(8)
    )
    datos["anio"] = pd.to_numeric(datos["anio"], errors="coerce").astype("Int64")
    datos["mes"] = pd.to_numeric(datos["mes"], errors="coerce").astype("Int64")
    if "estado_calidad_registro" not in datos.columns:
        datos["estado_calidad_registro"] = "VALIDO"

    columnas_catalogo = [
        "codigo_socio", "dni", "nombre_socio", "sexo", "comite_sectorial",
        "hectareas_produccion", "area_instalada_ha",
        "numero_parcelas_produccion", "anio_siembra_ponderado",
    ]
    catalogo = (
        datos.sort_values(["codigo_socio", "anio", "mes"], kind="stable")
        .drop_duplicates(subset=["codigo_socio"], keep="last")[columnas_catalogo]
        .sort_values("nombre_socio", kind="stable")
        .reset_index(drop=True)
    )
    return catalogo, datos


def _numero_seguro(valor, predeterminado: float = 0.0) -> float:
    if valor is None or pd.isna(valor):
        return float(predeterminado)
    try:
        return float(valor)
    except (TypeError, ValueError):
        return float(predeterminado)


def cargar_datos_asociados_en_estado(
    socio: pd.Series,
    datos_socios: pd.DataFrame,
    anio_base: int,
    mes_base: int,
    anio_objetivo: int,
    mes_objetivo: int,
) -> tuple[bool, str, list[str]]:
    """Precarga datos disponibles sin desplazar erróneamente los rezagos temporales."""
    socio_id = str(socio["codigo_socio"])
    filas_base = datos_socios[
        (datos_socios["codigo_socio"] == socio_id)
        & (datos_socios["anio"] == int(anio_base))
        & (datos_socios["mes"] == int(mes_base))
    ]
    filas_objetivo = datos_socios[
        (datos_socios["codigo_socio"] == socio_id)
        & (datos_socios["anio"] == int(anio_objetivo))
        & (datos_socios["mes"] == int(mes_objetivo))
    ]
    filas_objetivo_global = datos_socios[
        (datos_socios["anio"] == int(anio_objetivo))
        & (datos_socios["mes"] == int(mes_objetivo))
    ]
    fila_base = filas_base.iloc[0] if not filas_base.empty else None
    fila_objetivo = filas_objetivo.iloc[0] if not filas_objetivo.empty else None
    fila_objetivo_global = filas_objetivo_global.iloc[0] if not filas_objetivo_global.empty else None

    comite = str(socio.get("comite_sectorial", "") or "").strip()
    sexo = str(socio.get("sexo", "") or "").strip().upper()
    if sexo not in {"M", "F"}: sexo = "DESCONOCIDO"
    st.session_state["comite_sectorial"] = str(fila_base.get("comite_sectorial", comite)).strip() if fila_base is not None else comite
    st.session_state["sexo"] = str(fila_base.get("sexo", sexo)).strip().upper() if fila_base is not None else sexo
    st.session_state["hectareas"] = _numero_seguro(fila_base.get("hectareas_produccion") if fila_base is not None else socio.get("hectareas_produccion"))
    st.session_state["area_instalada"] = _numero_seguro(fila_base.get("area_instalada_ha") if fila_base is not None else socio.get("area_instalada_ha"))
    st.session_state["parcelas"] = int(round(_numero_seguro(fila_base.get("numero_parcelas_produccion") if fila_base is not None else socio.get("numero_parcelas_produccion"))))
    if fila_base is not None and not pd.isna(fila_base.get("edad_plantacion_anios")):
        edad = _numero_seguro(fila_base.get("edad_plantacion_anios"))
    else:
        anio_siembra = socio.get("anio_siembra_ponderado")
        edad = 0.0 if anio_siembra is None or pd.isna(anio_siembra) else max(0.0, float(anio_base)-float(anio_siembra))
    st.session_state["edad_plantacion"] = edad
    pendientes=[]
    st.session_state.pop("ultimo_resultado",None)

    if fila_base is not None:
        st.session_state["produccion_anterior"] = _numero_seguro(fila_base.get("produccion_tn"))
        st.session_state["rendimiento_anterior"] = _numero_seguro(fila_base.get("rendimiento_tn_ha"))
    else:
        st.session_state["produccion_anterior"] = None
        st.session_state["rendimiento_anterior"] = None
        pendientes += ["producción", "rendimiento"]

    if fila_objetivo is not None:
        st.session_state["precipitacion_anterior"] = _numero_seguro(fila_objetivo.get("precipitacion_mes_anterior_mm"))
        st.session_state["precipitacion_3_meses"] = _numero_seguro(fila_objetivo.get("precipitacion_acumulada_3_meses_mm"))
        fd=str(fila_objetivo.get("datos_fertilizantes_mes_anterior_disponibles","NO")).strip().upper().replace("SÍ","SI")
        fm=str(fila_objetivo.get("datos_fumigacion_mes_anterior_disponibles","NO")).strip().upper().replace("SÍ","SI")
        st.session_state["fertilizantes_disponibles"] = fd if fd in {"SI","NO"} else "NO"
        st.session_state["fumigacion_disponible"] = fm if fm in {"SI","NO"} else "NO"
        equivalencias={
            "movimientos_fertilizante":"movimientos_fertilizante_mes_anterior",
            "unidades_fertilizante":"unidades_fertilizante_mes_anterior",
            "monto_fertilizante":"monto_fertilizante_mes_anterior",
            "tipos_fertilizante":"tipos_fertilizante_mes_anterior",
            "numero_fumigaciones":"numero_fumigaciones_mes_anterior",
            "horas_maquina":"horas_maquina_mes_anterior",
            "tanques":"tanques_mes_anterior",
            "numero_plagas":"numero_plagas_mes_anterior",
        }
        for k,c in equivalencias.items(): st.session_state[k]=_numero_seguro(fila_objetivo.get(c))
    else:
        if fila_objetivo_global is not None:
            st.session_state["precipitacion_anterior"] = _numero_seguro(fila_objetivo_global.get("precipitacion_mes_anterior_mm"))
            st.session_state["precipitacion_3_meses"] = _numero_seguro(fila_objetivo_global.get("precipitacion_acumulada_3_meses_mm"))
        else:
            st.session_state["precipitacion_anterior"] = None
            st.session_state["precipitacion_3_meses"] = None
            pendientes.append("información climática")
        st.session_state["fertilizantes_disponibles"] = "NO"
        st.session_state["fumigacion_disponible"] = "NO"
        for k in ("movimientos_fertilizante","unidades_fertilizante","monto_fertilizante","tipos_fertilizante","numero_fumigaciones","horas_maquina","tanques","numero_plagas"):
            st.session_state[k]=0
        pendientes += ["fertilización", "fumigación y plagas"]

    if fila_base is None:
        return False, f"No existe un registro productivo de {MESES[int(mes_base)]} de {int(anio_base)} para este socio. Complete los campos faltantes antes de predecir.", pendientes
    if not pendientes:
        return True, f"Datos de {MESES[int(mes_base)]} de {int(anio_base)} cargados automáticamente desde la base oficial ACEPAT. Todos los campos permanecen visibles y editables.", pendientes
    return True, f"Se cargaron automáticamente los datos disponibles de {MESES[int(mes_base)]} de {int(anio_base)}. Revise o complete únicamente: {', '.join(pendientes)}. Los valores precargados también pueden corregirse si ACEPAT cuenta con información más actualizada.", pendientes


def numero(
    etiqueta: str,
    clave: str,
    *,
    min_value: float = 0.0,
    step: float = 0.1,
    entero: bool = False,
    ayuda: str | None = None,
    disabled: bool = False,
):
    if entero:
        return st.number_input(
            etiqueta,
            min_value=int(min_value),
            step=max(1, int(step)),
            placeholder="Ingresar datos",
            key=clave,
            help=ayuda,
            disabled=disabled,
        )
    return st.number_input(
        etiqueta,
        min_value=float(min_value),
        step=float(step),
        format="%.2f",
        placeholder="Ingresar datos",
        key=clave,
        help=ayuda,
        disabled=disabled,
    )


try:
    modelo, metadatos, ganador, perfil = recursos_modelo()
    catalogo_socios, datos_socios = cargar_base_socios()
except Exception as exc:
    st.error(str(exc))
    st.stop()

SECCIONES_VALIDAS = {"produccion", "prediccion", "historial", "modelo"}
seccion = str(st.query_params.get("seccion", "prediccion")).lower().strip()
if seccion not in SECCIONES_VALIDAS:
    seccion = "prediccion"

hero_por_seccion = {
    "produccion": {
        "eyebrow": "Cooperativa agraria · Tocache · Perú",
        "titulo": "Consulta productiva de socios",
        "descripcion": "Revise la información registrada de cada socio y su evolución mensual de producción y rendimiento antes de realizar una predicción.",
        "kicker": "Información productiva",
        "nota": "Perfil e historial del productor en una sola vista.",
        "detalle": "Los datos mostrados provienen de la base local preparada para el sistema y se vinculan mediante el identificador interno del socio.",
    },
    "prediccion": {
        "eyebrow": "Cooperativa agraria · Tocache · Perú",
        "titulo": "Predicción productiva para palma aceitera",
        "descripcion": "Una herramienta de apoyo para anticipar el nivel de producción del siguiente mes a partir de información productiva, climática y agronómica registrada en ACEPAT.",
        "kicker": "Sistema de apoyo productivo",
        "nota": "Datos de campo convertidos en una señal para planificar.",
        "detalle": "El resultado clasifica el periodo como BAJA, MEDIA o ALTA y muestra las probabilidades estimadas por el modelo.",
    },
    "historial": {
        "eyebrow": "Seguimiento de resultados",
        "titulo": "Historial de predicciones realizadas",
        "descripcion": "Consulte los resultados generados por esta instalación, identifique al socio y periodo evaluado y descargue el registro para análisis posterior.",
        "kicker": "Trazabilidad local",
        "nota": "Cada predicción queda registrada para su consulta.",
        "detalle": "El historial local conserva el socio, periodo, nivel predicho, probabilidades y modelo utilizado.",
    },
    "modelo": {
        "eyebrow": "Machine Learning aplicado",
        "titulo": "Modelo utilizado por el sistema",
        "descripcion": "Consulte el algoritmo seleccionado después de la evaluación comparativa y las métricas empleadas para determinar su desempeño.",
        "kicker": "Información técnica",
        "nota": "El modelo se utiliza para clasificación productiva.",
        "detalle": "La salida corresponde a los niveles BAJA, MEDIA o ALTA; no representa una cantidad exacta de toneladas futuras.",
    },
}
hero = hero_por_seccion[seccion]

def clase_nav(nombre: str) -> str:
    return "active" if seccion == nombre else ""

st.markdown(
    f"""
    <div class="acepat-site-header">
      <div class="acepat-nav">
        <div class="acepat-logo"><img src="{MARCA_ACEPAT}" alt="ACEPAT"></div>
        <nav class="acepat-navlinks" aria-label="Navegación principal del sistema">
          <a class="{clase_nav('produccion')}" href="?seccion=produccion" target="_self">Producción</a>
          <a class="{clase_nav('prediccion')}" href="?seccion=prediccion" target="_self">Predicción</a>
          <a class="{clase_nav('historial')}" href="?seccion=historial" target="_self">Historial</a>
          <a class="{clase_nav('modelo')}" href="?seccion=modelo" target="_self">Modelo</a>
          <span class="acepat-navpill" title="Identificador del sistema; no es un botón">Sistema ML</span>
        </nav>
      </div>
    </div>

    <section class="acepat-hero">
      <div>
        <div class="acepat-eyebrow">{hero['eyebrow']}</div>
        <h1>{hero['titulo']}</h1>
        <p>{hero['descripcion']}</p>
      </div>
      <div class="acepat-hero-note">
        <div class="note-kicker">{hero['kicker']}</div>
        <strong>{hero['nota']}</strong>
        <p>{hero['detalle']}</p>
      </div>
    </section>

    <div class="acepat-stat-strip">
      <div class="acepat-stat"><span>Modelo seleccionado</span><strong>{ganador.get('modelo', 'No disponible')}</strong></div>
      <div class="acepat-stat"><span>Base de trabajo</span><strong>7 150 registros</strong></div>
      <div class="acepat-stat"><span>Salida del sistema</span><strong>BAJA · MEDIA · ALTA</strong></div>
    </div>
    """,
    unsafe_allow_html=True,
)

def render_produccion():
    st.markdown(
        """
        <div class="acepat-intro">
          <div>
            <h2>Información productiva por socio</h2>
            <p>Seleccione un productor para consultar sus datos generales y los registros mensuales disponibles en la base del sistema.</p>
          </div>
          <div class="acepat-rule"><strong>Uso de esta vista.</strong> Permite revisar el historial real antes de pasar a la sección Predicción.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    ids_socios = catalogo_socios["codigo_socio"].astype(str).tolist()
    nombres_por_id = dict(
        zip(
            catalogo_socios["codigo_socio"].astype(str),
            catalogo_socios["nombre_socio"].astype(str),
        )
    )
    socio_id = st.selectbox(
        "Nombre del socio o productor",
        options=ids_socios,
        format_func=lambda valor: nombres_por_id.get(str(valor), str(valor)),
        key="socio_seleccionado",
        help="Seleccione un socio para cargar su información productiva registrada.",
    )
    socio = catalogo_socios[
        catalogo_socios["codigo_socio"].astype(str) == str(socio_id)
    ].iloc[0]

    nombre = str(socio.get("nombre_socio", "")).strip()
    dni = str(socio.get("dni", "")).strip()
    sexo = str(socio.get("sexo", "")).strip().upper()
    sexo_texto = {"M": "Masculino", "F": "Femenino"}.get(sexo, "No registrado")
    comite = str(socio.get("comite_sectorial", "")).strip() or "No registrado"

    st.subheader("Datos generales")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Socio", nombre)
    c2.metric("DNI", dni)
    c3.metric("Comité sectorial", comite)
    c4.metric("Sexo", sexo_texto)

    c5, c6, c7, c8 = st.columns(4)
    c5.metric("Hectáreas en producción", f"{_numero_seguro(socio.get('hectareas_produccion')):.2f} ha")
    c6.metric("Área instalada", f"{_numero_seguro(socio.get('area_instalada_ha')):.2f} ha")
    c7.metric("Parcelas", f"{int(round(_numero_seguro(socio.get('numero_parcelas_produccion'))))}")
    anio_siembra = socio.get("anio_siembra_ponderado")
    c8.metric(
        "Año de siembra estimado",
        "—" if anio_siembra is None or pd.isna(anio_siembra) else f"{float(anio_siembra):.0f}",
    )

    registros = datos_socios[
        datos_socios["codigo_socio"].astype(str) == str(socio_id)
    ].copy()
    registros = registros.dropna(subset=["anio", "mes"]).sort_values(["anio", "mes"])

    if registros.empty:
        st.info("No existen registros productivos mensuales asociados a este socio en la base local.")
        return

    registros["fecha"] = pd.to_datetime(
        {
            "year": registros["anio"].astype(int),
            "month": registros["mes"].astype(int),
            "day": 1,
        }
    )
    registros["periodo"] = registros.apply(
        lambda fila: f"{MESES[int(fila['mes'])]} {int(fila['anio'])}", axis=1
    )

    ultima = registros.iloc[-1]
    promedio_prod = pd.to_numeric(registros["produccion_tn"], errors="coerce").mean()
    promedio_rend = pd.to_numeric(registros["rendimiento_tn_ha"], errors="coerce").mean()

    st.subheader("Resumen del historial disponible")
    r1, r2, r3, r4 = st.columns(4)
    r1.metric("Último periodo", str(ultima["periodo"]))
    r2.metric("Última producción", f"{_numero_seguro(ultima.get('produccion_tn')):.2f} t")
    r3.metric("Producción promedio", f"{0.0 if pd.isna(promedio_prod) else promedio_prod:.2f} t")
    r4.metric("Rendimiento promedio", f"{0.0 if pd.isna(promedio_rend) else promedio_rend:.3f} t/ha")

    st.subheader("Evolución mensual de producción")
    grafico_produccion = registros.set_index("fecha")[["produccion_tn"]].rename(
        columns={"produccion_tn": "Producción (t)"}
    )
    st.line_chart(grafico_produccion)

    st.subheader("Registros productivos")
    tabla = registros[
        [
            "periodo",
            "produccion_tn",
            "rendimiento_tn_ha",
            "edad_plantacion_anios",
            "estado_calidad_registro",
        ]
    ].copy()
    tabla.columns = [
        "Periodo",
        "Producción (t)",
        "Rendimiento (t/ha)",
        "Edad plantación (años)",
        "Estado del registro",
    ]
    st.dataframe(tabla.iloc[::-1], use_container_width=True, hide_index=True)

    st.markdown(
        '<a href="?seccion=prediccion" target="_self" style="font-weight:800;color:#14352A;text-decoration:none;border-bottom:2px solid #C8A43A;padding-bottom:2px;">Ir a realizar una predicción →</a>',
        unsafe_allow_html=True,
    )

def render_prediccion():
    st.caption(
        "Seleccione el socio y el periodo. El sistema precarga automáticamente la información disponible del mes base desde ACEPAT; todos los valores quedan visibles y editables antes de ejecutar la predicción."
    )

    col_periodo_1, col_periodo_2, col_periodo_3 = st.columns([1, 1, 1.4])
    with col_periodo_1:
        mes_objetivo = st.selectbox(
            "Mes que se desea predecir",
            options=list(MESES),
            index=4,
            format_func=lambda valor: MESES[valor],
        )
    with col_periodo_2:
        anio_objetivo = st.number_input(
            "Año que se desea predecir",
            min_value=2026,
            max_value=2035,
            value=2026,
            step=1,
        )
    anio_base, mes_base = periodo_anterior(int(anio_objetivo), int(mes_objetivo))
    with col_periodo_3:
        st.metric(
            "Periodo base de la predicción",
            formatear_periodo(anio_base, mes_base),
        )

    if not periodo_es_valido(int(anio_objetivo), int(mes_objetivo)):
        st.error("Seleccione mayo de 2026 o un periodo posterior.")

    st.subheader("1. Identificación del socio")

    ids_socios = catalogo_socios["codigo_socio"].astype(str).tolist()
    nombres_por_id = dict(
        zip(
            catalogo_socios["codigo_socio"].astype(str),
            catalogo_socios["nombre_socio"].astype(str),
        )
    )

    socio_id = st.selectbox(
        "Nombre del socio o productor",
        options=ids_socios,
        format_func=lambda valor: nombres_por_id.get(str(valor), str(valor)),
        key="socio_seleccionado",
        help="Seleccione al socio. El sistema cargará automáticamente la información disponible asociada a su registro.",
    )
    socio = catalogo_socios[
        catalogo_socios["codigo_socio"].astype(str) == str(socio_id)
    ].iloc[0]

    firma_carga = f"{socio_id}|{int(anio_base):04d}-{int(mes_base):02d}"
    if st.session_state.get("_firma_carga_socio") != firma_carga:
        datos_base_encontrados, mensaje_carga, campos_pendientes = cargar_datos_asociados_en_estado(
            socio, datos_socios, int(anio_base), int(mes_base), int(anio_objetivo), int(mes_objetivo)
        )
        st.session_state["_firma_carga_socio"] = firma_carga
        st.session_state["_datos_base_encontrados"] = datos_base_encontrados
        st.session_state["_mensaje_carga"] = mensaje_carga
        st.session_state["_campos_pendientes_auto"] = campos_pendientes

    nombre_socio = str(socio["nombre_socio"]).strip()
    dni_socio = str(socio["dni"]).strip()
    codigo_socio = str(socio["codigo_socio"]).strip()

    col_socio_1, col_socio_2, col_socio_3 = st.columns([1.5, 1, 1])
    with col_socio_1:
        st.metric("Socio seleccionado", nombre_socio)
    with col_socio_2:
        st.metric("DNI", dni_socio)
    with col_socio_3:
        sexo = st.selectbox(
            "Sexo registrado",
            options=["M", "F", "DESCONOCIDO"],
            format_func=lambda valor: {
                "M": "Masculino",
                "F": "Femenino",
                "DESCONOCIDO": "No registrado",
            }[valor],
            key="sexo",
        )

    comite_sectorial = st.selectbox(
        "Comité sectorial",
        options=perfil["categorias"]["comite_sectorial"],
        key="comite_sectorial",
    )

    pendientes_auto = st.session_state.get("_campos_pendientes_auto", [])
    if st.session_state.get("_datos_base_encontrados") and not pendientes_auto:
        st.success(st.session_state.get("_mensaje_carga", "Datos del socio cargados."))
    else:
        st.warning(st.session_state.get("_mensaje_carga", ""))
    st.caption(
        "Los datos encontrados en ACEPAT se muestran directamente en el formulario, pero no quedan bloqueados: pueden editarse antes de predecir si el registro institucional requiere una corrección o actualización."
    )

    st.subheader("2. Características productivas")
    col_prod_1, col_prod_2, col_prod_3, col_prod_4 = st.columns(4)
    with col_prod_1:
        hectareas = numero(
            "Hectáreas en producción",
            "hectareas",
            step=0.1,
            ayuda="Superficie que actualmente produce palma aceitera.",
        )
    with col_prod_2:
        area_instalada = numero(
            "Área instalada total (ha)",
            "area_instalada",
            step=0.1,
        )
    with col_prod_3:
        parcelas = numero(
            "Número de parcelas",
            "parcelas",
            min_value=0,
            step=1,
            entero=True,
        )
    with col_prod_4:
        edad_plantacion = numero(
            "Edad de la plantación (años)",
            "edad_plantacion",
            min_value=0,
            step=1,
        )

    col_hist_1, col_hist_2 = st.columns(2)
    with col_hist_1:
        produccion_anterior = numero(
            f"Producción de {MESES[mes_base]} (t)",
            "produccion_anterior",
            step=0.1,
        )
    with col_hist_2:
        rendimiento_anterior = numero(
            f"Rendimiento de {MESES[mes_base]} (t/ha)",
            "rendimiento_anterior",
            step=0.01,
        )

    st.subheader("3. Información climática del periodo base")
    col_clima_1, col_clima_2 = st.columns(2)
    with col_clima_1:
        precipitacion_anterior = numero(
            f"Precipitación de {MESES[mes_base]} (mm)",
            "precipitacion_anterior",
            step=1,
        )
    with col_clima_2:
        precipitacion_3_meses = numero(
            "Precipitación acumulada de los últimos 3 meses (mm)",
            "precipitacion_3_meses",
            step=1,
        )

    st.subheader("4. Fertilización del periodo base")
    fertilizantes_disponibles = st.radio(
        "¿Cuenta con información de fertilizantes?",
        options=["SI", "NO"],
        horizontal=True,
        key="fertilizantes_disponibles",
    )
    col_fert_1, col_fert_2, col_fert_3, col_fert_4 = st.columns(4)
    deshabilitar_fert = fertilizantes_disponibles == "NO"
    with col_fert_1:
        movimientos_fertilizante = numero(
            "Movimientos registrados",
            "movimientos_fertilizante",
            min_value=0,
            step=1,
            entero=True,
            disabled=deshabilitar_fert,
        )
    with col_fert_2:
        unidades_fertilizante = numero(
            "Unidades utilizadas",
            "unidades_fertilizante",
            min_value=0,
            step=1,
            disabled=deshabilitar_fert,
        )
    with col_fert_3:
        monto_fertilizante = numero(
            "Monto utilizado (S/)",
            "monto_fertilizante",
            min_value=0,
            step=10,
            disabled=deshabilitar_fert,
        )
    with col_fert_4:
        tipos_fertilizante = numero(
            "Tipos de fertilizante",
            "tipos_fertilizante",
            min_value=0,
            step=1,
            entero=True,
            disabled=deshabilitar_fert,
        )

    st.subheader("5. Fumigación y plagas del periodo base")
    fumigacion_disponible = st.radio(
        "¿Cuenta con información de fumigación?",
        options=["SI", "NO"],
        horizontal=True,
        key="fumigacion_disponible",
    )
    col_fum_1, col_fum_2, col_fum_3, col_fum_4 = st.columns(4)
    deshabilitar_fum = fumigacion_disponible == "NO"
    with col_fum_1:
        numero_fumigaciones = numero(
            "Número de fumigaciones",
            "numero_fumigaciones",
            min_value=0,
            step=1,
            entero=True,
            disabled=deshabilitar_fum,
        )
    with col_fum_2:
        horas_maquina = numero(
            "Horas máquina",
            "horas_maquina",
            min_value=0,
            step=0.1,
            disabled=deshabilitar_fum,
        )
    with col_fum_3:
        tanques = numero(
            "Número de tanques",
            "tanques",
            min_value=0,
            step=1,
            entero=True,
            disabled=deshabilitar_fum,
        )
    with col_fum_4:
        numero_plagas = numero(
            "Número de plagas registradas",
            "numero_plagas",
            min_value=0,
            step=1,
            entero=True,
            disabled=deshabilitar_fum,
        )

    datos = {
        "codigo_socio": codigo_socio,
        "nombre_socio": nombre_socio,
        "dni": dni_socio,
        "comite_sectorial": comite_sectorial,
        "sexo": sexo,
        "hectareas_produccion": hectareas,
        "area_instalada_ha": area_instalada,
        "numero_parcelas_produccion": parcelas,
        "edad_plantacion_anios": edad_plantacion,
        "produccion_mes_anterior_tn": produccion_anterior,
        "rendimiento_mes_anterior_tn_ha": rendimiento_anterior,
        "precipitacion_mes_anterior_mm": precipitacion_anterior,
        "precipitacion_acumulada_3_meses_mm": precipitacion_3_meses,
        "datos_fertilizantes_mes_anterior_disponibles": fertilizantes_disponibles,
        "movimientos_fertilizante_mes_anterior": movimientos_fertilizante,
        "unidades_fertilizante_mes_anterior": unidades_fertilizante,
        "monto_fertilizante_mes_anterior": monto_fertilizante,
        "tipos_fertilizante_mes_anterior": tipos_fertilizante,
        "datos_fumigacion_mes_anterior_disponibles": fumigacion_disponible,
        "numero_fumigaciones_mes_anterior": numero_fumigaciones,
        "horas_maquina_mes_anterior": horas_maquina,
        "tanques_mes_anterior": tanques,
        "numero_plagas_mes_anterior": numero_plagas,
    }

    st.divider()
    boton_predecir = st.button(
        "Predecir nivel de producción",
        type="primary",
        use_container_width=True,
    )
    #1 
    if boton_predecir:
        try:
            entrada = construir_entrada_modelo(
                datos,
                int(anio_objetivo),
                int(mes_objetivo),
                metadatos["predictores"],
            )
            advertencias = advertencias_fuera_de_rango(datos, perfil)
            nivel, probabilidades = ejecutar_prediccion(modelo, entrada)
            registro = construir_registro_resultado(
                datos,
                int(anio_objetivo),
                int(mes_objetivo),
                nivel,
                probabilidades,
                ganador,
            )
            guardar_historial(registro)
            st.session_state["ultimo_resultado"] = {
                "registro": registro,
                "datos": datos,
                "probabilidades": probabilidades,
                "advertencias": advertencias,
            }
        except Exception as exc:
            st.error(str(exc))

    if "ultimo_resultado" in st.session_state:
        resultado = st.session_state["ultimo_resultado"]
        registro = resultado["registro"]
        probabilidades = resultado["probabilidades"]

        st.subheader("Resultado de la predicción")
        st.markdown(
            f"""
            <div class="result-card">
              <div class="small-muted">Socio</div>
              <strong>{registro.get('nombre_socio', '')}</strong>
              <div class="small-muted" style="margin-top:.65rem;">Periodo predicho</div>
              <strong>{registro['periodo_predicho']}</strong>
              <div class="result-level level-{registro['nivel_predicho']}">
                Nivel {registro['nivel_predicho']}
              </div>
              <div class="small-muted">
                Modelo seleccionado por la evaluación final: {registro['modelo']}
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        col_prob_1, col_prob_2, col_prob_3 = st.columns(3)
        col_prob_1.metric("Probabilidad BAJA", f"{probabilidades['BAJA']:.1%}")
        col_prob_2.metric("Probabilidad MEDIA", f"{probabilidades['MEDIA']:.1%}")
        col_prob_3.metric("Probabilidad ALTA", f"{probabilidades['ALTA']:.1%}")

        grafico = pd.DataFrame(
            {"Probabilidad": [probabilidades[clase] for clase in CLASES]},
            index=CLASES,
        )
        st.bar_chart(grafico, y="Probabilidad", horizontal=True)

        for advertencia in resultado["advertencias"]:
            st.warning(advertencia)

        st.caption(
            "Las probabilidades expresan el comportamiento estimado del modelo "
            "y no garantizan el nivel real que se obtendrá."
        )
        archivo = generar_excel_resultado(registro, resultado["datos"])
        nombre_seguro = "".join(
            caracter if caracter.isalnum() else "_"
            for caracter in registro.get("nombre_socio", registro["codigo_socio"])
        ).strip("_")
        nombre_archivo = (
            f"prediccion_{nombre_seguro}_"
            f"{registro['periodo_predicho'].replace(' ', '_')}.xlsx"
        )
        st.download_button(
            "Descargar reporte de la predicción",
            data=archivo,
            file_name=nombre_archivo,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )

def render_historial():
    st.subheader("Historial local de predicciones")
    st.caption(
        "El historial se guarda en data/historial_predicciones.csv dentro de esta "
        "instalación. Para producción institucional se deberá migrar a una base "
        "de datos con usuarios, permisos y copias de seguridad."
    )
    historial = leer_historial()
    if historial.empty:
        st.info("Todavía no se han registrado predicciones.")
    else:
        columnas_porcentaje = [
            "probabilidad_baja",
            "probabilidad_media",
            "probabilidad_alta",
            "f1_macro_prueba",
            "accuracy_prueba",
        ]
        configuracion_columnas = {
            columna: st.column_config.NumberColumn(format="%.2f")
            for columna in columnas_porcentaje
            if columna in historial.columns
        }
        historial_visible = historial.copy()
        historial_visible = historial_visible.drop(
            columns=["codigo_socio"],
            errors="ignore",
        )
        orden_preferido = [
            "fecha_hora_prediccion",
            "nombre_socio",
            "dni",
            "comite_sectorial",
            "periodo_base",
            "periodo_predicho",
            "nivel_predicho",
            "probabilidad_baja",
            "probabilidad_media",
            "probabilidad_alta",
            "modelo",
        ]
        columnas_ordenadas = [
            columna for columna in orden_preferido if columna in historial_visible.columns
        ] + [
            columna
            for columna in historial_visible.columns
            if columna not in orden_preferido
        ]
        historial_visible = historial_visible[columnas_ordenadas]

        st.dataframe(
            historial_visible.sort_index(ascending=False),
            use_container_width=True,
            hide_index=True,
            column_config=configuracion_columnas,
        )
        st.download_button(
            "Descargar historial en CSV",
            data=historial.to_csv(index=False).encode("utf-8-sig"),
            file_name="historial_predicciones_acepat.csv",
            mime="text/csv",
        )
#2 la vista de modelo lee los resultados ya almacenados y muestra las metricas del ganador
def render_modelo():
    st.subheader("Información técnica del modelo utilizado")
    col_mod_1, col_mod_2, col_mod_3, col_mod_4 = st.columns(4)

    col_mod_1.metric("Accuracy", f"{ganador.get('accuracy', 0):.4f}")
    col_mod_2.metric("Precisión macro", f"{ganador.get('precision_macro', 0):.4f}")
    col_mod_3.metric("Recall macro", f"{ganador.get('recall_macro', 0):.4f}")
    col_mod_4.metric("F1 macro", f"{ganador.get('f1_macro', 0):.4f}")

    st.write(
        "El modelo fue seleccionado por el mayor F1 macro en la prueba reservada "
        "de 2026, con desempate por Accuracy y Recall macro."
    )
    st.write(
        f"**Registros de entrenamiento:** {metadatos.get('registros_entrenamiento', 0):,}"
    )
    st.write(
        f"**Registros de prueba reservada:** {metadatos.get('registros_prueba_reservada', 0):,}"
    )
    st.write(f"**Cantidad de predictores:** {len(metadatos.get('predictores', []))}")
    st.warning(
        "El sistema clasifica el nivel de producción como BAJA, MEDIA o ALTA. "
        "No calcula directamente la cantidad futura de toneladas."
    )

if seccion == "produccion":
    render_produccion()
elif seccion == "historial":
    render_historial()
elif seccion == "modelo":
    render_modelo()
else:
    render_prediccion()


st.markdown(
    """
    <footer class="acepat-footer">
      <span><strong>ACEPAT</strong> · Sistema de predicción productiva · Tocache, San Martín, Perú</span>
      <span><a href="https://www.acepat.org/" target="_blank">Sitio institucional ACEPAT</a></span>
    </footer>
    """,
    unsafe_allow_html=True,
)
