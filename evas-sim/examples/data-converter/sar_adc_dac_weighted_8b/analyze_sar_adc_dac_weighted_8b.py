"""Analyze sar_adc_dac_weighted_8b: 8-bit binary SAR ADC -> DAC round-trip.

Four plots (sine testbench) + one plot (ramp testbench):
  1. analyze_time.png     — time-domain: vin/vin_sh/vout, code staircase, quant. error
  2. analyze_transfer.png — transfer characteristics: ADC curve, DAC reconstruction
  3. analyze_dnl_inl.png  — DNL and INL (transition-voltage, ramp testbench)
  4. analyze_spectrum.png — power spectrum: ENOB, SNDR, SFDR (via adctoolbox)

DNL/INL uses a dedicated slow-ramp testbench (~50 samples/code) so every
code bin is densely populated — the sine testbench is too fast near the zero
crossing (1.57 LSB/sample) to reliably detect all 255 transitions.

LSB = vdd/255 (binary-weight DAC with total_sum=255).
"""
import time
from pathlib import Path

import matplotlib
import numpy as np

matplotlib.use('Agg')
import matplotlib.pyplot as plt

from evas.netlist.runner import evas_simulate

HERE = Path(__file__).parent
_DEFAULT_OUT = HERE.parent.parent.parent / 'output' / 'sar_adc_dac_weighted_8b'

NBITS      = 8
NLEVELS    = 2 ** NBITS          # 256 codes (0..255)
VDD        = 0.9
TOTAL_SUM  = NLEVELS - 1         # 255  (sum of binary weights 128+…+1)
LSB        = VDD / TOTAL_SUM     # vdd/255 ≈ 3.53 mV

T_RST_US   = 0.020               # reset released at 20 ns
T_PLOT_US  = T_RST_US + 0.020    # 40 ns guard for first valid code


def _compute_dnl_inl(vin_sh_edges, code_edges):
    """Transition-voltage DNL/INL from clock-edge (vin_sh, code) sample pairs.

    Only single-step transitions (code k → k+1) are used.  When a transition
    is detected multiple times (sine input revisits the same code boundary),
    the median transition voltage is taken for robustness.

    Returns (codes, dnl, inl) aligned to detected transitions.
    """
    idx    = np.argsort(vin_sh_edges)
    v_s    = vin_sh_edges[idx]
    c_s    = np.round(code_edges[idx]).astype(int)

    # Collect transition voltages: for code k→k+1, midpoint of consecutive pair
    from collections import defaultdict
    trans_vins = defaultdict(list)
    for i in range(1, len(c_s)):
        if c_s[i] == c_s[i - 1] + 1:          # single-step rising transition only
            trans_vins[c_s[i]].append((v_s[i] + v_s[i - 1]) / 2.0)

    if len(trans_vins) < 2:
        return np.array([]), np.array([]), np.array([])

    codes_with_edges = sorted(trans_vins.keys())
    edges = np.array([np.median(trans_vins[c]) for c in codes_with_edges])

    step_codes = np.array(codes_with_edges[1:])
    dnl = np.diff(edges) / LSB - 1.0
    inl = np.cumsum(dnl)
    return step_codes, dnl, inl


