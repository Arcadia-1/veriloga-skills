---
name: evas-sim
description: |
  How to use the EVAS Verilog-A behavioral simulator (pip package: evas-sim).
  Use this skill whenever the user wants to simulate a Verilog-A (.va) model,
  run a Spectre (.scs) netlist, check simulation feasibility, install evas-sim,
  or read simulation output (tran.csv, strobe.txt). Trigger on phrases like
  "simulate this", "run this VA model", "can EVAS handle this", "evas run",
  "evas simulate", "check if this is simulatable", or any mention of evas-sim.
license: MIT — see LICENSE.txt
evals: evals/evals.json
---

EVAS is a pure-Python, **voltage-mode, event-driven** Verilog-A simulator. No KCL/KVL, no analog solver.

## Compatibility check (do this first)

Read the `.va` file before simulating. If any unsupported pattern is found, stop and suggest ngspice or Xyce instead.

| Pattern | Support |
|---------|---------|
| `V(...) <+`, `V(a,b)` differential | ✅ |
| `@(cross(...))`, `@(above(...))`, `@(initial_step)` | ✅ |
| `@(timer(period))`, `@(final_step)` | ✅ |
| `transition()` with delay / rise / fall | ✅ |
| `for`, `if/else`, `case/endcase`, `begin/end` | ✅ |
| arrays, parameters (real / integer / string) | ✅ |
| `` `include ``, `` `define ``, `` `default_transition `` | ✅ |
| `$abstime`, `$temperature`, `$vt` | ✅ |
| `$bound_step(dt)` | ✅ |
| `$fopen()`, `$fclose()`, `$fstrobe()`, `$fwrite()`, `$fdisplay()` | ✅ |
| `$display`, `$strobe`, `$random`, `$dist_uniform()`, `$rdist_normal()` | ✅ |
| Math: `abs` `sqrt` `exp` `ln` `log` `pow` `sin` `cos` `floor` `ceil` `min` `max` | ✅ |
| `I(...) <+`, `q(...) <+`, `ddt(...)`, `idt(...)` | not supported by design |
| AC/DC analysis, transistors | not supported by design |
| Spectre `subckt` hierarchy | not yet implemented |

## Install

```bash
uv pip install evas-sim   # preferred
pip install evas-sim      # fallback
evas list                 # verify: prints 14 bundled example groups
```

If `evas` is not found after install, use `python -m evas` or check virtualenv activation.

## Simulate

```bash
# Custom netlist
evas simulate path/to/tb.scs -o output/mydesign

# Bundled example (default testbench)
evas run clk_div
evas run comparator

# Bundled example with specific sub-testbench
evas run comparator --tb tb_cmp_strongarm.scs
evas run comparator --tb tb_cmp_offset_search.scs
evas run digital_basics --tb tb_not_gate.scs
evas run adc_dac_ideal_4b --tb tb_adc_dac_ideal_4b_ramp.scs
```

## Bundled example groups (14 total)

Each group provides `.va` models, `.scs` testbench netlists, and Python analysis scripts.

| Group | Sub-examples |
|-------|-------------|
| `clk_div` | Clock divider |
| `clk_burst_gen` | Clock burst generator |
| `digital_basics` | AND, OR, NOT, DFF, inverter chain |
| `lfsr` | Linear feedback shift register |
| `noise_gen` | Gaussian noise generator |
| `ramp_gen` | Ramp generator |
| `edge_interval_timer` | Edge-interval timer |
| `d2b_4b` | 4-bit thermometer-to-binary |
| `dac_binary_clk_4b` | 4-bit binary DAC (clocked) |
| `dac_therm_16b` | 16-bit thermometer DAC |
| `adc_dac_ideal_4b` | 4-bit ADC+DAC: ramp / sine / 1000-pt sine |
| `comparator` | a) ideal  b) StrongARM  c) offset search  d) delay |
| `dwa_ptr_gen` | a) overlap  b) no-overlap — 100 MHz, `v2b_4b` voltage input |
| `sar_adc_dac_weighted_8b` | 8-bit SAR ADC+DAC, DNL/INL |

## Output files

| File | Contents |
|------|----------|
| `tran.csv` | Time-domain waveforms; `time` in seconds, voltages in volts, bus codes as integers |
| `strobe.txt` | `$strobe`/`$display` messages in time order |
| `tran.png` | Auto-generated multi-panel waveform plot |

## Common issues

| Symptom | Fix |
|---------|-----|
| `evas: command not found` | Activate virtualenv or use `python -m evas` |
| Empty `tran.csv` | Add `save sig1 sig2 ...` to the `.scs` netlist |
| All voltages are 0 | Model uses `I() <+` — not supported |
| `Compiled Verilog-A module` not printed | Parse error — check `ahdl_include` path in `.scs` |
| Cross event fires twice at same timestep | Fixed in v0.3.0 — upgrade with `pip install -U evas-sim` |
