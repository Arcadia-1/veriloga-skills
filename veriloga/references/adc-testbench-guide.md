# ADC Testbench & Verification Guide

Using **adctoolbox** for ADC behavioral model characterization and verification.

## ⛔ Mandatory Rule

**NEVER hand-roll FFT.** No `np.fft.fft`, no `scipy.signal`, no manual windowing, no manual ENOB formula.
Use `adctoolbox.analyze_spectrum()` for all spectrum analysis — it handles windowing, harmonic detection,
and metric calculation correctly.

---

## Overview

After writing an ADC behavioral model in Verilog-A, use **adctoolbox** to:
- Calculate coherent sampling parameters (avoid spectral leakage)
- Generate realistic test signals with jitter, noise, nonlinearity
- Quantize to your ADC's resolution
- Analyze with standard FFT and windowing
- Calculate industry-standard metrics: **ENOB, SNDR, SFDR, THD, SNR**
- Generate publication-quality plots

**Domain:** Voltage-domain behavioral models (SAR, flash, pipeline, TIADC, etc.)


---

## Installation

```bash
pip install adctoolbox
```

---

## Core Concepts

### Coherent Sampling

The key to accurate ADC metrics is **coherent sampling** — ensuring the test signal
frequency satisfies: **Fin = J × Fs / N**, where J is an integer coprime to N.

**Without coherent sampling:**
```
ENOB ≈ poor, spectral leakage contaminates bins
```

**With coherent sampling:**
```
ENOB ≈ ideal (e.g., 10.0 bits for 10-bit ADC)
```

#### Why It Matters

If the signal does not satisfy the coherent relationship, FFT bins contain spectral leakage,
which corrupts ENOB and THD measurements. adctoolbox's `find_coherent_frequency()`
calculates the nearest valid frequency.

### Standard Metrics (from adctoolbox)

| Metric | Key | Typical Value (10-bit) | Definition |
|---|---|---|---|
| **ENOB** | `result['enob']` | ~10.0 bits | Effective Number Of Bits |
| **SNDR** | `result['sndr_dbc']` | ~62 dB | Signal-to-Noise-and-Distortion Ratio (dBc) |
| **SFDR** | `result['sfdr_dbc']` | ~75 dB | Spurious-Free Dynamic Range (dBc) |
| **SNR** | `result['snr_dbc']` | ~62 dB | Signal-to-Noise Ratio (dBc) |
| **THD** | `result['thd_dbc']` | -70 dBc | Total Harmonic Distortion (dBc) |
| **NSD** | `result['nsd_dbfs_hz']` | -155 dBFS/Hz | Noise Spectral Density |

---

## Workflow

### Step 1: Find Coherent Frequency

```python
from adctoolbox import find_coherent_frequency

# Desired signal frequency and sampling rate
fin_target = 10e6      # 10 MHz target
fs = 100e6             # 100 MHz sampling rate
n_fft = 4096           # FFT size / number of samples

# Find nearest valid frequency that ensures integer cycles
fin_actual, bin_idx = find_coherent_frequency(
    fs=fs,
    fin_target=fin_target,
    n_fft=n_fft,
    force_odd=True      # J should be odd (better spectral properties)
)

print(f"Target fin: {fin_target / 1e6:.1f} MHz")
print(f"Actual fin: {fin_actual / 1e6:.4f} MHz")
print(f"FFT bin: {bin_idx}")
```

**Output:**
```
Target fin: 10.0 MHz
Actual fin: 10.0977 MHz
FFT bin: 419
```

The `fin_actual` satisfies **Fin = J × Fs / N** with J coprime to N.

### Step 2: Generate Test Signal (with Optional Effects)

Option A: **Simple sine wave** (ideal ADC test):
```python
import numpy as np

N = n_fft
t = np.arange(N) / fs
A = 0.49              # Amplitude (49% of FS to avoid clipping)
DC = 0.5              # DC offset (50% of FS)

v_in = DC + A * np.sin(2 * np.pi * fin_actual * t)
```

Option B: **Use adctoolbox signal generator** (realistic effects):
```python
from adctoolbox.siggen import ADC_Signal_Generator

gen = ADC_Signal_Generator(N=n_fft, Fs=fs, Fin=fin_actual, A=0.49, DC=0.5)

# Chain effects as needed
sig = gen.apply_thermal_noise(noise_rms=100e-6)  # White noise
sig = gen.apply_jitter(input_signal=sig, jitter_rms=1e-12)  # Sampling jitter
sig = gen.apply_quantization_noise(input_signal=sig, n_bits=10)  # Quantization
```

