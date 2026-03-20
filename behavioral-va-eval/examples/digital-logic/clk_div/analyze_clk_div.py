"""Analyze clk_div: clock divider — one plot per ratio."""
import time
from pathlib import Path

import matplotlib
import numpy as np

matplotlib.use('Agg')
import matplotlib.pyplot as plt

from evas.netlist.runner import evas_simulate

HERE = Path(__file__).parent
_DEFAULT_OUT = HERE.parent.parent.parent / 'output' / 'clk_div'

_RATIOS = [
    (2, 'div2', 'tb_clk_div_div2.scs'),
    (4, 'div4', 'tb_clk_div.scs'),
    (8, 'div8', 'tb_clk_div_div8.scs'),
]

_COLORS = ['#e07b39', '#2ca02c', '#9467bd']


def _measure_period_ns(t_ns: np.ndarray, sig: np.ndarray, thresh: float = 0.45) -> float:
    above = sig > thresh
    edges = np.where(np.diff(above.astype(int)) > 0)[0]
    if len(edges) < 2:
        return float('nan')
    return float(np.mean(np.diff(t_ns[edges])))


def analyze(out_dir: Path = _DEFAULT_OUT) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)

    # Run all three simulations, record wall-clock time per run
    wall_times: dict[int, float] = {}
    for ratio, subdir, tb_file in _RATIOS:
        sim_out = out_dir / subdir
        sim_out.mkdir(parents=True, exist_ok=True)
        t0 = time.perf_counter()
        evas_simulate(str(HERE / tb_file), output_dir=str(sim_out))
        wall_times[ratio] = time.perf_counter() - t0

    # One plot per ratio
    for (ratio, subdir, _), color in zip(_RATIOS, _COLORS):
        data = np.genfromtxt(
            out_dir / subdir / 'tran.csv',
            delimiter=',', names=True, dtype=None, encoding='utf-8',
        )
        t_ns    = data['time'] * 1e9
        clk_in  = data['clk_in']
        clk_out = data['clk_out']
        vdd     = clk_in.max()
        ylim    = (-0.1 * vdd, 1.2 * vdd)

        period_out_ns = _measure_period_ns(t_ns, clk_out)
        period_in_ns  = _measure_period_ns(t_ns, clk_in)
        wall_s = wall_times[ratio]

        fig, (ax0, ax1) = plt.subplots(2, 1, figsize=(10, 5), sharex=True)

        ax0.plot(t_ns, clk_in, linewidth=1.0, drawstyle='steps-post', color='steelblue')
        ax0.set_ylabel('clk_in')
        ax0.set_ylim(ylim)
        ax0.grid(True, alpha=0.3)

        ax1.plot(t_ns, clk_out, linewidth=1.0, drawstyle='steps-post', color=color)
        ax1.set_ylabel('clk_out')
        ax1.set_ylim(ylim)
        ax1.grid(True, alpha=0.3)
        ax1.set_xlabel('Time (ns)')
        ax0.set_xlim(t_ns[0], t_ns[-1])

        fig.suptitle(
            f'clk_div  ÷{ratio}  —  '
            f'in {period_in_ns:.0f} ns / out {period_out_ns:.0f} ns  |  '
            f'wall clock: {wall_s:.4f} s',
            fontsize=10,
        )
        fig.tight_layout()

        out_path = out_dir / f'clk_div_div{ratio}.png'
        fig.savefig(str(out_path), dpi=150, bbox_inches='tight')
        plt.close(fig)
        print(f"Plot saved: {out_path}")


if __name__ == "__main__":
    analyze()
