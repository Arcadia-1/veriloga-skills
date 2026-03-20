"""Validate dwa_ptr_gen_no_overlap: DWA (no overlap)."""
from pathlib import Path

import numpy as np

OUT = Path(__file__).parent.parent.parent / 'output' / 'dwa_ptr_gen' / 'dwa_ptr_gen_no_overlap'


def validate_csv(out_dir: Path = OUT) -> int:
    data = np.genfromtxt(out_dir / 'tran.csv', delimiter=',', names=True,
                         dtype=None, encoding='utf-8')
    failures = 0

    if data['clk_i'].max() < 0.8:
        print("FAIL: clk_i never reached VDD")
        failures += 1

    if data['rst_ni'].max() < 0.8:
        print("FAIL: rst_ni never went high")
        failures += 1

    # ptr_o must be one-hot after reset
    ptr_cols = [c for c in [f'ptr_{i}' for i in range(16)]
                if c in list(data.dtype.names)]
    if ptr_cols:
        ptr_matrix = np.column_stack([data[c] > 0.45 for c in ptr_cols])
        ones_per_row = ptr_matrix.sum(axis=1)
        active = data['time'] * 1e9 > 100.0
        if active.sum() > 0:
            bad = np.sum((ones_per_row[active] != 0) & (ones_per_row[active] != 1))
            if bad > 5:
                print(f"FAIL: ptr_o not one-hot in {bad} samples")
                failures += 1

    # cell_en must be active (> 0 cells) after reset
    cell_cols = [c for c in [f'cell_en_{i}' for i in range(16)]
                 if c in list(data.dtype.names)]
    if cell_cols:
        cell_count = sum((data[c] > 0.45).astype(int) for c in cell_cols)
        active_count = cell_count[data['time'] * 1e9 > 100.0]
        if len(active_count) > 0 and active_count.max() == 0:
            print("FAIL: cell_en_o all zeros after reset release")
            failures += 1

    # No-overlap check: consecutive cycles must NOT share the same cell
    # Sample at rising edges (approx every 100ns after reset)
    clk = data['clk_i']
    rising = np.where((clk[:-1] < 0.45) & (clk[1:] >= 0.45))[0] + 1
    si     = np.clip(rising + 10, 0, len(data) - 1)
    rst_ok = data['rst_ni'][si] > 0.45

    cell_mat = np.zeros((16, len(si)), dtype=int)
    for b in range(16):
        col = f'cell_en_{b}'
        if col in list(data.dtype.names):
            cell_mat[b] = (data[col][si] > 0.45).astype(int)

    valid = np.where(rst_ok)[0]
    for vi in range(1, len(valid)):
        prev, cur = valid[vi - 1], valid[vi]
        overlap = int((cell_mat[:, prev] & cell_mat[:, cur]).sum())
        if overlap > 0:
            print(f"FAIL: overlap of {overlap} cell(s) between cycle {prev} and {cur}")
            failures += 1

    if failures == 0:
        print("[CSV] All assertions passed.")
    return failures


if __name__ == '__main__':
    f = validate_csv()
    print(f"Validation: {f} failure(s)")
    raise SystemExit(0 if f == 0 else 1)
