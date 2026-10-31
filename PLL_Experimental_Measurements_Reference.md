# PLL Experimental Measurements & Analysis Reference

A consolidated reference for the measurements, calculations, model checks and report comparisons, organised by manual section.

## Notation and measurement conventions

| Symbol | Meaning |
|---|---|
| \(V_{DD}\) | Measured supply voltage. **Measure it; do not assume it is exactly 5.00 V.** |
| \(\phi\) | Phase difference |
| \(\omega\) | Angular frequency, \(\omega = 2\pi f\) |
| \(K_D\) | Phase-detector gain, in \(\mathrm{V/rad}\) |
| \(K_O\) | VCO gain, in \((\mathrm{rad/s})/\mathrm{V}\) |
| \(K_v\) | Combined loop gain, \(K_v \equiv K_O K_D\), in \(\mathrm{s^{-1}}\) |
| \(\tau\) | RC time constant, \(\tau = R_f C_f\) |

---

# 6. Measurements and characterisation

## Common to all sections: extracting frequency, phase and uncertainties from PicoScope traces

### Frequency

Calculate the frequency from \(N\) rising edges:

\[
f = \frac{N-1}{t_N-t_1}
\]

- Use **linearly interpolated threshold crossings** (for example, at \(V_{DD}/2\)).
- Interpolation matters because the 8-bit scope has coarse sampling.

### Frequency uncertainty

\[
\frac{\sigma_f}{f}
\approx
\frac{\sqrt{\sigma_t^2+\sigma_{cal}^2}}{T\sqrt{N-1}}
\]

- Include the scope timebase accuracy from the PicoScope datasheet.
- Repeated measurements provide the statistical contribution; use \(\mathrm{std}/\sqrt{n}\).

### Phase difference

For two signals, calculate the phase lag using

\[
\phi = 2\pi f\Delta t = \frac{2\pi\Delta t}{T}
\]

Determine \(\Delta t\) from either:

- Interpolated threshold crossings; or
- The cross-correlation peak, with parabolic sub-sample refinement.

### Phase uncertainty

\[
\sigma_\phi = 2\pi f\sigma_t
\]

where

\[
\sigma_t^2 = \sigma_{jitter}^2 + \left(\frac{1}{f_s\sqrt{12}}\right)^2
\]

Take \(\sigma_{jitter}\) from the cycle-to-cycle scatter of the Arduino/AWG edges.

### Component values

- Measure \(R\) and \(C\) with a DMM/LCR meter rather than relying on nominal values.
- Stray capacitance (approximately tens of pF) is significant compared with 1000 pF.
- Use the effective capacitance:

\[
C_{eff}=C+C_s
\]

## 6.2 Phase-shift supply (Arduino)

### Minimum phase step

The phase step actually delivered is

\[
\delta\phi = 2\pi f\,\delta t_{min}
\]

The ATmega328P clock is 16 MHz, so

\[
\delta t_{min}\approx 62.5\text{ ns}
\]

### Linearity and jitter

- Fit commanded phase against measured \(\phi\).
- Use the fit slope to assess linearity.
- Use the residual standard deviation as the phase jitter, \(\sigma_\phi\).
- This justifies the error bars on every \(K_D\) plot below.

## 6.3 Type-1 (XOR) comparator — PC1

The mean output is averaged over an integer number of output periods:

\[
\overline V = \frac{1}{T_o}\int V\,dt,
\qquad T_o=\frac{T_{in}}{2}
\]

The XOR duty cycle is \(\phi/\pi\), giving

\[
\overline V(\phi)=
\begin{cases}
V_{DD}\dfrac{\phi}{\pi}, & 0\leq\phi\leq\pi,\\[6pt]
V_{DD}\left(2-\dfrac{\phi}{\pi}\right), & \pi\leq\phi\leq 2\pi.
\end{cases}
\]

### Phase-detector gain

\[
\boxed{K_D\text{ (PC1)}=\frac{V_{OH}-V_{OL}}{\pi}\approx\frac{V_{DD}}{\pi}\approx 1.6\text{ V/rad}}
\]

- Obtain \(K_D\) from the slope of a straight-line fit of \(\overline V\) against \(\phi\) over the linear range.
- Take the slope uncertainty from the fit covariance.
- Read \(V_{OH}\) and \(V_{OL}\) from the waveforms. The logic levels sit slightly off the supply rails, which biases \(K_D\).

### Offset check

\[
\overline V(\pi/2)=\frac{V_{OH}+V_{OL}}{2}\approx\frac{V_{DD}}{2}
\]

### Output ripple

- Calculate the output-ripple amplitude at \(2f_{in}\).
- This is needed for Section 7.1.

## 6.4 Type-2 (edge-triggered) comparator — PC2

