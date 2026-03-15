---
name: veriloga
description: >
  Write Verilog-A behavioral modules for analog/mixed-signal IC design (Cadence Virtuoso / Spectre).
  Covers 12 circuit categories. Trigger on: write/generate/review/fix Verilog-A, .va files,
  "behavioral model", "veriloga", "analog HDL", circuit spec → behavioral model, or
  "simulate this module", "voltage-domain", "current-domain".
---

# Verilog-A Writer

Write correct, Virtuoso-ready Verilog-A behavioral modules. Rules extracted from 1,638
real-world .va files plus a 171-module reference library (14,311 LOC).

## How to Use This Skill

1. **Identify the circuit category** → see Category Index
2. **Read the category reference** in `references/categories/`
3. **Apply all mandatory rules** below
4. **Start from template** `assets/template.va`
5. **Check customization** `references/customize.md` for project overrides
6. **Classify domain** → scan code for voltage vs current constructs (see Domain Classification)
7. **Route to simulator** (optional) → EVAS for voltage-domain, openvaf for current-domain
8. **Verify** (optional) → smoke test on the appropriate simulator (see Smoke Test)
9. **Explain usage** → list every port (direction, what to connect) and key parameters
10. **Learn conventions** → if user comments on style, ask to save to `references/customize.md`

---

## Mandatory Rules

Violating any rule causes simulator errors or silently wrong results.

### Rule 1: All signals use `electrical` type

No `wire`, `logic`, or `reg`. Spectre accepts two port styles:

**Style A: ANSI inline**
```
module example (inout electrical VDD, inout electrical VSS, input electrical clk_i, output electrical [3:0] dout_o);
```

**Style B: Old-style separated**
```
module example (VDD, VSS, clk_i, dout_o);
inout VDD, VSS;
input clk_i;
output [3:0] dout_o;
electrical VDD, VSS, clk_i;
electrical [3:0] dout_o;
```

**NOT accepted** — combined `inout electrical` in body:
```
module example (VDD, VSS, clk_i, dout_o);
    inout electrical VDD, VSS;       // WRONG — Spectre syntax error
```

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

### Rule 5: Loop variables use `genvar`

`integer` loop index causes elaboration errors in most simulators.

### Rule 6: Initialize state in `@(initial_step)`

Uninitialized variables default to 0 or garbage depending on simulator.

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
| Testbench & Probe | `references/categories/testbench-probe.md` | voltage |
| Power & Switch | `references/categories/power-switch.md` | either |
| Calibration | `references/categories/calibration.md` | voltage |

---

## Module Template

Start from `assets/template.va`. Reference examples in `assets/examples/`.

---

## Useful Syntax

### `V(A, B)` — differential voltage
```
Dp = V(VINP, VINN) > VOS;        // compare differential pair against offset
```

### String parameters — `.len()` / `.substr()`
```
parameter conf = "10110";
integer conf_list[4:0];
@(initial_step) begin
    for (i = 0; i < conf.len(); i = i + 1)
        conf_list[i] = (conf.substr(i, i) == "1");
end
```

### `@(above())` — level-sensitive threshold
```
@(above(V(RST) - vth)) begin     // fires at t=0 if already true
    state = 0;
end
```

### Internal voltage nodes
```
voltage [15:0] shadow;
V(shadow[i]) <+ transition(active ? 1 : 0, 0, 100p, 1p);
V(OUT[i]) <+ transition((V(shadow[i]) > 0.5) ? vh : vl, 0);
```

### `transition()` as intermediate variable
```
real clk_delayed;
clk_delayed = transition(cond ? 1 : 0, 200p, 1p, 1p);
V(CLKOUT) <+ transition((clk_delayed > 0.5) ? vh : vl, 0);
```

### `analog` single-line (no `begin/end`)
```
analog
    V(sigout) <+ k1 * V(sigin1) + k2 * V(sigin2);
```

### `generate` — compile-time loop
```
generate j (0, 7) begin
    comp_var[j] = 1.0 + mismatch * abs($random(j) / `MAXINT);
