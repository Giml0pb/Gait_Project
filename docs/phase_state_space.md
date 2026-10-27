# Modelo experimental de fase en espacio de estados

_Formulación del prototipo y límites de interpretación — 26 de octubre de 2026_

---

## ⚙️ Estado y dinámica

Para cada pie se estima un estado independiente. En la muestra $k$, el vector de estado es

$$
x_k = [\phi_k,\ \omega_k,\ A_k,\ b_k]^\top.
$$

Aquí $\phi_k$ es la fase del ciclo en radianes, $\omega_k$ la frecuencia angular en radianes por segundo, $A_k$ una escala de amplitud positiva y $b_k$ el sesgo de la observación normalizada. Con intervalo temporal $\Delta t=1/f_s$ y frecuencia de análisis $f_s=25\,\mathrm{Hz}$, la predicción es

$$
x_{k+1}=F x_k+w_k,
\qquad
F=\begin{bmatrix}
1&\Delta t&0&0\\
0&1&0&0\\
0&0&1&0\\
0&0&0&1
\end{bmatrix},
\qquad w_k\sim\mathcal N(0,Q).
$$

Se usa $Q=\operatorname{diag}(0,(2\pi\,0.025)^2\Delta t,0.03^2\Delta t,0.03^2\Delta t)$. Es una elección operativa de seguimiento que no se ha ajustado a los errores del grupo evaluado. No existe término de acoplamiento entre pies ni restricción de antifase. El uso de EKF para estados de marcha tiene precedentes; este prototipo no reproduce exactamente ninguno de ellos.[^ekf]

## 📈 Modelo de observación

La señal giroscópica de cada tramo se divide por su percentil 95 de amplitud absoluta. Para la observación normalizada $y_k$, se utiliza

$$
y_k=b_k+A_k g(\phi_k)+v_k,
\qquad
v_k\sim\mathcal N(0,0.15^2),
$$

$$
g(\phi)=c_0+\sum_{j=1}^{3}\left[c_j\cos(j\phi)+s_j\sin(j\phi)\right].
$$

Los coeficientes $c_j,s_j$ se ajustan usando las señales y fases por eventos de otras personas. Cada ensayo se normaliza antes del ajuste; los coeficientes se promedian primero dentro de la persona y después entre personas. Se fija $c_0=0$ porque el filtro ya estima $b_k$. La observación no contiene eventos del participante evaluado.

El Jacobiano utilizado en la actualización del EKF es

$$
H_k=\left[A_k g'(\phi_k),\ 0,\ g(\phi_k),\ 1\right].
$$

Se utiliza la actualización de Joseph para la covarianza y se omite la corrección cuando falta una observación. La fase y la incertidumbre siguen evolucionando mediante predicción. La frecuencia se limita al intervalo operativo de 0,25 a 2 Hz y la amplitud al intervalo de 0,05 a 5. Se contabilizan los contactos con estos límites: no deben interpretarse como evidencia fisiológica. La proyección del estado a esos límites tampoco constituye una actualización bayesiana truncada de la covarianza.

## 📏 Referencia y error

Si $h_i$ y $h_{i+1}$ son apoyos consecutivos del mismo pie, la referencia temporal dentro de ese intervalo se define como

$$
\phi_{\mathrm{ref}}(t)=2\pi\left(i+\frac{t-h_i}{h_{i+1}-h_i}\right).
$$

Esta definición asigna un ciclo a cada zancada y progresión lineal entre sus apoyos. Los eventos son detectados automáticamente en el dataset; esta referencia no establece una fase biomecánica verdadera y continua.[^dataset]

La fase relativa se calcula como $\delta(t)=\phi_L(t)-\phi_R(t)$, donde $L$ y $R$ identifican los pies. Para el comparador dominante se mantiene además el desplazamiento derecho histórico de pi. Para las $N$ muestras comunes que pueden evaluarse, el error angular es

$$
\operatorname{MAE}_{\delta}
=\frac{180}{\pi N}\sum_{k=1}^{N}
\left|\operatorname{Arg}\left(\exp\{\mathrm{i}[\hat\delta_k-\delta_{\mathrm{ref},k}]\}\right)\right|.
$$

El origen de fase de Hilbert se calibra mediante las plantillas de entrenamiento. No se ajusta una rotación usando los errores del ensayo evaluado. Las métricas reales expresan concordancia con la convención por eventos; las métricas sintéticas comparan con la fase generativa conocida.

## ⚠️ Identificabilidad y límites

Cuando sólo están presentes armónicos pares, se cumple $g(\phi)=g(\phi+\pi)$. La observación no permite distinguir dos posiciones del ciclo separadas por media zancada. Una aproximación gaussiana local puede mantenerse cerca de una de esas soluciones sin representar la otra, incluso con covarianza pequeña. Se exporta un indicador de ambigüedad de inicialización; no se afirma que elimine el problema.

La plantilla fija también puede ser incorrecta para una persona o variar dentro del ensayo. Una discrepancia en la forma de la señal puede entonces corregirse artificialmente mediante la fase. Este fallo se evalúa expresamente con simulaciones de cambio de forma a coordinación constante.

La frecuencia inicial se estima a partir de la señal completa, el remuestreo usa información fuera de línea y la inicialización perfila dos ciclos nominales. Por ello, este prototipo es un estimador experimental offline con actualizaciones recursivas; no se presenta como un sistema de tiempo real. La formulación y las covarianzas deben revisarse antes de utilizar incertidumbres o parámetros como indicadores clínicos.

## 🔗 Referencias

[^ekf]: Medrano et al. (2023). Real-Time Gait Phase and Task Estimation for Controlling a Powered Ankle Exoskeleton on Extremely Uneven Terrain. https://pmc.ncbi.nlm.nih.gov/articles/PMC10249462/
[^dataset]: Voisard et al. (2025). A Dataset of Clinical Gait Signals with Wearable Sensors from Healthy, Neurological, and Orthopedic Cohorts. https://www.nature.com/articles/s41597-025-05959-w