With the equal-resistor divider, the high-impedance (Hi-Z) state sits at \(V_{DD}/2\). If the p-FET is on for a time \(t_p\) per input period,

\[
\overline V
=\frac{V_{DD}}{2}+\frac{V_{DD}}{2}\frac{t_p}{T}
=\frac{V_{DD}}{2}+\frac{V_{DD}\phi}{4\pi},
\qquad -2\pi<\phi<2\pi
\]

### Phase-detector gain

\[
\boxed{K_D\text{ (PC2)}=\frac{V_{DD}}{4\pi}\approx 0.40\text{ V/rad}}
\]

Fit the slope of \(\overline V\) against \(\phi\) in the same way as for PC1.

### Additional measurements and checks

- **State fractions:** for each trace, measure the fractions of the period spent high, low and floating. These provide an independent check on the slope.
- **Linear range:** the range is \(\pm 2\pi\), twice the span of PC1. PC2 responds to edge order, not signal levels.
- **Remove the divider later:** it sets the floating level and loads the output, so it destroys the hold behaviour of the three-state stage.

## 6.5 VCO characterisation — \(R_1\), \(R_2\) and \(C\) sweeps

### Model

Using the current mirror and \(I_c=I_{in}\):

\[
f=\frac{I_c}{2C\,\Delta V_{pp}}
\]

where \(\Delta V_{pp}\) is the peak-to-peak differential voltage across \(C\).

The input current is

\[
I_{in}=I_1+I_2,
\qquad
I_1\approx\frac{V_{in}-V_{GS}}{R_1},
\qquad
I_2\approx\frac{V_2}{R_2}
\]

Here, \(V_2\) is the voltage at the \(R_2\) pin.

### Extract these quantities for each \((R_1,R_2,C)\) dataset

1. **Minimum frequency, \(f_{min}\)**

   \[
   f_{min}=f(V_{in}=0)
   =\frac{V_2}{2R_2C\,\Delta V_{pp}}
   \]

   This sets the \(R_2\)-controlled offset.

2. **Slope, \(s=df/dV_{in}\)** over the linear region

   \[
   s\approx\frac{1}{2R_1C\,\Delta V_{pp}}
   \]

3. **VCO gain, \(K_O\)**

   \[
   K_O=2\pi s
   \]

   Units: \((\mathrm{rad/s})/\mathrm{V}\).

4. **Centre frequency and tuning range**

   \[
   f_c=f(V_{DD}/2),
   \qquad \text{range ratio}=\frac{f_{max}}{f_{min}}
   \]

5. **Scaling tests**

   - Plot \(s\) against \(1/(R_1C_{eff})\). It should be linear through the origin, with slope \(1/(2\Delta V_{pp})\).
   - Plot \(f_{min}\) against \(1/(R_2C_{eff})\).
   - Also fit \(C_s\) from the \(1/C\) scaling, using the intercept of \(1/f\) against \(C\).

