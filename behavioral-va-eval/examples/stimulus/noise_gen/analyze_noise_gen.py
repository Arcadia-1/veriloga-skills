"""Analyze noise_gen: Gaussian noise added to a DC input (sigma=0.1V, vin=1.0V)."""
import time
from pathlib import Path

import matplotlib
import numpy as np

matplotlib.use('Agg')
import matplotlib.pyplot as plt

from evas.netlist.runner import evas_simulate

HERE = Path(__file__).parent
_DEFAULT_OUT = HERE.parent.parent.parent / 'output' / 'noise_gen'


def analyze(out_dir: Path = _DEFAULT_OUT) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)

    t0 = time.perf_counter()
    evas_simulate(str(HERE / 'tb_noise_gen.scs'), output_dir=str(out_dir))
    wall_s = time.perf_counter() - t0

    data  = np.genfromtxt(out_dir / 'tran.csv', delimiter=',', names=True, dtype=None, encoding='utf-8')
    t     = data['time'] * 1e9
    noise = data['vout_o'] - data['vin_i']

    fig, axes = plt.subplots(2, 1, figsize=(12, 7))

    axes[0].plot(t, data['vin_i'],  linewidth=1.0, color='steelblue', label='vin_i (DC=1.0V)', zorder=3)
    axes[0].plot(t, data['vout_o'], linewidth=1.0, color='tomato', alpha=0.8, label='vout_o (noisy)')
    axes[0].set_ylabel('Voltage (V)')
    axes[0].set_title(f'noise_gen (sigma=0.1V, vin=1.0V DC)  |  wall clock: {wall_s:.4f} s')
    axes[0].legend(fontsize=9)
    axes[0].grid(True, alpha=0.3)
    v_mean = float(data['vin_i'].mean())
    axes[0].set_ylim(v_mean - 0.5, v_mean + 0.5)
    _margin = 0.05 * (t[-1] - t[0])
    axes[0].set_xlim(t[0] - _margin, t[-1] + _margin)

    axes[1].plot(t, noise, linewidth=1.0, color='purple', alpha=0.8)
    axes[1].axhline(0,    color='black', linewidth=1.0, linestyle='--')
    axes[1].axhline( 0.1, color='red',   linewidth=1.0, linestyle=':', label='+1σ')
    axes[1].axhline(-0.1, color='red',   linewidth=1.0, linestyle=':', label='-1σ')
    axes[1].set_ylabel('Noise (V)')
    axes[1].set_xlabel('Time (ns)')
    axes[1].legend(fontsize=8)
    axes[1].grid(True, alpha=0.3)
    _noise_abs = max(float(np.abs(noise).max()) * 1.05, 0.15)
    axes[1].set_ylim(-_noise_abs, _noise_abs)
    axes[1].set_xlim(t[0] - _margin, t[-1] + _margin)

    fig.tight_layout()
    fig.savefig(str(out_dir / 'analyze_noise_gen.png'), dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f"Plot saved: {out_dir / 'analyze_noise_gen.png'}")


if __name__ == "__main__":
    analyze()
