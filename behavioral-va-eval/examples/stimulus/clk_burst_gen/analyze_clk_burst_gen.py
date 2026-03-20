"""Analyze clk_burst_gen: outputs 2 CLK pulses every div input cycles."""
import time
from pathlib import Path

import matplotlib
import numpy as np

matplotlib.use('Agg')
import matplotlib.pyplot as plt

from evas.netlist.runner import evas_simulate

HERE = Path(__file__).parent
_DEFAULT_OUT = HERE.parent.parent.parent / 'output' / 'clk_burst_gen'


def analyze(out_dir: Path = _DEFAULT_OUT) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)

    t0 = time.perf_counter()
    evas_simulate(str(HERE / 'tb_clk_burst_gen.scs'), output_dir=str(out_dir))
    wall_s = time.perf_counter() - t0

    data = np.genfromtxt(out_dir / 'tran.csv', delimiter=',', names=True, dtype=None, encoding='utf-8')
    t   = data['time'] * 1e9
    vdd = max(data[s].max() for s in ['CLK', 'RST_N', 'CLK_OUT'])

    signals = ['CLK', 'RST_N', 'CLK_OUT']
    fig, axes = plt.subplots(len(signals), 1, figsize=(12, 6), sharex=True)

    for i, sig in enumerate(signals):
        axes[i].plot(t, data[sig], linewidth=1.0, drawstyle='steps-post')
        axes[i].set_ylabel(sig)
        axes[i].set_ylim(-vdd * 0.1, vdd * 1.2)
        axes[i].grid(True, alpha=0.3)

    axes[0].set_title(f'clk_burst_gen (div=8: 2 pulses per 8 CLK cycles)  |  wall clock: {wall_s:.4f} s')
    axes[0].set_xlim(t[0], t[-1])
    axes[-1].set_xlabel('Time (ns)')
    fig.tight_layout()
    fig.savefig(str(out_dir / 'analyze_clk_burst_gen.png'), dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f"Plot saved: {out_dir / 'analyze_clk_burst_gen.png'}")


if __name__ == "__main__":
    analyze()
