---
name: evas-sim
description: |
  How to use the EVAS Verilog-A behavioral simulator (pip package: evas-sim).
  Use this skill whenever the user wants to simulate a Verilog-A (.va) model,
  run a Spectre (.scs) netlist, check simulation feasibility, install evas-sim,
  or read simulation output (tran.csv, strobe.txt). Trigger on phrases like
  "simulate this", "run this VA model", "can EVAS handle this", "evas run",
  "evas simulate", "check if this is simulatable", or any mention of evas-sim.
license: MIT - see LICENSE.txt
evals: evals/evals.json
---

EVAS is a pure-Python, **voltage-mode, event-driven** Verilog-A simulator. No KCL/KVL, no analog solver.

## Compatibility check (do this first)

Read the `.va` file before simulating. If any unsupported pattern is found, stop and suggest ngspice or Xyce instead.

| Pattern | Support |
|---------|---------|
| `V(...) <+`, `V(a,b)` differential | yes |
| `@(cross(...))`, `@(above(...))`, `@(initial_step)` | yes |
| `@(timer(period))`, `@(final_step)` | yes |
| `transition()` with delay / rise / fall | yes |
| `for`, `if/else`, `case/endcase`, `begin/end` | yes |
| arrays, parameters (real / integer / string) | yes |
| `` `include ``, `` `define ``, `` `default_transition `` | yes |
| `$abstime`, `$temperature`, `$vt` | yes |
| `$bound_step(dt)` | yes |
| `$fopen()`, `$fclose()`, `$fstrobe()`, `$fwrite()`, `$fdisplay()` | yes |
| `$display`, `$strobe`, `$random`, `$dist_uniform()`, `$rdist_normal()` | yes |
| Math: `abs` `sqrt` `exp` `ln` `log` `pow` `sin` `cos` `floor` `ceil` `min` `max` | yes |
| `global 0` | silently ignored |
| PDK `include` lines (transistor models) | silently ignored - EVAS has no transistor solver |
| Spectre PSF options (`write=`, `writefinal=`, `savetime=`, `savefile=`, `flushtime=`) | ignored - EVAS output is controlled by `-o output/dir`, not these Spectre-specific keys |
| `info` statements (`finalTimeOP`, `modelParameter`, `element`, etc.) | silently ignored |
| `I(...) <+`, `q(...) <+`, `ddt(...)`, `idt(...)` | not supported by design |
| AC/DC analysis, transistors | not supported by design |
| Spectre `subckt` hierarchy | not yet implemented |

## Install

```bash
uv tool install evas-sim  # preferred CLI install
pip install evas-sim      # fallback if using a virtualenv
evas list                 # verify CLI install; current v0.4.3 prints 14 bundled groups
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

## Complete testbench example (10-bit SAR ADC)

A realistic testbench for a behavioural 10-bit ADC. Use this as a writing reference.

```spectre
// Library name: my_project
// Cell name:    tb_adc_10b
// View name:    schematic
simulator lang=spectre
global 0

// --- Sources ---
V1 (VDD 0) vsource dc=900m type=dc
V0 (VSS 0) vsource type=dc
V2 (clk_i 0) vsource type=pulse val0=0 val1=900m period=10n width=5n rise=10p fall=10p
V3 (vin_i 0) vsource type=sine sinedc=450m ampl=450m freq=10Meg

// --- DUT: ports by position, parameters inline ---
I3 (VDD VSS vin_i clk_i DOUT\<9\> DOUT\<8\> DOUT\<7\> DOUT\<6\> DOUT\<5\> \
        DOUT\<4\> DOUT\<3\> DOUT\<2\> DOUT\<1\> DOUT\<0\>) adc_10b \
    vrefp=1 vrefn=0 tedge=10p

// --- Simulator settings ---
simulatorOptions options reltol=1e-4 vabstol=1e-6 iabstol=1e-12 \
    temp=27 tnom=27 gmin=1e-12

// --- Analysis ---
tran tran stop=1u errpreset=conservative

// --- Save: explicit list keeps tran.csv narrow ---
save vin_i clk_i DOUT\<9\>:0

// --- VA model: always last ---
ahdl_include "./adc_10b.va"
```

