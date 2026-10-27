# Resultados de la validación exploratoria de fase

_Ejecución completa del 26 de octubre de 2026; modelo experimental 0.1.0_

---

## 📋 Resultado principal

La selección espectral del pipeline sigue habitualmente un componente próximo al segundo armónico de la zancada. La selección de fundamental basada sólo en señal mejora la correspondencia de frecuencia y el recuento de apoyos. El EKF armónico implementado no mejora el criterio principal de concordancia de fase relativa respecto a Hilbert fundamental. Su menor error temporal entre eventos emparejados es un resultado secundario y no compensa automáticamente los eventos perdidos o sobrantes.

La simulación confirma que una variación de forma de señal puede producir una aparente alteración de coordinación, incluso con fase generativa constante entre pies. Esto demuestra una vulnerabilidad metodológica; no demuestra que las diferencias reales entre diagnósticos sean artefactos.

## 🔬 Alcance y verificaciones

Se prepararon y compararon 1.356 ensayos de 260 personas, con cinco particiones por participante, manteniendo juntas todas sus sesiones. Las plantillas se aprendieron con las otras 208 personas de cada partición. No hubo excepciones de procesamiento. Dos ensayos de una persona sana no alcanzaron un segundo de soporte bilateral común tras el calentamiento: las distribuciones de fase relativa contienen 1.354 ensayos y 259 personas. La evaluación por pie dispone de 2.709 observaciones pie-ensayo por método, de las 2.712 disponibles; sus resúmenes de eventos incluyen 260 personas.

En la ejecución de este estudio, la suite completa superó 55 pruebas. También se comprobaron formato, lint, ausencia de participantes compartidos entre entrenamiento y evaluación, hashes de las fuentes y conservación de los resultados numéricos bilaterales al añadir el emparejamiento de eventos. Los resultados del pipeline consolidado permanecen en sus rutas originales.

El [protocolo](phase_validation_protocol.md) y la [formulación del EKF](phase_state_space.md) describen parámetros, unidades, máscaras, calibración e identificabilidad. La primera corrida completa, previa a incorporar las métricas de eventos, se conserva en `outputs/phase_validation_initial/`; las salidas definitivas están en `outputs/phase_validation/`.

## 📈 Frecuencia y significado del ciclo

En las 2.712 observaciones pie-ensayo, el cociente mediano pico dominante/frecuencia por eventos es **2.0117**. Para la fundamental seleccionada desde la señal, el cociente mediano es **0.9996**. 2686 de 2.712 observaciones quedan dentro de ±10% de la frecuencia por eventos. Dos se marcaron con soporte débil de la fundamental.

El intervalo entre percentiles 5 y 95 del cociente es 1,781–2,207 para el pico dominante y 0,973–1,035 para la fundamental. El resultado es compatible con seguir principalmente el segundo armónico en el método previo. No basta con dividir toda frecuencia por dos: el componente dominante puede cambiar de orden entre señales o condiciones.

La interpretación previa de una señal bilateral en fase como prueba de orientación especular debe revisarse: una antifase a nivel de zancada también se convierte en fase coincidente al observar su segundo armónico. Un desplazamiento fijo de pi no resuelve esa ambigüedad de definición.

![Comparación de frecuencias con la referencia por eventos](assets/validation_frequency_reference.png)

## 📏 Concordancia con los eventos

El error de fase relativa se calcula en las mismas muestras para los tres métodos. Primero se promedia dentro de cada participante y después se resume entre las 259 personas evaluables. La tabla presenta mediana y rango intercuartílico; no es una prueba de superioridad estadística.

| Método | Error relativo mediano | Percentiles 25–75 |
| --- | ---: | ---: |
| Hilbert dominante | 9.28° | 5.98–16.53° |
| Hilbert fundamental | 8.89° | 6.71–13.98° |
| EKF armónico | 13.59° | 8.46–28.23° |

La diferencia central entre ambas versiones de Hilbert es pequeña para este criterio. En personas sanas, la mediana descriptiva incluso favorece al comparador dominante (6,19° frente a 7,26°). No se concluye que elegir la fundamental mejore todas las métricas o todos los subgrupos. El EKF tiene una distribución más dispersa: su percentil 75 alcanza 28,23°.

![Distribuciones del error por participante](assets/validation_participant_phase_error.png)

Los apoyos predichos se emparejan uno a uno con una tolerancia de 150 ms. Las cifras siguientes son medianas entre 260 personas; cada F1 combina falsos positivos, falsos negativos y verdaderos positivos de sus pies y ensayos. El error temporal considera únicamente los eventos emparejados y se pondera por su número dentro de la persona.

| Método | F1 de eventos | Error temporal de eventos emparejados |
| --- | ---: | ---: |
| Hilbert dominante | 0.634 | 20.9 ms |
| Hilbert fundamental | 0.975 | 28.9 ms |
| EKF armónico | 0.962 | 21.9 ms |

El pico dominante ofrece un error pequeño entre apoyos emparejados, pero genera 38.026 cruces adicionales en el conjunto evaluado. Este ejemplo muestra por qué informar sólo de proximidad al apoyo más cercano ocultaría el recuento incorrecto de ciclos. La fundamental reduce los falsos positivos a 3.622 y el EKF a 3.937; esos recuentos agregados no deben tratarse como observaciones independientes de personas.

