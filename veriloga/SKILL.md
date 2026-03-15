---
name: veriloga
description: >
  Write production-quality Verilog-A behavioral modules for analog and mixed-signal IC design.
  Covers all major circuit categories: ADC/SAR, DAC, comparators, PLL/clock, amplifiers,
  filters, digital logic, counters, registers, state machines, sample-and-hold, signal sources,
  passive device models, testbenches, switches, and calibration/trim blocks.
  Use this skill whenever the user asks to write, generate, review, fix, or refactor Verilog-A
  code (.va files), or asks about Verilog-A syntax, patterns, or best practices — even if they
  just say "behavioral model", "veriloga block", "analog HDL", or describe a circuit function
  without mentioning Verilog-A by name. Also trigger when the user pastes Verilog-A code and
  asks for help, or wants to convert a circuit spec into a behavioral model. Also trigger when
  the user asks to "simulate this module", "which simulator", "voltage-domain", or "current-domain".
---

# Verilog-A Writer

Write correct, simulator-ready Verilog-A behavioral modules. This skill encodes rules extracted
from 1,638 real-world .va files across 10+ circuit domains, plus battle-tested coding guidelines.

## How to Use This Skill

1. **Identify the circuit category** from the user's request (see Category Index below)
2. **Read the relevant category reference** in `references/categories/` for port conventions,
   parameter patterns, and analog block structures specific to that circuit type
3. **Apply all mandatory rules** (below) — these are non-negotiable
4. **Use the module template** in `assets/template.va` as your starting skeleton
5. **Customize** — check `references/customize.md` if the user has project-specific overrides
6. **Classify the module's domain** — after writing code, scan the `analog begin` block to
   determine voltage-domain vs. current-domain (see Domain Classification below)
7. **Route to the correct simulator** — based on the domain classification, route the module
   to the appropriate simulation path (see Simulation Routing below)
8. **Verify (optional)** — when the user asks to confirm the module works, run a smoke test
   on the appropriate simulator (see Smoke Test below)

If the user's request spans multiple categories (e.g., "write me a SAR ADC"), compose modules
from the relevant categories — one module per function block.

---

## Mandatory Rules

These 8 rules come from analyzing thousands of real designs. Violating any one of them will
cause simulator errors or silently wrong results. Every module you write must pass all 8.

### Rule 1: All signals use `electrical` type
Every port and internal node must be declared `electrical`. No `wire`, `logic`, or other types.

Spectre accepts two port declaration styles — both are valid:

**Style A: ANSI inline** (direction + type in the module port list)
```
module example (inout electrical VDD, inout electrical VSS, input electrical clk_i, output electrical [3:0] dout_o);
```

**Style B: Old-style separated** (direction and type as separate statements in body)
```
module example (VDD, VSS, clk_i, dout_o);
inout VDD, VSS;
input clk_i;
output [3:0] dout_o;
electrical VDD, VSS, clk_i;
electrical [3:0] dout_o;
```

**NOT accepted by Spectre** — combined `inout electrical` in body:
```
module example (VDD, VSS, clk_i, dout_o);
    inout electrical VDD, VSS;       // WRONG — Spectre syntax error
    input electrical clk_i;          // WRONG
```

### Rule 2: Power ports are `inout`, not `input`
VDD and VSS must be `inout` because the simulator needs to solve current through them.
Declaring them as `input` silently breaks power-aware simulation.
```
inout VDD, VSS;    // Correct (old-style)
input VDD, VSS;    // WRONG — simulator can't solve supply current
```

### Rule 3: Supply voltages — read from ports or parameterize
Never hardcode voltage literals like `1.8` directly in the logic. Two approaches:

**Option A: Read from power ports** (when VDD/VSS are module ports)
```
vh = V(VDD);
vl = V(VSS);
vth = (vh + vl) / 2.0;
```

**Option B: Use parameters** (when no power ports, e.g., ideal models)
```
parameter real vdd = 1.0;
parameter real vth = vdd / 2.0;
```

Both are acceptable — choose based on user's needs. Default threshold is `vth = (vdd + vss) / 2`.

