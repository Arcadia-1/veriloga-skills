#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT.parent / "veriloga" / "evals" / "evals.json"
TASKS = ROOT / "tasks"


CATEGORY_SLUGS = {
    "ADC/SAR": "adc-sar",
    "PLL/Clock": "pll-clock",
    "Amplifier/Filter": "amplifier-filter",
    "Digital Logic": "digital-logic",
    "DAC": "dac",
    "Signal Source": "signal-source",
    "Passive/Model": "passive-model",
    "Power/Switch": "power-switch",
    "Calibration": "calibration",
    "Testbench": "testbench",
}


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")


def family_for(entry: dict) -> str:
    if entry["category"] == "Testbench":
        return "tb-generation"
    return "spec-to-va"


def backend_for(entry: dict) -> str:
    return "evas"


def difficulty_for(entry: dict) -> str:
    prompt = entry["prompt"].lower()
    if any(k in prompt for k in ["two-stage", "butterworth", "background calibration", "complete sar adc"]):
        return "hard"
    if any(k in prompt for k in ["14-bit", "12-bit", "differential", "programmable", "pipeline", "prbs-15"]):
        return "medium"
    return "easy"


def must_include(entry: dict) -> list[str]:
    text = (entry["expected_output"] + " " + entry["prompt"]).lower()
    items: list[str] = []
    if "@(cross(" in text or "cross()" in text:
        items.append("@(cross(")
    if "transition()" in text or "transition(" in text:
        items.append("transition(")
    if "genvar" in text:
        items.append("genvar")
    if "ddt()" in text or "ddt(" in text:
        items.append("ddt(")
    if "laplace_nd()" in text or "laplace_nd(" in text:
        items.append("laplace_nd(")
    if "idtmod()" in text or "idtmod(" in text:
        items.append("idtmod(")
    if "flicker_noise()" in text or "flicker_noise(" in text:
        items.append("flicker_noise(")
    if "transition()" in text or entry["domain"] == "voltage":
        items.append("electrical")
    return sorted(set(items))


def must_not_include(entry: dict) -> list[str]:
    return ["I(", "ddt("]


def scoring_for(entry: dict) -> list[str]:
    family = family_for(entry)
    if family == "tb-generation":
        return ["tb_compile"]
    return ["dut_compile", "tb_compile", "sim_correct"]


def checks_for(entry: dict) -> dict:
    family = family_for(entry)
    checks: dict = {}
    syntax = {}
    inc = must_include(entry)
    exc = must_not_include(entry)
    if inc:
        syntax["must_include"] = inc
    if exc:
        syntax["must_not_include"] = exc
    if family == "tb-generation":
        syntax.setdefault("must_include", []).extend(["simulator lang=spectre", "ahdl_include"])
    checks["syntax"] = syntax
    if family == "tb-generation":
        checks["tb_compile"] = {"backend": "evas"}
    else:
        checks["dut_compile"] = {"backend": "evas"}
        checks["tb_compile"] = {"backend": "evas"}
        checks["sim_correct"] = {"checks": ["manual_review_expected_output"]}
    return checks


def write_case(entry: dict) -> None:
    if entry["domain"] != "voltage":
        return
    family = family_for(entry)
    category = CATEGORY_SLUGS.get(entry["category"], slugify(entry["category"]))
    case = slugify(entry["name"].removeprefix("eval-"))
    case_dir = TASKS / family / entry["domain"] / category / case
    case_dir.mkdir(parents=True, exist_ok=True)

    prompt_path = case_dir / "prompt.md"
    meta_path = case_dir / "meta.json"
    checks_path = case_dir / "checks.yaml"

    prompt_path.write_text(entry["prompt"].strip() + "\n", encoding="utf-8")

    meta = {
        "id": case,
        "family": family,
        "category": category,
        "domain": "voltage",
        "difficulty": difficulty_for(entry),
        "expected_backend": "evas",
        "must_include": must_include(entry),
        "must_not_include": must_not_include(entry),
        "inputs": ["prompt.md"],
        "artifacts": ["candidate.out"],
        "scoring": scoring_for(entry),
        "source_eval_id": entry["id"],
        "source_name": entry["name"],
        "expected_output_summary": entry["expected_output"],
        "source_files": entry.get("files", []),
    }
    meta_path.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")

    checks = checks_for(entry)
    lines: list[str] = []
    for section, body in checks.items():
        lines.append(f"{section}:")
        for key, value in body.items():
            if isinstance(value, list):
                lines.append(f"  {key}:")
                for item in value:
                    lines.append(f"    - {json.dumps(item)}")
            elif isinstance(value, dict):
                lines.append(f"  {key}:")
                for k2, v2 in value.items():
                    lines.append(f"    {k2}: {json.dumps(v2)}")
            else:
                lines.append(f"  {key}: {json.dumps(value)}")
    checks_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    data = json.loads(SRC.read_text(encoding="utf-8"))
    count = 0
    for entry in data["evals"]:
        if entry["domain"] == "voltage":
            write_case(entry)
            count += 1
    print(f"migrated {count} voltage-domain eval cases into {TASKS}")


if __name__ == "__main__":
    main()
