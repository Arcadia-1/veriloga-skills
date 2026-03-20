"""Validate d2b_4b: unified static code driver (trim_code=9).

Checks all six encoding buses:
  bin_o    — binary active-high:       9 = 0b1001
  bin_n_o  — binary active-low:        inverted
  onehot_o — one-hot active-high:      only bit 9 high
  onehot_n_o — one-cold active-low:    only bit 9 low
  therm_o  — thermometer active-high:  bits 0..8 high
  therm_n_o — thermometer active-low:  bits 0..8 low

Also verifies the $strobe INIT line.
"""
import re
from pathlib import Path

import numpy as np

OUT = Path(__file__).parent.parent.parent / 'output' / 'd2b_4b'

_TRIM_CODE = 9
_VDD       = 0.9
_THRESH    = _VDD * 0.5   # 0.45 V midpoint


def _high(v: float) -> bool:
    return v > _THRESH


def validate_csv(out_dir: Path = OUT) -> int:
    data = np.genfromtxt(out_dir / 'tran.csv', delimiter=',', names=True, dtype=None, encoding='utf-8')
    last = data[-1]
    failures = 0
    n = _TRIM_CODE  # 9

    # --- bin_o: binary active-high (9 = 0b1001) ---
    bin_cols = [f'bin_o_{i}' for i in range(4)]
    missing = [c for c in bin_cols if c not in list(data.dtype.names)]
    if missing:
        print(f"FAIL: missing columns: {missing}")
        return 1
    for i, col in enumerate(bin_cols):
        expected = (n >> i) & 1
        got = 1 if _high(last[col]) else 0
        if got != expected:
            print(f"FAIL: {col}={last[col]:.3f}V, expected {'high' if expected else 'low'}")
            failures += 1

    # --- bin_n_o: binary active-low (inverted) ---
    bin_n_cols = [f'bin_n_o_{i}' for i in range(4)]
    missing = [c for c in bin_n_cols if c not in list(data.dtype.names)]
    if missing:
        print(f"FAIL: missing columns: {missing}")
        return 1
    for i, col in enumerate(bin_n_cols):
        expected = 1 - ((n >> i) & 1)
        got = 1 if _high(last[col]) else 0
        if got != expected:
            print(f"FAIL: {col}={last[col]:.3f}V, expected {'high' if expected else 'low'}")
            failures += 1

    # --- onehot_o: one-hot active-high (only bit 9 high) ---
    onehot_cols = [f'onehot_o_{i}' for i in range(16)]
    missing = [c for c in onehot_cols if c not in list(data.dtype.names)]
    if missing:
        print(f"FAIL: missing columns: {missing}")
        return 1
    high_bits = [i for i, col in enumerate(onehot_cols) if _high(last[col])]
    if len(high_bits) != 1:
        print(f"FAIL: onehot_o — {len(high_bits)} bits high: {high_bits}, expected exactly 1 (bit {n})")
        failures += 1
    elif high_bits[0] != n:
        print(f"FAIL: onehot_o — high bit={high_bits[0]}, expected {n}")
        failures += 1

    # --- onehot_n_o: one-cold active-low (only bit 9 low) ---
    onehot_n_cols = [f'onehot_n_o_{i}' for i in range(16)]
    missing = [c for c in onehot_n_cols if c not in list(data.dtype.names)]
    if missing:
        print(f"FAIL: missing columns: {missing}")
        return 1
    low_bits = [i for i, col in enumerate(onehot_n_cols) if not _high(last[col])]
    if len(low_bits) != 1:
        print(f"FAIL: onehot_n_o — {len(low_bits)} bits low: {low_bits}, expected exactly 1 (bit {n})")
        failures += 1
    elif low_bits[0] != n:
        print(f"FAIL: onehot_n_o — low bit={low_bits[0]}, expected {n}")
        failures += 1

    # --- therm_o: thermometer active-high (bits 0..8 high) ---
    therm_cols = [f'therm_o_{i}' for i in range(15)]
    missing = [c for c in therm_cols if c not in list(data.dtype.names)]
    if missing:
        print(f"FAIL: missing columns: {missing}")
        return 1
    ones = sum(1 for col in therm_cols if _high(last[col]))
    if ones != n:
        print(f"FAIL: therm_o — {ones} bits high, expected {n}")
        failures += 1
    for i, col in enumerate(therm_cols):
        exp_high = i < n
        is_high = _high(last[col])
        if exp_high != is_high:
            state = 'high' if exp_high else 'low'
            print(f"FAIL: {col}={last[col]:.3f}V, expected {state}")
            failures += 1

    # --- therm_n_o: thermometer active-low (bits 0..8 low) ---
    therm_n_cols = [f'therm_n_o_{i}' for i in range(15)]
    missing = [c for c in therm_n_cols if c not in list(data.dtype.names)]
    if missing:
        print(f"FAIL: missing columns: {missing}")
        return 1
    zeros = sum(1 for col in therm_n_cols if not _high(last[col]))
    if zeros != n:
        print(f"FAIL: therm_n_o — {zeros} bits low, expected {n}")
        failures += 1
    for i, col in enumerate(therm_n_cols):
        exp_low = i < n
        is_low = not _high(last[col])
        if exp_low != is_low:
            state = 'low' if exp_low else 'high'
            print(f"FAIL: {col}={last[col]:.3f}V, expected {state}")
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
    init_lines = [ln for ln in lines if '[d2b_4b] INIT' in ln]
    if init_lines:
        m = re.search(r'trim_code=(\d+)', init_lines[0])
        if m:
            code = int(m.group(1))
            if code != _TRIM_CODE:
                print(f"FAIL: strobe INIT trim_code={code}, expected {_TRIM_CODE}")
                failures += 1
    return failures


if __name__ == '__main__':
    f1 = validate_csv()
    f2 = validate_txt()
    total = f1 + f2
    print(f"Validation: {total} failure(s) [{f1} CSV, {f2} TXT]")
    raise SystemExit(0 if total == 0 else 1)
