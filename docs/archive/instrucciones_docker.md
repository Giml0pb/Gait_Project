# Instrucciones de Ejecucion - Docker (Windows)

> Documento histórico de la implementación anterior. Para el comportamiento y la validación actuales, consultar [baseline_validation.md](../baseline_validation.md) y el [README](../../README.md). Sus cifras y conclusiones deben recalcularse con la versión actual.

**Guia de 3 pasos para ejecutar el Gait Analysis Pipeline sin instalar Python**

---

## ANTES DE EMPEZAR

### Requisitos del sistema:
- **Windows 10/11** (64-bit)
- **8 GB RAM** minimo (16 GB recomendado)
- **5 GB espacio libre** en disco
- **Conexion a Internet** (solo para la instalacion inicial)

---

## PASO 1: Instalar Docker Desktop (SOLO UNA VEZ)

### 1.1 Descargar Docker Desktop

1. Ir a: **https://www.docker.com/products/docker-desktop**
2. Hacer clic en **"Download for Windows"**
3. Esperar a que descargue el instalador (~500 MB)

### 1.2 Instalar Docker Desktop

1. Hacer **doble clic** en el archivo descargado: `Docker Desktop Installer.exe`
2. Si aparece un mensaje de seguridad, hacer clic en **"Si, permitir"**
3. En la ventana del instalador:
   - Dejar todas las opciones por defecto
   - Hacer clic en **"OK"**
4. Esperar a que se instale (2-5 minutos)
5. Hacer clic en **"Close and restart"** cuando termine
6. El ordenador se **reiniciara automaticamente**

### 1.3 Verificar la instalacion

1. Despues de reiniciar, Docker Desktop se abrira automaticamente
2. Puede aparecer un tutorial - hacer clic en **"Skip tutorial"**
3. Esperar a que aparezca "Docker Desktop is running" en la esquina inferior izquierda
4. **LISTO** - Docker esta instalado

> **NOTA**: Docker Desktop debe estar ejecutandose (icono de ballena en la barra de tareas) cada vez que uses el pipeline.

---

## PASO 2: Preparar el proyecto y los datos

### 2.1 Descomprimir el proyecto

1. Descomprimir el archivo **`Gait_Project.zip`** en el **Escritorio**
2. Debe quedar una carpeta: `C:\Users\TuNombre\Desktop\Gait_Project\`

### 2.2 Colocar los datos

**MUY IMPORTANTE: Los datos deben estar en la ubicacion correcta**

Dentro de la carpeta `Gait_Project`, crear esta estructura:

```
Gait_Project\
├── data\
│   └── raw\
│       └── dataset\
│           └── data\
│               ├── healthy\
│               │   └── HS\
│               │       ├── HS_1\
│               │       │   ├── HS_1_1.csv
│               │       │   ├── HS_1_2.csv
│               │       │   └── ...
│               │       └── HS_2\
│               ├── neuro\
│               │   ├── CIPN\
│               │   ├── CVA\
│               │   └── PD\
│               └── ortho\
│                   ├── ACL\
│                   ├── HOA\
│                   ├── KOA\
│                   └── RIL\
├── EJECUTAR.bat    ← Este archivo debe existir
├── Dockerfile
└── ... (otros archivos del proyecto)
```

**Pasos para colocar los datos:**

1. Si tienes los datos en un ZIP, descomprimirlos
2. Copiar las carpetas `healthy`, `neuro`, `ortho` dentro de:
   ```
   Gait_Project\data\raw\dataset\data\
   ```
3. Verificar que existe al menos:
   ```
   Gait_Project\data\raw\dataset\data\healthy\HS\HS_1\HS_1_1.csv
   ```

---

## PASO 3: Ejecutar el pipeline

### 3.1 Ejecutar el script automatico

1. Abrir la carpeta `Gait_Project` en el Explorador de archivos
2. Hacer **doble clic** en el archivo: **`EJECUTAR.bat`**
3. Apareceran varias ventanas:
   - Una ventana negra (cmd) con texto
   - **NO CERRAR** esta ventana

### 3.2 Primera ejecucion (construccion de imagen)

La **primera vez**, el script hara lo siguiente:

1. Verificar que Docker esta instalado
2. Verificar que los datos estan en la carpeta correcta
3. **Construir la imagen Docker** (esto tarda 2-5 minutos)
   - Aparecera texto tecnico en la ventana
   - Veras lineas como "Step 1/10", "Step 2/10", etc.
   - Es normal, solo esperar

### 3.3 Seleccionar opcion de procesamiento

Despues de construir la imagen, apareceran 4 opciones:

```
Seleccione una opcion:

  1. Procesar UN trial de ejemplo (rapido - 10 segundos)
  2. Procesar 8 trials por grupo (medio - 5 minutos)
  3. Procesar 20 trials por grupo (completo - 15 minutos)
  4. Procesar TODOS los trials (987 trials - 2 horas)

