# Desafío Ingeniero de Software (ML & LLMs)

## Descripción General

Bienvenido al **Desafío de Aplicación para Ingeniero de Software (ML & LLMs)**. En este, tendrás la oportunidad de acercarte a una parte de la realidad del rol, y demostrar tus habilidades y conocimientos en machine learning y cloud.

## Problema

Se ha proporcionado un jupyter notebook (`exploration.ipynb`) con el trabajo de un Científico de Datos (de ahora en adelante, el DS). El DS entrenó un modelo para predecir la probabilidad de **retraso** de un vuelo despegado o aterrizado en el aeropuerto SCL. El modelo fue entrenado con datos públicos y reales, a continuación te proporcionamos la descripción del dataset:

|Columna|Descripción|
|-----|-----------|
|`Fecha-I`|Fecha y hora programada del vuelo.|
|`Vlo-I`|Número de vuelo programado.|
|`Ori-I`|Código de ciudad de origen programado.|
|`Des-I`|Código de ciudad de destino programado.|
|`Emp-I`|Código de aerolinea del vuelo programado.|
|`Fecha-O`|Fecha y hora de operación del vuelo.|
|`Vlo-O`|Número de operación del vuelo.|
|`Ori-O`|Código de ciudad de origen de operación.|
|`Des-O`|Código de ciudad de destino de operación.|
|`Emp-O`|Código de aerolinea del vuelo operado.|
|`DIA`|Día del mes de operación del vuelo.|
|`MES`|Número del mes de operación del vuelo.|
|`AÑO`|Año de operación del vuelo.|
|`DIANOM`|Día de la semana de operación del vuelo.|
|`TIPOVUELO`|Tipo de vuelo, I =Internacional, N =Nacional.|
|`OPERA`|Nombre de la aerolinea que opera.|
|`SIGLAORI`|Nombre de la ciudad de origen.|
|`SIGLADES`|Nombre de la ciudad de destino.|

Además, el DS consideró relevante la creación de las siguientes columnas:

|Columna|Descripción|
|-----|-----------|
|`high_season`|1 si `Fecha-I` está entre Dic-15 y Mar-3, o Jul-15 y Jul-31, o Sep-11 y Sep-30, 0 de lo contrario.|
|`min_diff`|diferencia en minutos entre `Fecha-O` y `Fecha-I`|
|`period_day`|mañana (entre 5:00 y 11:59), tarde (entre 12:00 y 18:59) y noche (entre 19:00 y 4:59), basado en `Fecha-I`.|
|`delay`|1 si `min_diff` > 15, 0 si no.|

## Desafío

### Instrucciones

1. Crea un repositorio en **github** y copia todo el contenido del desafío en él. Recuerda que el repositorio debe ser **público**.

2. Usa la rama **main** para cualquier lanzamiento oficial que debamos revisar. Se recomienda altamente usar prácticas de desarrollo de [GitFlow](https://www.atlassian.com/git/tutorials/comparing-workflows/gitflow-workflow). **NOTA: no elimines tus ramas de desarrollo.**
    
3. Por favor, no cambies la estructura del desafío (nombres de carpetas y archivos).
    
4. Toda la documentación y explicaciones que debas darnos deben ir en el archivo `challenge.md` dentro de la carpeta `docs`.

5. Para enviar tu desafío, debes hacer una solicitud `POST` a:
    `https://advana-challenge-check-api-cr-k4hdbggvoq-uc.a.run.app/software-engineer`
    Este es un ejemplo del `body` que debes enviar:
    ```json
    {
      "name": "Juan Perez",
      "mail": "juan.perez@example.com",
      "github_url": "https://github.com/juanperez/latam-challenge.git",
      "api_url": "https://juan-perez.api"
    }
    ```
    ##### ***POR FAVOR, ENVÍA LA SOLICITUD UNA SOLA VEZ.***

    Si tu solicitud fue exitosa, recibirás este mensaje:
    ```json
    {
      "status": "OK",
      "detail": "your request was received"
    }
    ```

***NOTA: Recomendamos enviar el desafío incluso si no lograste terminar todas las partes.***

### Contexto:

Necesitamos operacionalizar el trabajo de ciencia de datos para el equipo del aeropuerto. Para esto, hemos decidido habilitar una `API` en la cual puedan consultar la predicción de retraso de un vuelo.

*Recomendamos leer todo el desafío (todas sus partes) antes de empezar a desarrollar.*

### Parte I

Para operacionalizar el modelo, transcribe el archivo `.ipynb` al archivo `model.py`:

- Si encuentras algún bug, arréglalo.
- El DS propuso algunos modelos al final. Elige el mejor modelo a tu criterio, argumenta por qué. **No es necesario hacer mejoras al modelo.**
- Aplica todas las buenas prácticas de programación que consideres necesarias en este ítem.
- El modelo debe pasar las pruebas ejecutando `make model-test`.

> **Nota:**
> - **No puedes** eliminar o cambiar el nombre o argumentos de los métodos **proporcionados**.
> - **Puedes** cambiar/completar la implementación de los métodos proporcionados.
> - **Puedes** crear las clases y métodos extra que consideres necesarios.

### Parte II

Despliega el modelo en una `API` con `FastAPI` usando el archivo `api.py`.

- La `API` debe pasar las pruebas ejecutando `make api-test`.

> **Nota:** 
> - **No puedes** usar otro framework.

### Parte III

Despliega la `API` en tu proveedor de nube favorito (recomendamos usar GCP).

- Pon la url de la `API` en el `Makefile` (`línea 26`).
- La `API` debe pasar las pruebas ejecutando `make stress-test`.

> **Nota:** 
> - **Es importante que la API esté desplegada hasta que revisemos las pruebas.**

### Parte IV

Buscamos una implementación adecuada de `CI/CD` para este desarrollo.

- Crea una nueva carpeta llamada `.github` y copia la carpeta `workflows` que te proporcionamos dentro de ella.
- Completa tanto `ci.yml` como `cd.yml` (considera lo que hiciste en las partes anteriores).