El EKF presenta 12 inicializaciones marcadas como ambiguas. En 47 observaciones pie-ensayo se alcanzó algún límite de frecuencia y en 549 algún límite de amplitud. Son contactos en cualquier momento del tramo, incluidos los transitorios; no equivalen a 47 o 549 fallos clínicos.

## 🧪 Simulación con fase conocida

Se ejecutaron 200 combinaciones de escenario, forma de onda, ruido y semilla, evaluadas con los tres métodos. La plantilla inicial del EKF coincide con el generador sintético: representa una calibración ideal que no existe para cada persona nueva. La tabla resume el error relativo mediano en grados, combinando las cuatro proporciones armónicas y los dos niveles de ruido de cada escenario.

| Escenario | Hilbert fundamental | EKF armónico |
| --- | ---: | ---: |
| Asimetría fija | 2.73° | 0.73° |
| Cambio de forma, coordinación constante | 3.44° | 14.91° |
| Deriva de coordinación | 2.95° | 0.86° |
| Modulación de frecuencia | 3.50° | 1.18° |
| Pérdida temporal de sensor | 3.77° | 0.73° |

El modelo funciona bien cuando su plantilla es adecuada, pero el cambio de forma lo perjudica aun sin alterar la coordinación real. En los huecos sintéticos de 1,2 s, el EKF mantiene una predicción con error mediano de fase de 0,77°. Hilbert se abstiene dentro del hueco: esa ausencia se informa como cobertura cero y no como error cero.

Los resultados del comparador dominante para todos los escenarios también se publican. Al combinar casos donde domina el primer armónico y casos donde domina el segundo, su desplazamiento fijo derecho de pi puede cambiar la interpretación de fase. Su error global frente a una referencia de zancada mezcla esa diferencia de definición con el error de seguimiento; no se interpreta como una comparación pura de precisión algorítmica.

![Cambio de forma con coordinación constante](assets/validation_morphology_counterexample.png)

La figura muestra también los transitorios de los bordes; esas muestras no contribuyen a las métricas. Para una observación con sólo armónicos pares, la diferencia máxima entre observar una fase o esa fase más pi fue de 3,33 × 10⁻¹⁶: indistinguible a precisión numérica. Este caso impide identificar de manera única la rama del ciclo a partir de esa observación.

## ⚠️ Interpretación y límites

Los eventos reales proceden de detectores automáticos del propio dataset.[^dataset] No se ha validado la fase continua contra captura óptica o una plataforma de fuerzas independiente. La interpolación lineal entre apoyos es una referencia temporal útil, pero no define una fase biomecánica verdadera dentro del ciclo.

Los archivos procesados del dataset ya contienen filtrado e interpolación de algunas pérdidas originales.[^dataset] La prueba de pérdidas de sensor de este estudio es sintética; no demuestra rendimiento frente a pérdidas naturales de los archivos raw. La inicialización y el preprocesamiento del prototipo son offline.

No se han optimizado los parámetros para conseguir que el EKF gane. Los resultados describen este prototipo y esta plantilla poblacional fija, no un límite de todos los modelos en espacio de estados. Tampoco se ha calibrado su covarianza como incertidumbre clínica. La plantilla poblacional, las diferencias de forma entre personas y la inicialización son explicaciones que necesitan pruebas específicas.

El estudio es exploratorio y el problema armónico se observó inicialmente en el mismo dataset. Las particiones controlan el ajuste de plantillas, pero no eliminan esa selección previa de la pregunta. No hay inferencia confirmatoria sobre patología, edad, velocidad o control neural ni estimación de una fuerza de acoplamiento fisiológica.

## 📍 Decisión de trabajo

La referencia más defendible para continuar estudiando ciclos y apoyos es la fundamental seleccionada por señal, conservando el pico dominante como medida espectral con significado distinto. La mejora de F1 es clara descriptivamente; la mejora del error relativo central es pequeña y no uniforme entre grupos.

No está justificado sustituir ahora esa referencia sencilla por este EKF para estudiar coordinación bilateral. Antes de ampliar su complejidad, conviene comprobar calibración con otras personas y sesiones, analizar residuales de forma e inicialización y evaluar sensibilidad a bandas, máscaras y tolerancia de eventos. Una evaluación clínica posterior debe acotarse a una patología y controlar al menos edad y ritmo. El pipeline consolidado se conserva como referencia; este estudio no modifica automáticamente sus definiciones.

## 🔁 Artefactos y reproducción

Las tablas, cuatro figuras, el resumen y el manifiesto están en `outputs/phase_validation/`. Los archivos se generan localmente y no se versionan con los datos. La tabla de errores está vacía; los casos sin soporte se identifican explícitamente en las tablas comparativas. Las 55 pruebas de esa etapa incluyen recuperación de frecuencia, ambigüedad armónica, predicción durante huecos, ausencia de filtración entre participantes y emparejamiento uno a uno de eventos.

```bash
uv run python scripts/validate_phase_model.py --output-dir outputs/phase_validation_replicate
uv run pytest
```

## 🔗 Referencias

[^dataset]: Voisard et al. (2025). A Dataset of Clinical Gait Signals with Wearable Sensors from Healthy, Neurological, and Orthopedic Cohorts. https://www.nature.com/articles/s41597-025-05959-w
