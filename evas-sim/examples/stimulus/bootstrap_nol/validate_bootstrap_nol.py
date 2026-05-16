"""Validate bootstrap_nol behavior from CSV output."""
from pathlib import Path

import numpy as np

OUT = Path(__file__).parent.parent.parent / "output" / "bootstrap_nol"
VTH = 0.45
TNOL_S = 200e-12
TNOL_TOL_S = 60e-12


def contiguous_segments(mask: np.ndarray) -> list[tuple[int, int]]:
    idx = np.flatnonzero(mask)
    if idx.size == 0:
        return []
    breaks = np.where(np.diff(idx) > 1)[0]
    starts = np.concatenate(([0], breaks + 1))
    ends = np.concatenate((breaks, [idx.size - 1]))
    return [(int(idx[s]), int(idx[e])) for s, e in zip(starts, ends)]


def validate_csv(out_dir: Path = OUT) -> int:
    data = np.genfromtxt(out_dir / "tran.csv", delimiter=",", names=True, dtype=None, encoding="utf-8")
    failures = 0

    for sig in ["CLKD", "RST_N", "GATE", "GATE_B", "EN_DAC"]:
        if sig not in data.dtype.names:
            print(f"FAIL: missing signal {sig} in tran.csv")
            return 1

    if data["CLKD"].max() < 0.8:
        print("FAIL: CLKD never reached VDD")
        failures += 1
    if data["RST_N"].max() < 0.8:
        print("FAIL: RST_N never went high")
        failures += 1

    active = data["RST_N"] > VTH
    if active.sum() == 0:
        print("FAIL: no active window after reset release")
        return failures + 1

    for sig in ["GATE", "GATE_B", "EN_DAC"]:
        vals = data[sig][active]
        if vals.max() < 0.8 or vals.min() > 0.1:
            print(f"FAIL: {sig} did not toggle across the active window")
            failures += 1

    if np.any((data["GATE"][active] > VTH) & (data["GATE_B"][active] > VTH)):
        print("FAIL: GATE and GATE_B overlap high")
        failures += 1

    if np.max(np.abs(data["EN_DAC"][active] - data["GATE_B"][active])) > 0.2:
        print("FAIL: EN_DAC does not follow GATE_B when en_dac_on_hold=1")
        failures += 1

    both_low = active & (data["GATE"] < VTH) & (data["GATE_B"] < VTH)
    segments = contiguous_segments(both_low)
    widths = []
    time = data["time"]
    for start, end in segments:
        width = time[end] - time[start]
        if width > 50e-12:
            widths.append(width)

    if len(widths) < 2:
        print("FAIL: did not observe repeated both-low non-overlap windows")
        failures += 1
    else:
        if not any(abs(width - TNOL_S) <= TNOL_TOL_S for width in widths):
            widths_ps = ", ".join(f"{width * 1e12:.1f}" for width in widths[:6])
            print(f"FAIL: both-low window widths [{widths_ps}] ps did not match t_nol approx 200 ps")
            failures += 1

    if failures == 0:
        print("[CSV] All assertions passed.")
    return failures


if __name__ == "__main__":
    failures = validate_csv()
    print(f"Validation: {failures} failure(s)")
    raise SystemExit(0 if failures == 0 else 1)