### Step 3: Quantize to ADC Codes

```python
nbits = 10
num_levels = 2 ** nbits
vref_min, vref_max = 0.0, 1.0
vfull_scale = vref_max - vref_min

# Convert voltage to integer codes [0, 2^nbits - 1]
code_out = np.floor((v_in - vref_min) / vfull_scale * num_levels)
code_out = np.clip(code_out, 0, num_levels - 1).astype(int)
```

### Step 4: Analyze with adctoolbox

```python
from adctoolbox import analyze_spectrum

# Run comprehensive FFT analysis
# Normalized frequency (not Hz): norm_freq = Fin / Fs
norm_freq = fin_actual / fs

result = analyze_spectrum(
    data=code_out,
    fs=fs,
    create_plot=False,          # Suppress auto-plotting
    win_type='hann',            # Hanning window (good for ADC testing)
    max_harmonic=5              # Analyze up to 5th harmonic
)

# Extract metrics (dict keys)
enob = result['enob']
sndr = result['sndr_dbc']       # Signal-to-Noise-and-Distortion Ratio
sfdr = result['sfdr_dbc']       # Spurious-Free Dynamic Range
snr = result['snr_dbc']
thd = result['thd_dbc']
nsd = result['nsd_dbfs_hz']     # Noise Spectral Density

print(f"ENOB:  {enob:.2f} bits")
print(f"SNDR:  {sndr:.2f} dBc")
print(f"SFDR:  {sfdr:.2f} dBc")
print(f"SNR:   {snr:.2f} dBc")
print(f"THD:   {thd:.2f} dBc")
print(f"NSD:   {nsd:.2f} dBFS/Hz")
```

### Step 5: Generate Publication-Quality Plots

Always use `create_plot=False` for headless execution, then create plots manually:

```python
import matplotlib.pyplot as plt
import os

os.makedirs('results', exist_ok=True)

# Plot 1: Input waveform
fig, ax = plt.subplots(figsize=(12, 4))
ax.plot(t[:500] * 1e9, v_in[:500], 'b-', linewidth=1)
ax.set_xlabel('Time [ns]')
ax.set_ylabel('Voltage [V]')
ax.set_title('ADC Input Signal (first 500 samples)')
ax.grid(True, alpha=0.3)
plt.savefig('results/01_input_signal.png', dpi=150, bbox_inches='tight')
plt.close(fig)

# Plot 2: Spectrum (use adctoolbox)
fig, ax = plt.subplots(figsize=(12, 5))
result = analyze_spectrum(code_out, fs=fs, create_plot=True, ax=ax, win_type='hann')
ax.set_xlim([0, fs/2/1e6])  # Set x-axis to Nyquist
plt.savefig('results/02_fft_spectrum.png', dpi=150, bbox_inches='tight')
plt.close(fig)

# Plot 3: Histogram of codes
fig, ax = plt.subplots(figsize=(10, 6))
ax.hist(code_out, bins=min(100, 2**nbits), color='green', alpha=0.7, edgecolor='black')
ax.set_xlabel('Digital Code')
ax.set_ylabel('Count')
ax.set_title('ADC Output Code Distribution')
ax.grid(True, alpha=0.3, axis='y')
plt.savefig('results/03_histogram.png', dpi=150, bbox_inches='tight')
plt.close(fig)
```

---

## Complete Example

See `references/testbench_sar.py` — SAR ADC behavioral model with coherent sampling,
ideal quantization comparison, and `analyze_spectrum()` output.

---

## Best Practices

### ✅ Do This

1. **Always use coherent sampling** — find valid frequency automatically
   ```python
   fin_actual, bin_idx = find_coherent_frequency(fs, fin_target, n_fft)
   # Use fin_actual, NOT fin_target
   ```

2. **Suppress auto-plotting** — scripts must be non-interactive
   ```python
   result = analyze_spectrum(data, fs=fs, create_plot=False)  # No display
   ```

3. **Save plots explicitly** — use `ax` parameter for full control
   ```python
   fig, ax = plt.subplots()
   analyze_spectrum(data, fs=fs, create_plot=True, ax=ax)
   plt.savefig('spectrum.png')
   plt.close(fig)
   ```