Ingrese el numero de opcion (1-4):
```

**Recomendacion para la primera prueba:** Escribir **`1`** y presionar **Enter**

### 3.4 Ver el procesamiento

- Aparecera texto mostrando el progreso:
  ```
  ======================================================================
  PHASE 3 PIPELINE - Trial: HS_1_1
  ======================================================================

  [Step 1/3] Running Phase 2 for LEFT foot...
  [Step 2/3] Running Phase 2 for RIGHT foot...
  [Step 3/3] Analyzing bilateral synchronization...

  Phase 3 pipeline completed!
  PLV:                0.987
  Mean phase diff:    3.098 rad
  ...
  ```

- Cuando termine, aparecera:
  ```
  ====================================================
    PROCESAMIENTO COMPLETADO
  ====================================================

  Resultados guardados en:
    - Graficas: C:\Users\...\Gait_Project\outputs\figures\
    - Metricas: C:\Users\...\Gait_Project\outputs\tables\

  Presione una tecla para continuar...
  ```

### 3.5 Ver los resultados

1. Abrir la carpeta `Gait_Project\outputs\` en el Explorador
2. **Carpeta `figures\`**: Contiene las graficas en formato PNG
   - Abrir cualquier PNG para ver las visualizaciones
3. **Carpeta `tables\`**: Contiene las metricas en formato CSV
   - Abrir con Excel para ver las metricas numericas

---

## SIGUIENTES EJECUCIONES

### Ejecuciones posteriores son RAPIDAS

Despues de la primera vez:
- NO necesitas reconstruir la imagen (ya esta guardada)
- Solo ejecutar `EJECUTAR.bat` nuevamente
- Seleccionar la opcion deseada
- El procesamiento comenzara inmediatamente

### Opciones disponibles

**Opcion 1: Trial de ejemplo** (para probar que funciona)
- 1 solo trial
- Tarda: ~10 segundos
- Genera: 3-4 figuras + metricas CSV

**Opcion 2: Procesamiento medio** (balanceado)
- 8 trials por grupo = 24 trials totales
- Tarda: ~5 minutos
- Suficiente para ver diferencias entre grupos

**Opcion 3: Procesamiento completo** (analisis robusto)
- 20 trials por grupo = 60 trials totales
- Tarda: ~15 minutos
- Recomendado para reportes

**Opcion 4: Procesamiento total** (dataset completo)
- 987 trials (todos los datos)
- Tarda: ~2 horas
- Para analisis estadistico completo

---

## SOLUCION DE PROBLEMAS

### Problema 1: "Docker no esta instalado o no esta en el PATH"

**Causas:**
- Docker Desktop no esta instalado
- Docker Desktop no esta ejecutandose

**Soluciones:**
1. Verificar que Docker Desktop esta abierto (icono de ballena en la barra de tareas)
2. Si no esta abierto, buscar "Docker Desktop" en el menu Inicio y ejecutarlo
3. Esperar a que aparezca "Docker Desktop is running"
4. Volver a ejecutar `EJECUTAR.bat`

### Problema 2: "No se encuentra la carpeta de datos"

**Causas:**
- Los datos no estan en la ubicacion correcta
- Falta la estructura de carpetas

**Soluciones:**
1. Verificar que existe: `Gait_Project\data\raw\dataset\data\`
2. Dentro debe haber 3 carpetas: `healthy`, `neuro`, `ortho`
3. Si no existen, crearlas manualmente y copiar los datos

### Problema 3: "Error al construir la imagen Docker"

**Causas:**
- Falta conexion a Internet
- Poco espacio en disco

**Soluciones:**
1. Verificar conexion a Internet
2. Liberar espacio en disco (necesitas al menos 5 GB libres)
3. Cerrar Docker Desktop y volverlo a abrir
4. Volver a ejecutar `EJECUTAR.bat`

### Problema 4: El procesamiento es muy lento

**Causas:**
- Muchos trials seleccionados
- Ordenador con poca RAM

**Soluciones:**
1. Cerrar otros programas para liberar RAM
2. Seleccionar una opcion mas rapida (Opcion 1 o 2)
3. Ser paciente - el procesamiento de 987 trials REALMENTE tarda 2 horas

### Problema 5: No aparecen los resultados en `outputs\`

**Causas:**
- El procesamiento fallo (error en los datos)
- Permisos de escritura

**Soluciones:**
1. Revisar la ventana cmd - buscar mensajes de error en rojo
2. Verificar que `outputs\` existe y tiene permisos de escritura
3. Ejecutar `EJECUTAR.bat` como Administrador (clic derecho → "Ejecutar como administrador")

---

## ARCHIVOS GENERADOS

### Carpeta `outputs\figures\`

Para cada trial procesado, se generan 3 graficas:

1. **`{trial}_phase1_spectral.png`**: Analisis espectral
   - Muestra la frecuencia dominante de marcha
   - Power Spectral Density (PSD)

2. **`{trial}_phase2_instantaneous_phase.png`**: Fase instantanea
   - Fase instant��nea de ambos pies
   - Frecuencia instantanea
   - Validacion de calidad

3. **`{trial}_phase3_synchronization.png`**: Sincronizacion bilateral
   - Comparacion de fases entre pies
   - Diferencia de fase circular
   - Metricas de coordinacion

### Carpeta `outputs\tables\`

Archivos CSV con metricas numericas:

1. **`master_metrics.csv`**: Metricas de todos los trials procesados
   - 1 fila por trial
   - 36 columnas de metricas
   - **Archivo principal para analisis**

2. **`frequency_summary.csv`**: Metricas espectrales (Fase 1)
3. **`phase_summary.csv`**: Metricas de fase instantanea (Fase 2)
4. **`synchronization_summary.csv`**: Metricas de sincronizacion (Fase 3)

### Metricas clave en `master_metrics.csv`

- **`plv`**: Sincronizacion global (0-1, mayor = mejor coordinacion)
- **`anti_phase_error_deg`**: Error de coordinacion (0-180°, menor = mejor)
- **`phase_slip_rate`**: Tasa de perdida de sincronizacion (slips/min)
- **`cadence_steps_per_min_left/right`**: Cadencia (pasos/minuto)
- **`stride_time_left/right_s`**: Tiempo de zancada (segundos)

---

## COMANDOS DOCKER AVANZADOS (OPCIONAL)

Si eres usuario avanzado, puedes ejecutar comandos Docker directamente:

### Ver imagenes Docker instaladas
```cmd
docker images
```

### Ejecutar un trial especifico
```cmd
docker run --rm -v "%cd%\data:/app/data" -v "%cd%\outputs:/app/outputs" gait-pipeline uv run python scripts/run_single_trial.py HS_2_3
```

### Procesar solo grupo healthy
```cmd
docker run --rm -v "%cd%\data:/app/data" -v "%cd%\outputs:/app/outputs" gait-pipeline uv run python scripts/run_batch_processing.py --groups healthy
```

### Entrar al contenedor (para debugging)
```cmd
docker run --rm -it -v "%cd%\data:/app/data" -v "%cd%\outputs:/app/outputs" gait-pipeline bash
```

### Eliminar la imagen (para reconstruir desde cero)
```cmd
docker rmi gait-pipeline
```

---

## RESUMEN DE 3 PASOS

1. **Instalar Docker Desktop** (una sola vez)
   - Descargar desde docker.com
   - Instalar y reiniciar

2. **Preparar datos**
   - Descomprimir proyecto en Escritorio
   - Colocar datos en `data\raw\dataset\data\`

3. **Ejecutar**
   - Doble clic en `EJECUTAR.bat`
   - Seleccionar opcion
   - Ver resultados en `outputs\`

---

## SOPORTE

Para mas informacion:
- **README.md**: Documentacion tecnica completa
- **Repositorio**: https://github.com/Giml0pb/Gait_Project

---

**Version:** 1.0
**Fecha:** 2026-03-10
**Sistema:** Windows 10/11 con Docker Desktop
