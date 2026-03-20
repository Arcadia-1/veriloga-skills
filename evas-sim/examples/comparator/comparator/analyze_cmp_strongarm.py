"""Analyze cmp_strongarm: clocked strong-arm comparator."""
import time
from pathlib import Path

import matplotlib
import numpy as np

matplotlib.use('Agg')
import matplotlib.pyplot as plt

from evas.netlist.runner import evas_simulate

HERE = Path(__file__).parent
_DEFAULT_BASE = HERE.parent.parent.parent / 'output' / 'comparator'


def analyze(base_dir: Path = _DEFAULT_BASE) -> None:
    out_dir = base_dir / 'cmp_strongarm'
    out_dir.mkdir(parents=True, exist_ok=True)

    t0 = time.perf_counter()
    evas_simulate(str(HERE / 'tb_cmp_strongarm.scs'), output_dir=str(out_dir))
    wall_s = time.perf_counter() - t0

    data = np.genfromtxt(out_dir / 'tran.csv', delimiter=',', names=True, dtype=None, encoding='utf-8')
    t   = data['time'] * 1e9
    vdd = data['clk'].max()

    fig, axes = plt.subplots(3, 1, figsize=(8, 5), sharex=True,
                             gridspec_kw={'height_ratios': [1.5, 2.5, 2.5]})
    fig.suptitle(f'cmp_strongarm — Clocked Comparator  |  wall clock: {wall_s:.4f} s')

    axes[0].plot(t, data['clk'], linewidth=1.0)
    axes[0].set_ylabel('clk (V)')
    axes[0].set_ylim(-vdd * 0.1, vdd * 1.2)
    axes[0].grid(True, alpha=0.3)

    axes[1].plot(t, data['vinp'], linewidth=1.0, label='vinp')
    axes[1].plot(t, data['vinn'], linewidth=1.0, label='vinn')
    axes[1].set_ylabel('input (V)')
    vin_all = np.concatenate([data['vinp'], data['vinn']])
    vin_min, vin_max = vin_all.min(), vin_all.max()
    vin_margin = max((vin_max - vin_min) * 0.2, 1e-3)  # at least 1mV margin
    axes[1].set_ylim(vin_min - vin_margin, vin_max + vin_margin)
    axes[1].legend(loc='upper right')
    axes[1].grid(True, alpha=0.3)

    axes[2].plot(t, data['out_p'], linewidth=1.0, label='out_p')
    axes[2].plot(t, data['out_n'], linewidth=1.0, label='out_n')
    axes[2].set_ylabel('output (V)')
    axes[2].set_ylim(-vdd * 0.1, vdd * 1.2)
    axes[2].legend(loc='upper right')
    axes[2].grid(True, alpha=0.3)

    axes[0].set_xlim(t[0], t[-1])
    axes[-1].set_xlabel('Time (ns)')
    fig.tight_layout()
    fig.savefig(str(base_dir / 'analyze_cmp_strongarm.png'), dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f"Plot saved: {base_dir / 'analyze_cmp_strongarm.png'}")


if __name__ == "__main__":
    analyze()
