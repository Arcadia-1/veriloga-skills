"""Analyze dac_binary_clk_4b: 4-bit clocked binary DAC full code sweep (0 → 15)."""
import time
from pathlib import Path

import matplotlib
import numpy as np

matplotlib.use('Agg')
import matplotlib.pyplot as plt

from evas.netlist.runner import evas_simulate

HERE = Path(__file__).parent
_DEFAULT_OUT = HERE.parent.parent.parent / 'output' / 'dac_binary_clk_4b'


def analyze(out_dir: Path = _DEFAULT_OUT) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)

    t0 = time.perf_counter()
    evas_simulate(str(HERE / 'tb_dac_binary_clk_4b.scs'), output_dir=str(out_dir))
    wall_s = time.perf_counter() - t0

    data = np.genfromtxt(out_dir / 'tran.csv', delimiter=',', names=True, dtype=None, encoding='utf-8')
    t   = data['time'] * 1e9
    vdd = 0.9
    code = (data['din3'] * 8 + data['din2'] * 4
          + data['din1'] * 2 + data['din0'] * 1)

    fig, axes = plt.subplots(3, 1, figsize=(12, 7), sharex=True,
                             gridspec_kw={'height_ratios': [1.5, 2.5, 2.5]})
    fig.suptitle(f'dac_binary_clk_4b — Full Code Sweep (0 → 15)  |  wall clock: {wall_s:.4f} s')

    axes[0].plot(t, data['rdy'], linewidth=1.0)
    axes[0].set_ylabel('clk (V)')
    axes[0].set_ylim(-vdd * 0.1, vdd * 1.2)
    axes[0].grid(True, alpha=0.3)

    axes[1].plot(t, code, linewidth=1.0, drawstyle='steps-post')
    axes[1].set_ylabel('input code')
    axes[1].set_ylim(-0.5, 16.5)
    axes[1].yaxis.set_major_locator(plt.MaxNLocator(integer=True))
    axes[1].grid(True, alpha=0.3)

    axes[2].plot(t, data['aout'], linewidth=1.0, color='tab:orange')
    axes[2].set_ylabel('aout (V)')
    axes[2].set_ylim(-vdd * 0.1, vdd * 1.2)
    axes[2].grid(True, alpha=0.3)

    axes[0].set_xlim(t[0], t[-1])
    axes[-1].set_xlabel('Time (ns)')
    fig.tight_layout()
    fig.savefig(str(out_dir / 'analyze_dac_binary_clk_4b.png'), dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f"Plot saved: {out_dir / 'analyze_dac_binary_clk_4b.png'}")

    bits = ['din3', 'din2', 'din1', 'din0']
    fig2, axes2 = plt.subplots(len(bits), 1, figsize=(12, 6), sharex=True)
    fig2.suptitle('dac_binary_clk_4b — Input Bits')
    for ax, bit in zip(axes2, bits):
        ax.plot(t, data[bit], linewidth=1.0)
        ax.set_ylabel(bit)
        ax.set_ylim(-vdd * 0.1, vdd * 1.2)
        ax.set_yticks([0, 1])
        ax.grid(True, alpha=0.3)
    axes2[0].set_xlim(t[0], t[-1])
    axes2[-1].set_xlabel('Time (ns)')
    fig2.tight_layout()
    fig2.savefig(str(out_dir / 'analyze_dac_binary_clk_4b_bits.png'), dpi=150, bbox_inches='tight')
    plt.close(fig2)
    print(f"Plot saved: {out_dir / 'analyze_dac_binary_clk_4b_bits.png'}")


if __name__ == "__main__":
    analyze()
