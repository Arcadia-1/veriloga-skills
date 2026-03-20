"""Analyze dwa_ptr_gen: DWA pointer rotation generator."""
import time
from pathlib import Path

import matplotlib
import numpy as np

matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

from evas.netlist.runner import evas_simulate

HERE = Path(__file__).parent
_DEFAULT_BASE = HERE.parent.parent.parent / 'output' / 'dwa_ptr_gen'


def analyze(base_dir: Path = _DEFAULT_BASE) -> None:
    out_dir = base_dir / 'dwa_ptr_gen'
    out_dir.mkdir(parents=True, exist_ok=True)

    t0 = time.perf_counter()
    evas_simulate(str(HERE / 'tb_dwa_ptr_gen.scs'), output_dir=str(out_dir))
    wall_s = time.perf_counter() - t0

    data = np.genfromtxt(out_dir / 'tran.csv', delimiter=',', names=True,
                         dtype=None, encoding='utf-8')
    t    = data['time'] * 1e9  # noqa: F841
    cols = set(data.dtype.names)
    vth  = 0.45

    # ── Clock period from netlist (100 ns → 10 MHz) ─────────────────────
    CLK_PERIOD_NS = 10.0
    CLK_MHZ       = 1e3 / CLK_PERIOD_NS   # 100 MHz

    # ── Find clock rising edges ──────────────────────────────────────────
    clk    = data['clk_i']
    rising = np.where((clk[:-1] < vth) & (clk[1:] >= vth))[0] + 1
    si     = np.clip(rising + 10, 0, len(data) - 1)
    N      = len(rising)
    rst_ok = data['rst_ni'][si] > vth

    # ── Per-cell matrices  [16 × N_cycles] ──────────────────────────────
    cell_mat = np.zeros((16, N), dtype=int)
    ptr_mat  = np.zeros((16, N), dtype=int)
    for b in range(16):
        if f'cell_en_{b}' in cols:
            cell_mat[b] = (data[f'cell_en_{b}'][si] > vth).astype(int)
        if f'ptr_{b}' in cols:
            ptr_mat[b]  = (data[f'ptr_{b}'][si]  > vth).astype(int)

    ptr_pos = np.full(N, -1, dtype=int)
    for b in range(16):
        ptr_pos[ptr_mat[b] == 1] = b

    code     = np.zeros(N, dtype=int)
    prev_ptr = 0
    for ci in range(N):
        if rst_ok[ci]:
            code[ci] = (ptr_pos[ci] - prev_ptr + 16) % 16
            prev_ptr  = ptr_pos[ci]
        else:
            prev_ptr = 0

    # ── Plot ─────────────────────────────────────────────────────────────
    BAR_W = 0.45   # half-width of each column bar

    fig, ax = plt.subplots(figsize=(max(10, N * 1.1), 6))

    for ci in range(N):
        if not rst_ok[ci]:
            ax.axvspan(ci - BAR_W, ci + BAR_W, color='#cccccc',
                       alpha=0.45, zorder=0, linewidth=0)
            ax.text(ci, 15.8, 'RST', ha='center', va='bottom',
                    fontsize=7, color='gray')
            continue

        sel  = sorted(np.where(cell_mat[:, ci] == 1)[0].tolist())
        gaps = np.diff(sel) if len(sel) > 1 else np.array([1])

        # Split into contiguous segments (handles circular wrap-around)
        segs = []
        if len(sel) > 0 and gaps.max() > 1:
            cut = int(np.argmax(gaps))
            segs = [sel[:cut + 1], sel[cut + 1:]]
        elif sel:
            segs = [sel]

        for seg in segs:
            ax.fill_betweenx(
                [seg[0] - 0.42, seg[-1] + 0.42],
                ci - BAR_W, ci + BAR_W,
                color='#4c8edd', alpha=0.45, linewidth=0, zorder=1)
            # Thin border
            ax.fill_betweenx(
                [seg[0] - 0.42, seg[-1] + 0.42],
                ci - BAR_W, ci + BAR_W,
                color='none', linewidth=0.8,
                edgecolor='#2a6ab0', zorder=2)

        # Ptr diamond
        if ptr_pos[ci] >= 0:
            ax.scatter(ci, ptr_pos[ci], s=110, marker='D',
                       color='#e05020', zorder=5, linewidths=0)
            ax.text(ci, ptr_pos[ci] + 0.65, f'+{code[ci]}',
                    ha='center', va='bottom', fontsize=8,
                    color='#c03010', fontweight='bold')

    # Dashed trajectory line through ptr positions
    vc = [ci for ci in range(N) if rst_ok[ci] and ptr_pos[ci] >= 0]
    if vc:
        ax.plot(vc, [ptr_pos[ci] for ci in vc],
                color='#e05020', linewidth=1.0, linestyle='--',
                alpha=0.5, zorder=3)

    # ── Axes ─────────────────────────────────────────────────────────────
    ax.set_xlim(-0.6, N - 0.4)
    ax.set_ylim(-0.8, 17.2)
    ax.set_xticks(range(N))
    ax.set_xticklabels([f'{ci}T' for ci in range(N)], fontsize=9)
    ax.set_xlabel(f'Clock cycle    (T = {CLK_PERIOD_NS:.0f} ns,  clk = {CLK_MHZ:.0f} MHz)',
                  fontsize=10)
    ax.set_yticks(range(16))
    ax.set_ylabel('Cell index', fontsize=10)
    ax.yaxis.grid(True, alpha=0.18, color='gray', zorder=0)
    ax.set_axisbelow(True)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    ax.set_title(
        f'dwa_ptr_gen  —  DWA pointer rotation, overlap (code+1 cells/cycle)  '
        f'|  wall clock: {wall_s:.4f} s',
        fontsize=11)

    ax.legend(handles=[
        Patch(facecolor='#4c8edd', alpha=0.5, label='cell_en (selected range)'),
        Line2D([0], [0], marker='D', color='#e05020', linestyle='--',
               markersize=7, label='ptr  (+N = advance code)'),
    ], fontsize=9, loc='upper right', framealpha=0.9)

    fig.tight_layout()
    fig.savefig(str(base_dir / 'analyze_dwa_ptr_gen.png'), dpi=150,
                bbox_inches='tight')
    plt.close(fig)
    print(f"Plot saved: {base_dir / 'analyze_dwa_ptr_gen.png'}")


if __name__ == "__main__":
    analyze()
