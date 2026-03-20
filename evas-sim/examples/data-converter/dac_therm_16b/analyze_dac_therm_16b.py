"""Analyze dac_therm_16b: 16-bit thermometer DAC (vstep=1.0V)."""
import time
from pathlib import Path

import matplotlib
import numpy as np

matplotlib.use('Agg')
import matplotlib.pyplot as plt

from evas.netlist.runner import evas_simulate

HERE = Path(__file__).parent
_DEFAULT_OUT = HERE.parent.parent.parent / 'output' / 'dac_therm_16b'


def analyze(out_dir: Path = _DEFAULT_OUT) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)

    t0 = time.perf_counter()
    evas_simulate(str(HERE / 'tb_dac_therm_16b.scs'), output_dir=str(out_dir))
    wall_s = time.perf_counter() - t0

    data = np.genfromtxt(out_dir / 'tran.csv', delimiter=',', names=True, dtype=None, encoding='utf-8')
    t   = data['time'] * 1e9
    vdd = data['rst_n'].max()

    din_cols  = [f'd{i}' for i in range(16)]
    ones_count = np.zeros(len(data), dtype=int)
    for col in din_cols:
        if col in list(data.dtype.names):
            ones_count += (data[col] > 0.45).astype(int)

    fig, axes = plt.subplots(3, 1, figsize=(12, 8), sharex=True)

    axes[0].plot(t, data['rst_n'], linewidth=1.0, drawstyle='steps-post', color='orange')
    axes[0].set_ylabel('rst_n')
    axes[0].set_ylim(-vdd * 0.1, vdd * 1.2)
    axes[0].set_title(f'dac_therm_16b (thermometer DAC, vstep=1.0V)  |  wall clock: {wall_s:.4f} s')
    axes[0].grid(True, alpha=0.3)

    axes[1].plot(t, ones_count, linewidth=1.0, drawstyle='steps-post', color='steelblue')
    axes[1].set_ylabel('thermometer ones count')
    axes[1].set_ylim(-1, 18)
    axes[1].grid(True, alpha=0.3)

    axes[2].plot(t, data['vout'], linewidth=1.0, color='green')
    axes[2].set_ylabel('vout (V)')
    axes[2].grid(True, alpha=0.3)

    axes[0].set_xlim(t[0], t[-1])
    axes[-1].set_xlabel('Time (ns)')
    fig.tight_layout()
    fig.savefig(str(out_dir / 'analyze_dac_therm_16b.png'), dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f"Plot saved: {out_dir / 'analyze_dac_therm_16b.png'}")


if __name__ == "__main__":
    analyze()
