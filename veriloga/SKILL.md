---
name: veriloga
description: >
  Write Verilog-A behavioral modules for analog/mixed-signal IC design (Cadence Virtuoso / Spectre).
  Covers 12 circuit categories. TRIGGER FIRST (before evas-sim) when the user needs to write or
  generate a new .va file. Key trigger phrases: "write", "create", "generate", "code", "implement" +
  "Verilog-A / veriloga / va / .va / behavioral model".
  Also triggers on: review/fix Verilog-A, "behavioral model", "veriloga", "analog HDL",
  circuit spec → behavioral model, "voltage-domain", "current-domain".
  Do NOT defer to evas-sim for authoring — evas-sim is for running an already-written file.
---

# Verilog-A Writer

Write correct, Virtuoso-ready Verilog-A behavioral modules. Rules extracted from 1,638
real-world .va files plus a 171-module reference library (14,311 LOC).

## How to Use This Skill

**Core workflow:**

1. **Identify the circuit category** → see Category Index
2. **Apply all mandatory rules** below
3. **Start from template** `assets/template.va`
4. **Classify domain** → scan code for voltage vs current constructs (see Domain Classification)
5. **Verify** (optional) → smoke test on the appropriate simulator (see Smoke Test)
6. **Explain usage** → list every port (direction, what to connect) and key parameters

**Need guidance? Search these resources:**

- **Category-specific patterns** → `references/categories/adc-sar.md`, `comparator.md`, etc.
- **Project overrides** (naming, supply voltage, headers) → `references/customize.md`
- **Domain classification help** → `references/domain-routing.md`
- **EVAS simulator support check** → `references/evas-capabilities.manifest`
- **ADC behavioral verification** → `references/adc-testbench-guide.md` + `assets/examples/adc-verification/`
- **Advanced syntax** (string parsing, current-domain functions, conditional compilation) → `references/verilog-a-advanced.md`
- **Working examples** → `assets/examples/`

---

## Reference File Guide

**When you need help with a specific task:**

| Task | Reference | Purpose |
|---|---|---|
| "How do I structure a comparator / ADC / DAC / filter?" | `references/categories/` | Circuit-specific best practices, patterns, edge cases |
| "What naming convention should I use?" | `references/customize.md` | Project-specific overrides for ports, parameters, file headers |
| "Is my module voltage-domain or current-domain?" | `references/domain-routing.md` | Classification guide + mixed-domain splitting strategies |
| "Can EVAS simulate my voltage-domain module?" | `references/evas-capabilities.manifest` | Check EVAS supported constructs |
| "How do I verify my ADC behavioral model?" | `references/adc-testbench-guide.md` | Full adctoolbox workflow with coherent sampling + spectral analysis |
| "Show me working examples" | `assets/examples/` | Correct/incorrect patterns by category or technique |
| "What's this advanced syntax for?" | `references/verilog-a-advanced.md` | String parsing, `$vt`, `branch`, `@(timer)`, conditional compilation, etc. |

---

## Scope: This Skill Writes DUT Modules Only

**This skill only writes the DUT (Device Under Test) — the Verilog-A behavioral module.**

To simulate, you need a testbench. That is a separate concern handled by the `evas-sim` skill.

| Step | What | File | Skill |
|---|---|---|---|
| 1 | Write behavioral module | `.va` | **this skill** |
| 2 | Write testbench + run simulation | `.scs` | **`evas-sim`** |

**Correct naming convention:**
- DUT: `sar_adc.va`, `comparator.va`, `dac_8b.va` — behavioral module, no `tb_` prefix
- Testbench: `tb_sar_adc.scs`, `tb_comparator.scs` — `.scs` netlist, `tb_` prefix here

**NEVER create `tb_*.va`.** See `evas-sim/SKILL.md` for testbench structure and simulation workflow.

---

## Mandatory Rules

Violating any rule causes simulator errors or silently wrong results.

### Rule 1: All signals use `electrical` type

No `wire`, `logic`, or `reg`. Spectre accepts two port styles:

**Style A: ANSI inline — each port on its own line, each with its own `electrical`**
```verilog
module example (
    inout  electrical VDD,
    inout  electrical VSS,
    input  electrical clk_i,
    output electrical [3:0] dout_o
);
```