### Rule 4: All variable declarations at module level
Every `parameter`, `real`, `integer`, and `genvar` declaration must appear between the port
declarations and `analog begin`. Declaring variables inside `analog begin` is a syntax error
in standard Verilog-A (some simulators accept it, most don't).
```
module example (inout electrical VDD, inout electrical VSS, input electrical in_i, output electrical out_o);

    parameter real vth = 0.5;       // Here — at module level
    real vh, vl, in_val;            // Here — at module level
    integer state;                  // Here — at module level

    analog begin
        // NO declarations here
        vh = V(VDD);
        ...
    end
endmodule
```

### Rule 5: Loop variables use `genvar`
For `for` loops inside `analog begin`, the loop index must be `genvar`, not `integer`.
```
genvar i;                           // Correct
// integer i;                       // WRONG — causes elaboration error

analog begin
    for (i = 0; i < 8; i = i + 1) begin
        ...
    end
end
```

### Rule 6: Initialize state in `@(initial_step)`
All state variables (counters, registers, flags) must be set to known values inside
`@(initial_step)`. Uninitialized variables default to 0 in some simulators but garbage in
others — always be explicit.
```
@(initial_step) begin
    count = 0;
    state = 0;
    prev_val = 0.0;
end
```

### Rule 7: Edge detection uses `@(cross())` with direction
Rising edge: `+1`. Falling edge: `-1`. Always specify the direction explicitly.
The threshold should be derived from the supply, not hardcoded.
```
vth = (vh + vl) / 2.0;
@(cross(V(clk_i) - vth, +1))       // Rising edge
    count = count + 1;
@(cross(V(clk_i) - vth, -1))       // Falling edge
    state = 0;
```

### Rule 8: Outputs use `transition()` with supply voltages
Every digital output must go through `transition()` to avoid discontinuities that crash the
simulator. Use the actual supply voltages, not literals.
```
V(out_o) <+ transition(state ? vh : vl, trise, tfall);
```
Never put macros (`` `define`` values) as the delay/rise/fall arguments of `transition()` —
some simulators can't resolve them there.

---

## Category Index

Read the matching reference file before writing a module in that category.

| Category | Reference File | When to Use | Domain |
|---|---|---|---|
| ADC / SAR | `references/categories/adc-sar.md` | SAR logic, bit-cycling, pipeline stages, flash sub-ADC, CDAC | voltage |
| DAC | `references/categories/dac.md` | Current-steering, R-string, binary-weighted, thermometer DAC | either |
| Comparator | `references/categories/comparator.md` | StrongARM, dynamic, latching, clocked comparators | voltage |
| PLL / Clock | `references/categories/pll-clock.md` | VCO, DCO, PFD, charge pump, dividers, TDC, DTC | either |
| Sample & Hold | `references/categories/sample-hold.md` | Track-and-hold, bootstrap switch, sampler | voltage |
| Amplifier & Filter | `references/categories/amplifier-filter.md` | Opamp, OTA, LPF, BPF, HPF, integrators | current |
| Digital Logic | `references/categories/digital-logic.md` | Gates, flip-flops, MUX, decoder, counter, register, FSM | voltage |
| Signal Source | `references/categories/signal-source.md` | AM/FM/QAM modulators, pulse gen, ramp, sinusoidal | voltage |
| Passive & Model | `references/categories/passive-model.md` | Behavioral R/C/L, MOSFET, BJT, diode models | current |
| Testbench & Probe | `references/categories/testbench-probe.md` | TB wrappers, probes, meters, stimulus drivers | voltage |
| Power & Switch | `references/categories/power-switch.md` | Bootstrap, ESD clamp, switched-cap, conductance switch | either |
| Calibration | `references/categories/calibration.md` | Trim DAC, foreground/background cal, code generators | voltage |

---

## Module Template

Start every new module from `assets/template.va`. It has the correct structure with
placeholder comments showing where each section goes.

---

## Common Pitfalls

Mistakes that compile but produce wrong simulation results — the worst kind of bugs:

1. **Forgetting `@(initial_step)`** — state variables start at 0 or garbage depending on
   simulator. Your counter works in Spectre but fails in ADS.

2. **Wrong `cross()` direction** — `+1` means rising, `-1` means falling. Mixing them up
   makes your flip-flop trigger on the wrong edge. Double-check against the spec.

3. **Hardcoded voltages in `transition()`** — writing `transition(1.8, ...)` instead of
   `transition(vh, ...)` means your block breaks at 0.9V supply. Always use variables.

4. **Multiple `<+` to same node** — Verilog-A *adds* contributions. If you accidentally write
   `V(out) <+` twice to the same output, you get the sum, not an overwrite. Use a temporary
   variable and assign once.

5. **`integer` loop variable** — works in some simulators, fails in others. Always `genvar`.

6. **Variables inside `analog begin`** — accepted by Cadence Spectre in some modes, rejected
   by everything else. Always declare at module level.

7. **Missing power ports** — if your module references VDD/VSS but doesn't declare them as
   `inout`, the simulator either errors or silently uses 0V.

---

## Domain Classification

After writing the module code, scan the `analog begin` block to classify the module's domain.
This determines which simulator can run it.

| Constructs present in `analog begin` | Domain |
|---|---|
| `V() <+` with `@(cross())` or `transition()`, and NO `I() <+` | **voltage** |
| `I() <+` or `ddt()` / `idt()` / `laplace_nd()`, and NO `@(cross())` / `transition()` | **current** |
| Both voltage-domain and current-domain constructs | **mixed → reject** |
| Pure `V(node) <+ expression` with no `I() <+`, no `@(cross())`, no `transition()` | **voltage** |

**Special case:** `V(a,b) <+ I(a,b) * R` (branch voltage as function of branch current) is
a current-domain construct — it requires a SPICE-class solver.

**"either" categories** (DAC, PLL/Clock, Power & Switch) require code-level analysis — do not
guess the domain from the category name alone. Check what constructs the generated code actually uses.

---

## Simulation Routing

After classifying the domain, route the module to the correct simulator. See
`references/domain-routing.md` for full details on each path. The voltage-domain
simulator's actual capabilities are declared in `references/evas-capabilities.manifest`
— that file is the single source of truth; if it has been updated, its contents
override the snapshot below.

Decision tree:

```
IF code contains @(cross()) OR transition() OR genvar OR arrays:
    IF code also contains I() <+:
        → MIXED: reject — suggest splitting (see domain-routing.md § Mixed)
    ELSE:
        → VOLTAGE-DOMAIN: route to custom voltage-domain simulator
          (see domain-routing.md § Voltage)

ELSE IF code contains I() <+ OR ddt() OR idt() OR laplace_nd():
    → CURRENT-DOMAIN: route to OpenVAF + ngspice
      (see domain-routing.md § Current)

ELSE:
    → VOLTAGE-DOMAIN: pure V(node) <+ expression defaults to voltage domain
```

When routing:
- **Voltage-domain** — the module is ready for the custom voltage-domain simulator as-is
- **Current-domain** — delegate to the `openvaf` skill for compilation and simulation
- **Mixed** — do NOT attempt simulation; explain the conflict and guide the user to split
  the module into separate voltage-domain and current-domain sub-modules

---

## Smoke Test

When the user asks to verify a module actually works (e.g., "run it", "test it",
"confirm it compiles", "can you check this"), run a smoke test on the appropriate simulator.

### Current-domain smoke test

Delegate to the `openvaf` skill. The minimal verification is:

1. **Compile check:** `openvaf <file>.va` — confirms syntax and construct compatibility
2. **Load check:** generate a minimal ngspice netlist that instantiates the module, run
   `ngspice -b` — confirms OSDI loading and port binding
3. **Tran sanity:** if the module has a meaningful transient response, run a short `.tran`
   and verify the output is non-zero / non-NaN

Report: pass/fail for each step, with the first error message if any step fails.

### Voltage-domain smoke test

EVAS is still in development (`evas_status: in-development` in `customize.md`).
While EVAS CLI is not yet available:

1. **Static check only:** scan the module code and confirm no `[unsupported]` constructs
   from `references/evas-capabilities.manifest` are present
2. **Report compatibility:** tell the user "this module is EVAS-compatible (static check
   passed)" or list the incompatible constructs found

Once EVAS CLI is ready (`evas_status: ready`):

1. **Compile check:** `evas compile <file>.va` (or configured `voltage_simulator_cmd`)
2. **Run check:** `evas run <file>.va` with a minimal stimulus
3. **Output sanity:** verify output waveform is non-trivial

### Mixed-domain smoke test

Do not attempt. Explain the conflict and refer to `domain-routing.md § Mixed` for
the splitting guide.

---

## Customization

Users can override default conventions (port naming, default parameters, header style) by
editing `references/customize.md`. Read that file at the start of every session to pick up
any project-specific settings.
