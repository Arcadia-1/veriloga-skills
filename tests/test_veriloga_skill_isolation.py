from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "veriloga"


def _skill_files() -> list[Path]:
    return sorted(path for path in SKILL.rglob("*") if path.is_file())


def _read_all_skill_text() -> str:
    return "\n".join(path.read_text(encoding="utf-8") for path in _skill_files())


def test_frontmatter_contains_only_name_and_description() -> None:
    text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)

    assert match, "SKILL.md must start with YAML frontmatter"
    frontmatter = match.group(1)
    keys = {line.split(":", 1)[0] for line in frontmatter.splitlines() if re.match(r"^[a-z_]+:", line)}
    assert keys == {"name", "description"}
    assert re.search(r"^name:\s*veriloga\s*$", frontmatter, re.MULTILINE)


def test_veriloga_skill_has_no_external_workflow_dependencies() -> None:
    forbidden = [
        "adctoolbox",
        "benchmark",
        "cadence",
        "comparator",
        "dff",
        "dac",
        "evas",
        "ngspice",
        "openvaf",
        "pfd",
        "sar",
        "spectre",
        "testbench",
        "virtuoso",
    ]
    text = _read_all_skill_text().lower()
    hits = {term for term in forbidden if term in text}

    assert not hits


def test_veriloga_skill_has_no_external_resource_shapes() -> None:
    text = _read_all_skill_text().lower()
    forbidden_text = ["http://", "https://", "../", ".scs"]
    hits = {term for term in forbidden_text if term in text}
    python_files = sorted(SKILL.rglob("*.py"))

    assert not hits
    assert not python_files


def test_skill_md_local_links_exist() -> None:
    skill_text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
    code_paths = re.findall(r"`((?:references|assets|evals)/[^`]+)`", skill_text)

    assert code_paths
    for raw_path in code_paths:
        assert ".." not in raw_path
        assert not re.match(r"https?://", raw_path)
        assert (SKILL / raw_path).exists(), raw_path


def test_index_local_links_exist() -> None:
    index = (ROOT / "index.html").read_text(encoding="utf-8")
    hrefs = re.findall(r'href="([^"]+)"', index)

    assert hrefs
    for href in hrefs:
        if href.startswith(("http://", "https://", "#", "mailto:")):
            continue
        assert ".." not in href
        assert (ROOT / href).exists(), href


def test_repository_docs_match_standalone_skill_installation() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    index = (ROOT / "index.html").read_text(encoding="utf-8")
    banner = (ROOT / "assets" / "banner.svg").read_text(encoding="utf-8").lower()

    for text in [readme, index]:
        assert ".agents/skills" in text
        assert ".codex/skills" not in text

    for stale_term in ["cadence", "spectre", "1,809"]:
        assert stale_term not in banner


def test_references_are_one_level_deep_and_linked_from_skill() -> None:
    skill_text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
    refs = sorted((SKILL / "references").glob("*.md"))

    assert refs
    assert not [path for path in (SKILL / "references").rglob("*") if path.is_file() and path.parent != SKILL / "references"]
    for ref in refs:
        assert f"references/{ref.name}" in skill_text


def test_assets_are_minimal_language_examples() -> None:
    examples = sorted((SKILL / "assets" / "examples").glob("*.va"))
    template = SKILL / "assets" / "template.va"
    expected_names = {
        "branch_access_probe.va",
        "cross_logging_probe.va",
        "declaration_parameter_probe.va",
        "minimal_zero_probe.va",
        "transition_syntax_probe.va",
        "vector_genvar_zero_probe.va",
    }

    assert template.exists()
    assert {path.name for path in examples} == expected_names
    assert 4 <= len(examples) <= 6
    for path in [template, *examples]:
        text = path.read_text(encoding="utf-8")
        assert "`include \"constants.vams\"" in text
        assert "`include \"disciplines.vams\"" in text
        assert "module " in text
        assert "endmodule" in text


def test_language_assets_do_not_encode_benchmark_like_recipes() -> None:
    asset_text = "\n".join(path.read_text(encoding="utf-8").lower() for path in (SKILL / "assets").rglob("*.va"))
    forbidden = [
        "event_state_forms",
        "timer_event_forms",
        "parameter_array_forms",
        "analog_contribution_forms",
        "branch_alias_forms",
        "smooth_transition_forms",
        "held",
        "sample",
        "toggle",
        "state = 1 - state",
        "gain",
        "offset",
        "g0",
        "conductance",
        "* v(",
        "+ v(",
    ]
    hits = {term for term in forbidden if term in asset_text}

    assert not hits


def test_evals_are_language_tasks() -> None:
    data = json.loads((SKILL / "evals" / "evals.json").read_text(encoding="utf-8"))
    eval_text = (SKILL / "evals" / "evals.json").read_text(encoding="utf-8").lower()
    forbidden = [
        "sample",
        "held",
        "toggle",
        "gain",
        "offset",
        "conductance",
        "controlled voltage",
        "pass-through",
        "state machine",
    ]

    assert data["skill_name"] == "veriloga"
    assert data["evals"]
    assert not {term for term in forbidden if term in eval_text}
    for item in data["evals"]:
        assert set(item) == {"id", "name", "category", "domain", "prompt", "expected_output", "files"}
        assert item["category"] == "language-review"
        assert item["domain"] == "source"
