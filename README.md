# veriloga-skills

Instructs an Agent to write Verilog-A behavioral models that conform to Cadence Virtuoso conventions and can be used directly inside Virtuoso.

> **If you are a human**: the skill overview and structure below will help you understand what this package contains. After installation, ask the Agent to write Verilog-A for you.

> **If you are an AI Agent**: skip the overview and go straight to the [Installation](#installation) section. `veriloga/SKILL.md` is the complete coding instruction set (8 mandatory rules + 12 circuit-category references); the code template is at `assets/template.va`; the DUT references are organized as a curated core set under `assets/examples/` plus an archive under `assets/examples-archive/`; the self-contained benchmark / runnable verification dataset is in `behavioral-va-eval/examples/`.

---

## Skill Overview

| Skill | Role | Function |
|-------|------|----------|
| **veriloga** | Core — code writing | 8 mandatory rules + 12 circuit-category references + curated core DUT examples; produces Verilog-A ready to drop into a Virtuoso cellview |
| **evas-sim** | Optional — voltage-domain verification | Drives the EVAS simulator to verify voltage-domain modules (SAR logic, DFF, counter, etc.) |
| **openvaf** | Optional — current-domain verification | OpenVAF compile → ngspice/OSDI load → simulation verification |

`veriloga` is the core skill and handles all code writing on its own. `evas-sim` and `openvaf` are optional companion skills for local verification of voltage-domain and current-domain modules respectively.

---

## Skill 1: veriloga

Rules and patterns distilled from 1,809 real `.va` designs, covering 12 circuit categories for analog/mixed-signal IC design. Generated code conforms to Cadence Virtuoso / Spectre conventions and can be placed directly into a cellview.

Contains 8 mandatory rules, 12 circuit-category references, and a curated core DUT example set with a broader supplemental archive. See [`veriloga/SKILL.md`](./veriloga/SKILL.md).

---

## Local Verification (Optional)

Finished modules can be verified locally. There are two verification paths depending on the constructs used in the code:

| Method | Applicable modules | Deciding criterion | Tool |
|--------|-------------------|--------------------|------|
| **EVAS** | Voltage-domain | `V() <+` + `@(cross())` / `transition()`, no `I() <+` | [EVAS](https://evas.tokenzhang.com/) event-driven simulator |
| **OpenVAF + ngspice** | Current-domain | `I() <+` / `ddt()` / `idt()` / `laplace_nd()` | `openvaf` skill |

```
Finish module → scan analog begin → classify domain
                                    ├── voltage-domain → EVAS verification
                                    ├── current-domain → OpenVAF compile + ngspice simulation
                                    └── mixed-domain   → recommended: split into two sub-modules
```

- **Voltage-domain** typical modules: SAR logic, DFF, counter, comparator, data generator
- **Current-domain** typical modules: Opamp, RLC network, VCO core, LDO, filter

Full domain classification and routing logic: `veriloga/references/domain-routing.md`.

### Skill 2: evas-sim

Handles simulation verification for voltage-domain modules:

```
.va file → EVAS event-driven simulation → waveform verification
```

Covers: EVAS installation and configuration, simulation commands, waveform viewing, list of supported constructs, troubleshooting guide. See [`evas-sim/SKILL.md`](./evas-sim/SKILL.md).

### Skill 3: openvaf

Handles compilation and simulation for current-domain modules:

```
.va file → OpenVAF compile → .osdi file → ngspice load → simulation verification
```

Covers: OpenVAF installation and configuration, compile commands, ngspice OSDI loading, list of supported features, troubleshooting guide. See [`openvaf/SKILL.md`](./openvaf/SKILL.md).

---

## Installation

> If you are an AI Agent (Claude Code, Cursor, Copilot, etc.), run the commands below directly — no manual action required from the user.

**Step 1 — Choose installation scope**

| Scenario | Choice |
|----------|--------|
| Current project only (recommended) | Project-level install → `.claude/skills/` |
| All projects | Global install → `~/.claude/skills/` |

> For other Agents, replace `.claude/skills/` with the appropriate skills directory (e.g. `.agent/skills/`).

**Step 2 — Run the install command** (bash; works on macOS / Linux / Windows)

Global:
```bash
git clone --depth 1 https://github.com/Arcadia-1/veriloga-skills /tmp/veriloga-skills \
  && cp -r /tmp/veriloga-skills/{veriloga,evas-sim,openvaf} ~/.claude/skills/ \
  && rm -rf /tmp/veriloga-skills
```

Project-level (run from the project root):
```bash
git clone --depth 1 https://github.com/Arcadia-1/veriloga-skills /tmp/veriloga-skills \
  && mkdir -p .claude/skills \
  && cp -r /tmp/veriloga-skills/{veriloga,evas-sim,openvaf} .claude/skills/ \
  && rm -rf /tmp/veriloga-skills
```

**Step 3 — Verify**

Run `/skills` in the Agent; confirm `veriloga`, `evas-sim`, and `openvaf` appear in the output list ✅

> **If you are an AI Agent**: execute the installation steps above on behalf of the user, choosing global or project-level scope based on their needs — no manual action required. After installation, read `veriloga/SKILL.md` and start working.

### Project Customization

Edit `veriloga/references/customize.md` to override defaults: port naming conventions, supply voltages, file-header templates, simulator-specific options, etc.

## Requirements

- **veriloga skill**: no external dependencies — pure documentation/reference skill
- **Local verification (optional)**:
  - Voltage-domain → [EVAS](https://evas.tokenzhang.com/)
  - Current-domain → [OpenVAF](https://openvaf.semimod.de/) + [ngspice](http://ngspice.sourceforge.net/) (≥ 38, with OSDI support)

See [requirements.md](./requirements.md) for details.
