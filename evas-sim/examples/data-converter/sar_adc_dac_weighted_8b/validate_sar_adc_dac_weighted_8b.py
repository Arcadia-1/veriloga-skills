"""Validate and analyze sar_adc_dac_weighted_8b: 8-bit binary SAR ADC → DAC round-trip.

validate_csv(out_dir)  — called by the pytest suite; returns failure count.
Run as a script        — simulates, validates, and saves three plots.

The first 20 ns (reset period) is excluded from all error / INL / DNL metrics.

Figure 1 — Time domain (first 2 µs, post-reset):
  • vin / vout overlay   (256-level staircase visible)
  • dout_code            (0..255)
  • quantisation error   (mV)

Figure 2 — Transfer characteristics (post-reset):
  • ADC transfer curve   (vin → code, 256 steps)
  • DAC reconstruction   (vin vs vout, staircase vs ideal diagonal)

Figure 3 — ADC nonlinearity (post-reset):
  • DNL                  (per-code step width error, in LSB)
  • INL                  (cumulative integral nonlinearity, in LSB)
"""
import time
from pathlib import Path

import matplotlib
import numpy as np

matplotlib.use('Agg')
import matplotlib.pyplot as plt

from evas.netlist.runner import evas_simulate

HERE = Path(__file__).parent
OUT  = HERE.parent.parent / 'output' / 'sar_adc_dac_weighted_8b'

NBITS    = 8
NLEVELS  = 2 ** NBITS   # 256
VDD      = 0.9           # must match testbench parameter
T_RST_US = 0.020        # reset released at 20 ns = 0.020 µs
LSB      = VDD / NLEVELS  # 0.9 / 256 ≈ 3.52 mV  (standard 8-bit reference)


# ── DNL / INL helper ──────────────────────────────────────────────────────────

def compute_dnl_inl(vin_arr, code_arr):
    """Estimate DNL and INL from (vin, code) pairs using transition voltages.

    Returns (codes, dnl, inl) — arrays aligned to detected code transitions.
    DNL[k] = (step_k - LSB) / LSB,  INL[k] = cumsum(DNL).
    """
    # Sort by input voltage
    idx = np.argsort(vin_arr)
    vin_s = vin_arr[idx]
    code_s = np.round(code_arr[idx]).astype(int)

    # Find transition edges: where code changes
    transitions = {}   # code → midpoint vin at its lower edge
    for i in range(1, len(code_s)):
        if code_s[i] > code_s[i - 1]:
            # rising transition
            edge_vin = (vin_s[i] + vin_s[i - 1]) / 2.0
            transitions[code_s[i]] = edge_vin

    if len(transitions) < 2:
        return np.array([]), np.array([]), np.array([])

    codes_with_edges = sorted(transitions.keys())
    edges = np.array([transitions[c] for c in codes_with_edges])

    # Step widths: gap between consecutive edges
    step_codes = np.array(codes_with_edges[1:])
    steps = np.diff(edges)           # step_k = edge[k+1] - edge[k]

    dnl = steps / LSB - 1.0
    inl = np.cumsum(dnl)

    return step_codes, dnl, inl


# ── Validation (called by pytest) ─────────────────────────────────────────────

