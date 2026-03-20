"""Validate cmp_strongarm: clocked StrongARM comparator.

Testbench: VCM=0.45V (VDD/2), diff=1mV (VINP=450.5mV, VINN=449.5mV), polarity swaps at 2ns.
Clock: 1GHz, VDD=0.9V.

Expected:
  - Before swap (t < 2ns):  vinp > vinn (+1mV) -> out_p HIGH, out_n LOW
  - After  swap (t > 2ns):  vinp < vinn (-1mV) -> out_p LOW,  out_n HIGH
"""
from pathlib import Path

import numpy as np

OUT = Path(__file__).parent.parent.parent / 'output' / 'comparator' / 'cmp_strongarm'

_VTH = 0.45   # half of VDD=0.9


def validate_csv(out_dir: Path = OUT) -> int:
    data = np.genfromtxt(out_dir / 'tran.csv', delimiter=',', names=True, dtype=None, encoding='utf-8')
    failures = 0

    t_ns   = data['time'] * 1e9
    out_p  = data['out_p']
    out_n  = data['out_n']

    # Both outputs must toggle (non-trivial comparator decisions)
    if out_p.max() - out_p.min() < _VTH:
        print("FAIL: out_p never toggles")
        failures += 1
    if out_n.max() - out_n.min() < _VTH:
        print("FAIL: out_n never toggles")
        failures += 1

    # Before swap (0.6ns < t < 2ns): vinp > vinn -> out_p HIGH
    pre = out_p[(t_ns > 0.6) & (t_ns < 2.0)]
    if len(pre) == 0 or (pre > _VTH).mean() < 0.4:
        pct = 0 if len(pre) == 0 else (pre > _VTH).mean() * 100
        print(f"FAIL: before swap, out_p HIGH only {pct:.0f}% (expected >40%)")
        failures += 1

    # After swap (2.5ns < t < 4ns): vinp < vinn -> out_p LOW
    post = out_p[(t_ns > 2.5) & (t_ns < 4.0)]
    if len(post) == 0 or (post < _VTH).mean() < 0.4:
        pct = 0 if len(post) == 0 else (post < _VTH).mean() * 100
        print(f"FAIL: after swap, out_p LOW only {pct:.0f}% (expected >40%)")
        failures += 1

    if failures == 0:
        print("[CSV] All assertions passed.")
    return failures


if __name__ == '__main__':
    raise SystemExit(0 if validate_csv() == 0 else 1)
