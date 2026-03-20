"""Analyze d2b_4b: unified static code driver (trim_code=9)."""
import time
from pathlib import Path

import matplotlib
import numpy as np

matplotlib.use('Agg')
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt

from evas.netlist.runner import evas_simulate

HERE = Path(__file__).parent
_DEFAULT_OUT = HERE.parent.parent.parent / 'output' / 'd2b_4b'

TRIM = 9
N_COLS = 16  # display grid width (widest bus)


def _read_bits(data, cols, vth=0.45):
    """Read steady-state bit values from CSV (take midpoint sample)."""
    mid = len(data) // 2
    names = set(data.dtype.names)
    return np.array([(data[c][mid] > vth) if c in names else 0
                     for c in cols], dtype=float)


def _draw_bus(ax, bits_lsb, n_valid, label, color_hi, color_lo='#dde5f0',
              color_na='#f0f0f0'):
    """
    Draw a single bus row as colored bit cells.
    bits_lsb: array indexed [0]=LSB ... [N-1]=MSB (length N_COLS, padded with NaN).
    n_valid: number of meaningful bits (rest shown as inactive).
    Display order: MSB on left (column 0 = bit n_valid-1).
    """
    # Reverse to MSB-first
    bits_msb = bits_lsb[:n_valid][::-1]

    for col in range(N_COLS):
        if col < n_valid:
            b = bits_msb[col]
            fc = color_hi if b else color_lo
            tc = 'white' if b else '#8898b0'
            bit_idx = n_valid - 1 - col
        else:
            b = np.nan
            fc = color_na
            tc = '#cccccc'
            bit_idx = None

        rect = mpatches.FancyBboxPatch(
            (col + 0.06, 0.08), 0.88, 0.84,
            boxstyle='round,pad=0.03',
            facecolor=fc, edgecolor='#c4ccd8', linewidth=0.4, zorder=2)
        ax.add_patch(rect)

        if col < n_valid:
            ax.text(col + 0.5, 0.50, str(int(b)),
                    ha='center', va='center', fontsize=7.5,
                    color=tc, fontweight='bold' if b else 'normal', zorder=3)
            ax.text(col + 0.5, 0.04, str(bit_idx),
                    ha='center', va='bottom', fontsize=5.5,
                    color='#aab0c0', zorder=3)

    ax.set_xlim(0, N_COLS)
    ax.set_ylim(0, 1)
    ax.set_yticks([])
    ax.set_xticks([])
    for sp in ax.spines.values():
        sp.set_visible(False)
    ax.set_ylabel(label, fontsize=8.5, rotation=0, ha='right', va='center',
                  labelpad=8)


def analyze(out_dir: Path = _DEFAULT_OUT) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)

    t0 = time.perf_counter()
    evas_simulate(str(HERE / 'tb_d2b_4b.scs'), output_dir=str(out_dir))
    wall_s = time.perf_counter() - t0

    data = np.genfromtxt(out_dir / 'tran.csv', delimiter=',', names=True,
                         dtype=None, encoding='utf-8')

    def read(prefix, n):
        arr = _read_bits(data, [f'{prefix}_{i}' for i in range(n)])
        # Pad to N_COLS
        padded = np.full(N_COLS, np.nan)
        padded[:n] = arr
        return arr, padded

    bin_arr,      bin_pad      = read('bin_o',      4)
    bin_n_arr,    bin_n_pad    = read('bin_n_o',    4)
    onehot_arr,   onehot_pad   = read('onehot_o',   16)
    onehot_n_arr, onehot_n_pad = read('onehot_n_o', 16)
    therm_arr,    therm_pad    = read('therm_o',    15)
    therm_n_arr,  therm_n_pad  = read('therm_n_o',  15)

    bin_str = ''.join(str(int(b)) for b in bin_arr[::-1])  # MSB-first

    rows = [
        (bin_pad,      4,  'bin_o[3:0]',       '#2a7de1'),
        (bin_n_pad,    4,  'bin_n_o[3:0]',      '#d45020'),
        (onehot_pad,   16, 'onehot_o[15:0]',    '#2a7de1'),
        (onehot_n_pad, 16, 'onehot_n_o[15:0]',  '#d45020'),
        (therm_pad,    15, 'therm_o[14:0]',     '#2a7de1'),
        (therm_n_pad,  15, 'therm_n_o[14:0]',   '#d45020'),
    ]

    fig, axes = plt.subplots(len(rows), 1, figsize=(13, 5.5),
                             gridspec_kw={'hspace': 0.18})

    fig.suptitle(
        f'd2b_4b  |  trim_code = {TRIM}  (binary: {bin_str})  |  wall clock: {wall_s:.4f} s',
        fontsize=11, y=1.01)

    # Color-coding legend patches
    hi_patch  = mpatches.Patch(facecolor='#2a7de1', edgecolor='#aab',
                               linewidth=0.5, label='active-high = 1')
    lo_patch  = mpatches.Patch(facecolor='#d45020', edgecolor='#aab',
                               linewidth=0.5, label='active-low = 0  (inverted)')
    off_patch = mpatches.Patch(facecolor='#dde5f0', edgecolor='#c4ccd8',
                               linewidth=0.4, label='inactive (0 / 1)')
    na_patch  = mpatches.Patch(facecolor='#f0f0f0', edgecolor='#c4ccd8',
                               linewidth=0.4, label='unused bit')
    fig.legend(handles=[hi_patch, lo_patch, off_patch, na_patch],
               loc='lower center', ncol=4, fontsize=7.5, framealpha=0.9,
               bbox_to_anchor=(0.5, -0.06))

    for ax, (bits, n_valid, label, color) in zip(axes, rows):
        _draw_bus(ax, bits, n_valid, label, color_hi=color)

    fig.tight_layout()
    fig.savefig(str(out_dir / 'analyze_d2b_4b.png'), dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f"Plot saved: {out_dir / 'analyze_d2b_4b.png'}")


if __name__ == "__main__":
    analyze()
