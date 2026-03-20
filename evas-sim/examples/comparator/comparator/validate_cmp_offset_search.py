"""Validate cmp_offset_search behavior from CSV and strobe output."""
import re
from pathlib import Path

import numpy as np

OUT = Path(__file__).parent.parent.parent / 'output' / 'comparator' / 'cmp_offset_search'


def validate_csv(out_dir: Path = OUT) -> int:
    data = np.genfromtxt(out_dir / 'tran.csv', delimiter=',', names=True, dtype=None, encoding='utf-8')
    failures = 0

    # CLK should reach 0.8V
    if data['CLK'].max() < 0.7:
        print("FAIL: CLK never reached VDD")
        failures += 1

    # VINP and VINN should exist and be near VCM=0.4V
    for sig in ['vinp_node', 'vinn_node']:
        mean_v = data[sig].mean()
        if abs(mean_v - 0.4) > 0.15:
            print(f"FAIL: {sig} mean={mean_v:.3f}V, expected near 0.4V (VCM)")
            failures += 1

    # After convergence (last 20% of simulation), differential should converge
    # toward the comparator offset (~10mV for this testbench)
    t = data['time']
    late_mask = t > t[-1] * 0.7
    if late_mask.sum() > 5:
        vdiff_late = (data['vinp_node'][late_mask] - data['vinn_node'][late_mask]) * 1e3
        final_diff = float(np.mean(vdiff_late))
        # Should converge to ~10mV offset; allow ±20mV tolerance
        if abs(final_diff - 10.0) > 20.0:
            print(f"FAIL: final VINP-VINN={final_diff:.1f}mV, expected ~10mV (offset)")
            failures += 1

    if failures == 0:
        print("[CSV] All assertions passed.")
    return failures


def validate_txt(out_dir: Path = OUT) -> int:
    txt_path = out_dir / 'strobe.txt'
    if not txt_path.exists():
        return 0
    lines = txt_path.read_text().splitlines()
    failures = 0
    pattern = re.compile(
        r'\[cmp_strongarm\].*Time=([0-9.eE+\-]+)\s*ns.*decision=(\d+)'
    )
    decisions = []
    for line in lines:
        m = pattern.search(line)
        if m:
            decisions.append(int(m.group(2)))

    if len(decisions) == 0:
        print("WARN: no [cmp_strongarm] strobe lines found")
        return 0

    # After binary search, decisions should stabilize
    # Last 5 decisions should all be the same (converged)
    if len(decisions) >= 5:
        last = decisions[-5:]
        if len(set(last)) > 1:
            print(f"FAIL: comparator decisions did not stabilize: last 5 = {last}")
            failures += 1

    return failures


if __name__ == '__main__':
    f1 = validate_csv()
    f2 = validate_txt()
    total = f1 + f2
    print(f"Validation: {total} failure(s) [{f1} CSV, {f2} TXT]")
    raise SystemExit(0 if total == 0 else 1)
