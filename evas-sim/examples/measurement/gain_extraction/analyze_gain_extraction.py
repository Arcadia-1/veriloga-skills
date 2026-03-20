"""Analyze gain_extraction simulation results.

Plots:
  1. waveform.png       — VIN_diff & VAMP_diff (first 10 us, from EVAS)
  2. gain_convergence.png — A_est vs N for 3 LFSR seeds (2^8..2^18, EVAS)

All 4 simulations (1 waveform + 3 convergence) run in parallel via
ProcessPoolExecutor to meet the ~30 s wall-clock target.
"""

import re
import subprocess
import sys
import time
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

HERE = Path(__file__).parent

# ── Parameters (must match testbench files) ───────────────────────────────────
GAIN_ERR    = 0.08
ACTUAL_GAIN = 8.0 * (1.0 + GAIN_ERR)   # 8.64
DITHER_AMP  = 0.014063
VIN_NOISE   = 0.01

# (lfsr_seed, vin_seed) for each of the 3 convergence runs
SEEDS  = [(42, 0), (123, 1), (7, 2)]
COLORS = ['#0071e3', '#ff9500', '#34c759']

_DEFAULT_OUT = HERE.parent.parent.parent / 'output' / 'gain_extraction'


# ── worker (top-level so ProcessPoolExecutor can pickle it) ───────────────────

