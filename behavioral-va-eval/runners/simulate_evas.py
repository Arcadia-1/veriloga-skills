#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path


def read_meta(task_dir: Path) -> dict:
    return json.loads((task_dir / "meta.json").read_text(encoding="utf-8"))


def copy_inputs(run_dir: Path, dut_path: Path, tb_path: Path) -> tuple[Path, Path]:
    example_dir = tb_path.parent
    for src in example_dir.iterdir():
        dst = run_dir / src.name
        if src.is_dir():
            shutil.copytree(src, dst)
        else:
            shutil.copy2(src, dst)

    # If the candidate DUT lives outside the example directory, stage it too.
    if dut_path.parent != example_dir:
        shutil.copy2(dut_path, run_dir / dut_path.name)

    dut_dst = run_dir / dut_path.name
    tb_dst = run_dir / tb_path.name
    return dut_dst, tb_dst


def run_evas(run_dir: Path, tb_file: Path, output_dir: Path, timeout_s: int) -> subprocess.CompletedProcess[str]:
    cmd = ["evas", "simulate", tb_file.name, "-o", str(output_dir)]
    return subprocess.run(
        cmd,
        cwd=run_dir,
        capture_output=True,
        text=True,
        timeout=timeout_s,
    )


def load_csv(csv_path: Path) -> list[dict[str, float]]:
    rows: list[dict[str, float]] = []
    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append({k: float(v) for k, v in row.items()})
    return rows


def rising_edges(values: list[float], times: list[float], threshold: float = 0.45) -> list[float]:
    edges: list[float] = []
    for i in range(1, len(values)):
        if values[i - 1] < threshold <= values[i]:
            edges.append(times[i])
    return edges


def decode_bus(rows: list[dict[str, float]], bit_names: list[str], threshold: float = 0.45) -> list[int]:
    decoded: list[int] = []
    for row in rows:
        code = 0
        for bit_name in bit_names:
            bit = 1 if row[bit_name] >= threshold else 0
            m = re.search(r"(\d+)$", bit_name)
            idx = int(m.group(1)) if m else 0
            code |= bit << idx
        decoded.append(code)
    return decoded


def check_clk_div(rows: list[dict[str, float]]) -> tuple[bool, str]:
    if not rows or "clk_in" not in rows[0] or "clk_out" not in rows[0]:
        return False, "missing clk_in/clk_out"
    times = [r["time"] for r in rows]
    in_edges = rising_edges([r["clk_in"] for r in rows], times)
    out_edges = rising_edges([r["clk_out"] for r in rows], times)
    if len(in_edges) < 8 or len(out_edges) < 2:
        return False, "not enough clock edges"
    ratio = len(in_edges) / max(len(out_edges), 1)
    return (3.0 <= ratio <= 5.0), f"edge_ratio={ratio:.2f}"


def check_comparator(rows: list[dict[str, float]]) -> tuple[bool, str]:
    if not rows or not {"vinp", "vinn", "out_p"}.issubset(rows[0]):
        return False, "missing vinp/vinn/out_p"
    before = [r["out_p"] for r in rows if r["time"] < 2e-9]
    after = [r["out_p"] for r in rows if r["time"] >= 2e-9]
    if not before or not after:
        return False, "insufficient time windows"
    delta = abs(sum(before) / len(before) - sum(after) / len(after))
    return (delta > 0.2), f"output_mean_delta={delta:.3f}"


def check_ramp_gen(rows: list[dict[str, float]]) -> tuple[bool, str]:
    bit_names = [f"code_{i}" for i in range(12) if f"code_{i}" in rows[0]]
    if not bit_names:
        return False, "missing code_* bits"
    codes = decode_bus(rows, bit_names)
    nondecreasing = all(codes[i] <= codes[i + 1] for i in range(len(codes) - 1))
    return nondecreasing, f"code_start={codes[0]} code_end={codes[-1]}"


def check_d2b(rows: list[dict[str, float]]) -> tuple[bool, str]:
    if not rows:
        return False, "empty tran.csv"
    if all(k in rows[0] for k in ["bin_o_3", "bin_o_2", "bin_o_1", "bin_o_0"]):
        codes = decode_bus(rows, ["bin_o_0", "bin_o_1", "bin_o_2", "bin_o_3"])
        stable = len(set(codes)) == 1
        return stable and codes[0] == 9, f"stable_code={codes[0]}"
    dout_bits = [k for k in rows[0] if re.fullmatch(r"DOUT[_\[]?\d+\]?", k)]
    vin_col = next((k for k in rows[0] if k.lower().startswith("vin")), None)
    if vin_col and dout_bits:
        codes = decode_bus(rows, dout_bits)
        vins = [r[vin_col] for r in rows]
        pairs = sorted(zip(vins, codes), key=lambda x: x[0])
        monotonic = all(pairs[i][1] <= pairs[i + 1][1] for i in range(len(pairs) - 1))
        return monotonic, "dynamic monotonic code check"
    return False, "missing d2b outputs"