> **Cadence Spectre VACOMP pitfall:** `electrical` does NOT carry across a comma.
> `inout electrical VDD, VSS` gives VSS no discipline → Spectre error.
> EVAS tolerates this; Spectre rejects it. Always one port per line.
>
> | Style | EVAS | Cadence Spectre |
> |---|---|---|
> | `inout electrical VDD, VSS` | ✓ tolerates | ✗ VSS has no discipline |
> | `inout electrical VDD,`<br>`inout electrical VSS,` | ✓ | ✓ |

**Style B: Old-style separated** — discipline declared separately, comma-sharing is safe here:
```verilog
module example (VDD, VSS, clk_i, dout_o);
inout VDD, VSS;
input clk_i;
output [3:0] dout_o;
electrical VDD, VSS, clk_i;
electrical [3:0] dout_o;
```

**NOT accepted** — combined `inout electrical` in body:
```verilog
module example (VDD, VSS, clk_i, dout_o);
    inout electrical VDD, VSS;       // WRONG — Spectre syntax error
```

#### Vector (Array) Ports

For multi-bit buses, use **vector notation** with **MSB at left, LSB at right** (MSB:LSB).
Default convention: `[31:0]` means bit 31 is MSB, bit 0 is LSB.

**Correct — vector ports (preferred for buses):**
```verilog
// Single-ended 10-bit data buses
input electrical [9:0] data_i [0:31];      // 32 channels, 10-bit each
output electrical [15:0] result_o;         // Single 16-bit output

// Clock array
input electrical clk_i [0:31];             // 32 clock signals
```

**Wrong — individual port enumeration:**
```verilog
// DON'T do this for large buses:
input electrical [9:0] DIN_0, DIN_1, DIN_2, ..., DIN_31;  // Verbose and error-prone
input electrical CLK_0, CLK_1, CLK_2, ..., CLK_31;        // Hard to maintain
```

**Access vector elements:**
```verilog
genvar ch;

analog begin
    for (ch = 0; ch < 32; ch = ch + 1) begin
        code[ch] = V(data_i[ch]);          // Access channel ch
        sync[ch] = V(clk_i[ch]);           // Clock for channel ch
    end
end
```

---

### Rule 2: Power ports are `inout`, not `input`

`input VDD` silently breaks power-aware simulation.

### Rule 3: Supply voltages — read from ports or parameterize

Never hardcode `1.8` directly. Two approaches:
```
// Option A: from ports          // Option B: parameterized
vh = V(VDD);                     parameter real vdd = 1.0;
vl = V(VSS);                     parameter real vth = vdd / 2.0;
vth = (vh + vl) / 2.0;
```

Default threshold: `vth = (vdd + vss) / 2`.

### Rule 4: All declarations at module level

`parameter`, `real`, `integer`, `genvar` must appear before `analog begin`.

**Correct:**
```verilog
module example (input electrical clk_i, output electrical [3:0] dout_o);
    parameter integer nbits = 4;
    real vth;
    integer state;
    genvar k;

    analog begin
        vth = 0.5;  // Initialize in analog block
        // ... rest of module
    end
endmodule
```

**Wrong — declaration inside analog block:**
```verilog
module example (input electrical clk_i, output electrical [3:0] dout_o);
    analog begin
        integer state;      // ERROR: declaration not at module level
        real vth;           // ERROR: declaration not at module level
        // ...
    end
endmodule
```

### Rule 5: Loop variables use `genvar`

Loop indices must use `genvar`, **not** `integer`. Integer loop indices cause elaboration
errors in most simulators.

**Correct — genvar in @event block (runtime loop):**
```verilog
genvar i;

analog begin
    @(initial_step or cross(V(CLKS)-vdd/2, +1)) begin
        $strobe("[reset]");
        for (i = `NUM_ADC_BITS; i >= 1; i = i - 1) begin
            dout[i] = 0;
        end
    end
end
```

**Correct — genvar in bare block (compile-time expansion):**
```verilog
genvar k;

analog begin
    // These assignments are compile-time expanded
    for (k = 0; k < N_BIT; k = k + 1) begin
        if ((code >> k) & 1)
            V(DOUT_o[k]) <+ transition(V(VDD), 0, tedge);
        else
            V(DOUT_o[k]) <+ transition(V(VSS), 0, tedge);
    end
end
```

**Wrong — integer loop index:**
```verilog
integer i;  // Declared at module level (OK)

analog begin
    @(initial_step) begin
        for (i = 0; i < 10; i = i + 1) begin  // ERROR: loop uses integer
            code[i] = 0;
        end
    end
