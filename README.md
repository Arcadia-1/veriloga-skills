# veriloga-skills

Reusable skills for Verilog-A authoring and optional local verification.

## Skills

| Skill | Role | Scope |
| --- | --- | --- |
| `veriloga` | Core authoring skill | Self-contained Verilog-A language syntax and semantics for `.va` source files |
| `evas-sim` | Optional companion | Local voltage-domain verification workflow |
| `openvaf` | Optional companion | Local compile/simulation workflow for supported analog models |

The `veriloga` folder can be copied or installed by itself. It does not depend on the companion
skills, local simulators, external packages, project conventions, or task datasets.

## `veriloga`

`veriloga/SKILL.md` is a compact language authoring guide. Detailed material is split into
one-level references:

- `references/modules-ports-disciplines.md`
- `references/analog-contributions.md`
- `references/events-state-control.md`
- `references/operators-system-tasks.md`

The assets are intentionally minimal:

- `assets/template.va`
- `assets/examples/*.va`, small examples named by Verilog-A language construct

## Installation

Copy any skill folder you need into your agent's skill directory. For the standalone authoring
skill:

```bash
git clone --depth 1 https://github.com/Arcadia-1/veriloga-skills /tmp/veriloga-skills
mkdir -p .codex/skills
cp -r /tmp/veriloga-skills/veriloga .codex/skills/
```

The clone command is only a copy/install method. Once `veriloga/` is copied, the skill has no
runtime dependency on Git, the repository, Python, local simulators, or the sibling skill folders.

To install all skills from this repository, copy `veriloga`, `evas-sim`, and `openvaf` together.

## Requirements

See `requirements.md`. The standalone `veriloga` skill has no runtime requirements.