Key points illustrated here:
- Clock `val1` matches supply voltage; `rise`/`fall` match DUT `tedge`
- Sine source has explicit `sinedc` (mid-rail) and `ampl`
- Bus saved with range syntax `DOUT\<9\>:0` instead of listing all 10 bits
- `ahdl_include` is the last statement
- No `info` statements, no PSF save keys (`write=`, `savetime=` etc.) - EVAS does not use them; output goes to `-o output/dir`

## Example library

Use the local repository example library as the primary reference:

- `examples/README.md`
- `examples/manifest.json`

The current `evas-sim` PyPI release (`0.4.3`) still bundles 14 runnable example
groups for smoke testing via `evas list` / `evas run`, but the skill-owned
examples in this repo are the source of truth for structure and categorization.

### Local categories

| Category | Examples |
|-------|-------------|
| `data-converter` | `adc_dac_ideal_4b`, `d2b_4b`, `dac_binary_clk_4b`, `dac_therm_16b`, `sar_adc_dac_weighted_8b` |
| `comparator` | `comparator` |
| `digital-logic` | `clk_div`, `digital_basics`, `lfsr` |
| `calibration` | `dwa_ptr_gen` |
| `stimulus` | `clk_burst_gen`, `noise_gen`, `ramp_gen` |
| `measurement` | `gain_extraction` |

## Output files

| File | Contents |
|------|----------|
| `tran.csv` | Time-domain waveforms; `time` in seconds, voltages in volts, bus codes as integers |
| `strobe.txt` | `$strobe`/`$display` messages in time order |
| `tran.png` | Auto-generated multi-panel waveform plot |

## Result processing

### Visualization
After simulation, load `tran.csv` with pandas and plot with matplotlib. **One signal per subplot** - never stack more than ~4 signals in one panel, and never overlay unrelated signals on the same axis.

```python
import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("output/mydesign/tran.csv")
signals = [c for c in df.columns if c != "time"]

# One subplot per signal (or small logical groups)
fig, axes = plt.subplots(len(signals), 1, figsize=(10, 2.5 * len(signals)), sharex=True)
if len(signals) == 1:
    axes = [axes]

for ax, sig in zip(axes, signals):
    ax.plot(df["time"] * 1e9, df[sig])   # time in ns
    ax.set_ylabel(sig)
    ax.grid(True, linestyle="--", alpha=0.5)

axes[-1].set_xlabel("Time (ns)")
fig.tight_layout()
fig.savefig("output/mydesign/waveforms.png", dpi=150)
plt.show()
```

### Saving figures
- Always call `fig.savefig(...)` **before** `plt.show()` so the file is written even in non-interactive mode.
- Use `dpi=150` for screen-quality images; use `dpi=300` for reports.
- Keep figure width ≤ 12 inches; height = `2.5 × number_of_subplots` (minimum 2 in per subplot).
- If there are more than 6 signals, split into multiple figures (e.g., digital bus codes in one figure, analog voltages in another).

### Reading strobe output
```python
with open("output/mydesign/strobe.txt") as f:
    for line in f:
        print(line, end="")
```

## Test file structure

Split every simulation project into exactly **two files**:

| File | Role | Contains |
|------|------|----------|
| `dut.va` (or a descriptive name) | **DUT** - the model under test | Verilog-A `module ... endmodule`; no stimulus, no analysis |
| `tb_<name>.scs` | **Testbench** - stimulus + analysis | `ahdl_include`, sources, `save`, `tran` statement |

### DUT (`dut.va`)
- Pure behavioural model; no hardcoded stimulus voltages.
- Expose all tuneable quantities as `parameter`.
- One module per file.

### Testbench (`tb_<name>.scs`) - writing guidelines

#### 1. File header
Always start with identifying comments so the file is self-documenting:
```spectre
// Library name: <project>
// Cell name:    tb_<dut>
// View name:    schematic
```

#### 2. Statement ordering
Follow this fixed order - mixing it causes parse errors in some tools:
```
1. header comments
2. sources (vsource / isource)
3. DUT instance
4. simulatorOptions
5. tran / dc / ac analysis
6. info statements (oppoint, models, etc.)
7. saveOptions
8. ahdl_include   // always last
```

`ahdl_include` must be the **last** statement. Placing it earlier can cause forward-reference errors.