def analyze(out_dir: Path = _DEFAULT_OUT) -> None:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    t0 = time.perf_counter()
    evas_simulate(str(HERE / 'tb_sar_adc_dac_weighted_8b.scs'), output_dir=str(out_dir))
    wall_s = time.perf_counter() - t0

    data   = np.genfromtxt(out_dir / 'tran.csv', delimiter=',', names=True, dtype=None, encoding='utf-8')
    t_us   = data['time'] * 1e6
    vin    = data['vin'].astype(float)
    vin_sh = data['vin_sh'].astype(float)
    vout   = data['vout'].astype(float)
    clks   = data['clks'].astype(float)
    code   = data['dout_code'].astype(float)

    # CLK rising-edge indices
    vth    = VDD / 2
    rising = np.where((clks[:-1] < vth) & (clks[1:] >= vth))[0] + 1
    t_samp      = t_us[rising]
    vin_sh_samp = vin_sh[rising]  # noqa: F841
    vout_samp   = vout[rising]
    code_samp   = code[rising]  # noqa: F841
    post_samp   = t_samp > T_PLOT_US

    post  = t_us > T_PLOT_US
    mask1 = post & (t_us <= T_PLOT_US + 2.0)   # 2 µs window (2 sine cycles)

    # ── Figure 1: Time domain ────────────────────────────────────────────────
    lsb_mv = LSB * 1e3

    fig, axes = plt.subplots(3, 1, figsize=(12, 7), sharex=True,
                             gridspec_kw={'height_ratios': [2, 1.5, 2]})

    ax = axes[0]
    ax.plot(t_us[mask1], vin[mask1],    linewidth=1.0, label='vin (sine)')
    ax.plot(t_us[mask1], vin_sh[mask1], linewidth=1.0, linestyle=':', color='C2', label='vin_sh (S&H)')
    ax.plot(t_us[mask1], vout[mask1],   linewidth=1.0, linestyle='--', label='vout (DAC)')
    ax.set_ylabel('Voltage (V)')
    ax.set_title(f'8-bit SAR ADC (binary weights) -> DAC  Time domain  |  wall clock: {wall_s:.4f} s')
    ax.legend(loc='upper right', fontsize=9)
    ax.grid(True, alpha=0.3)

    ax = axes[1]
    ax.step(t_us[mask1], code[mask1], where='post', linewidth=1.0, color='C2')
    ax.set_ylabel('dout_code')
    ax.set_ylim(-2, NLEVELS + 2)
    ax.yaxis.set_major_locator(plt.MultipleLocator(64))
    ax.grid(True, alpha=0.3)

    ax = axes[2]
    q_err_mv = (vin_sh[mask1] - vout[mask1]) * 1e3
    ax.plot(t_us[mask1], q_err_mv, linewidth=1.0, color='C3')
    ax.axhline(0, color='k', linewidth=1.0, linestyle='--')
    ax.axhline(+lsb_mv, color='gray', linewidth=1.0, linestyle=':', alpha=0.7,
               label=f'+1 LSB ({lsb_mv:.1f} mV)')
    ax.axhline(-lsb_mv, color='gray', linewidth=1.0, linestyle=':', alpha=0.7,
               label='-1 LSB')
    ax.set_ylabel('quant. error vin_sh-vout (mV)')
    ax.set_xlabel('Time (µs)')
    ax.legend(fontsize=8, loc='upper right')
    ax.grid(True, alpha=0.3)

    axes[0].set_xlim(t_us[mask1][0], t_us[mask1][-1])
    fig.tight_layout()
    p1 = out_dir / 'analyze_time.png'
    fig.savefig(str(p1), dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f"Plot saved: {p1}")

    # ── Figure 2: Transfer characteristics ──────────────────────────────────
    vin_sh_p = vin_sh[post]
    vout_p   = vout[post]
    code_p   = code[post]

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    fig.suptitle(
        f'8-bit SAR ADC (binary weights) -> DAC  Transfer characteristics  |  wall clock: {wall_s:.4f} s',
        fontsize=11)

    ax = axes[0]
    ax.plot(vin_sh_p, code_p, linewidth=0.5, color='C0', alpha=0.5)
    ax.set_xlabel('vin_sh (V)')
    ax.set_ylabel('ADC code')
    ax.set_title('ADC transfer curve  (256 steps)')
    ax.set_ylim(-2, NLEVELS + 2)
    ax.yaxis.set_major_locator(plt.MultipleLocator(64))
    ax.grid(True, alpha=0.3)

    ax = axes[1]
    ax.plot(vin_sh_p, vout_p, linewidth=0.5, color='C1', alpha=0.5, label='vout vs vin_sh')
    v_lo, v_hi = vin_sh_p.min(), vin_sh_p.max()
    ax.plot([v_lo, v_hi], [v_lo, v_hi], 'k--', linewidth=1.0, alpha=0.5, label='ideal (no quant.)')
    ax.set_xlabel('vin_sh (V)')
    ax.set_ylabel('vout (V)')
    ax.set_title('DAC reconstruction  (256-level staircase)')
    ax.legend(fontsize=9)
    ax.set_aspect('equal')
    ax.grid(True, alpha=0.3)

    fig.tight_layout()
    p2 = out_dir / 'analyze_transfer.png'
    fig.savefig(str(p2), dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f"Plot saved: {p2}")

    # ── Figure 3: DNL / INL  (ramp testbench — ~50 samples/code) ────────────
    out_ramp = out_dir / 'ramp'
    out_ramp.mkdir(parents=True, exist_ok=True)
    evas_simulate(str(HERE / 'tb_sar_adc_dac_weighted_8b_ramp.scs'), output_dir=str(out_ramp))

    dr     = np.genfromtxt(out_ramp / 'tran.csv', delimiter=',', names=True, dtype=None, encoding='utf-8')
    t_r_us = dr['time'] * 1e6
    clks_r = dr['clks'].astype(float)
    vsh_r  = dr['vin_sh'].astype(float)
    code_r = dr['dout_code'].astype(float)

    rising_r = np.where((clks_r[:-1] < vth) & (clks_r[1:] >= vth))[0] + 1
    post_r   = t_r_us[rising_r] > T_PLOT_US
    vsh_samp_r  = vsh_r[rising_r][post_r]
    code_samp_r = code_r[rising_r][post_r]

    n_samp_r = post_r.sum()
    step_codes, dnl, inl = _compute_dnl_inl(vsh_samp_r, code_samp_r)

    fig, axes = plt.subplots(2, 1, figsize=(12, 6), sharex=True)
    fig.suptitle(
        f'8-bit SAR ADC (binary weights)  DNL / INL  |  wall clock: {wall_s:.4f} s\n'
        f'transition-voltage method  |  ramp input  |  {n_samp_r} CLK-edge samples  |  '
        f'{len(step_codes)} / 255 transitions detected',
        fontsize=10)

    ax = axes[0]
    ax.bar(step_codes, dnl, width=0.8, color='C0', alpha=0.7)
    ax.axhline(0,  color='k', linewidth=1.0)
    ax.axhline(+1, color='r', linewidth=1.0, linestyle='--', alpha=0.6, label='+1 LSB')
    ax.axhline(-1, color='r', linewidth=1.0, linestyle='--', alpha=0.6, label='-1 LSB')
    ax.set_ylabel('DNL (LSB)')
    ax.set_ylim(-1.5, 1.5)
    ax.legend(fontsize=8, loc='upper right')
    ax.grid(True, alpha=0.3)

    ax = axes[1]
    ax.plot(step_codes, inl, linewidth=1.0, color='C1')
    ax.axhline(0,    color='k', linewidth=1.0)
    ax.axhline(+0.5, color='r', linewidth=1.0, linestyle='--', alpha=0.6, label='+0.5 LSB')
    ax.axhline(-0.5, color='r', linewidth=1.0, linestyle='--', alpha=0.6, label='-0.5 LSB')
    ax.set_ylabel('INL (LSB)')
    ax.set_xlabel('ADC code')
    ax.legend(fontsize=8, loc='upper right')
    ax.grid(True, alpha=0.3)

    if len(step_codes):
        axes[0].set_xlim(step_codes[0], step_codes[-1])
    fig.tight_layout()
    p3 = out_dir / 'analyze_dnl_inl.png'
    fig.savefig(str(p3), dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f"Plot saved: {p3}")

    # ── Figure 4: Power spectrum (adctoolbox) ────────────────────────────────
    try:
        from adctoolbox import analyze_spectrum as _analyze_spectrum

        # Coherent sampling: N = k × (fs/fin) gives exactly k complete cycles
        fs_adc   = 500e6
        fin_adc  = 1e6
        spc      = int(round(fs_adc / fin_adc))    # 500 samples per cycle
        vout_post = vout_samp[post_samp]
        n_cycles  = len(vout_post) // spc
        vout_spec = vout_post[:n_cycles * spc]

        # FSR: 0 to VDD (code 0 → 0 V, code 255 → VDD)
        adc_range = [0.0, VDD]

        fig, ax = plt.subplots(figsize=(10, 5))
        plt.sca(ax)
        res = _analyze_spectrum(vout_spec, fs=fs_adc, max_scale_range=adc_range,
                                create_plot=True, show_title=False)
        ax.set_ylim(bottom=-120)
        n_pts   = n_cycles * spc
        fin_str = f'Fin / N = {n_cycles}/{n_pts} * {fs_adc/1e6:.0f} MHz'
        ax.set_title(
            f'8-bit SAR ADC (binary weights)  Power Spectrum  |  wall clock: {wall_s:.4f} s\n'
            f'ENOB = {res["enob"]:.2f} bits  |  SNDR = {res["sndr_dbc"]:.2f} dBc  |  '
            f'SFDR = {res["sfdr_dbc"]:.2f} dBc  |  {fin_str}',
            fontsize=9)
        fig.tight_layout()
        p4 = out_dir / 'analyze_spectrum.png'
        fig.savefig(str(p4), dpi=150, bbox_inches='tight')
        plt.close(fig)
        print(f"Plot saved: {p4}")
    except ImportError:
        print("adctoolbox not available — skipping spectrum plot")


if __name__ == "__main__":
    analyze()
