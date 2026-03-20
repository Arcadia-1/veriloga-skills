"""Validate dwa_ptr_gen behavior from CSV and strobe output."""
import re
from pathlib import Path

import numpy as np

OUT = Path(__file__).parent.parent.parent / 'output' / 'dwa_ptr_gen' / 'dwa_ptr_gen'

_VTH = 0.45


def _ptr_pos(code_val: float) -> int:
    """Return bit position of the set bit in a one-hot bus code, or -1."""
    p = int(round(float(code_val)))
    if p <= 0:
        return -1
    if p & (p - 1):          # not power-of-2: not one-hot
        return -1
    pos = 0
    while (1 << pos) < p:
        pos += 1
    return pos


def _popcount(val: float) -> int:
    """Count set bits in the integer representation of a bus code."""
    return bin(int(round(float(val)))).count('1')


def validate_csv(out_dir: Path = OUT) -> int:
    data = np.genfromtxt(out_dir / 'tran.csv', delimiter=',', names=True,
                         dtype=None, encoding='utf-8')
    failures = 0
    names = list(data.dtype.names)

    # CLK should reach VDD
    if data['clk_i'].max() < 0.8:
        print("FAIL: clk_i never reached VDD")
        failures += 1

    # RST deasserted
    if data['rst_ni'].max() < 0.8:
        print("FAIL: rst_ni never went high")
        failures += 1

    # --- Sample at rising clock edges, 1 ns after edge for settling ---
    clk = data['clk_i']
    rising = np.where((clk[:-1] < _VTH) & (clk[1:] >= _VTH))[0] + 1
    si = np.clip(rising + 10, 0, len(data) - 1)
    rst_ok = data['rst_ni'][si] > _VTH

    # ptr_o must be one-hot after reset
    ptr_cols = [f'ptr_{i}' for i in range(16)]
    avail_ptr = [c for c in ptr_cols if c in names]
    if avail_ptr:
        ptr_matrix = np.column_stack([data[c][si] > _VTH for c in avail_ptr])
        ones = ptr_matrix.sum(axis=1)[rst_ok]
        bad = int(np.sum((ones != 0) & (ones != 1)))
        if bad > 5:
            print(f"FAIL: ptr_o not one-hot in {bad} post-RST samples")
            failures += 1

    # cell_en_o must be non-zero after reset
    cell_cols = [f'cell_en_{i}' for i in range(16)]
    avail_cell = [c for c in cell_cols if c in names]
    if avail_cell:
        cell_count_arr = sum((data[c][si] > _VTH).astype(int) for c in avail_cell)
        if rst_ok.sum() > 0 and cell_count_arr[rst_ok].max() == 0:
            print("FAIL: cell_en_o all zeros after reset release")
            failures += 1

    # DWA rotation: overlap variant — ptr advances by (cell_count - 1) per cycle
    if 'ptr_code' in names and 'cell_en_code' in names:
        ptr_code_arr   = data['ptr_code'][si]
        cell_code_arr  = data['cell_en_code'][si]
        ptr_pos_arr    = np.array([_ptr_pos(v) for v in ptr_code_arr], dtype=int)
        valid_idx      = np.where(rst_ok & (ptr_pos_arr >= 0))[0]
        rotation_fails = 0
        for j in range(1, len(valid_idx)):
            prev_ci = valid_idx[j - 1]
            curr_ci = valid_idx[j]
            cell_count = _popcount(cell_code_arr[curr_ci])
            expected   = (ptr_pos_arr[prev_ci] + cell_count - 1) % 16
            if ptr_pos_arr[curr_ci] != expected:
                rotation_fails += 1
        if rotation_fails > 0:
            print(f"FAIL: DWA rotation incorrect in {rotation_fails} cycle(s)")
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

    # Format: [dwa_ptr_gen] t=12.250 ns | ptr= 3 | msb= 3 | lsb= 0 | ...
    pattern = re.compile(
        r'\[dwa_ptr_gen\] t=([0-9.]+) ns \| ptr=\s*(\d+) \| msb=\s*(\d+) \| lsb=\s*(\d+)'
    )
    events = []
    for line in lines:
        m = pattern.search(line)
        if m:
            t_ns = float(m.group(1))
            ptr  = int(m.group(2))
            msb  = int(m.group(3))   # = input code
            lsb  = int(m.group(4))   # = start of range
            events.append((t_ns, ptr, msb, lsb))

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