end
```

### Rule 6: Initialize state in `@(initial_step)`

Uninitialized variables default to 0 or garbage depending on simulator.

**Rule 6 corollary — execution order:** EVAS compiles the analog block into two methods:
`initial_step()` (fires first, at t=0) and `evaluate()` (fires second, then every timestep).
Variables assigned in the bare `analog begin` block live in `evaluate()` and are still at their
`__init__` default (0) when `initial_step()` runs. If `@(initial_step)` reads a variable that
is computed in the bare block — e.g., via `$strobe` — it will print 0 even though the driven
voltages are correct. Fix: compute the value inside `@(initial_step)` itself, or avoid reading
bare-block variables from `@(initial_step)`.

### Rule 7: Edge detection uses `@(cross())` with direction

`+1` rising, `-1` falling. Omit direction only when both edges are needed.

### Rule 8: Outputs use `transition()` — use `` `default_transition ``

```
`default_transition 10p
V(out_o) <+ transition(state ? vh : vl, 0);
```

**Pitfall:** Multiple `<+` to the same node *adds* contributions, not overwrites.
Use a temporary variable and assign once.

---

## Category Index

| Category | Reference File | Domain |
|---|---|---|
| ADC / SAR | `references/categories/adc-sar.md` | voltage |
| DAC | `references/categories/dac.md` | either |
| Comparator | `references/categories/comparator.md` | voltage |
| PLL / Clock | `references/categories/pll-clock.md` | either |
| Sample & Hold | `references/categories/sample-hold.md` | voltage |
| Amplifier & Filter | `references/categories/amplifier-filter.md` | current |
| Digital Logic | `references/categories/digital-logic.md` | voltage |
| Signal Source | `references/categories/signal-source.md` | voltage |
| Passive & Model | `references/categories/passive-model.md` | current |
| Measurement Helpers | `references/categories/measurement-helpers.md` | voltage |
| Testbench (`.scs`) | `references/categories/testbench-spectre.md` | N/A |
| Power & Switch | `references/categories/power-switch.md` | either |
| Calibration | `references/categories/calibration.md` | voltage |

---

## Module Template

Start from `assets/template.va`. Reference examples in `assets/examples/`.

---

## Useful Syntax — Common Patterns

### Mathematical Constants — Define at Top

Verilog-A does not predefine `PI`. Define at module top or use numeric literals:

**Option A: Use `define` macro**
```verilog
`define PI 3.14159265359

module example (...);
    // ...
    phase = 2 * `PI * freq * $abstime;
endmodule
```

**Option B: Use numeric literal**
```verilog
module example (...);
    // ...
    phase = 2 * 3.14159265359 * freq * $abstime;
endmodule
```

---

### `V(A, B)` — differential voltage
```verilog
Dp = V(VINP, VINN) > VOS;        // compare differential pair against offset
```

### `@(above())` — level-sensitive threshold
```verilog
@(above(V(RST) - vth)) begin     // fires at t=0 if already true
    state = 0;
end
```

### Internal voltage nodes
```verilog
voltage [15:0] shadow;
V(shadow[i]) <+ transition(active ? 1 : 0, 0, 100p, 1p);
V(OUT[i]) <+ transition((V(shadow[i]) > 0.5) ? vh : vl, 0);
```

### `transition()` as intermediate variable
```verilog
real clk_delayed;
clk_delayed = transition(cond ? 1 : 0, 200p, 1p, 1p);
V(CLKOUT) <+ transition((clk_delayed > 0.5) ? vh : vl, 0);
```

### `analog` single-line (no `begin/end`)
```verilog
analog
    V(sigout) <+ k1 * V(sigin1) + k2 * V(sigin2);
```

### `generate` — compile-time loop
```verilog
generate j (0, 7) begin
    comp_var[j] = 1.0 + mismatch * abs($random(j) / `MAXINT);
end
```

### `$random()` — mismatch modeling
```verilog
r1 = abs($random(seed) / `MAXINT);   // uniform [0, 1]
cap = cap_nominal * (1.0 + r1 * mismatch);
```

### `@(final_step)` — end-of-simulation
```verilog
@(final_step) begin
    $strobe("samples = %d, avg = %f", cnt, sum / cnt);
    $fclose(fh);
end
```

### `@(initial_step("analysis"))` — filtered init
```verilog
`define PI 3.14159265359

@(initial_step("ac", "dc")) begin
    c = 1 / (2 * `PI * r * bandwidth);
