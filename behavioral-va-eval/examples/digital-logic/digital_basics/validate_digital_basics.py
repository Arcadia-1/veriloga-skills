"""Validate digital_basics: AND, OR, NOT gates and DFF with synchronous reset.

Truth-table checks for gates; clocked-sequence checks for DFF.
All four circuits are validated against pre-computed expected values.
"""
from pathlib import Path

import numpy as np

BASE = Path(__file__).parent.parent.parent / 'output' / 'digital_basics'
VTH  = 0.4   # VDD/2
VHIGH = 0.8


def _high(v: float) -> bool:
    return v > VTH


def _sample(data, t_ns: float):
    """Return the row closest to t_ns nanoseconds."""
    idx = int(np.argmin(np.abs(data['time'] * 1e9 - t_ns)))
    return data[idx]


# ── AND gate ──────────────────────────────────────────────────────────────────
# States (A,B) = 00→01→10→11, 2 ns each; sample at mid-window (1, 3, 5, 7 ns)
_AND_TRUTH = [
    (1.0, False, False, False),  # A=0 B=0 → out=0
    (3.0, False, True,  False),  # A=0 B=1 → out=0
    (5.0, True,  False, False),  # A=1 B=0 → out=0
    (7.0, True,  True,  True),   # A=1 B=1 → out=1
]

def validate_and(out_dir: Path = BASE / 'and_gate') -> int:
    data = np.genfromtxt(out_dir / 'tran.csv', delimiter=',', names=True, dtype=None, encoding='utf-8')
    failures = 0
    for t_ns, exp_a, exp_b, exp_y in _AND_TRUTH:
        row = _sample(data, t_ns)
        got_y = _high(row['y'])
        if got_y != exp_y:
            print(f"FAIL AND @{t_ns}ns: A={int(exp_a)} B={int(exp_b)} "
                  f"→ y={row['y']:.3f}V, expected {'HIGH' if exp_y else 'LOW'}")
            failures += 1
    if failures == 0:
        print("[AND] All truth-table checks passed.")
    return failures


# ── OR gate ───────────────────────────────────────────────────────────────────
_OR_TRUTH = [
    (1.0, False, False, False),
    (3.0, False, True,  True),
    (5.0, True,  False, True),
    (7.0, True,  True,  True),
]

def validate_or(out_dir: Path = BASE / 'or_gate') -> int:
    data = np.genfromtxt(out_dir / 'tran.csv', delimiter=',', names=True, dtype=None, encoding='utf-8')
    failures = 0
    for t_ns, exp_a, exp_b, exp_y in _OR_TRUTH:
        row = _sample(data, t_ns)
        got_y = _high(row['y'])
        if got_y != exp_y:
            print(f"FAIL OR @{t_ns}ns: A={int(exp_a)} B={int(exp_b)} "
                  f"→ y={row['y']:.3f}V, expected {'HIGH' if exp_y else 'LOW'}")
            failures += 1
    if failures == 0:
        print("[OR] All truth-table checks passed.")
    return failures


# ── NOT gate ──────────────────────────────────────────────────────────────────
# A toggles every 2 ns; sample at 1, 3, 5, 7 ns
_NOT_TRUTH = [
    (1.0, False, True),   # A=0 → out=1
    (3.0, True,  False),  # A=1 → out=0
    (5.0, False, True),
    (7.0, True,  False),
]

def validate_not(out_dir: Path = BASE / 'not_gate') -> int:
    data = np.genfromtxt(out_dir / 'tran.csv', delimiter=',', names=True, dtype=None, encoding='utf-8')
    failures = 0
    for t_ns, exp_a, exp_y in _NOT_TRUTH:
        row = _sample(data, t_ns)
        got_y = _high(row['y'])
        if got_y != exp_y:
            print(f"FAIL NOT @{t_ns}ns: A={int(exp_a)} "
                  f"→ y={row['y']:.3f}V, expected {'HIGH' if exp_y else 'LOW'}")
            failures += 1
    if failures == 0:
        print("[NOT] All inversion checks passed.")
    return failures


# ── DFF ───────────────────────────────────────────────────────────────────────
# CLK rising edges at 0.5, 2.5, 4.5, 6.5, 8.5, 10.5, 12.5, 14.5, 16.5, 18.5 ns
# Sample 0.5 ns after each edge to let output settle.
# (d, rst, expected_q)
_DFF_SEQ = [
    (1.0,  False, False, False),   # edge @0.5n  D=0 RST=0 → Q=0
    (3.0,  False, False, False),   # edge @2.5n  D=0 RST=0 → Q=0
    (5.0,  False, False, False),   # edge @4.5n  D=0 RST=0 → Q=0 (D↑ at 5n)
    (7.0,  True,  False, True),    # edge @6.5n  D=1 RST=0 → Q=1
    (9.0,  True,  True,  False),   # edge @8.5n  D=1 RST=1 → Q=0 (sync reset)
    (11.0, True,  False, True),    # edge @10.5n D=1 RST=0 → Q=1
    (13.0, False, False, False),   # edge @12.5n D=0 RST=0 → Q=0 (D↓ at 11n)
    (17.0, False, False, False),   # edge @16.5n D=0 RST=0 → Q=0 (D↑ at 17n)
    (19.0, True,  False, True),    # edge @18.5n D=1 RST=0 → Q=1
]

def validate_dff(out_dir: Path = BASE / 'dff_rst') -> int:
    data = np.genfromtxt(out_dir / 'tran.csv', delimiter=',', names=True, dtype=None, encoding='utf-8')
    failures = 0
    for t_ns, exp_d, exp_rst, exp_q in _DFF_SEQ:
        row = _sample(data, t_ns)
        got_q    = _high(row['q'])
        got_qbar = _high(row['qbar'])
        if got_q != exp_q:
            print(f"FAIL DFF @{t_ns}ns: D={int(exp_d)} RST={int(exp_rst)} "
                  f"→ q={row['q']:.3f}V, expected {'HIGH' if exp_q else 'LOW'}")
            failures += 1
        # Verify complementary output
        if got_q == got_qbar:
            print(f"FAIL DFF @{t_ns}ns: Q and QB are not complementary "
                  f"(q={row['q']:.3f}V, qbar={row['qbar']:.3f}V)")
            failures += 1
    if failures == 0:
        print("[DFF] All clocked-sequence checks passed.")
    return failures


# ── Main ──────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    f1 = validate_and()
    f2 = validate_or()
    f3 = validate_not()
    f4 = validate_dff()
    total = f1 + f2 + f3 + f4
    print(f"\nValidation: {total} failure(s)  "
          f"[AND={f1}, OR={f2}, NOT={f3}, DFF={f4}]")
    raise SystemExit(0 if total == 0 else 1)