4. **Check FFT bin** — verify signal landed where expected via adctoolbox result
   ```python
   print(f"Signal at bin {result['signal_bin']}, expected ~{bin_idx}")
   ```

5. **Log metrics to file** — for documentation
   ```python
   with open('results/metrics.txt', 'w') as f:
       f.write(f"ENOB: {enob:.2f} bits\n")
       f.write(f"SNDR: {sndr:.2f} dBc\n")
   ```

### ❌ Avoid This

1. **Hand-rolling FFT** — always forbidden
   ```python
   # WRONG — never do this
   X = np.fft.fft(code_out)
   psd = np.abs(X)**2
   enob = ...   # manual formula
   # scipy.signal is equally forbidden
   ```
   Use `analyze_spectrum()` instead. Always.

2. **Non-coherent frequencies** — causes spectral leakage
   ```python
   # WRONG: arbitrary frequency
   fin = 9.7e6
   # Result: ENOB ≈ 9.2 bits (corrupted by leakage)
   ```

2. **plt.show()** — blocks script execution
   ```python
   # WRONG
   plt.show()
   ```

3. **Using `create_plot=True` without axis control**
   ```python
   # Can work but less controllable
   # Better: control axis explicitly
   ```

4. **Assuming FFT bin zero = DC** — actual FFT convention
   ```python
   # FFT bin k → frequency = k * Fs / N
   # Not all FFT libraries index the same way
   ```

5. **Ignoring signal clipping** — distorts metrics
   ```python
   # Keep amplitude < 0.5 FS to avoid rail saturation
   A = 0.49  # Good
   A = 0.99  # Bad (clips)
   ```

---

## Mismatch Modeling (TIADC)

For time-interleaved ADCs with per-channel gain/offset mismatch:

```python
# Per-channel parameters
n_channels = 32
gain_mismatch = 0.001  # 0.1% gain error per channel
offset_mismatch = 0.01 * vfull_scale  # 1% offset per channel

# Generate per-channel mismatch coefficients
np.random.seed(42)
ch_gains = 1.0 + np.random.normal(0, gain_mismatch, n_channels)
ch_offsets = np.random.normal(0, offset_mismatch, n_channels)

# Apply to samples (simplified)
for i in range(len(v_in)):
    ch_idx = i % n_channels
    v_adj = ch_gains[ch_idx] * v_in[i] + ch_offsets[ch_idx]
    code_out[i] = np.floor(
        np.clip(v_adj, vref_min, vref_max - 1/num_levels) * num_levels
    )
```

Then analyze as usual — adctoolbox will show the effect of mismatch on SINAD/THD.

---

## Troubleshooting

### Issue: ENOB is too low (~8 bits instead of 10)

**Check 1: Coherent frequency?**

Use `result['signal_bin']` returned by `analyze_spectrum()` to verify the signal bin.

**Check 2: ADC full-scale range?**
```python
# Verify quantizer limits
min_code = np.min(code_out)
max_code = np.max(code_out)
num_levels = 2 ** nbits
if min_code == 0 and max_code == num_levels - 1:
    print("Full scale used (good)")
else:
    print(f"Under-utilizing range: [{min_code}, {max_code}]")
```

**Check 3: Signal amplitude?**
```python
# Keep amplitude to 40-49% of full scale
# Avoid clipping/rail saturation
A_percent = (np.max(v_in) - np.min(v_in)) / (vref_max - vref_min)
print(f"Amplitude utilization: {A_percent*100:.1f}%")
if A_percent > 0.95:
    print("WARNING: Clipping likely!")
```

### Issue: SNDR shows many spurious tones (not just harmonics)

**Check:** Unintended frequency content in signal:
```python
# Plot raw spectrum to identify unwanted tones
result = analyze_spectrum(code_out, fs=fs, create_plot=True,
                         plot_harmonics_up_to=10)
# Look for peaks not at signal or harmonic frequencies
```

### Issue: Can't match expected ENOB exactly

**Normal** — ENOB includes quantization noise, jitter, and nonlinearity. For ideal 10-bit ADC:
- Quantization limit: ENOB ≈ 10.0 − 0.5 = 9.5 bits
- With jitter/noise: ENOB decreases further
- With distortion: SNDR < SNR

Match ENOB only if you match signal amplitude, frequency, and ADC model exactly.

---
