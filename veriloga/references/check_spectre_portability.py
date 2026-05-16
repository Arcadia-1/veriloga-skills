from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from itertools import combinations
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[2]
BLOCK_COMMENT_RE = re.compile(r"/\*.*?\*/", re.DOTALL)
LINE_COMMENT_RE = re.compile(r"//.*$")
VOLTAGE_BRANCH_RE = re.compile(r"\bV\s*\(\s*([^,\)\n]+)\s*,\s*([^)]+?)\s*\)\s*<\+")
ANALOG_BUS_READ_RE = re.compile(
    r"\bV\s*\(\s*([A-Za-z_]\w*)\s*\[\s*([^\]\n]+?)\s*\](?:\s*,|\s*\))"
)
GENVAR_DECL_RE = re.compile(r"\bgenvar\s+([^;]+);")
IDENT_RE = re.compile(r"[A-Za-z_]\w*")
MACRO_RE = re.compile(r"`[A-Za-z_]\w*")


@dataclass(frozen=True)
class Finding:
    path: Path
    lineno: int
    message: str

    def format(self) -> str:
        try:
            display_path = self.path.relative_to(ROOT)
        except ValueError:
            display_path = self.path
        return f"{display_path}:{self.lineno}: {self.message}"


def _strip_block_comments_preserve_lines(text: str) -> str:
    def replace(match: re.Match[str]) -> str:
        return "\n" * match.group(0).count("\n")

    return BLOCK_COMMENT_RE.sub(replace, text)


def _normalize_node(node: str) -> str:
    return re.sub(r"\s+", "", node)


def _collect_genvars(text: str) -> set[str]:
    genvars: set[str] = set()
    for match in GENVAR_DECL_RE.finditer(text):
        genvars.update(IDENT_RE.findall(match.group(1)))
    return genvars


def _is_static_bus_index(index: str, genvars: set[str]) -> bool:
    index = index.strip()
    if re.fullmatch(r"\d+", index):
        return True
    if index in genvars:
        return True
    expr = MACRO_RE.sub("0", index)
    identifiers = IDENT_RE.findall(expr)
    return bool(identifiers) and all(identifier in genvars for identifier in identifiers)


def scan_text(path: Path, text: str) -> list[Finding]:
    """Find Spectre-portability hazards that EVAS-style checks can miss."""
    cleaned = _strip_block_comments_preserve_lines(text)
    genvars = _collect_genvars(cleaned)
    pair_lines: dict[tuple[str, str], list[int]] = {}
    nodes: set[str] = set()
    findings: list[Finding] = []

    for lineno, raw_line in enumerate(cleaned.splitlines(), start=1):
        line = LINE_COMMENT_RE.sub("", raw_line)
        for match in VOLTAGE_BRANCH_RE.finditer(line):
            a = _normalize_node(match.group(1))
            b = _normalize_node(match.group(2))
            if not a or not b or a == b:
                continue
            pair = tuple(sorted((a, b)))
            pair_lines.setdefault(pair, []).append(lineno)
            nodes.update(pair)

        for match in ANALOG_BUS_READ_RE.finditer(line):
            bus = match.group(1)
            index = match.group(2).strip()
            if not _is_static_bus_index(index, genvars):
                findings.append(
                    Finding(
                        path=path,
                        lineno=lineno,
                        message=(
                            f"runtime-indexed analog bus read V({bus}[{index}]); "
                            "Spectre requires fixed indices or genvar-unrolled access"
                        ),
                    )
                )

    for trio in combinations(sorted(nodes), 3):
        pairs = [
            tuple(sorted((trio[0], trio[1]))),
            tuple(sorted((trio[0], trio[2]))),
            tuple(sorted((trio[1], trio[2]))),
        ]
        if all(pair in pair_lines for pair in pairs):
            first_line = min(pair_lines[pair][0] for pair in pairs)
            findings.append(
                Finding(
                    path=path,
                    lineno=first_line,
                    message=(
                        "rigid ideal voltage-branch triangle among "
                        f"{trio[0]}, {trio[1]}, {trio[2]}; avoid independent "
                        "V(a,b) <+ constraints on all three node pairs"
                    ),
                )
            )

    return findings


def iter_veriloga_files(paths: Iterable[Path]) -> Iterable[Path]:
    for path in paths:
        if path.is_dir():
            yield from sorted(path.rglob("*.va"))
        elif path.suffix == ".va":
            yield path


def check_paths(paths: Iterable[Path]) -> list[Finding]:
    findings: list[Finding] = []
    for path in iter_veriloga_files(paths):
        findings.extend(scan_text(path, path.read_text(encoding="utf-8")))
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description="Check Verilog-A Spectre portability hazards.")
    parser.add_argument(
        "paths",
        nargs="*",
        type=Path,
        default=[ROOT / "veriloga"],
        help="Verilog-A files or directories to scan",
    )
    args = parser.parse_args()

    findings = check_paths(args.paths)
    for finding in findings:
        print(finding.format())
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
