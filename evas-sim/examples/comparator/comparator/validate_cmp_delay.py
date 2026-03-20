"""Validate cmp_delay: log-linear regeneration delay td = td_0 + tau*ln(VDD/|Vdiff|).

Testbench: 4 phases of 4ns each (16ns total), 1GHz CLK. VDD=0.9V.
Phase diffs: 10mV, 1mV, 0.1mV, 0.01mV.
Expected: out_p goes HIGH in each phase; delay increases with decreasing |Vdiff|.
"""
from pathlib import Path

import numpy as np

OUT = Path(__file__).parent.parent.parent / 'output' / 'comparator' / 'cmp_delay'

_VTH = 0.45
_PHASES_NS = [(0, 4, 10e-3), (4, 8, 1e-3), (8, 12, 0.1e-3), (12, 16, 0.01e-3)]


def validate_csv(out_dir: Path = OUT) -> int:
    data = np.genfromtxt(out_dir / 'tran.csv', delimiter=',', names=True, dtype=None, encoding='utf-8')
    failures = 0
    t_ns  = data['time'] * 1e9
    out_p = data['out_p']

    # out_p must go HIGH in every phase
    for t0, t1, diff_v in _PHASES_NS:
        mask = (t_ns >= t0) & (t_ns < t1)
        if out_p[mask].max() < _VTH:
            print(f"FAIL: out_p never goes HIGH in phase {t0}-{t1}ns (diff={diff_v*1e3:.2g}mV)")
            failures += 1

    # Measured delay must increase across phases (log-linear trend)
    delays = []
    clk_rise_ns = 0.1   # CLK delay=100ps
    for i, (t0, _, diff_v) in enumerate(_PHASES_NS):
        tr = t0 + clk_rise_ns
        mask = (t_ns >= tr) & (t_ns < tr + 3.0)
        idx = np.where((out_p[mask] > _VTH))[0]
        if len(idx) > 0:
            delays.append(t_ns[mask][idx[0]] - tr)
        else:
            delays.append(None)

    valid = [d for d in delays if d is not None]
    if len(valid) >= 2:
        if not all(valid[i] <= valid[i+1] + 0.1 for i in range(len(valid)-1)):
            print(f"FAIL: delays not monotonically increasing: {[f'{d:.2f}ns' for d in valid]}")
            failures += 1
        else:
            print(f"[CSV] Delays: {[f'{d:.2f}ns' for d in valid]} — monotonically increasing ✓")

    if failures == 0:
        print("[CSV] All assertions passed.")
    return failures


if __name__ == '__main__':
    raise SystemExit(0 if validate_csv() == 0 else 1)
