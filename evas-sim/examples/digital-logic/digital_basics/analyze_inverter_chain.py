"""Analyze 4-stage inverter chain: td=100ps, tr=50ps per stage."""
import time
from pathlib import Path

import matplotlib
import numpy as np

matplotlib.use('Agg')
import matplotlib.pyplot as plt

from evas.netlist.runner import evas_simulate

HERE = Path(__file__).parent
_DEFAULT_BASE = HERE.parent.parent.parent / 'output' / 'digital_basics'


def analyze(out_dir: Path = _DEFAULT_BASE) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    out_dir_chain = out_dir / 'inverter_chain'

    t0 = time.perf_counter()
    evas_simulate(str(HERE / 'tb_inverter_chain.scs'), output_dir=str(out_dir_chain))
    wall_s = time.perf_counter() - t0

    data = np.genfromtxt(out_dir_chain / 'tran.csv', delimiter=',', names=True, dtype=None, encoding='utf-8')
    t = data['time'] * 1e9

    signals = [
        ('in',  'IN',   'tab:blue'),
        ('n1',  'OUT1', 'tab:orange'),
        ('n2',  'OUT2', 'tab:green'),
        ('n3',  'OUT3', 'tab:red'),
        ('out', 'OUT4', 'tab:purple'),
    ]

    OFFSET = 1.1
    N = len(signals)

    fig, ax = plt.subplots(figsize=(12, 6))

    for i, (col, label, color) in enumerate(signals):
        offset = (N - 1 - i) * OFFSET
        ax.plot(t, data[col] + offset, color=color, linewidth=1, label=label)
        ax.axhline(offset,       color=color, linewidth=1, linestyle='--', alpha=0.4)
        ax.axhline(offset + 0.8, color=color, linewidth=1, linestyle='--', alpha=0.4)

    ax.set_xlabel('Time (ns)')
    ax.set_ylabel('Voltage (V)  +  stage offset')
    ax.set_title(f'4-stage inverter chain  —  td=100 ps, tr=50 ps per stage  |  wall clock: {wall_s:.4f} s')
    ax.set_xlim(t[0], t[-1])

    yticks, ylabels = [], []
    for i, (_, label, _) in enumerate(signals):
        yticks.append((N - 1 - i) * OFFSET)
        ylabels.append(label)
    ax.set_yticks(yticks)
    ax.set_yticklabels(ylabels, fontsize=8)
    ax.set_ylim(-0.3, N * OFFSET + 0.2)

    ax.legend(loc='upper right', fontsize=9)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()

    path = out_dir / 'analyze_inverter_chain.png'
    fig.savefig(str(path), dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f"Saved: {path}")


if __name__ == "__main__":
    analyze()