end
```

### `$abstime` — simulation time
```verilog
`define PI 3.14159265359

phase = 2 * `PI * freq * $abstime;
```

### `$bound_step()` — timestep control
```verilog
$bound_step(1.0 / (32 * inst_freq));
```

### `$display` / `$strobe` / `$finish`
```verilog
$display("val = %f at t = %e", val, $abstime);   // immediate
$strobe("val = %f", val);                          // end of timestep
$finish;                                            // terminate
```

### File I/O: `$fopen` / `$fstrobe` / `$fclose`
```verilog
@(initial_step) fh = $fopen("output.dat", "w");
@(timer(next)) $fstrobe(fh, "%e\t%e", $abstime, V(sig));
@(final_step) $fclose(fh);
```

### `idtmod()` — modular integration (VCO)
```verilog
`define PI 3.14159265359

phase = idtmod(freq, 0, 1);
V(out) <+ amp * sin(2 * `PI * phase);
```

### `case/endcase`
```verilog
case (state)
    0: out = vl;
    1: out = vh;
endcase
```

---

## Advanced Syntax

For specialized use cases (string parsing, analysis-specific code, current-domain functions, etc.),
see `references/verilog-a-advanced.md`.

---

## Domain Classification

Scan the `analog begin` block to classify the module's domain.

### Construct → Domain

**Voltage-domain** (event-driven — EVAS):
Read from EVAS manifest for the latest list. Obtain manifest in order:
1. EVAS CLI: `evas --capabilities` (if installed)
2. GitHub: `https://raw.githubusercontent.com/Arcadia-1/EVAS/main/evas-capabilities.manifest`
3. Local cache: `references/evas-capabilities.manifest`

If fetched successfully, update the local cache.

**Current-domain** (KCL solver — OpenVAF + ngspice) — these are permanent, won't change:
`I() <+`, `V(a,b) <+ I(a,b)*R`, `ddt()`, `idt()`, `idtmod()`, `laplace_nd()`,
`limexp()`, `slew()`, `$vt`/`$temperature`, `flicker_noise()`, `white_noise()`,
`branch`, `nature`/`discipline`

**Domain-neutral** (either):
`V()` read-only, `parameter`/`real`/`integer`, `if/else`/`for`/`generate`,
`` `define ``/`` `ifdef ``/`` `include ``, math functions, `exclude`/`from`

### Decision tree

```
1. Has current-domain constructs? (I() <+, ddt, idt, idtmod, laplace_nd, limexp, slew, branch)
   YES → also has voltage-only? (@(cross), transition, genvar, arrays)
         YES → MIXED: reject, suggest splitting (see domain-routing.md)
         NO  → CURRENT-DOMAIN → OpenVAF + ngspice
   NO  → VOLTAGE-DOMAIN → EVAS (or pure V() <+ expression default)
```

"Either" categories (DAC, PLL, Power/Switch) require code-level analysis.

---

## Simulation Routing

See `references/domain-routing.md` for full details.

EVAS capabilities: fetch manifest per § Domain Classification above.
Local cache: `references/evas-capabilities.manifest`.

- **Voltage-domain** → ready for EVAS as-is
- **Current-domain** → delegate to `openvaf` skill
- **Mixed** → do NOT simulate; guide user to split (see domain-routing.md § Mixed)

---

## Smoke Test

### Current-domain
Delegate to `openvaf` skill: compile check → load check → tran sanity.

### Voltage-domain
Use EVAS for local simulation when the CLI is installed/configured.
If EVAS is unavailable in the current environment, fall back to a static
compatibility check against `evas-capabilities.manifest`.

### Mixed-domain
Do not attempt. Refer to `domain-routing.md § Mixed`.

---

## ADC Characterization & Verification

**If the module is ADC-related (SAR, flash, pipeline, TIADC, etc.), always use python library adctoolbox for verification. Never hand-roll FFT with scipy.**

- Metrics: ENOB, SNDR, SFDR, THD, SNR; TIADC per-channel mismatch, nonlinearity, jitter
- Always call `find_coherent_frequency()` to avoid spectral leakage
- Read results from the dict: `result['enob']`, `result['sndr_db']`, `result['sfdr_db']`, `result['bin_idx']`, etc.
- Full workflow: `references/adc-testbench-guide.md` · Examples: `assets/examples/adc-verification/`

---

## Customization

Read `references/customize.md` at session start for project-specific overrides
(port naming, supply voltage, file headers, simulator config).