def check_adc_dac_ideal_4b(rows: list[dict[str, float]]) -> tuple[bool, str]:
    if not rows or not {"vin", "vout", "dout_code", "rst_n"}.issubset(rows[0]):
        return False, "missing vin/vout/dout_code/rst_n"
    post = [r for r in rows if r["rst_n"] > 0.45]
    if not post:
        return False, "no post-reset samples"
    codes = [int(round(r["dout_code"])) for r in post]
    vouts = [r["vout"] for r in post]
    unique_codes = len(set(codes))
    monotonic = all(codes[i] <= codes[i + 1] for i in range(len(codes) - 1))
    span = max(vouts) - min(vouts)
    ok = unique_codes >= 8 and monotonic and span > 0.5
    return ok, f"unique_codes={unique_codes} vout_span={span:.3f}"


def check_dac_binary_clk_4b(rows: list[dict[str, float]]) -> tuple[bool, str]:
    if not rows or not {"din3", "din2", "din1", "din0", "aout"}.issubset(rows[0]):
        return False, "missing din*/aout"
    levels: dict[int, list[float]] = {}
    for r in rows:
        code = (
            (1 if r["din3"] > 0.45 else 0) * 8
            + (1 if r["din2"] > 0.45 else 0) * 4
            + (1 if r["din1"] > 0.45 else 0) * 2
            + (1 if r["din0"] > 0.45 else 0)
        )
        levels.setdefault(code, []).append(r["aout"])
    medians = {c: sum(vs) / len(vs) for c, vs in levels.items()}
    sorted_codes = sorted(medians)
    monotonic = all(medians[sorted_codes[i]] <= medians[sorted_codes[i + 1]] + 1e-9 for i in range(len(sorted_codes) - 1))
    span = medians[sorted_codes[-1]] - medians[sorted_codes[0]] if sorted_codes else 0.0
    ok = len(sorted_codes) >= 14 and monotonic and span > 0.7
    return ok, f"levels={len(sorted_codes)} aout_span={span:.3f}"


def check_dac_therm_16b(rows: list[dict[str, float]]) -> tuple[bool, str]:
    bit_names = [f"d{i}" for i in range(16) if f"d{i}" in rows[0]]
    if not rows or not bit_names or "vout" not in rows[0]:
        return False, "missing d*/vout"
    ones_counts = [sum(1 for b in bit_names if r[b] > 0.45) for r in rows]
    vouts = [r["vout"] for r in rows]
    max_ones = max(ones_counts)
    max_vout = max(vouts)
    last_pairs: dict[int, float] = {}
    for ones, vout in zip(ones_counts, vouts):
        last_pairs[ones] = vout
    sorted_ones = sorted(last_pairs)
    monotonic = all(last_pairs[sorted_ones[i]] <= last_pairs[sorted_ones[i + 1]] + 1e-9 for i in range(len(sorted_ones) - 1))
    ok = max_ones == 16 and max_vout > 15.0 and monotonic
    return ok, f"max_ones={max_ones} max_vout={max_vout:.3f}"


def check_sar_adc_dac_weighted_8b(rows: list[dict[str, float]]) -> tuple[bool, str]:
    if not rows or not {"vin", "vin_sh", "vout", "dout_code", "rst_n"}.issubset(rows[0]):
        return False, "missing vin/vin_sh/vout/dout_code/rst_n"
    post = [r for r in rows if r["rst_n"] > 0.45]
    if not post:
        return False, "no post-reset samples"
    codes = [int(round(r["dout_code"])) for r in post]
    vinsh = [r["vin_sh"] for r in post]
    vouts = [r["vout"] for r in post]
    unique_codes = len(set(codes))
    avg_abs_err = sum(abs(a - b) for a, b in zip(vinsh, vouts)) / len(post)
    ok = unique_codes >= 64 and max(vouts) - min(vouts) > 0.5 and avg_abs_err < 0.12
    return ok, f"unique_codes={unique_codes} avg_abs_err={avg_abs_err:.4f}"