#### 3. DUT instantiation
Connect ports **by position**, matching the Verilog-A port list exactly:
```spectre
I3 (VDD VSS vin_i clk_i DOUT\<9\> DOUT\<8\> DOUT\<7\> DOUT\<6\> DOUT\<5\> \
        DOUT\<4\> DOUT\<3\> DOUT\<2\> DOUT\<1\> DOUT\<0\>) adc_10b \
    vrefp=1 vrefn=0 tedge=1e-11
```
- Parameters follow the module name on the same line (or continued with `\`).
- Use line continuation `\` - one parameter group per logical line.

**Bus bit notation - important:**

| Context | Syntax | Example |
|---------|--------|---------|
| Port connection list | each bit written out individually, MSB to LSB | `DOUT\<9\> DOUT\<8\> ... DOUT\<0\>` |
| `save` statement | range shorthand allowed | `save DOUT\<9\>:0` |
| Single bit reference | one index only | `DOUT\<3\>` |

Rules:
- Angle brackets **must** be backslash-escaped: `\<9\>` not `<9>`
- In the port list there is **no range shorthand** - every bit must appear explicitly
- Range syntax `NET\<msb\>:lsb` (e.g. `DOUT\<9\>:0`) is only valid in `save` statements
- Bit order in the port list must match the Verilog-A `output [9:0] DOUT` declaration exactly (MSB first)

#### 4. Sources
| Purpose | Type | Key parameters |
|---------|------|----------------|
| Supply rail | `vsource dc=900m type=dc` | `dc` value only |
| Ground rail | `vsource type=dc` | omit `dc=` (defaults to 0) |
| Digital clock | `vsource type=pulse val0=0 val1=VDD period=... width=...` | match DUT `tedge` rise/fall |
| Analog input (ADC) | `vsource type=sine sinedc=... ampl=... freq=...` | set `sinedc` to mid-rail |
| Ramp / step | `vsource type=pwl` | explicit time-value pairs |

#### 5. `simulatorOptions`
Minimal recommended set for behavioural Verilog-A:
```spectre
simulatorOptions options reltol=1e-4 vabstol=1e-6 iabstol=1e-12 \
    temp=27 tnom=27 gmin=1e-12
```
- `reltol=1e-4` is sufficient for behavioural models; tighten only if needed.
- Always set `temp` and `tnom` explicitly.

#### 6. `tran` analysis
```spectre
tran tran stop=<end_time> errpreset=conservative
```
- `errpreset=conservative` is the safe default for behavioural VA.
- Choose `stop` to cover at least the settling time plus the measurement window.
- Avoid `savetime` / `savefile` / `write` / `writefinal` - these are Spectre PSF keys; EVAS ignores them. EVAS output (tran.csv, strobe.txt, tran.png) is written to the directory set by `-o output/dir`.

#### 7. `saveOptions` and explicit `save`
```spectre
saveOptions options save=allpub   // save all public nodes (default)
// -- or explicitly list signals --
save vin_i clk_i DOUT\<9\>:0     // bus range syntax
```
- With EVAS use `save sig1 sig2 ...` (explicit list) for a lean `tran.csv`.
- `save=allpub` produces a wide CSV - fine for exploration, noisy for scripts.

#### 8. `info` statements
These are Spectre PSF post-processing directives; **EVAS ignores them**. Include them only when targeting a dual Spectre/EVAS flow:
```spectre
finalTimeOP info what=oppoint   where=rawfile
modelParameter info what=models where=rawfile
```
Omit them in EVAS-only testbenches to keep the file clean.

#### 9. `ahdl_include` path
```spectre
ahdl_include "/absolute/path/to/dut.va"          // absolute - robust
ahdl_include "./dut.va"                           // relative - simpler for portable repos
```
Use an absolute path when the testbench is generated by a flow tool; use a relative path for hand-written, version-controlled testbenches.

#### 10. One testbench per scenario
Name files `tb_<scenario>.scs` (e.g., `tb_ramp.scs`, `tb_sine.scs`, `tb_offset_search.scs`) so `evas simulate` and `evas run --tb` can select them individually.

## Common issues

| Symptom | Fix |
|---------|-----|
| `evas: command not found` | Activate virtualenv or use `python -m evas` |
| Empty `tran.csv` | Add `save sig1 sig2 ...` to the `.scs` netlist |
| All voltages are 0 | Model uses `I() <+` - not supported |
| `Compiled Verilog-A module` not printed | Parse error - check `ahdl_include` path in `.scs` |
| Cross event fires twice at same timestep | Fixed in v0.3.0 - upgrade with `pip install -U evas-sim` |