def validate_csv(out_dir=None):
    """Check the simulation CSV for correctness. Returns failure count."""
    if out_dir is None:
        out_dir = OUT
    out_dir = Path(out_dir)

    df   = np.genfromtxt(out_dir / 'tran.csv', delimiter=',', names=True, dtype=None, encoding='utf-8')
    t_us = df['time'] * 1e6

    # Exclude reset period
    post = t_us > T_RST_US
    code = df['dout_code'][post].astype(float)
    vout = df['vout'][post].astype(float)

    failures = 0

    unique_codes = set(int(round(c)) for c in code)
    min_code, max_code = min(unique_codes), max(unique_codes)

    # Sine spans [0.01, 0.89] V → expected code range ≈ [2, 252]
    if min_code > 10:
        print(f"FAIL: min code = {min_code} (expected ≤ 10)")
        failures += 1
    if max_code < NLEVELS - 10:
        print(f"FAIL: max code = {max_code} (expected ≥ {NLEVELS - 10})")
        failures += 1

    # At least 200 distinct codes (≥ 78 % of 256)
    if len(unique_codes) < 200:
        print(f"FAIL: only {len(unique_codes)} distinct codes (expected ≥ 200)")
        failures += 1

    # VOUT must stay within [−0.05, VDD + 0.05] V
    if vout.min() < -0.05 or vout.max() > VDD + 0.05:
        print(f"FAIL: vout range [{vout.min():.3f}, {vout.max():.3f}] V")
        failures += 1

    # dout_code must be integer-valued
    fractional = np.abs(code - np.round(code)).max()
    if fractional > 0.01:
        print(f"FAIL: dout_code non-integer (max err = {fractional:.4f})")
        failures += 1

    # DNL is computed for informational display only — not validated here.
    # Sine-based transition-voltage DNL is unreliable when the input sweeps
    # ~1.6 LSBs per clock sample near the zero crossing (fin=1 MHz, fs=500 MHz),
    # producing alternating over/under-count artefacts that do not reflect actual
    # ADC nonlinearity.
    vin_post = df['vin'][post]
    _, dnl, _ = compute_dnl_inl(vin_post, code)

    if failures == 0:
        dnl_info = f", |DNL|_max = {np.abs(dnl).max():.3f} LSB (sine est.)" if len(dnl) > 0 else ""
        print(f"PASS: {len(unique_codes)} distinct codes [{min_code}..{max_code}], "
              f"vout ∈ [{vout.min():.3f}, {vout.max():.3f}] V"
              f"{dnl_info}")
    return failures


# ── Standalone: simulate + plot ───────────────────────────────────────────────