def check_not_gate(rows: list[dict[str, float]]) -> tuple[bool, str]:
    if not rows or not {"a", "y"}.issubset(rows[0]):
        return False, "missing a/y"
    good = 0
    for r in rows:
        if (r["a"] > 0.4) != (r["y"] > 0.4):
            good += 1
    frac = good / len(rows)
    return frac > 0.9, f"invert_match_frac={frac:.3f}"


def check_lfsr(rows: list[dict[str, float]]) -> tuple[bool, str]:
    if not rows or not {"dpn", "rstb"}.issubset(rows[0]):
        return False, "missing dpn/rstb"
    post = [r["dpn"] for r in rows if r["rstb"] > 0.45]
    if len(post) < 2:
        return False, "not enough post-reset samples"
    binary = [1 if v > 0.45 else 0 for v in post]
    hi_frac = sum(binary) / len(binary)
    transitions = sum(1 for i in range(len(binary) - 1) if binary[i] != binary[i + 1])
    ok = 0.05 < hi_frac < 0.95 and transitions >= 10
    return ok, f"transitions={transitions} hi_frac={hi_frac:.3f}"


def check_dwa_ptr_gen(rows: list[dict[str, float]]) -> tuple[bool, str]:
    if not rows or not {"clk_i", "rst_ni", "cell_en_code", "ptr_code"}.issubset(rows[0]):
        return False, "missing clk_i/rst_ni/cell_en_code/ptr_code"
    post = [r for r in rows if r["rst_ni"] > 0.45]
    if not post:
        return False, "no post-reset samples"
    ptr_codes = [int(round(r["ptr_code"])) for r in post]
    cell_codes = [int(round(r["cell_en_code"])) for r in post]
    ptr_nonzero = all(v > 0 for v in ptr_codes)
    ptr_unique = len(set(ptr_codes))
    cell_active = max(cell_codes) > 0
    ok = ptr_nonzero and cell_active and ptr_unique >= 4
    return ok, f"ptr_unique={ptr_unique} max_cell_code={max(cell_codes)}"


def check_clk_burst_gen(rows: list[dict[str, float]]) -> tuple[bool, str]:
    if not rows or not {"CLK", "RST_N", "CLK_OUT"}.issubset(rows[0]):
        return False, "missing CLK/RST_N/CLK_OUT"
    post = [r for r in rows if r["RST_N"] > 0.45]
    if not post:
        return False, "no post-reset samples"
    clk_out = [r["CLK_OUT"] for r in post]
    times = [r["time"] for r in post]
    hi_frac = sum(1 for v in clk_out if v > 0.45) / len(clk_out)
    edges = rising_edges(clk_out, times)
    ok = 0.05 < hi_frac < 0.4 and len(edges) >= 4
    return ok, f"clk_out_hi_frac={hi_frac:.3f} rising_edges={len(edges)}"


def check_noise_gen(rows: list[dict[str, float]]) -> tuple[bool, str]:
    if not rows or not {"vin_i", "vout_o"}.issubset(rows[0]):
        return False, "missing vin_i/vout_o"
    noises = [r["vout_o"] - r["vin_i"] for r in rows]
    mean = sum(noises) / len(noises)
    var = sum((x - mean) ** 2 for x in noises) / len(noises)
    std = var ** 0.5
    ok = std > 0.01 and max(abs(x) for x in noises) > 0.05
    return ok, f"noise_std={std:.4f}"


def check_gain_extraction(rows: list[dict[str, float]]) -> tuple[bool, str]:
    if not rows or not {"vinp", "vinn", "vamp_p", "vamp_n"}.issubset(rows[0]):
        return False, "missing vinp/vinn/vamp_p/vamp_n"
    vin_diff = [r["vinp"] - r["vinn"] for r in rows]
    vamp_diff = [r["vamp_p"] - r["vamp_n"] for r in rows]
    mean_in = sum(vin_diff) / len(vin_diff)
    mean_out = sum(vamp_diff) / len(vamp_diff)
    std_in = (sum((x - mean_in) ** 2 for x in vin_diff) / len(vin_diff)) ** 0.5
    std_out = (sum((x - mean_out) ** 2 for x in vamp_diff) / len(vamp_diff)) ** 0.5
    gain = std_out / std_in if std_in > 1e-12 else 0.0
    ok = gain > 4.0 and std_out > std_in
    return ok, f"diff_gain={gain:.2f}"


