"""Validate clk_burst_gen behavior from CSV output."""
from pathlib import Path

import numpy as np

OUT = Path(__file__).parent.parent.parent / 'output' / 'clk_burst_gen'


def validate_csv(out_dir: Path = OUT) -> int:
    data = np.genfromtxt(out_dir / 'tran.csv', delimiter=',', names=True, dtype=None, encoding='utf-8')
    failures = 0

    # CLK should reach VDD=0.9V
    if data['CLK'].max() < 0.8:
        print("FAIL: CLK never reached VDD")
        failures += 1

    # RST_N should be high for most of simulation
    if data['RST_N'].max() < 0.8:
        print("FAIL: RST_N never went high")
        failures += 1

    # CLK_OUT should be present (max > 0.8)
    if data['CLK_OUT'].max() < 0.8:
        print("FAIL: CLK_OUT never went high")
        failures += 1

    # CLK_OUT high fraction should be ~25% after reset (2/8 cycles × 50% duty)
    active_mask = data['RST_N'] > 0.45
    if active_mask.sum() > 10:
        frac_high = np.mean(data['CLK_OUT'][active_mask] > 0.45)
        if frac_high > 0.5:
            print(f"FAIL: CLK_OUT high fraction={frac_high:.2f}, expected < 0.5 (burst mode)")
            failures += 1

    if failures == 0:
        print("[CSV] All assertions passed.")
    return failures

if __name__ == '__main__':
    failures = validate_csv()
    print(f"Validation: {failures} failure(s)")
    raise SystemExit(0 if failures == 0 else 1)
