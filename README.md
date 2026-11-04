# ACEPAT ML — Sistema de predicción de producción de palma aceitera

Este proyecto implementa el sistema desarrollado para ACEPAT y los seis algoritmos de Machine Learning evaluados en la tesis:

1. Regresión logística.
2. Árbol de decisiones.
3. Random Forest.
4. SVM.
5. Gradient Boosting.
6. KNN.

La población metodológica es de 10 000 registros y la muestra utilizada es de **7 150 registros**.

> **Importante:** para abrir y utilizar la interfaz web **no es necesario volver a entrenar los modelos**. El proyecto ya incluye el modelo ganador guardado. Para visualizar el sistema, basta con preparar el entorno una sola vez y ejecutar `app.py` mediante Streamlit.

---

# PARTE A. Levantar la interfaz web de ACEPAT

## 1. Requisitos previos

Para ejecutar el sistema en Windows se necesita:

- Windows 10 u 11.
- Visual Studio Code.
- Python 3.12.
- Conexión a internet únicamente durante la primera instalación de las librerías.

Se recomienda utilizar **Python 3.12**, porque es la versión compatible con el entorno utilizado para los modelos guardados del proyecto.

---

## 2. Descomprimir y abrir correctamente el proyecto

1. Descomprima el archivo ZIP del proyecto.
2. Abra **Visual Studio Code**.
3. Seleccione **Archivo > Abrir carpeta**.
4. Seleccione directamente la carpeta:

```text
ACEPAT_ML_VSCode
```

5. En el panel izquierdo de Visual Studio Code debe poder ver, entre otros, estos archivos y carpetas:

```text
ACEPAT_ML_VSCode/
├── app.py
├── requirements.txt
├── funciones_prediccion.py
├── data/
├── modelos/
├── evidencia_metodologica/
└── README.md
```



## 3. Abrir la terminal de Visual Studio Code

En Visual Studio Code seleccione:

```text
Terminal > Nueva terminal
```

La terminal debe quedar ubicada dentro del proyecto. Por ejemplo:

```text
PS C:\Users\Usuario\Documents\ACEPAT_ML_VSCode>
```

No debería aparecer una ruta como:

```text
PS C:\WINDOWS\system32>
```

---

## 4. Verificar que se abrió la carpeta correcta

Ejecute los siguientes comandos 

```powershell
Test-Path .\app.py
```

Debe responder:

```text
True
```

Luego:

```powershell
Test-Path .\requirements.txt
```

Debe responder:

```text
True
```

Si alguno responde `False`, no continúe todavía. Significa que la terminal no está ubicada en la carpeta correcta del proyecto.

---

## 5. Comprobar Python instalado

Ejecute:

```powershell
py -0p
```

Busque una instalación de **Python 3.12**.

### Si Python 3.12 ya aparece

Continúe con el paso 6.

### Si Python 3.12 no aparece

Ejecute:

```powershell
py install 3.12
```

Cuando termine, vuelva a comprobar:

```powershell
py -0p
```

---

## 6. Crear el entorno virtual

Este paso se realiza **solo la primera vez** que se prepara el proyecto en una computadora.

Ejecute:

```powershell
py -3.12 -m venv .venv
```

Espere hasta que vuelva a aparecer el cursor de PowerShell.

Después compruebe que el entorno fue creado:

```powershell
Test-Path .\.venv\Scripts\python.exe
```

Debe responder:

```text
True
```

---

## 7. Verificar la versión de Python del entorno

Ejecute:

```powershell
.\.venv\Scripts\python.exe --version
```

Debe mostrar una versión similar a:

```text
Python 3.12.x
```

> No es necesario activar `.venv` con `Activate.ps1`. Los comandos de esta guía llaman directamente al Python del entorno virtual, evitando problemas con las políticas de ejecución de PowerShell.

---

## 8. Actualizar `pip`

Ejecute:

```powershell
.\.venv\Scripts\python.exe -m pip install --upgrade pip
```

Espere hasta que la instalación termine completamente.

---

