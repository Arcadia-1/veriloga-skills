"""Analyze cmp_delay: log-linear regeneration delay."""
import time
from pathlib import Path

import matplotlib
import numpy as np

matplotlib.use('Agg')
import matplotlib.pyplot as plt

from evas.netlist.runner import evas_simulate

HERE = Path(__file__).parent
_DEFAULT_BASE = HERE.parent.parent.parent / 'output' / 'comparator'

_PHASES = [
    (0,   4,  10.0),
    (4,   8,   1.0),
    (8,  12,   0.1),
    (12, 16,   0.01),
]
_EXPECTED_DELAYS_PS = [40.0, 50.0, 60.0, 70.0]


def analyze(base_dir: Path = _DEFAULT_BASE) -> None:
    out_dir = base_dir / 'cmp_delay'
    out_dir.mkdir(parents=True, exist_ok=True)

    t0 = time.perf_counter()
    evas_simulate(str(HERE / 'tb_cmp_delay.scs'), output_dir=str(out_dir))
    wall_s = time.perf_counter() - t0

    data  = np.genfromtxt(out_dir / 'tran.csv', delimiter=',', names=True, dtype=None, encoding='utf-8')
    t     = data['time'] * 1e9
    vdd   = data['clk'].max()
    vdiff = (data['vinp'] - data['vinn']) * 1e3

    fig, axes = plt.subplots(4, 1, figsize=(12, 10), sharex=True,
                             gridspec_kw={'height_ratios': [1.5, 2, 2.5, 2]})
    fig.suptitle(
        r'cmp_delay — Log-linear Regeneration Delay:  $t_d = t_0 + \tau \cdot \ln(V_{DD}/|V_{diff}|)$'
        '\n'
        r'$\tau = 4.34\,\mathrm{ps}$,  $t_0 = 20.5\,\mathrm{ps}$  |  '
        f'wall clock: {wall_s:.4f} s'
    )

    axes[0].plot(t, data['clk'], linewidth=1.0, color='gray')
    axes[0].set_ylabel('clk (V)')
    axes[0].set_ylim(-vdd * 0.1, vdd * 1.2)
    axes[0].grid(True, alpha=0.3)

    vdiff_abs = np.abs(vdiff)
    axes[1].semilogy(t, np.where(vdiff_abs > 1e-4, vdiff_abs, np.nan),
                     linewidth=1.0, color='tab:purple')
    axes[1].set_ylabel('|VINP−VINN| (mV, log)')
    axes[1].grid(True, alpha=0.3)
    for t0_ph, t1_ph, diff_mv in _PHASES:
        axes[1].annotate(f'{diff_mv:g} mV', xy=((t0_ph + t1_ph) / 2, diff_mv),
                         ha='center', va='bottom', fontsize=8, color='tab:purple')

    axes[2].plot(t, data['out_p'], linewidth=1.0, color='tab:blue', label='out_p')
    axes[2].set_ylabel('out_p (V)')
    axes[2].set_ylim(-vdd * 0.1, vdd * 1.2)
    axes[2].legend(loc='upper right')
    axes[2].grid(True, alpha=0.3)

    # Parse per-cycle delay from strobe log (one measurement per CLK cycle)
    meas_t, meas_d = [], []
    strobe_path = out_dir / 'strobe.txt'
    if strobe_path.exists():
        import re
        pat = re.compile(r'\[edge_interval_timer\] t=([\d.]+) ns \| delay=([\d.]+) ps')
        for line in strobe_path.read_text().splitlines():
            m = pat.search(line)
            if m:
                meas_t.append(float(m.group(1)))
                meas_d.append(float(m.group(2)))
    meas_t = np.array(meas_t)
    meas_d = np.array(meas_d)

    axes[3].scatter(meas_t, meas_d, s=40, color='tab:orange', zorder=5,
                    label='measured delay (per cycle)')
    axes[3].set_ylabel('Delay (ps)')
    axes[3].grid(True, alpha=0.3)
    ref_colors = ['tab:red', 'tab:green', 'tab:brown', 'tab:pink']
    for td_ref, color in zip(_EXPECTED_DELAYS_PS, ref_colors):
        axes[3].axhline(td_ref, linestyle='--', linewidth=0.8, color=color, alpha=0.7,
                        label=f'expected {td_ref:.0f} ps')
    axes[3].legend(loc='upper left', fontsize=7, ncol=2)

    axes[0].set_xlim(t[0], t[-1])
    axes[-1].set_xlabel('Time (ns)')
    fig.tight_layout()
    fig.savefig(str(base_dir / 'analyze_cmp_delay.png'), dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f"Plot saved: {base_dir / 'analyze_cmp_delay.png'}")


if __name__ == "__main__":
    analyze()
