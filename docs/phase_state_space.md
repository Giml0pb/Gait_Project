# Experimental phase state-space model

_Prototype formulation and interpretation limits — 28 October 2026_

---

## ⚙️ State and dynamics

Each foot has an independent state. At sample $k$,

$$
x_k = [\phi_k,\ \omega_k,\ A_k,\ b_k]^\top.
$$

Here $\phi_k$ is cycle phase in radians, $\omega_k$ is angular frequency in radians per second, $A_k$ is a positive amplitude scale, and $b_k$ is the normalized observation offset. With time step $\Delta t=1/f_s$ and analysis sampling rate $f_s=25\,\mathrm{Hz}$, the prediction is

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

The process covariance is $Q=\mathrm{diag}(0,(2\pi\,0.025)^2\Delta t,0.03^2\Delta t,0.03^2\Delta t)$. These are operational tracking settings; they were not tuned against held-out participant errors. There is no coupling term between feet or imposed antiphase constraint. Previous work has used EKFs for gait-state estimation; this prototype does not reproduce a particular published model.[^ekf]

## 📈 Observation model

Each gyroscope segment is divided by its 95th percentile of absolute amplitude. For normalized observation $y_k$,

$$
y_k=b_k+A_k g(\phi_k)+v_k,
\qquad
v_k\sim\mathcal N(0,0.15^2),
$$

$$
g(\phi)=c_0+\sum_{j=1}^{3}\left[c_j\cos(j\phi)+s_j\sin(j\phi)\right].
$$

In the dataset benchmark, coefficients $c_j,s_j$ are fitted using signals and event-derived phases from other participants. Each trial is normalized before fitting; coefficients are averaged first within participants and then across participants. The synthetic demo instead uses a separate calibration record with known phase. The intercept is fixed at $c_0=0$ because the filter estimates $b_k$. Held-out test events never enter the observation model.

The measurement Jacobian is

$$
H_k=\left[A_k g'(\phi_k),\ 0,\ g(\phi_k),\ 1\right].
$$

The covariance uses the Joseph update. Missing observations skip correction while phase and uncertainty continue through prediction. Frequency is bounded to 0.25–2 Hz and amplitude to 0.05–5. Bound contacts are counted and do not constitute physiological evidence. Projecting the state onto these bounds is not a truncated Bayesian update of its covariance.

Initialization reserves two nominal active-signal cycles, with a minimum of two seconds, to profile phase, amplitude and offset. The fitted state is placed at the final bootstrap timestamp; prediction and correction begin on the next sample. Reserved observations are never corrected a second time, and their output estimates remain undefined. Covariance at this boundary is a fixed operational assumption, not a posterior inferred from the bootstrap fit.

## 📏 Reference and error

For consecutive same-foot heel strikes $h_i$ and $h_{i+1}$, the temporal reference phase is

$$
\phi_{\mathrm{ref}}(t)=2\pi\left(i+\frac{t-h_i}{h_{i+1}-h_i}\right).
$$

This assigns one cycle per stride and linear progression between heel strikes. Dataset events were detected algorithmically; this reference does not establish a true continuous biomechanical phase.[^dataset]

Relative phase is $\delta(t)=\phi_L(t)-\phi_R(t)$, with $L$ and $R$ denoting the feet. The dominant-band comparator additionally retains its historical right-foot shift of $\pi$. For $N$ shared scored samples, circular mean absolute error is

$$
\mathrm{MAE}_{\delta}
=\frac{180}{\pi N}\sum_{k=1}^{N}
\left|\mathrm{Arg}\left(\exp\{\mathrm{i}[\hat\delta_k-\delta_{\mathrm{ref},k}]\}\right)\right|.
$$

Hilbert phase origins are calibrated using training templates. No rotation is fitted against held-out trial errors. Dataset metrics measure agreement with an event convention; synthetic metrics compare with known generative phase.

## 🧪 Uncertainty diagnostics

Before each available observation is corrected, the filter records innovation $\nu_k$ and innovation variance $S_k$:

$$
\nu_k=y_k-h(\hat x_k^-),\qquad
S_k=H_kP_k^-H_k^\top+R,\qquad
\mathrm{NIS}_k=\frac{\nu_k^2}{S_k}.
$$

Here $\hat x_k^-$ and $P_k^-$ are predicted state and covariance. For scored synthetic samples, phase coverage is the fraction whose absolute circular error lies within $1.96\sqrt{P_{k,\phi\phi}}$, using posterior covariance. Bootstrap and missing-observation innovations remain undefined and never count as zero residuals.

The demo compares fixed and changing waveforms over 20 seeds per condition, with separate calibration records and unchanged $Q$, $R$ and initial covariance. It summarizes coverage, mean NIS and lag-1 correlation of standardized innovations using run medians and 10th–90th percentiles. Correlation uses adjacent observed samples only.

Coverage of 95%, mean scalar NIS of 1 and uncorrelated innovations are ideal-model references, not guarantees or acceptance thresholds. The simulations do not exactly reproduce the filter's stochastic model, and timestamps within a run are dependent. Low NIS can coexist with biased phase when the filter absorbs waveform deformation into its state; known reference phase exposes that failure. These diagnostics do not calibrate the full four-state joint distribution or represent multiple phase branches.

## ⚠️ Identifiability and limits

With even harmonics only, $g(\phi)=g(\phi+\pi)$. Observations cannot distinguish cycle positions separated by half a stride. A local Gaussian approximation can remain near one solution without representing the other, even with small covariance. The exported initialization-ambiguity flag identifies this concern without resolving it.

A fixed template can also be inappropriate for a participant or change within a recording. The filter may absorb observation-shape error into its phase estimate. Simulated waveform changes at constant bilateral timing explicitly test this failure.

Initial frequency and normalization use the full observed signal, resampling is offline, and initialization profiles two nominal cycles. This is an experimental offline estimator with recursive updates. Its formulation and uncertainty need further validation before use as clinical indicators or a real-time controller.

## 🔗 References

[^ekf]: Medrano et al. (2023). Real-Time Gait Phase and Task Estimation for Controlling a Powered Ankle Exoskeleton on Extremely Uneven Terrain. https://pmc.ncbi.nlm.nih.gov/articles/PMC10249462/
[^dataset]: Voisard et al. (2025). A Dataset of Clinical Gait Signals with Wearable Sensors from Healthy, Neurological, and Orthopedic Cohorts. https://www.nature.com/articles/s41597-025-05959-w
