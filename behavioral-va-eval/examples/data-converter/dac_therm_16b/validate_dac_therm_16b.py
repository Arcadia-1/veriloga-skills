"""Validate dac_therm_16b: 16-bit thermometer DAC (vstep=1.0V).

Checkpoints (ones count -> vout):
  t=100ns:  0 ones  -> vout = 0.0V
  t=300ns:  4 ones  -> vout = 4.0V
  t=500ns:  8 ones  -> vout = 8.0V
  t=700ns:  12 ones -> vout = 12.0V
  t=1000ns: 16 ones -> vout = 16.0V
"""
from pathlib import Path

import numpy as np

OUT = Path(__file__).parent.parent.parent / 'output' / 'dac_therm_16b'

_CHECKPOINTS = [
    (100.0,  0,   0.0),
    (300.0,  4,   4.0),
    (500.0,  8,   8.0),
    (700.0,  12,  12.0),
    (1000.0, 16,  16.0),
]
_TOL = 0.1


def validate_csv(out_dir: Path = OUT) -> int:
    data = np.genfromtxt(out_dir / 'tran.csv', delimiter=',', names=True, dtype=None, encoding='utf-8')
    failures = 0

    t_ns = data['time'] * 1e9

    for t_check, exp_ones, exp_vout in _CHECKPOINTS:
        idx = int(np.argmin(np.abs(t_ns - t_check)))
        got_vout = float(data['vout'][idx])
        if abs(got_vout - exp_vout) > _TOL:
            print(f"FAIL: at t={t_check}ns (ones={exp_ones}): vout={got_vout:.3f}V, expected {exp_vout:.3f}V")
            failures += 1

    # vout should be monotonically non-decreasing after reset
    active = data['vout'][t_ns > 10.0]
    diffs = np.diff(active)
    if np.any(diffs < -0.1):
        print("FAIL: vout decreased unexpectedly")
        failures += 1

    if failures == 0:
        print("[CSV] All assertions passed.")
    return failures

if __name__ == '__main__':
    failures = validate_csv()
    print(f"Validation: {failures} failure(s)")
    raise SystemExit(0 if failures == 0 else 1)
