# Domain Routing

Route Verilog-A modules to the correct simulator based on domain classification.

> **Source of truth:** EVAS manifest from `https://github.com/Arcadia-1/EVAS`.
> Obtain per SKILL.md § Domain Classification (CLI → GitHub raw → local cache).
> Local cache: `evas-capabilities.manifest` in this directory.

---

## Voltage-Domain (EVAS)

**Site:** https://evas.tokenzhang.com/
**Status:** In development.

Supported/unsupported constructs: read `evas-capabilities.manifest`.

### Pre-flight Checklist

1. No constructs from manifest `[unsupported]` appear in the module
2. All outputs use `V(node) <+ transition(...)` or `V(node) <+ expression`
3. Edge detection uses `@(cross(...))` with explicit direction
4. All state initialized in `@(initial_step)`

### Invocation

Check `customize.md` for `voltage_simulator_cmd`. If not configured, report
the module as EVAS-compatible pending CLI availability.

---

## Current-Domain (OpenVAF + ngspice)

Delegate to the `openvaf` companion skill:
1. **Compile:** `openvaf file.va` → `.osdi`
2. **Load:** ngspice loads OSDI at startup
3. **Simulate:** DC, AC, tran, noise

### Voltage→Current Adaptation Checklist

If converting a voltage-domain module to current-domain:
1. `@(cross())` → continuous-time threshold comparisons
2. `transition()` → `tanh()`-based smooth switching or `ddt()`-based slew
3. `genvar` loops → unrolled statements
4. Array indexing → explicit variable naming
5. `@(initial_step)` → parameter-based initial conditions

---

## Mixed Domain — Reject and Split

Module contains both voltage-only (`@(cross)`, `transition`) and current-only
(`I() <+`, `ddt()`) constructs → cannot run on either simulator.

### Split Strategy

Create two `.va` files:
- **Sub-module A (voltage):** `@(cross())`, `transition()`, FSMs, counters → `V(node) <+ transition(...)` outputs
- **Sub-module B (current):** `I() <+`, `ddt()`, `laplace_nd()` → reads `V(node)` inputs

| Original | Voltage Sub-module | Current Sub-module |
|---|---|---|
| Charge pump + PFD | PFD: edge detection, UP/DOWN | CP: `I() <+` current steering |
| LDO + digital controller | Controller: FSM, trim logic | Regulator: `laplace_nd()` loop |
| SAR ADC + CDAC | SAR logic: bit-cycling FSM | CDAC: `I() <+ ddt(C*V)` |
| VCO + digital divider | Divider: counter, modulus | VCO: `idtmod()`, `I() <+` tank |

### Interface Conventions

- Use `V(node)` signals at boundary (no `I() <+` across interface)
- Voltage sub-module drives with `transition()`, current sub-module reads as `V(node)`
- Document interface in both sub-module headers

---

## Syncing with EVAS

EVAS `[unsupported]` constructs (`I() <+`, `ddt()`, `idt()`) are **permanent
architectural exclusions** — EVAS will never add KCL solving.

What may change:
1. New `[supported]` constructs → update manifest
2. CLI/runtime changes → update `voltage_simulator_cmd` and related examples in `customize.md`
