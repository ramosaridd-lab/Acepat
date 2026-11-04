# Interfaz de predicción ACEPAT


La interfaz permite:

- Seleccionar al socio por su nombre completo desde el padrón incorporado.
- Cargar automáticamente desde la base oficial el código, nombre, DNI, comité, sexo, superficie, parcelas y los datos disponibles del periodo base.
- Seleccionar el mes y año que se desea predecir.
- Revisar y editar los valores precargados antes de ejecutar la predicción.
- Completar manualmente solo los campos que no puedan recuperarse con exactitud desde la base para ese periodo.
- Obtener el nivel estimado de producción: BAJA, MEDIA o ALTA.
- Ver las probabilidades estimadas de las tres clases.
- Descargar un reporte Excel por predicción.
- Consultar y descargar el historial local.

## Regla temporal

La base reservada de prueba contiene información hasta abril de 2026. Por ello:

- La primera predicción operativa es mayo de 2026.
- Para predecir mayo, el sistema busca primero los datos reales de abril en la base oficial y los precarga cuando están disponibles.
- Todos los valores precargados permanecen visibles y editables.
- Para predecir junio, el periodo base será mayo; ACEPAT deberá incorporar o completar los registros reales de mayo.
- El sistema no genera automáticamente varios meses futuros con una sola entrada.

## Instalación recomendada

Los modelos fueron generados con Python 3.12.13. Para reproducibilidad, use Python 3.12 y cree un entorno virtual nuevo.

En Visual Studio Code, abra una terminal PowerShell dentro de la carpeta del proyecto y ejecute:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## Ejecución

```powershell
streamlit run app.py
```

También puede abrir **Ejecutar y depurar** en Visual Studio Code y seleccionar:

```text
04 - Interfaz ACEPAT
```

La aplicación se abrirá normalmente en:

```text
http://localhost:8501
```

## Estructura de datos consolidada

```text
data/
├── ACEPAT_Dataset_Limpio_7150.xlsx
└── historial_predicciones.csv

evidencia_metodologica/
└── Dataset_ACEPAT_ML_Anonimizado_7150.xlsx
```

Nota: La copia anonimizada queda como evidencia reproducible del experimento de Machine Learning y no es consultada por la interfaz.

`ACEPAT_Dataset_Limpio_7150.xlsx` contiene una sola hoja llamada `Datos`, con los 7 150 registros y únicamente la información necesaria para el funcionamiento de la interfaz.

## Historial

Las predicciones se guardan localmente en:

```text
data/historial_predicciones.csv
```

Este archivo no participa en el entrenamiento y está excluido de Git. En una instalación institucional definitiva, el historial debe trasladarse a una base de datos con autenticación, permisos, copias de seguridad y trazabilidad.


## Identidad visual ACEPAT

La interfaz utiliza una identidad visual inspirada en el sitio institucional de ACEPAT:

- marca ACEPAT visible en el encabezado;
- verde bosque, verde hoja, crema y arena como paleta principal;
- encabezado institucional con referencia a Tocache, San Martín y Perú;
- navegación horizontal funcional, botones, métricas y formularios adaptados a la misma línea visual;
- diseño adaptable a computadora y pantalla móvil.


## Navegación funcional del encabezado 

El menú superior de la aplicación funciona como navegación principal:

- **Producción:** permite seleccionar un socio por nombre y revisar sus datos generales, último periodo, producción promedio, rendimiento promedio, evolución mensual y registros disponibles.
- **Predicción:** contiene el formulario de predicción y la carga automática de información asociada al socio.
- **Historial:** consulta y descarga las predicciones realizadas.
- **Modelo:** muestra las métricas y características técnicas del modelo seleccionado.
- **Sistema ML:** es únicamente un identificador visual del aplicativo.

Las pestañas internas anteriores fueron retiradas para evitar duplicación y confusión.


## Precarga editable 
La aplicación carga automáticamente los valores que puede asociar con exactitud al socio y al periodo base. Los controles permanecen editables para que ACEPAT pueda corregir información desactualizada. Si un dato no puede reconstruirse con exactitud, se señala para revisión manual en vez de reutilizar un rezago de un mes incorrecto. El código, nombre y DNI nunca forman parte del vector enviado a Random Forest.