end
```

### `$random()` — mismatch modeling
```
r1 = abs($random(seed) / `MAXINT);   // uniform [0, 1]
cap = cap_nominal * (1.0 + r1 * mismatch);
```

### Parameterized `` `define ``
```
`define FRAC_MM(I) (1.0 + mismatch * abs($random(I) / `MAXINT))
comp_var[0] = `FRAC_MM(seed0);
`undef FRAC_MM
```

### `@(final_step)` — end-of-simulation
```
@(final_step) begin
    $strobe("samples = %d, avg = %f", cnt, sum / cnt);
    $fclose(fh);
end
```

### `@(initial_step("analysis"))` — filtered init
```
@(initial_step("ac", "dc")) begin
    c = 1 / (2 * `PI * r * bandwidth);
end
```

### `$abstime` — simulation time
```
phase = 2 * `PI * freq * $abstime;
```

### `$bound_step()` — timestep control
```
$bound_step(1.0 / (32 * inst_freq));
```

### `$display` / `$strobe` / `$finish`
```
$display("val = %f at t = %e", val, $abstime);   // immediate
$strobe("val = %f", val);                          // end of timestep
$finish;                                            // terminate
```

### File I/O: `$fopen` / `$fstrobe` / `$fclose`
```
@(initial_step) fh = $fopen("output.dat", "w");
@(timer(next)) $fstrobe(fh, "%e\t%e", $abstime, V(sig));
@(final_step) $fclose(fh);
```

### `$vt` / `$temperature`
```
I(a, c) <+ is * (limexp(V(a, c) / $vt) - 1);   // $vt ≈ 25.86 mV @ 300K
```

### `@(timer())` — periodic event
```
@(timer(next_sample)) begin
    val = V(sig);
    next_sample = next_sample + t_sample;
end
```

### `idtmod()` — modular integration (VCO)
```
phase = idtmod(freq, 0, 1);
V(out) <+ amp * sin(2 * `PI * phase);
```

### `slew()` — rate limiter
```
V(out) <+ slew(V(in), max_slope, -max_slope);
```

### `limexp()` — convergence-safe exponential
```
I(a, c) <+ is * (limexp(V(a, c) / $vt) - 1);
```

### `last_crossing()` — time of last crossing
```
t_cross = last_crossing(V(sig) - vth, +1);
```

### `case/endcase`
```
case (state)
    0: out = vl;
    1: out = vh;
endcase
```

### `branch` — named branch
```
branch (IN, OUT) sw;
I(IN, OUT) <+ V(sw) * transition(cond, 0, 10p);
```

### `analysis()` — test analysis type
```
if (analysis("ac")) V(out) <+ gain * V(in);
```

### `` `ifdef `` — conditional compilation
```
`ifdef __VAMS_ENABLE__
    iin = I(<vin>);
`else
    iin = I(vin, vin);
`endif
```

### `exclude` — parameter range exclusion
```
parameter real gain = 1 from (-inf:inf) exclude 0;
```

### `current` type / `I()` single-node
```
output current iout;
I(iout) <+ gm * V(vin);
```

### `nature` — custom physical quantity
```
nature Position
    units = "m"; access = Pos; abstol = 1u;
endnature
```

---

## Domain Classification

Scan the `analog begin` block to classify the module's domain.

### Construct → Domain

**Voltage-domain** (event-driven — EVAS):
`V() <+`, `transition()`, `@(cross)`, `@(above)`, `@(timer)`, `@(initial_step)`,
`@(final_step)`, `genvar`, arrays, `case`, `$abstime`, `$bound_step()`,
`$display`/`$strobe`/`$finish`, `$fopen`/`$fstrobe`/`$fclose`, `$random()`,
`last_crossing()`, `analysis()`

**Current-domain** (KCL solver — OpenVAF + ngspice):
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

See `references/domain-routing.md` for full details. EVAS capabilities declared in
`references/evas-capabilities.manifest` (single source of truth).

- **Voltage-domain** → ready for EVAS as-is
- **Current-domain** → delegate to `openvaf` skill
- **Mixed** → do NOT simulate; guide user to split (see domain-routing.md § Mixed)

---

## Smoke Test

### Current-domain
Delegate to `openvaf` skill: compile check → load check → tran sanity.

### Voltage-domain
EVAS in development (`evas_status` in `customize.md`). While unavailable:
static check against `evas-capabilities.manifest` only.

### Mixed-domain
Do not attempt. Refer to `domain-routing.md § Mixed`.

---

## Customization

Read `references/customize.md` at session start for project-specific overrides
(port naming, supply voltage, file headers, simulator config).
