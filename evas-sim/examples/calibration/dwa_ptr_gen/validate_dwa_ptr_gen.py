"""Validate dwa_ptr_gen behavior from CSV and strobe output."""
import re
from pathlib import Path

import numpy as np

OUT = Path(__file__).parent.parent.parent / 'output' / 'dwa_ptr_gen' / 'dwa_ptr_gen'


def _parse_strobe_events(out_dir: Path):
    txt_path = out_dir / 'strobe.txt'
    if not txt_path.exists():
        return []
    lines = txt_path.read_text().splitlines()
    pattern = re.compile(
        r'\[dwa_ptr_gen\] t=([0-9.]+) ns \| ptr=\s*(\d+) \| msb=\s*(\d+) \| lsb=\s*(\d+)'
    )
    events = []
    for line in lines:
        m = pattern.search(line)
        if m:
            t_ns = float(m.group(1))
            ptr = int(m.group(2))
            msb = int(m.group(3))
            lsb = int(m.group(4))
            events.append((t_ns, ptr, msb, lsb))
    return events


def validate_csv(out_dir: Path = OUT) -> int:
    data = np.genfromtxt(out_dir / 'tran.csv', delimiter=',', names=True,
                         dtype=None, encoding='utf-8')
    failures = 0

    # CLK should reach VDD
    if data['clk_i'].max() < 0.8:
        print("FAIL: clk_i never reached VDD")
        failures += 1

    # RST deasserted
    if data['rst_ni'].max() < 0.8:
        print("FAIL: rst_ni never went high")
        failures += 1

    # For bus-heavy outputs, validate against strobe events to avoid counting
    # transient transition() edge mixtures as functional failures.
    events = _parse_strobe_events(out_dir)
    if events:
        for t_ns, ptr, msb, lsb in events:
            if not (0 <= ptr <= 15):
                print(f"FAIL: ptr={ptr} out of range [0,15] at t={t_ns}ns")
                failures += 1
        rotation_fails = 0
        for _, ptr, msb, lsb in events:
            expected = (lsb + msb) % 16
            if ptr != expected:
                rotation_fails += 1
        if rotation_fails > 0:
            print(f"FAIL: DWA rotation incorrect in {rotation_fails} cycle(s)")
            failures += 1

    if failures == 0:
        print("[CSV] All assertions passed.")
    return failures


def validate_txt(out_dir: Path = OUT) -> int:
    events = _parse_strobe_events(out_dir)
    failures = 0

    if not events:
        print("WARN: no [dwa_ptr_gen] strobe lines found")
        return 0

    for t_ns, ptr, msb, lsb in events:
        if not (0 <= ptr <= 15):
            print(f"FAIL: ptr={ptr} out of range [0,15] at t={t_ns}ns")
            failures += 1

    # Overlap variant: ptr = (lsb + msb) % 16
    for t_ns, ptr, msb, lsb in events:
        expected = (lsb + msb) % 16
        if ptr != expected:
            print(f"FAIL: at t={t_ns}ns ptr={ptr}, expected (lsb={lsb}+msb={msb})%16={expected}")
            failures += 1

    return failures


if __name__ == '__main__':
    f1 = validate_csv()
    f2 = validate_txt()
    total = f1 + f2
    print(f"Validation: {total} failure(s) [{f1} CSV, {f2} TXT]")
    raise SystemExit(0 if total == 0 else 1)