CHECKS = {
    "adc_dac_ideal_4b": check_adc_dac_ideal_4b,
    "clk_burst_gen": check_clk_burst_gen,
    "clk_div_smoke": check_clk_div,
    "comparator_smoke": check_comparator,
    "dac_binary_clk_4b": check_dac_binary_clk_4b,
    "dac_therm_16b": check_dac_therm_16b,
    "ramp_gen_smoke": check_ramp_gen,
    "d2b_4bit_smoke": check_d2b,
    "digital_basics": check_not_gate,
    "dwa_ptr_gen": check_dwa_ptr_gen,
    "gain_extraction": check_gain_extraction,
    "lfsr": check_lfsr,
    "noise_gen": check_noise_gen,
    "sar_adc_dac_weighted_8b": check_sar_adc_dac_weighted_8b,
}


def has_behavior_check(task_id: str) -> bool:
    return task_id in CHECKS


def evaluate_behavior(task_id: str, csv_path: Path) -> tuple[float, list[str]]:
    if task_id not in CHECKS:
        return 0.0, [f"no behavior check implemented for {task_id}"]
    rows = load_csv(csv_path)
    ok, note = CHECKS[task_id](rows)
    return (1.0 if ok else 0.0), [note]


def run_case(
    task_dir: Path,
    dut_path: Path,
    tb_path: Path,
    *,
    output_root: Path | None = None,
    keep_run_dir: bool = False,
    timeout_s: int = 120,
    task_id_override: str | None = None,
) -> dict:
    meta = read_meta(task_dir)
    task_id = task_id_override or meta["id"]

    temp_ctx = tempfile.TemporaryDirectory(prefix=f"{task_id}_")
    run_dir = Path(temp_ctx.name)
    out_dir = output_root.resolve() if output_root else run_dir / "output"
    out_dir.mkdir(parents=True, exist_ok=True)

    try:
        dut_dst, tb_dst = copy_inputs(run_dir, dut_path, tb_path)
        proc = run_evas(run_dir, tb_dst, out_dir, timeout_s)
        combined = (proc.stdout or "") + "\n" + (proc.stderr or "")

        dut_compile = 1.0 if "Compiled Verilog-A module:" in combined else 0.0
        tb_compile = 1.0 if ("Transient Analysis" in combined or (out_dir / "tran.csv").exists()) else 0.0

        notes = [f"returncode={proc.returncode}"]
        if dut_compile == 0.0:
            notes.append("dut_not_compiled")
        if tb_compile == 0.0:
            notes.append("tb_not_executed")

        csv_path = out_dir / "tran.csv"
        if proc.returncode == 0 and csv_path.exists():
            sim_correct, behavior_notes = evaluate_behavior(task_id, csv_path)
            notes.extend(behavior_notes)
        else:
            sim_correct = 0.0
            notes.append("tran.csv missing")

        weighted_total = round((dut_compile + tb_compile + sim_correct) / 3.0, 4)

        if dut_compile < 1.0:
            status = "FAIL_DUT_COMPILE"
        elif tb_compile < 1.0:
            status = "FAIL_TB_COMPILE"
        elif sim_correct < 1.0:
            status = "FAIL_SIM_CORRECTNESS"
        else:
            status = "PASS"

        return {
            "task_id": task_id,
            "status": status,
            "backend_used": "evas",
            "scores": {
                "dut_compile": dut_compile,
                "tb_compile": tb_compile,
                "sim_correct": sim_correct,
                "weighted_total": weighted_total,
            },
            "artifacts": [
                str(dut_dst),
                str(tb_dst),
                str(out_dir / "tran.csv"),
                str(out_dir / "strobe.txt"),
            ],
            "notes": notes,
            "stdout_tail": combined[-4000:],
        }
    finally:
        if not keep_run_dir:
            temp_ctx.cleanup()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("task_dir")
    ap.add_argument("dut")
    ap.add_argument("tb")
    ap.add_argument("--output-root", default=None)
    ap.add_argument("--keep-run-dir", action="store_true")
    ap.add_argument("--timeout-s", type=int, default=120)
    ap.add_argument("--task-id", default=None)
    args = ap.parse_args()

    task_dir = Path(args.task_dir).resolve()
    dut_path = Path(args.dut).resolve()
    tb_path = Path(args.tb).resolve()
    output_root = Path(args.output_root).resolve() if args.output_root else None
    result = run_case(
        task_dir,
        dut_path,
        tb_path,
        output_root=output_root,
        keep_run_dir=args.keep_run_dir,
        timeout_s=args.timeout_s,
        task_id_override=args.task_id,
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