if __name__ == '__main__':
    t0 = time.perf_counter()
    evas_simulate(str(HERE / 'tb_sar_adc_dac_weighted_8b.scs'), output_dir=str(OUT))
    elapsed = time.perf_counter() - t0

    failures = validate_csv(OUT)
    print(f"Validation: {failures} failure(s)")

    df   = np.genfromtxt(OUT / 'tran.csv', delimiter=',', names=True, dtype=None, encoding='utf-8')
    t_us = df['time'] * 1e6
    vin  = df['vin']
    vout = df['vout']
    code = df['dout_code'].astype(float)

    # Post-reset mask for figures: exclude reset + first SAR conversion.
    # Reset releases at 20 ns; first valid code appears after 8 clock cycles
    # (8 × 2 ns = 16 ns), so use 40 ns guard for all plots.
    T_PLOT_US = T_RST_US + 0.020   # 40 ns
    post = t_us > T_PLOT_US

    # ── Figure 1: Time domain (first full sine cycle post-reset) ──────────────
    # Show 1 µs window starting just after first valid sample
    mask1 = post & (t_us <= T_PLOT_US + 1.0)

    fig1, axes = plt.subplots(3, 1, figsize=(11, 7), sharex=True,
                              gridspec_kw={'height_ratios': [2, 1.5, 2]})
    fig1.suptitle(
        f'8-bit SAR ADC (binary weights) → DAC  —  Time domain  [{elapsed:.3f} s]',
        fontsize=11)

    ax = axes[0]
    ax.plot(t_us[mask1], vin[mask1],  label='vin (sine)',  linewidth=1.0)
    ax.plot(t_us[mask1], vout[mask1], label='vout (DAC)',  linewidth=1.0,
            linestyle='--')
    ax.set_ylabel('Voltage (V)')
    ax.legend(loc='upper right', fontsize=9)
    ax.grid(True, alpha=0.3)

    ax = axes[1]
    ax.step(t_us[mask1], code[mask1], where='post', linewidth=1.0, color='C2')
    ax.set_ylabel('dout_code')
    ax.set_ylim(-2, NLEVELS + 2)
    ax.yaxis.set_major_locator(plt.MultipleLocator(64))
    ax.grid(True, alpha=0.3)

    ax = axes[2]
    q_err = (vout[mask1] - vin[mask1]) * 1e3
    ax.plot(t_us[mask1], q_err, linewidth=1.0, color='C3')
    ax.axhline(0, color='k', linewidth=1.0, linestyle='--')
    lsb_mv = LSB * 1e3
    ax.axhline(+lsb_mv, color='gray', linewidth=1.0, linestyle=':', alpha=0.7,
               label=f'+1 LSB ({lsb_mv:.1f} mV)')
    ax.axhline(-lsb_mv, color='gray', linewidth=1.0, linestyle=':', alpha=0.7,
               label='−1 LSB')
    ax.set_ylabel('Error (mV)')
    ax.set_xlabel('Time (µs)')
    ax.legend(fontsize=8, loc='upper right')
    ax.grid(True, alpha=0.3)

    fig1.tight_layout()
    p1 = OUT / 'fig1_time_domain.png'
    fig1.savefig(str(p1), dpi=150, bbox_inches='tight')
    plt.close(fig1)
    print(f"Saved: {p1}")

    # ── Figure 2: Transfer characteristics (post-reset) ───────────────────────
    vin_p  = vin[post]
    vout_p = vout[post]
    code_p = code[post]

    fig2, axes = plt.subplots(1, 2, figsize=(11, 5))
    fig2.suptitle(
        f'8-bit SAR ADC (binary weights) → DAC  —  Transfer characteristics  [{elapsed:.3f} s]',
        fontsize=11)

    ax = axes[0]
    ax.step(vin_p, code_p, where='post', linewidth=1.0, color='C0', alpha=0.7)
    ax.set_xlabel('vin (V)')
    ax.set_ylabel('ADC code')
    ax.set_title('ADC transfer curve  (256 steps)')
    ax.set_ylim(-2, NLEVELS + 2)
    ax.yaxis.set_major_locator(plt.MultipleLocator(64))
    ax.grid(True, alpha=0.3)

    ax = axes[1]
    ax.plot(vin_p, vout_p, linewidth=1.0, color='C1', alpha=0.8,
            label='vout vs vin')
    v_lo, v_hi = vin_p.min(), vin_p.max()
    ax.plot([v_lo, v_hi], [v_lo, v_hi],
            'k--', linewidth=1.0, alpha=0.4, label='ideal (no quant.)')
    ax.set_xlabel('vin (V)')
    ax.set_ylabel('vout (V)')
    ax.set_title('DAC reconstruction  (256-level staircase)')
    ax.legend(fontsize=9)
    ax.set_aspect('equal')
    ax.grid(True, alpha=0.3)

    fig2.tight_layout()
    p2 = OUT / 'fig2_transfer.png'
    fig2.savefig(str(p2), dpi=150, bbox_inches='tight')
    plt.close(fig2)
    print(f"Saved: {p2}")

    # ── Figure 3: DNL / INL (post-reset) ─────────────────────────────────────
    step_codes, dnl, inl = compute_dnl_inl(vin_p, code_p)

    fig3, axes = plt.subplots(2, 1, figsize=(11, 6), sharex=True)
    fig3.suptitle(
        f'8-bit SAR ADC (binary weights)  —  DNL / INL  [{elapsed:.3f} s]',
        fontsize=11)

    ax = axes[0]
    ax.bar(step_codes, dnl, width=0.8, color='C0', alpha=0.7)
    ax.axhline(0, color='k', linewidth=1.0)
    ax.axhline(+1, color='r', linewidth=1.0, linestyle='--', alpha=0.5)
    ax.axhline(-1, color='r', linewidth=1.0, linestyle='--', alpha=0.5)
    ax.set_ylabel('DNL (LSB)')
    ax.set_ylim(-1.5, 1.5)
    ax.grid(True, alpha=0.3)

    ax = axes[1]
    ax.plot(step_codes, inl, linewidth=1.0, color='C1')
    ax.axhline(0, color='k', linewidth=1.0)
    ax.axhline(+0.5, color='r', linewidth=1.0, linestyle='--', alpha=0.5)
    ax.axhline(-0.5, color='r', linewidth=1.0, linestyle='--', alpha=0.5)
    ax.set_ylabel('INL (LSB)')
    ax.set_xlabel('ADC code')
    ax.grid(True, alpha=0.3)

    fig3.tight_layout()
    p3 = OUT / 'fig3_dnl_inl.png'
    fig3.savefig(str(p3), dpi=150, bbox_inches='tight')
    plt.close(fig3)
    print(f"Saved: {p3}")
