"""Validate dac_binary_clk_4b: 4-bit clocked binary DAC, full code sweep 0→15.

Testbench sweeps din[3:0] through codes 0..15 in order, one code per 40ns clock.
VDD = 0.9V, so LSB = 0.9/16 ≈ 56.25 mV.

Expected:
  - aout has 16 distinct levels (one per code).
  - Levels are monotonically non-decreasing as code increases.
  - Full output range spans at least 12/15 of VDD.
"""
from pathlib import Path

import numpy as np

OUT = Path(__file__).parent.parent.parent / 'output' / 'dac_binary_clk_4b'


def validate_csv(out_dir: Path = OUT) -> int:
    data = np.genfromtxt(out_dir / 'tran.csv', delimiter=',', names=True, dtype=None, encoding='utf-8')
    failures = 0

    vdd = max(data[c].max() for c in ['din3', 'din2', 'din1', 'din0', 'aout'])
    lsb = vdd / 16.0

    # Decode input code
    thr = vdd * 0.5
    code = (
        (data['din3'] > thr).astype(int) * 8 +
        (data['din2'] > thr).astype(int) * 4 +
        (data['din1'] > thr).astype(int) * 2 +
        (data['din0'] > thr).astype(int) * 1
    )

    aout = data['aout']
    levels = {}
    for c in range(16):
        mask = code == c
        if mask.any():
            levels[c] = float(np.median(aout[mask]))

    if len(levels) < 14:
        print(f"FAIL: only {len(levels)} distinct input codes seen (expected 16)")
        failures += 1

    if levels:
        sorted_codes = sorted(levels.keys())
        for i in range(1, len(sorted_codes)):
            c0, c1 = sorted_codes[i-1], sorted_codes[i]
            if levels[c1] < levels[c0] - lsb * 0.5:
                print(f"FAIL: aout decreased from code {c0} ({levels[c0]:.4f}V) to {c1} ({levels[c1]:.4f}V)")
                failures += 1
                break

        lo = levels.get(0, levels[sorted_codes[0]])
        hi = levels.get(15, levels[sorted_codes[-1]])
        if hi - lo < vdd * 0.75:
            print(f"FAIL: output range [{lo:.3f}, {hi:.3f}]V is too narrow (expected ≥ 75% of VDD)")
            failures += 1

    if failures == 0:
        print("[CSV] All assertions passed.")
    return failures


if __name__ == '__main__':
    raise SystemExit(0 if validate_csv() == 0 else 1)
