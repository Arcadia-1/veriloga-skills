"""Analyze digital_basics: AND gate, OR gate, NOT gate, D flip-flop."""
import time
from pathlib import Path

import matplotlib
import numpy as np

matplotlib.use('Agg')
import matplotlib.pyplot as plt

from evas.netlist.runner import evas_simulate

HERE = Path(__file__).parent
_DEFAULT_OUT = HERE.parent.parent.parent / 'output' / 'digital_basics'


def analyze(out_dir: Path = _DEFAULT_OUT) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)

    SIMS = {
        'and_gate': HERE / 'tb_and_gate.scs',
        'or_gate':  HERE / 'tb_or_gate.scs',
        'not_gate': HERE / 'tb_not_gate.scs',
        'dff_rst':  HERE / 'tb_dff_rst.scs',
    }

    elapsed = {}
    for name, tb in SIMS.items():
        t0 = time.perf_counter()
        evas_simulate(str(tb), output_dir=str(out_dir / name))
        elapsed[name] = time.perf_counter() - t0

    def load(name):
        data = np.genfromtxt(out_dir / name / 'tran.csv', delimiter=',', names=True, dtype=None, encoding='utf-8')
        return data, data['time'] * 1e9

    def savefig(fig, name):
        path = out_dir / f'analyze_{name}.png'
        fig.savefig(str(path), dpi=150, bbox_inches='tight')
        plt.close(fig)
        print(f"Saved: {path}")

    # AND gate
    data, t = load('and_gate')
    vdd = max(data[c].max() for c in ['a', 'b', 'y'])
    fig, axes = plt.subplots(2, 1, figsize=(10, 5), sharex=True)
    axes[0].plot(t, data['a'], linewidth=1, label='A')
    axes[0].plot(t, data['b'], linewidth=1, label='B')
    axes[0].set_ylabel('Input (V)')
    axes[0].set_ylim(-vdd * 0.1, vdd * 1.2)
    axes[0].legend(loc='upper right', fontsize=9)
    axes[0].set_title(f'AND gate  —  (A,B): 00→01→10→11  |  wall clock: {elapsed["and_gate"]:.4f} s')
    axes[0].grid(True, alpha=0.3)
    axes[1].plot(t, data['y'], linewidth=1, color='tab:green', label='OUT')
    axes[1].set_ylabel('Output (V)')
    axes[1].set_ylim(-vdd * 0.1, vdd * 1.2)
    axes[1].legend(loc='upper right', fontsize=9)
    axes[1].grid(True, alpha=0.3)
    axes[1].set_xlabel('Time (ns)')
    axes[0].set_xlim(t[0], t[-1])
    fig.tight_layout()
    savefig(fig, 'and_gate')

    # OR gate
    data, t = load('or_gate')
    vdd = max(data[c].max() for c in ['a', 'b', 'y'])
    fig, axes = plt.subplots(2, 1, figsize=(10, 5), sharex=True)
    axes[0].plot(t, data['a'], linewidth=1, label='A')
    axes[0].plot(t, data['b'], linewidth=1, label='B')
    axes[0].set_ylabel('Input (V)')
    axes[0].set_ylim(-vdd * 0.1, vdd * 1.2)
    axes[0].legend(loc='upper right', fontsize=9)
    axes[0].set_title(f'OR gate  —  (A,B): 00→01→10→11  |  wall clock: {elapsed["or_gate"]:.4f} s')
    axes[0].grid(True, alpha=0.3)
    axes[1].plot(t, data['y'], linewidth=1, color='tab:orange', label='OUT')
    axes[1].set_ylabel('Output (V)')
    axes[1].set_ylim(-vdd * 0.1, vdd * 1.2)
    axes[1].legend(loc='upper right', fontsize=9)
    axes[1].grid(True, alpha=0.3)
    axes[1].set_xlabel('Time (ns)')
    axes[0].set_xlim(t[0], t[-1])
    fig.tight_layout()
    savefig(fig, 'or_gate')

    # NOT gate
    data, t = load('not_gate')
    vdd = max(data[c].max() for c in ['a', 'y'])
    fig, axes = plt.subplots(2, 1, figsize=(10, 5), sharex=True)
    axes[0].plot(t, data['a'], linewidth=1, label='A')
    axes[0].set_ylabel('Input (V)')
    axes[0].set_ylim(-vdd * 0.1, vdd * 1.2)
    axes[0].legend(loc='upper right', fontsize=9)
    axes[0].set_title(f'NOT gate  —  A: 0→1→0→1  |  wall clock: {elapsed["not_gate"]:.4f} s')
    axes[0].grid(True, alpha=0.3)
    axes[1].plot(t, data['y'], linewidth=1, color='tab:red', label='OUT')
    axes[1].set_ylabel('Output (V)')
    axes[1].set_ylim(-vdd * 0.1, vdd * 1.2)
    axes[1].legend(loc='upper right', fontsize=9)
    axes[1].grid(True, alpha=0.3)
    axes[1].set_xlabel('Time (ns)')
    axes[0].set_xlim(t[0], t[-1])
    fig.tight_layout()
    savefig(fig, 'not_gate')

    # DFF
    data, t = load('dff_rst')
    vdd = max(data[c].max() for c in ['clk', 'rst', 'd', 'q', 'qbar'])
    fig, axes = plt.subplots(4, 1, figsize=(12, 8), sharex=True)
    axes[0].plot(t, data['clk'],  linewidth=1, color='gray',      label='CLK')
    axes[1].plot(t, data['rst'],  linewidth=1, color='tab:red',   label='RST')
    axes[2].plot(t, data['d'],    linewidth=1, color='tab:blue',  label='D')
    axes[3].plot(t, data['q'],    linewidth=1, color='tab:green', label='Q')
    axes[3].plot(t, data['qbar'], linewidth=1, color='tab:purple',
                 linestyle='--', label='QB', alpha=0.7)
    for ax, ylbl in zip(axes, ['CLK (V)', 'RST (V)', 'D (V)', 'Q / QB (V)']):
        ax.set_ylabel(ylbl)
        ax.set_ylim(-vdd * 0.1, vdd * 1.2)
        ax.legend(loc='upper right', fontsize=9)
        ax.grid(True, alpha=0.3)
    axes[0].set_title(f'D flip-flop with synchronous reset  |  wall clock: {elapsed["dff_rst"]:.4f} s')
    axes[0].set_xlim(t[0], t[-1])
    axes[-1].set_xlabel('Time (ns)')
    fig.tight_layout()
    savefig(fig, 'dff_rst')


if __name__ == "__main__":
    analyze()
