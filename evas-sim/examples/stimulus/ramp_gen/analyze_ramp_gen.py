"""Analyze ramp_gen: up-ramp from 0 to MAX (DIRECTION=1, STEP=1, N_CYCLE_START=2)."""
import time
from pathlib import Path

import matplotlib
import numpy as np

matplotlib.use('Agg')
import matplotlib.pyplot as plt

from evas.netlist.runner import evas_simulate

HERE = Path(__file__).parent
_DEFAULT_OUT = HERE.parent.parent.parent / 'output' / 'ramp_gen'


def analyze(out_dir: Path = _DEFAULT_OUT) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)

    t0 = time.perf_counter()
    evas_simulate(str(HERE / 'tb_ramp_gen.scs'), output_dir=str(out_dir))
    wall_s = time.perf_counter() - t0

    data = np.genfromtxt(out_dir / 'tran.csv', delimiter=',', names=True, dtype=None, encoding='utf-8')
    t   = data['time'] * 1e9
    vdd = max(data[c].max() for c in ['clk_dtc', 'rst_n'])

    code_cols = [f'code_{i}' for i in range(12)]
    ramp_code = np.zeros(len(data), dtype=int)
    for i, col in enumerate(code_cols):
        if col in list(data.dtype.names):
            ramp_code += ((data[col] > 0.45).astype(int) << i)

    fig, axes = plt.subplots(3, 1, figsize=(12, 8), sharex=True)

    axes[0].plot(t, data['clk_dtc'], linewidth=1.0, drawstyle='steps-post', label='clk_dtc')
    axes[0].plot(t, data['rst_n'],   linewidth=1.0, drawstyle='steps-post', label='rst_n', alpha=0.7)
    axes[0].set_ylabel('Control (V)')
    axes[0].set_ylim(-vdd * 0.1, vdd * 1.2)
    axes[0].legend(fontsize=8)
    axes[0].set_title(f'ramp_gen (DIRECTION=1, MIN=0, MAX=127, STEP=1, N_CYCLE_START=2)  |  wall clock: {wall_s:.4f} s')
    axes[0].grid(True, alpha=0.3)

    for i in [0, 1, 2, 3]:
        col = f'code_{i}'
        if col in list(data.dtype.names):
            axes[1].plot(t, data[col] + i * 1.1, linewidth=1.0, drawstyle='steps-post', label=col)
    axes[1].set_ylabel('LSB bits (stacked)')
    axes[1].legend(fontsize=7)
    axes[1].grid(True, alpha=0.3)

    axes[2].plot(t, ramp_code, linewidth=1.0, drawstyle='steps-post', color='green')
    axes[2].set_ylabel('ramp code (integer)')
    axes[2].set_ylim(-1, 132)
    axes[2].grid(True, alpha=0.3)

    axes[0].set_xlim(t[0], t[-1])
    axes[-1].set_xlabel('Time (ns)')
    fig.tight_layout()
    fig.savefig(str(out_dir / 'analyze_ramp_gen.png'), dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f"Plot saved: {out_dir / 'analyze_ramp_gen.png'}")


if __name__ == "__main__":
    analyze()