## 9. Instalar las librerías necesarias

Ejecute:

```powershell
.\.venv\Scripts\python.exe -m pip install -r .\requirements.txt
```

Este paso puede tardar varios minutos la primera vez.

No cierre la terminal mientras se instalan las dependencias.

Entre las librerías instaladas se encuentran:

- pandas;
- NumPy;
- scikit-learn;
- joblib;
- matplotlib;
- openpyxl;
- Streamlit.

---

## 10. Verificar Streamlit

Cuando termine la instalación, ejecute:

```powershell
.\.venv\Scripts\python.exe -m streamlit --version
```

Debe mostrar una versión instalada de Streamlit.

Por ejemplo:

```text
Streamlit, version 1.x.x
```

---

## 11. Levantar la página web de ACEPAT

Ejecute:

```powershell
.\.venv\Scripts\python.exe -m streamlit run .\app.py
```

Después de unos segundos, la terminal mostrará una dirección similar a:

```text
Local URL: http://localhost:8501
```

Normalmente el navegador se abrirá automáticamente.

Si no ocurre, abra Chrome, Edge u otro navegador e ingrese manualmente:

```text
http://localhost:8501
```

Con esto se visualizará la interfaz del sistema ACEPAT.

---

## 12. Detener la aplicación

Para detener el servidor, vuelva a la terminal de Visual Studio Code y presione:

```text
Ctrl + C
```

---

## 13. Abrir la interfaz en las siguientes ocasiones

Después de haber realizado la instalación inicial, **no es necesario volver a crear `.venv` ni reinstalar las librerías cada vez**.

Solo debe:

1. Abrir la carpeta `ACEPAT_ML_VSCode` en Visual Studio Code.
2. Abrir **Terminal > Nueva terminal**.
3. Ejecutar:

```powershell
.\.venv\Scripts\python.exe -m streamlit run .\app.py
```

La aplicación volverá a estar disponible en:

```text
http://localhost:8501
```

---

## 14. Resumen de comandos para la primera instalación

Ejecute **uno por uno y en este orden**:

```powershell
Test-Path .\app.py
```

Resultado esperado:

```text
True
```

```powershell
Test-Path .\requirements.txt
```

Resultado esperado:

```text
True
```

```powershell
py -0p
```

Solo si Python 3.12 no está instalado:

```powershell
py install 3.12
```

Crear el entorno:

```powershell
py -3.12 -m venv .venv
```

Comprobarlo:

```powershell
Test-Path .\.venv\Scripts\python.exe
```

Resultado esperado:

```text
True
```

Verificar Python:

```powershell
.\.venv\Scripts\python.exe --version
```

Actualizar `pip`:

```powershell
.\.venv\Scripts\python.exe -m pip install --upgrade pip
```

Instalar dependencias:

```powershell
.\.venv\Scripts\python.exe -m pip install -r .\requirements.txt
```

Comprobar Streamlit:

```powershell
.\.venv\Scripts\python.exe -m streamlit --version
```

Levantar la interfaz:

```powershell
.\.venv\Scripts\python.exe -m streamlit run .\app.py
```

---

## 15. Problemas frecuentes al levantar la interfaz

### Error: `app.py` no existe

Si aparece un mensaje similar a:

```text
File does not exist: app.py
```

compruebe:

```powershell
Test-Path .\app.py
```

Si devuelve `False`, abra directamente la carpeta `ACEPAT_ML_VSCode` en Visual Studio Code.

### Error: `requirements.txt` no existe

Compruebe:

```powershell
Test-Path .\requirements.txt
```

Si devuelve `False`, la terminal está en una carpeta incorrecta.

### Error: `.venv\Scripts\python.exe` no se reconoce

Compruebe:

```powershell
Test-Path .\.venv\Scripts\python.exe
```

Si devuelve `False`, cree el entorno:

```powershell
py -3.12 -m venv .venv
```

### Error: `No module named streamlit`

Ejecute:

```powershell
.\.venv\Scripts\python.exe -m pip install -r .\requirements.txt
```

Después verifique:

```powershell
.\.venv\Scripts\python.exe -m streamlit --version
```

### Advertencia amarilla de Pylance sobre `import streamlit`

Si la aplicación funciona pero Visual Studio Code muestra:

```text
Import "streamlit" could not be resolved
```

seleccione el intérprete correcto:

1. Presione `Ctrl + Shift + P`.
2. Escriba `Python: Select Interpreter`.
3. Seleccione el intérprete cuya ruta termine en:

```text
.venv\Scripts\python.exe
```

### No escribir código Python directamente en PowerShell

Una instrucción como:

```python
import streamlit as st
```

pertenece a un archivo Python como `app.py`; no debe escribirse directamente en PowerShell.

---

# PARTE B. Estructura de datos del sistema

Para uso interno de ACEPAT, la interfaz trabaja con una única base oficial:

```text
data/ACEPAT_Dataset_Limpio_7150.xlsx
```

El libro contiene **una única hoja llamada `Datos`**, con exactamente **7 150 registros**. Cada fila corresponde al registro mensual de un socio de la muestra.

La misma fila incluye tanto la identificación del socio como las variables operativas necesarias, entre ellas:

- `codigo_socio`;
- DNI;
- nombre del socio;
- año y mes;
- comité sectorial;
- sexo;
- hectáreas en producción;
- área instalada;
- número de parcelas;
- edad de la plantación;
- producción;
- rendimiento;
- variables climáticas;
- variables de fertilización;
- variables de fumigación y plagas.

El código, nombre y DNI se utilizan únicamente para identificación y navegación dentro de la interfaz. **No se utilizan como predictores del modelo de Machine Learning.**

La copia anonimizada utilizada para reproducir el experimento metodológico se conserva en:

```text
evidencia_metodologica/Dataset_ACEPAT_ML_Anonimizado_7150.xlsx
```

El historial generado por la interfaz se almacena aparte en:

```text
data/historial_predicciones.csv
```

---

# PARTE C. Funcionamiento de la interfaz

La interfaz visual está implementada en:

```text
app.py
```

y utiliza el modelo ganador ya guardado. Abrir la interfaz **no vuelve a entrenar los seis algoritmos**.

El menú superior contiene:

- **Producción:** consulta la información y los registros mensuales del socio seleccionado.
- **Predicción:** abre el formulario para estimar el nivel de producción de un periodo posterior.
- **Historial:** muestra las predicciones realizadas desde esa instalación.
- **Modelo:** presenta el algoritmo ganador y sus métricas.
- **Sistema ML:** identificador visual de la aplicación.

La primera predicción habilitada corresponde a **mayo de 2026**, porque la información reservada para prueba llega hasta abril de 2026.

Cuando el usuario selecciona un socio y un periodo, el sistema consulta la misma muestra de 7 150 registros. Si existe información del mes inmediatamente anterior, los valores disponibles se cargan automáticamente en el formulario y permanecen **visibles y editables**. Si un valor requerido no está disponible dentro de la muestra, el usuario debe completarlo antes de realizar la predicción.

El modelo devuelve una clasificación del nivel de producción:

```text
BAJA
MEDIA
ALTA
```

junto con las probabilidades estimadas por clase.

---

# PARTE D. Entrenamiento y prueba de los modelos

## ¿Son procesos separados?

Sí. Los dos procesos principales se mantienen separados para proteger la prueba final:

- `01_entrenar_modelos.py`: utiliza 2025 para ajustar y validar los modelos.
- `02_probar_modelos.py`: abre los modelos ya entrenados y los evalúa con los registros reservados de 2026.

También existen archivos auxiliares:

- `00_verificar_dataset.py`: comprueba que el Excel metodológico sea apto.
- `configuracion.py`: contiene rutas, años, muestra, predictores y configuración del experimento.
- `funciones_datos.py`: carga, valida, separa y clasifica los datos.
- `funciones_modelos.py`: construye pipelines, algoritmos y validación temporal.
- `03_analizar_sensibilidad_enero.py`: ejecuta el análisis solicitado sobre la influencia de enero.