6. **Current-mirror check** (the manual's question)

   \[
   I_c=2C\,\Delta V_{pp}\,f
   \]

   Measure \(\Delta V_{pp}\) on the capacitor pins. Calculate the input current from the measured resistor voltage drops:

   \[
   I_{in}=\frac{V_{R1}}{R_1}+\frac{V_{R2}}{R_2}
   \]

   Test whether

   \[
   \frac{I_c}{I_{in}}=1
   \]

   within uncertainty.

7. **Choose between the two days of data**

   - Fit the same model to both datasets and compare \(s\) and \(f_{min}\) using

     \[
     z=\frac{|\Delta|}{\sqrt{\sigma_1^2+\sigma_2^2}}
     \]

   - Compare reduced \(\chi^2\) and residual structure. Systematic curvature or drift in the residuals indicates thermal or supply drift.
   - Check which day's \(V_{DD}\) and component measurements are documented.
   - Check which dataset collapses better onto a single curve of \(fC\) against \(V_{in}\), scaled by \(R_1\).
   - Choose the dataset with the cleaner scaling collapse and documented supply/component values. Mention the other dataset as a repeatability check.

## 6.6 Closed-loop operation

### Loop gain

\[
K_v=K_OK_D
\]

Use the values from Sections 6.3/6.4 and 6.5. Include the attenuator ratio if one was used.

### Static phase error versus input frequency

**PC1**

\[
\omega_s-\omega_c=K_v\left(\phi_e-\frac{\pi}{2}\right)
\]

Therefore,

\[
\phi_e=\frac{\pi}{2}+\frac{\omega_s-\omega_c}{K_v}
\]

- Fit \(\phi_e(\omega_s)\).
- The slope, \(1/K_v\), gives an independent estimate of \(K_v\). Compare it with \(K_OK_D\).

**PC2**

\[
\phi_e\rightarrow 0
\]

across the whole lock range. The tri-state stage holds charge, so no static error is needed to sustain a frequency offset.

### Lock (hold) range

Sweep \(f_{in}\) slowly up and down and record the frequencies at which lock is lost.

| Comparator | Predicted lock range |
|---|---|
| **PC1** | \(\Delta\omega_L=K_OV_{DD}/2\), limited by \(\phi_e\in(0,\pi)\), i.e. \(V_e\in(0,V_{DD})\). |
| **PC2** | The full VCO range, \([f_{min},f_{max}]\). |

Compare the measured range with the prediction, using \(K_O\) from Section 6.5.

### Capture range

Step \(f_{in}\) into lock from outside the lock range and find the nearest frequency at which lock is acquired.

- A sweep that is slow compared with \(1/\omega_n\) is quasi-static.
- The step method is the stricter capture-range test.

**PC1 with an RC filter — approximate capture range**

\[
\Delta\omega_C\approx\Delta\omega_L\left|F(j\Delta\omega_C)\right|
=\frac{\Delta\omega_L}{\sqrt{1+\Delta\omega_C^2\tau^2}}
\]

For \(\Delta\omega_C\tau\gg1\),

\[
\Delta\omega_C\approx\sqrt{\frac{\Delta\omega_L}{\tau}}
\]

This approximation assumes that the beat signal reaching the filter is roughly sinusoidal.

**PC2**

Capture range is approximately equal to the lock range, from the logic sequence in Section 5.5.

### Second-order loop parameters — PC1 with RC filter

\[
G(s)=\frac{K_v}{s(1+s\tau)},
\qquad
H(s)=\frac{K_v}{\tau s^2+s+K_v}
\]

Natural frequency:

\[
\omega_n=\sqrt{\frac{K_v}{\tau}}
\]

Damping ratio:

\[
\zeta=\frac{1}{2\sqrt{K_v\tau}}
\]

Phase margin:

\[
PM=90^\circ-\arctan(\omega_c\tau)
\]

where \(\omega_c\) is the crossover frequency, defined by

\[
|G(j\omega_c)|=1
\]

- The gain margin is infinite for this ideal model.
- Any finite measured gain margin comes from extra poles (comparator or amplifier delay, VCO).
- **VCO capacitor waveform:** measure \(\Delta V_{pp}\) and \(f\) against \(f_{in}\), and compare with the tracking range.

### Noise runs — PC1/PC2 at various noise levels

Signal-to-noise ratio:

\[
SNR=20\log_{10}\left(\frac{V_{sig,rms}}{V_{n,rms}}\right)
\]

Phase jitter:

\[
\sigma_\phi=2\pi f_{in}\sigma_t
\]

where \(\sigma_t\) is the standard deviation of edge-time errors relative to an ideal clock.

Loop noise bandwidth:

\[
B_L=\frac{\omega_n}{2}\left(\zeta+\frac{1}{4\zeta}\right)
\]

Measurements and analysis:

- Fit \(\sigma_\phi^2\) against \(B_L/SNR\). A linear relationship is expected in the small-noise regime.
- Measure lock probability against SNR (the fraction of trials that lock).
- Measure lock time against noise.
- Compare PC1 and PC2. The manual states that the noise effect on PC1 is immediate, whereas the effect on PC2 lingers.

---

# 7. Further experiments

## 7.1 Frequency multiplier — 204.8 kHz from 50 Hz

### Divider ratio

\[
N=\frac{204.8\text{ kHz}}{50\text{ Hz}}=4096=2^{12}
\]

Use a 4020 counter.

### Loop parameters

Because the comparator sees \(\theta_o/N\),

\[
G(s)=\frac{K_OK_D}{Ns(1+s\tau)}
\]

Therefore,

\[
\omega_n=\sqrt{\frac{K_OK_D}{N\tau}},
\qquad
\zeta=\frac{1}{2\sqrt{K_OK_D\tau/N}}
\]

### PC1 ripple-induced jitter

The PC1 output has a ripple fundamental at \(2f_{in}\), with approximate amplitude

\[
V_r\approx\frac{2V_{DD}/\pi}{2\pi\,2f_{in}\,\tau}
\]

The VCO phase modulation is

\[
\beta=\frac{K_OV_r}{2\pi\,2f_{in}}
\]

in radians.

### Other measurements

- **Lock range in input-frequency terms:**

  \[
  \frac{f_{min}\text{ to }f_{max}}{N}
  \]

- Measure lock time against \(\tau\) for each comparator.
- **Output frequency accuracy:** measure \(f_{out}/f_{in}\) against \(N\).
- Also check the output frequency stability.

## 7.2 Transient response and FM demodulation

For an input frequency step \(\Delta\omega\),

\[
\Phi_e(s)=\frac{\Delta\omega(1+\tau s)}{s(\tau s^2+s+K_v)}
\]

### Steady-state error

\[
\phi_e(\infty)=\frac{\Delta\omega}{K_v}
\]

### Demodulated output step

\[
\Delta V_{dem}=\frac{\Delta\omega}{K_O}
\]

This is independent of comparator type. A step of \(\pm5\%\) on an approximately 200 kHz carrier gives

\[
\Delta f\approx\pm10\text{ kHz}
\]

This provides another measurement of \(K_O\).

### Underdamped response parameters

Overshoot:

\[
M_p=\exp\left(-\frac{\pi\zeta}{\sqrt{1-\zeta^2}}\right)
\]

Damped ringing frequency:

\[
\omega_d=\omega_n\sqrt{1-\zeta^2}
\]

Logarithmic decrement:

\[
\delta=\ln\left(\frac{x_1}{x_2}\right)
=\frac{2\pi\zeta}{\sqrt{1-\zeta^2}}
\]

2% settling time:

\[
t_s(2\%)\approx\frac{4}{\zeta\omega_n}=8\tau
\]

for the case \(\zeta\omega_n=1/(2\tau)\).

### Closed-loop bandwidth

The frequency-domain \(-3\text{ dB}\) bandwidth is

\[
\omega_{-3dB}
=\omega_n\left[1-2\zeta^2+
\sqrt{4\zeta^4-4\zeta^2+2}\right]^{1/2}
\]

- Measure recovered amplitude against modulation frequency.
- The **maximum usable modulation frequency** is the \(f_m\) at which the recovered amplitude drops by 3 dB; determine it as a function of \(\tau\).
- **Modulator RC filter:** repeat with several time constants and compare the recovered rise time with \(\tau\).

## 7.3 Clock regeneration — pulse-response data

### Frequency offset at burst start

\[
\Delta\omega=\omega_{carrier}-\omega_{free}
\]

This is the quantity the manual asks you to relate to the error signal.

### Steady error voltage during the burst

\[
\Delta V_e=\frac{\Delta\omega}{K_O}
\]

It depends on \(R_1/R_2\) through

\[
K_O\approx\frac{1}{2\pi\,R_1\,C\,\ldots}
\]

### Acquisition

Fit \(V_e(t)\) with an exponential or damped sinusoid to obtain

\[
\zeta,\qquad \omega_n,\qquad t_s
\]

### Behaviour during the gap

**PC1**

- \(V_e\) relaxes to \(V_{DD}/2\) with time constant \(\tau\).
- The VCO frequency is

  \[
  \omega(t)=\omega_c+K_O\Delta V_e e^{-t/\tau}
  \]

**PC2**

- The VCO is driven towards its lower limit (Manual Section 5.5).

**For both cases:** measure the instantaneous VCO frequency per cycle during the gap:

\[
f_k=\frac{1}{t_{k+1}-t_k}
\]

### Accumulated phase drift during a gap

For a gap of length \(t_g\),

\[
\Delta\phi_{gap}
=K_O\Delta V_e\tau\left(1-e^{-t_g/\tau}\right)
\]

- **Longest gap survived:** record the gap length at which \(\Delta\phi_{gap}\) approaches \(\pi\), or at which the re-locked phase slips by a cycle. This is a useful headline result.
- Record the number of cycles required to re-lock after the burst resumes.

## 7.4 Input MOSFET — only if attempted

### Current measurement

\[
I_{DS}=\frac{V_R}{R}
\]

Use a known series resistor.

### MOSFET fits

**Saturation region**

\[
I_{DS}=\frac{\beta}{2}(V_{GS}-V_T)^2(1+\lambda V_{DS})
\]

**Triode region**

\[
I_{DS}=\beta\left[(V_{GS}-V_T)V_{DS}-\frac{V_{DS}^2}{2}\right]
\]

where

\[
\beta=\mu C_{ox}\frac{W}{L}
\]

### Transconductance

\[
g_m=\frac{\partial I_{DS}}{\partial V_{GS}}
\]

### Check against the VCO model in Section 6.5

Solve the source-follower equation for \(I_1\):

\[
V_{in}-I_1R_1=V_T+\sqrt{\frac{2I_1}{\beta}}
\]

Compare the predicted \(f(V_{in})\) with the measured VCO sweeps.

---

# Report cross-checks

Use these comparisons to check consistency between independent measurements and models:

1. **VCO gain:** compare \(K_O\) from Section 6.5 with \(K_O\) from the Section 7.2 voltage step.
2. **Loop gain:** compare \(K_v\) from the slope of \(\phi_e(\omega)\) with \(K_OK_D\).
3. **Lock range:** compare the measured lock range with \(K_OV_{DD}/2\).
4. **VCO capacitor swing:** compare \(\Delta V_{pp}\) from the Section 6.5 fit with \(\Delta V_{pp}\) measured directly on the capacitor pins.
