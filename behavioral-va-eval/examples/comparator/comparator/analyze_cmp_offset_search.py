"""Analyze cmp_offset_search: binary search for comparator offset."""
import time
from pathlib import Path

import matplotlib
import numpy as np

matplotlib.use('Agg')
import matplotlib.pyplot as plt

from evas.netlist.runner import evas_simulate

HERE = Path(__file__).parent
_DEFAULT_BASE = HERE.parent.parent.parent / 'output' / 'comparator'

_SWEEP_OFFSETS_MV = [-10.0, -5.0, -2.0, 0.0, 2.0, 5.0, 10.0]
_T_MEASURE_NS = 1950.0


def _write_sweep_scs(scs_path: Path, voffset_v: float) -> None:
    content = (
        f"// cmp_offset_search sweep: voffset={voffset_v*1e3:.1f}mV\n"
        "simulator lang=spectre\n"
        "global 0\n\n"
        'ahdl_include "cmp_offset_search.va"\n'
        'ahdl_include "cmp_strongarm.va"\n\n'
        "Vvdd (vdd 0) vsource type=dc dc=0.8\n"
        "Vvss (vss 0) vsource type=dc dc=0\n"
        "Vclk (CLK 0) vsource type=pulse val0=0 val1=0.8 period=200n delay=10n rise=2n fall=2n width=98n\n"
        "Vvincm (vincm 0) vsource type=dc dc=0.4\n"
        "Vlp (lp 0) vsource type=dc dc=0\n"
        "Vlm (lm 0) vsource type=dc dc=0\n\n"
        "ISEARCH (CLK dcmpp vincm vinp_node vinn_node) cmp_offset_search vdd=0.8\n"
        f"ICMP (CLK vinn_node vinp_node dcmpn dcmpp lp lm vss vdd) cmp_strongarm voffset={voffset_v}\n\n"
        "tran tran stop=2400n maxstep=1n\n"
        "save CLK:2e vinp_node:6f vinn_node:6f\n"
    )
    scs_path.write_text(content, encoding='utf-8')


def analyze(base_dir: Path = _DEFAULT_BASE) -> None:
    out_dir = base_dir / 'cmp_offset_search'
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1. Convergence simulation (voffset=10mV)
    t0 = time.perf_counter()
    evas_simulate(str(HERE / 'tb_cmp_offset_search.scs'), output_dir=str(out_dir))
    wall_s = time.perf_counter() - t0

    data = np.genfromtxt(out_dir / 'tran.csv', delimiter=',', names=True, dtype=None, encoding='utf-8')
    t   = data['time'] * 1e9
    vdd = max(data[c].max() for c in ['CLK', 'dcmpp'])

    fig, axes = plt.subplots(3, 1, figsize=(8, 6), sharex=True)

    for sig in ['CLK', 'dcmpp']:
        axes[0].plot(t, data[sig], linewidth=1.0, drawstyle='steps-post', label=sig)
    axes[0].set_ylabel('Digital (V)')
    axes[0].set_ylim(-vdd * 0.1, vdd * 1.2)
    axes[0].legend(loc='upper right', fontsize=8)
    axes[0].set_title(f'cmp_offset_search (voffset=10mV, 10 steps, 12 cycles)  |  wall clock: {wall_s:.4f} s')
    axes[0].grid(True, alpha=0.3)

    for sig in ['vinp_node', 'vinn_node']:
        axes[1].plot(t, data[sig] * 1e3, linewidth=1.0, label=sig)
    axes[1].set_ylabel('VINP/VINN (mV)')
    vin_all = np.concatenate([data['vinp_node'], data['vinn_node']]) * 1e3
    vin_min, vin_max = vin_all.min(), vin_all.max()
    vin_margin = (vin_max - vin_min) * 0.2
    axes[1].set_ylim(vin_min - vin_margin, vin_max + vin_margin)
    axes[1].legend(loc='upper right', fontsize=8)
    axes[1].grid(True, alpha=0.3)

    vdiff = (data['vinp_node'] - data['vinn_node']) * 1e3
    axes[2].plot(t, vdiff, linewidth=1.0, color='purple')
    axes[2].axhline(10.0, color='red', linestyle='--', linewidth=1.0, label='target=10mV')
    axes[2].set_ylabel('VINP−VINN (mV)')
    axes[2].legend(loc='upper right', fontsize=8)
    axes[2].grid(True, alpha=0.3)

    axes[0].set_xlim(t[0], t[-1])
    axes[-1].set_xlabel('Time (ns)')
    fig.tight_layout()
    fig.savefig(str(base_dir / 'analyze_cmp_offset_search.png'), dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f"Plot saved: {base_dir / 'analyze_cmp_offset_search.png'}")

    # 2. Offset sweep
    sweep_dir   = out_dir / 'sweep'
    measured_mv = []

    for voffset_mv in _SWEEP_OFFSETS_MV:
        voffset_v = voffset_mv * 1e-3
        label     = f'v{voffset_mv:+.0f}mV'.replace('+', 'p').replace('-', 'n')
        sim_dir   = sweep_dir / label
        sim_dir.mkdir(parents=True, exist_ok=True)
        # Write SCS next to VA files so bare ahdl_include paths resolve correctly
        scs_path  = HERE / f'_sweep_{label}.scs'
        _write_sweep_scs(scs_path, voffset_v)
        try:
            evas_simulate(str(scs_path), output_dir=str(sim_dir))
        finally:
            scs_path.unlink(missing_ok=True)

        sw   = np.genfromtxt(sim_dir / 'tran.csv', delimiter=',', names=True, dtype=None, encoding='utf-8')
        t_ns = sw['time'] * 1e9
        idx  = min(np.searchsorted(t_ns, _T_MEASURE_NS), len(sw) - 1)
        meas = (sw['vinp_node'][idx] - sw['vinn_node'][idx]) * 1e3
        measured_mv.append(meas)
        print(f"  voffset={voffset_mv:+.1f}mV → measured={meas:+.3f}mV")

    actual   = np.array(_SWEEP_OFFSETS_MV)
    measured = np.array(measured_mv)
    lim      = max(abs(actual).max(), abs(measured).max()) * 1.2

    fig2, ax = plt.subplots(figsize=(7, 6))
    ax.scatter(actual, measured, s=80, zorder=5, label='measured offset')
    ax.plot([-lim, lim], [-lim, lim], 'r--', linewidth=1, label='ideal (y=x)')
    ax.set_xlabel('Actual voffset (mV)')
    ax.set_ylabel('Measured offset at cycle 10 (mV)')
    ax.set_title('Offset search accuracy sweep\n(10 binary search iterations)')
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.set_xlim(-lim, lim)
    ax.set_ylim(-lim, lim)
    ax.set_aspect('equal')
    fig2.tight_layout()
    fig2.savefig(str(base_dir / 'analyze_offset_sweep.png'), dpi=150, bbox_inches='tight')
    plt.close(fig2)
    print(f"Plot saved: {base_dir / 'analyze_offset_sweep.png'}")


if __name__ == "__main__":
    analyze()