---

## 16. Verificar el dataset metodológico

Ejecute:

```powershell
.\.venv\Scripts\python.exe .\00_verificar_dataset.py
```

Debe indicar:

```text
Resultado: APTO PARA MODELADO
```

También se genera:

```text
resultados/verificacion_dataset.txt
```

---

## 17. Entrenar los seis algoritmos

> Este paso **no es necesario para simplemente abrir la interfaz**. Solo debe ejecutarse cuando se desea reproducir el entrenamiento de la tesis.

Ejecute:

```powershell
.\.venv\Scripts\python.exe .\01_entrenar_modelos.py
```

El script:

1. comprueba la muestra de 7 150 registros;
2. utiliza 2025 para entrenamiento y validación temporal;
3. mantiene 2026 reservado para prueba final;
4. calcula los terciles con los datos de entrenamiento;
5. genera las categorías BAJA, MEDIA y ALTA;
6. ejecuta la validación temporal;
7. entrena los seis algoritmos;
8. guarda los pipelines en `modelos/`;
9. genera los reportes correspondientes.

---

## 18. Ejecutar la prueba final

> Este paso tampoco es necesario para abrir la interfaz. Se utiliza para reproducir la evaluación final de la tesis.

Después del entrenamiento, ejecute:

```powershell
.\.venv\Scripts\python.exe .\02_probar_modelos.py
```

El script utiliza enero-abril de 2026 y genera, entre otros:

- `resultados/reporte_prueba_modelos.xlsx`;
- `resultados/comparacion_prueba_2026.csv`;
- predicciones por registro y algoritmo;
- matrices de confusión;
- `modelos/modelo_ganador.joblib`;
- `modelos/modelo_ganador.json`.

El modelo ganador se selecciona según **F1 macro** y, en caso de empate, Accuracy y Recall macro.

---

## 19. Ejecutar desde el depurador de Visual Studio Code

En **Ejecutar y depurar** están configuradas estas opciones:

- `00 - Verificar dataset`.
- `01 - Entrenar modelos`.
- `02 - Probar modelos`.
- `03 - Comparar con y sin enero`.
- `04 - Interfaz ACEPAT`.

Para visualizar directamente el sistema puede elegir:

```text
04 - Interfaz ACEPAT
```

y presionar el botón verde, siempre que `.venv` y las dependencias ya hayan sido instaladas.

---

## 20. Criterio de separación metodológica

```text
Muestra: 7 150 registros
├── Entrenamiento y validación temporal: 2025 — 5 402 registros
└── Prueba final: enero-abril 2026 — 1 748 registros
```

Los mismos socios pueden aparecer en ambos años. El sistema aprende del historial disponible y se evalúa con periodos posteriores.

---

## 21. Prevención de fuga de información

No se utilizan como variables de entrada del modelo:

- producción del mes objetivo;
- rendimiento del mes objetivo;
- nivel de producción real;
- código del socio;
- DNI;
- nombre del socio.

La imputación, codificación y transformación de variables se encuentran dentro del pipeline de Machine Learning.

---

## 22. Algoritmos evaluados

### Requieren escalado

- Regresión logística.
- SVM.
- KNN.

### No requieren escalado por su estructura basada en árboles

- Árbol de decisiones.
- Random Forest.
- Gradient Boosting.

---

## 23. Archivos que no deben eliminarse

Para conservar la reproducibilidad del proyecto, no elimine:

```text
requirements.txt
modelos/
evidencia_metodologica/
configuracion.py
funciones_datos.py
funciones_modelos.py
funciones_prediccion.py
```

Los archivos `.joblib` dependen de las versiones de las librerías con las que fueron generados, por lo que `requirements.txt` debe mantenerse junto con el proyecto.

---

## 24. Diseño visual institucional

La aplicación incorpora una interfaz inspirada en la identidad visual institucional de ACEPAT:

- logotipo oficial;
- encabezado verde oscuro;
- fondo marfil;
- acentos dorados;
- navegación horizontal funcional.

