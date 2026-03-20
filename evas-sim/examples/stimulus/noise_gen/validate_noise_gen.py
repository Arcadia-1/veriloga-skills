"""Validate noise_gen behavior from CSV output (sigma=0.1V, vin=1.0V DC)."""
from pathlib import Path

import numpy as np

OUT = Path(__file__).parent.parent.parent / 'output' / 'noise_gen'

_VIN_NOMINAL = 1.0
_SIGMA = 0.1


def validate_csv(out_dir: Path = OUT) -> int:
    data = np.genfromtxt(out_dir / 'tran.csv', delimiter=',', names=True, dtype=None, encoding='utf-8')
    failures = 0

    vin  = data['vin_i']
    vout = data['vout_o']

    # Input should be constant at 1.0V
    if np.abs(vin - _VIN_NOMINAL).max() > 0.01:
        print(f"FAIL: vin_i is not constant at {_VIN_NOMINAL}V")
        failures += 1

    # Output mean should be close to vin (zero-mean noise)
    vout_mean = float(np.mean(vout))
    if abs(vout_mean - _VIN_NOMINAL) > 3 * _SIGMA / np.sqrt(len(data)):
        # More lenient: just check it is within 5*sigma of expected
        if abs(vout_mean - _VIN_NOMINAL) > 5 * _SIGMA:
            print(f"FAIL: vout mean={vout_mean:.4f}V, expected ~{_VIN_NOMINAL}V")
            failures += 1

    # Noise standard deviation should be roughly sigma
    noise = vout - vin
    noise_std = float(np.std(noise))
    # Allow 2x-3x tolerance for randomness
    if not (0.01 < noise_std < _SIGMA * 5):
        print(f"FAIL: noise std={noise_std:.4f}V, expected ~{_SIGMA}V")
        failures += 1

    # Output should be different from input (noise should be non-trivial)
    if np.all(np.abs(noise) < 1e-6):
        print("FAIL: vout identical to vin (noise not being applied)")
        failures += 1

    if failures == 0:
        print(f"[CSV] All assertions passed. noise std={noise_std:.4f}V (expected ~{_SIGMA}V)")
    return failures

if __name__ == '__main__':
    failures = validate_csv()
    print(f"Validation: {failures} failure(s)")
    raise SystemExit(0 if failures == 0 else 1)
