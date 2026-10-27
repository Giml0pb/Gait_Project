@echo off
cd /d "%~dp0"
REM ============================================================
REM Script de ejecucion automatica para Windows
REM Gait Analysis Pipeline - Docker
REM ============================================================

echo.
echo ====================================================
echo   GAIT ANALYSIS PIPELINE - Ejecucion Automatica
echo ====================================================
echo.

REM Verificar si Docker esta instalado
docker --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Docker no esta instalado o no esta en el PATH
    echo.
    echo Por favor:
    echo   1. Instalar Docker Desktop desde: https://www.docker.com/products/docker-desktop
    echo   2. Reiniciar el ordenador
    echo   3. Volver a ejecutar este script
    echo.
    pause
    exit /b 1
)

echo [1/3] Docker detectado correctamente
echo.

REM Verificar si existe la carpeta de datos
if not exist "data\raw\dataset\data" (
    echo ADVERTENCIA: No se encuentra la carpeta de datos
    echo.
    echo Se espera: %cd%\data\raw\dataset\data\
    echo.
    echo Por favor colocar los datos en esa ubicacion y volver a ejecutar.
    echo.
    pause
    exit /b 1
)

echo [2/3] Datos encontrados en: %cd%\data
echo.

REM Construir la imagen Docker (solo si no existe o ha cambiado)
echo [3/3] Construyendo imagen Docker...
echo (Esto puede tardar 2-5 minutos la primera vez)
echo.
docker build -t gait-pipeline . 2>&1

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERROR: Fallo al construir la imagen Docker
    echo.
    pause
    exit /b 1
)

echo.
echo ====================================================
echo   IMAGEN DOCKER LISTA
echo ====================================================
echo.
echo Seleccione una opcion:
echo.
echo   1. Procesar UN trial de ejemplo (rapido - 10 segundos)
echo   2. Procesar 8 trials por grupo (medio - 5 minutos)
echo   3. Procesar 20 trials por grupo (completo - 15 minutos)
echo   4. Procesar TODOS los trials disponibles
echo.
set /p opcion="Ingrese el numero de opcion (1-4): "
if not "%opcion%"=="1" if not "%opcion%"=="2" if not "%opcion%"=="3" if not "%opcion%"=="4" (
    echo ERROR: Opcion no valida
    pause
    exit /b 1
)
set "run_name=run_%RANDOM%_%RANDOM%"
set "run_dir=/app/outputs/%run_name%"

echo.
echo ====================================================
echo   EJECUTANDO PROCESAMIENTO
echo ====================================================
echo.

if "%opcion%"=="1" (
    echo Procesando trial de ejemplo: HS_1_1
    echo.
    docker run --rm -v "%cd%\data:/app/data:ro" -v "%cd%\outputs:/app/outputs" gait-pipeline uv run python scripts/run_single_trial.py HS_1_1 --output-dir "%run_dir%"
    if errorlevel 1 goto error
)

if "%opcion%"=="2" (
    echo Procesando 8 trials por grupo (24 trials totales)
    echo.
    docker run --rm -v "%cd%\data:/app/data:ro" -v "%cd%\outputs:/app/outputs" gait-pipeline uv run python scripts/run_batch_processing.py --output-dir "%run_dir%"
    if errorlevel 1 goto error
)

if "%opcion%"=="3" (
    echo Procesando 20 trials por grupo (60 trials totales)
    echo.
    docker run --rm -v "%cd%\data:/app/data:ro" -v "%cd%\outputs:/app/outputs" gait-pipeline uv run python scripts/run_batch_processing.py --target 20 --output-dir "%run_dir%"
    if errorlevel 1 goto error
)

if "%opcion%"=="4" (
    echo Procesando TODOS los trials disponibles
    echo ATENCION: Esto puede tardar 1-2 horas
    echo.
    docker run --rm -v "%cd%\data:/app/data:ro" -v "%cd%\outputs:/app/outputs" gait-pipeline uv run python scripts/run_batch_processing.py --all --output-dir "%run_dir%"
    if errorlevel 1 goto error
)

echo.
echo ====================================================
echo   PROCESAMIENTO COMPLETADO
echo ====================================================
echo.
echo Resultados guardados en:
echo   - Carpeta de la ejecucion: %cd%\outputs\%run_name%\
echo   - Graficas, si se solicitan: figures\
echo   - Metricas: tables\
echo.
echo Puede abrir esas carpetas en el Explorador de archivos.
echo.
pause

exit /b 0

:error
echo ERROR: El procesamiento no se ha completado. Revise el mensaje anterior.
pause
exit /b 1
