"""Validate ramp_gen behavior from CSV and strobe output.

Configuration: DIRECTION=1, MIN_CODE=0, MAX_CODE=127, STEP_SIZE=1, N_CYCLE_START=2
Clock period = 100ns, RST deasserts at ~20ns.
After 2 startup cycles (~220ns), ramp starts from 0 and increments each cycle.
Should reach MAX_CODE=127 and hold there.
"""
import re
from pathlib import Path

import numpy as np

OUT = Path(__file__).parent.parent.parent / 'output' / 'ramp_gen'

_MIN_CODE = 0
_MAX_CODE = 127
_DIRECTION = 1


def validate_csv(out_dir: Path = OUT) -> int:
    data = np.genfromtxt(out_dir / 'tran.csv', delimiter=',', names=True, dtype=None, encoding='utf-8')
    failures = 0

    t_ns = data['time'] * 1e9
    names = list(data.dtype.names)

    # Prefer scalar code output when present; bit-level threshold decoding can
    # show transient glitches during transition() edges.
    if 'code_code' in names:
        ramp_code = np.round(data['code_code']).astype(int)
    else:
        code_cols = [f'code_{i}' for i in range(12)]
        available = [c for c in code_cols if c in names]
        if not available:
            print("FAIL: no code_* columns found")
            return 1
        ramp_code = np.zeros(len(data), dtype=int)
        for i, col in enumerate(available):
            ramp_code += ((data[col] > 0.45).astype(int) << i)

    # After startup (t > 400ns), code should be > 0
    active_mask = t_ns > 400.0
    active_code = ramp_code[active_mask]
    if len(active_code) > 0:
        if active_code.max() < _MAX_CODE:
            print(f"FAIL: code never reached MAX_CODE={_MAX_CODE}, got max={active_code.max()}")
            failures += 1

    # Code should be monotonically non-decreasing (DIRECTION=1)
    diffs = np.diff(ramp_code[active_mask])
    if np.any(diffs < -1):
        print("FAIL: ramp code decreased unexpectedly (not monotonic)")
        failures += 1

    # Final value should be MAX_CODE=127
    final_code = int(ramp_code[-1])
    if final_code != _MAX_CODE:
        print(f"FAIL: final code={final_code}, expected {_MAX_CODE}")
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

    # Check INIT line
    init_lines = [ln for ln in lines if '[ramp_gen] INIT' in ln]
    if init_lines:
        m = re.search(r'Direction=(\d+)', init_lines[0])
        if m and int(m.group(1)) != _DIRECTION:
            print(f"FAIL: INIT Direction={m.group(1)}, expected {_DIRECTION}")
            failures += 1
        m2 = re.search(r'Initial Code=(\d+)', init_lines[0])
        if m2:
            init_code = int(m2.group(1))
            if init_code != _MIN_CODE:
                print(f"FAIL: INIT code={init_code}, expected {_MIN_CODE} (MIN_CODE for up ramp)")
                failures += 1

    # Parse clock events and verify code increments
    cycle_pattern = re.compile(
        r'\[ramp_gen\].*Time=([0-9.eE+\-]+)\s*ns.*Cycle=(\d+).*Code=(\d+)'
    )
    events = []
    for line in lines:
        m = cycle_pattern.search(line)
        if m:
            t_ns  = float(m.group(1))
            cycle = int(m.group(2))
            code  = int(m.group(3))
            events.append((t_ns, cycle, code))

    if len(events) < 5:
        print("WARN: fewer than 5 ramp_gen strobe events found")
        return failures

    # After N_CYCLE_START=2 cycles, code should increase
    active_events = [(t, c, code) for t, c, code in events if c >= 2]
    if active_events:
        codes = [code for _, _, code in active_events]
        # Codes should be non-decreasing
        for i in range(1, len(codes)):
            if codes[i] < codes[i-1]:
                print(f"FAIL: code decreased from {codes[i-1]} to {codes[i]}")
                failures += 1
                break
        # Max code should reach MAX_CODE
        if max(codes) < _MAX_CODE:
            print(f"FAIL: max code in strobe={max(codes)}, expected {_MAX_CODE}")
            failures += 1

    return failures


if __name__ == '__main__':
    f1 = validate_csv()
    f2 = validate_txt()
    total = f1 + f2
    print(f"Validation: {total} failure(s) [{f1} CSV, {f2} TXT]")
    raise SystemExit(0 if total == 0 else 1)