def _launch_sim(scs_path: Path, out_dir: Path) -> subprocess.Popen:
    """Start one EVAS simulation in a child process; returns the Popen handle."""
    out_dir.mkdir(parents=True, exist_ok=True)
    script = (
        f"from pathlib import Path; "
        f"from evas.netlist.runner import evas_simulate; "
        f"evas_simulate({repr(str(scs_path))}, output_dir={repr(str(out_dir))})"
    )
    return subprocess.Popen(
        [sys.executable, '-c', script],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


# ── helpers ───────────────────────────────────────────────────────────────────

def _patch_convergence_scs(lfsr_seed: int, vin_seed: int) -> Path:
    """Write a seed-patched copy of tb_gain_convergence.scs to HERE."""
    text = (HERE / 'tb_gain_convergence.scs').read_text(encoding='utf-8')
    text = text.replace('LFSR_SEED=42', f'LFSR_SEED={lfsr_seed}')
    text = text.replace('VIN_SEED=0',   f'VIN_SEED={vin_seed}')
    p = HERE / f'_tb_conv_{lfsr_seed}.scs'
    p.write_text(text)
    return p


def _load_csv(out: Path) -> pd.DataFrame:
    df = pd.read_csv(out / 'tran.csv')
    df['vin_diff']  = df['vinp'] - df['vinn']
    df['vamp_diff'] = df['vamp_p'] - df['vamp_n']
    df['time_us']   = df['time'] * 1e6
    return df


def _parse_strobe(out: Path) -> pd.DataFrame:
    pattern = re.compile(r'\[gain_est\] N=(\d+) \| A_est=([0-9.]+)')
    rows = []
    for line in (out / 'strobe.txt').read_text(encoding='utf-8').splitlines():
        m = pattern.search(line)
        if m:
            rows.append({'N': int(m.group(1)), 'A_est': float(m.group(2))})
    return pd.DataFrame(rows)


# ── plots ─────────────────────────────────────────────────────────────────────

def _plot_waveform(df: pd.DataFrame, out: Path, wall_s: float):
    sub = df[df['time_us'] <= 10.0]
    fig, axes = plt.subplots(2, 1, figsize=(8, 5), sharex=True)

    axes[0].plot(sub['time_us'], sub['vin_diff'] * 1e3, color='#34c759', lw=0.8)
    axes[0].set_ylabel('VIN_diff  [mV]')
    axes[0].set_xlim(sub['time_us'].iloc[0], sub['time_us'].iloc[-1])
    axes[0].grid(True, alpha=0.35)
    axes[0].set_title(
        f'Input & output waveforms (first 10 us)\n'
        f'ACTUAL_GAIN = {ACTUAL_GAIN:.4f}   noise \u03c3 = {VIN_NOISE*1e3:.1f} mV   '
        f'wall clock: {wall_s:.1f} s'
    )

    axes[1].plot(sub['time_us'], sub['vamp_diff'] * 1e3, color='#ff9500', lw=0.8)
    axes[1].set_ylabel('VAMP_diff  [mV]')
    axes[1].set_xlabel('Time  [us]')
    axes[1].grid(True, alpha=0.35)

    fig.tight_layout()
    p = out / 'waveform.png'
    fig.savefig(p, dpi=150)
    plt.close(fig)
    print(f'Saved: {p}')


def _plot_convergence(strobes: list, out: Path, wall_s: float):
    Ns = strobes[0]['N'].values

    fig, axes = plt.subplots(2, 1, figsize=(9, 6), sharex=True)

    for idx, (df, (lfsr_seed, vin_seed)) in enumerate(zip(strobes, SEEDS)):
        Aest    = df['A_est'].values
        err_pct = (Aest - ACTUAL_GAIN) / ACTUAL_GAIN * 100.0
        label   = f'LFSR seed = {lfsr_seed}'
        axes[0].semilogx(Ns, Aest,    'o-', ms=4, color=COLORS[idx], lw=1.2, label=label)
        axes[1].semilogx(Ns, err_pct, 's-', ms=4, color=COLORS[idx], lw=1.2)

    axes[0].axhline(ACTUAL_GAIN, color='r', ls='--', lw=1.0,
                    label=f'actual = {ACTUAL_GAIN:.4f}')
    axes[0].set_ylabel('Gain estimate')
    axes[0].legend(fontsize=8)
    axes[0].grid(True, alpha=0.35, which='both')

    axes[1].axhline(0, color='r', ls='--', lw=1.0)
    axes[1].set_ylabel('Error  [%]')
    axes[1].set_xlabel('Sample count  N')
    axes[1].grid(True, alpha=0.35, which='both')

    axes[1].set_xticks(Ns)
    axes[1].set_xticklabels([f'$2^{{{int(np.log2(n))}}}$' for n in Ns], fontsize=8)

    fig.suptitle(
        f'Gain estimation convergence  (GAIN_ERR = {GAIN_ERR*100:+.0f}%,  '
        f'dither = {DITHER_AMP*1e3:.2f} mV,  noise \u03c3 = {VIN_NOISE*1e3:.1f} mV,  3 LFSR seeds)\n'
        f'ACTUAL_GAIN = {ACTUAL_GAIN:.4f}   wall clock: {wall_s:.1f} s (4 sims parallel)',
        fontsize=10,
    )
    fig.tight_layout()
    p = out / 'gain_convergence.png'
    fig.savefig(p, dpi=150)
    plt.close(fig)
    print(f'Saved: {p}')


# ── main entry ────────────────────────────────────────────────────────────────

def analyze(output_dir=_DEFAULT_OUT):
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    # Prepare patched .scs files for the 3 convergence runs
    conv_scs = []
    try:
        for lfsr_seed, vin_seed in SEEDS:
            conv_scs.append(_patch_convergence_scs(lfsr_seed, vin_seed))

        wf_out    = out / 'waveform'
        conv_outs = [out / f'seed_{ls}' for ls, _ in SEEDS]

        all_jobs = [(HERE / 'tb_gain_extraction.scs', wf_out)] + \
                   list(zip(conv_scs, conv_outs))

        t0    = time.perf_counter()
        procs = [_launch_sim(scs, od) for scs, od in all_jobs]
        for i, p in enumerate(procs):
            rc = p.wait()
            if rc != 0:
                raise RuntimeError(f'Simulation {i} failed (exit code {rc})')
        wall_s = time.perf_counter() - t0
        print(f'All simulations done in {wall_s:.1f} s (wall clock)')

    finally:
        for p in conv_scs:
            p.unlink(missing_ok=True)

    df      = _load_csv(wf_out)
    strobes = [_parse_strobe(od) for od in conv_outs]

    _plot_waveform(df, out, wall_s)
    _plot_convergence(strobes, out, wall_s)


if __name__ == '__main__':
    analyze()
