#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from simulate_evas import has_behavior_check, run_case


TASK_BY_EXAMPLE = {
    "clk_div": "clk_div_smoke",
    "comparator": "comparator_smoke",
    "ramp_gen": "ramp_gen_smoke",
    "d2b_4b": "d2b_4bit_smoke",
}


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def benchmark_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_manifest() -> list[dict]:
    manifest_path = benchmark_root() / "examples" / "manifest.json"
    return json.loads(manifest_path.read_text(encoding="utf-8"))


def first_ahdl_include(tb_path: Path) -> str | None:
    text = tb_path.read_text(encoding="utf-8")
    match = re.search(r'^\s*ahdl_include\s+"([^"]+)"', text, flags=re.MULTILINE)
    return match.group(1) if match else None


def task_dir_for(example_name: str) -> Path:
    task_id = TASK_BY_EXAMPLE.get(example_name, "clk_div_smoke")
    return benchmark_root() / "tasks" / "end-to-end" / "voltage" / task_id


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output-root", default="behavioral-va-eval/results/examples-suite")
    ap.add_argument("--timeout-s", type=int, default=180)
    args = ap.parse_args()

    root = repo_root()
    suite_output = (root / args.output_root).resolve()
    suite_output.mkdir(parents=True, exist_ok=True)

    results = []
    for item in load_manifest():
        example_dir = (root / item["path"]).resolve()
        tb_path = example_dir / item["default_testbench"]
        dut_name = first_ahdl_include(tb_path)
        if not dut_name:
            results.append(
                {
                    "example": item["name"],
                    "status": "FAIL_INFRA",
                    "notes": ["no ahdl_include found in default testbench"],
                }
            )
            continue

        dut_path = example_dir / dut_name
        result = run_case(
            task_dir_for(item["name"]),
            dut_path,
            tb_path,
            output_root=suite_output / item["name"],
            timeout_s=args.timeout_s,
            task_id_override=TASK_BY_EXAMPLE.get(item["name"], item["name"]),
        )
        result["example"] = item["name"]
        result["example_dir"] = str(example_dir)
        result["behavior_check_available"] = has_behavior_check(result["task_id"])
        result["smoke_status"] = (
            "PASS"
            if result["scores"]["dut_compile"] == 1.0 and result["scores"]["tb_compile"] == 1.0
            else "FAIL"
        )
        results.append(result)

    summary = {
        "examples_total": len(results),
        "smoke_pass_count": sum(1 for r in results if r["smoke_status"] == "PASS"),
        "smoke_fail_count": sum(1 for r in results if r["smoke_status"] != "PASS"),
        "behavior_checked_count": sum(1 for r in results if r["behavior_check_available"]),
        "behavior_pass_count": sum(1 for r in results if r["behavior_check_available"] and r["status"] == "PASS"),
        "behavior_fail_count": sum(1 for r in results if r["behavior_check_available"] and r["status"] != "PASS"),
        "results": results,
    }
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
