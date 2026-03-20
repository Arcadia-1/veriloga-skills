"""Validate clk_div behavior from CSV output."""
from pathlib import Path

import numpy as np

OUT = Path(__file__).parent.parent.parent / 'output' / 'clk_div'


def validate_csv(out_dir: Path = OUT) -> int:
    # analyze_clk_div now writes ratio=4 results into the 'div4' subdirectory
    csv_path = out_dir / 'div4' / 'tran.csv'
    if not csv_path.exists():
        # fall back to legacy flat layout
        csv_path = out_dir / 'tran.csv'
    data = np.genfromtxt(csv_path, delimiter=',', names=True, dtype=None, encoding='utf-8')
    failures = 0

    t = data['time']
    clk_in  = data['clk_in']
    clk_out = data['clk_out']

    # Both signals should reach VDD=0.9V
    if clk_in.max() < 0.8:
        print("FAIL: clk_in never reached VDD")
        failures += 1
    if clk_out.max() < 0.8:
        print("FAIL: clk_out never reached VDD")
        failures += 1

    # Measure input rising edges
    def count_rising_edges(sig, thresh=0.45):
        above = sig > thresh
        return int(np.sum(np.diff(above.astype(int)) > 0))

    n_in  = count_rising_edges(clk_in)
    n_out = count_rising_edges(clk_out)

    if n_in == 0:
        print("FAIL: no rising edges on clk_in")
        failures += 1
    else:
        # With ratio=4, n_out should be ~n_in/4
        expected_ratio = n_in / max(n_out, 1)
        if abs(expected_ratio - 4.0) > 1.0:
            print(f"FAIL: edge ratio clk_in/clk_out={expected_ratio:.2f}, expected ~4.0")
            failures += 1

    # clk_out should have ~50% duty cycle (for even ratio=4)
    active_out = clk_out[t > 200e-9]
    if len(active_out) > 0:
        duty = np.mean(active_out > 0.45)
        if abs(duty - 0.5) > 0.1:
            print(f"FAIL: clk_out duty cycle={duty:.2f}, expected ~0.50")
            failures += 1

    if failures == 0:
        print("[CSV] All assertions passed.")
    return failures

if __name__ == '__main__':
    failures = validate_csv()
    print(f"Validation: {failures} failure(s)")
    raise SystemExit(0 if failures == 0 else 1)
