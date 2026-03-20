"""Validate lfsr: Linear Feedback Shift Register output.

Testbench: seed=123, clock 1GHz, reset deasserts at t=101ns, run for 500ns.
Expected post-reset (t > 102ns):
  - dpn toggles at least 10 times (non-trivial LFSR sequence).
  - dpn is not stuck HIGH or stuck LOW.
"""
from pathlib import Path

import numpy as np

OUT = Path(__file__).parent.parent.parent / 'output' / 'lfsr'


def validate_csv(out_dir: Path = OUT) -> int:
    data = np.genfromtxt(out_dir / 'tran.csv', delimiter=',', names=True, dtype=None, encoding='utf-8')
    failures = 0

    t_ns = data['time'] * 1e9
    dpn  = data['dpn']
    vdd = max(data[c].max() for c in ['rstb', 'clk', 'dpn'])
    vth  = vdd * 0.5

    post = t_ns > 102.0
    dpn_post = dpn[post]

    if len(dpn_post) == 0:
        print("FAIL: no samples after reset")
        return 1

    hi_frac = (dpn_post > vth).mean()
    if hi_frac < 0.05:
        print(f"FAIL: dpn is stuck LOW (high fraction = {hi_frac:.2%})")
        failures += 1
    if hi_frac > 0.95:
        print(f"FAIL: dpn is stuck HIGH (high fraction = {hi_frac:.2%})")
        failures += 1

    binary = (dpn_post > vth).astype(int)
    transitions = int(np.sum(np.abs(np.diff(binary))))
    if transitions < 10:
        print(f"FAIL: only {transitions} transitions post-reset (expected ≥ 10)")
        failures += 1

    if failures == 0:
        print(f"[CSV] All assertions passed. ({transitions} transitions, {hi_frac:.1%} high)")
    return failures


if __name__ == '__main__':
    raise SystemExit(0 if validate_csv() == 0 else 1)
