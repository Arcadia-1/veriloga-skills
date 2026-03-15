# Domain Routing

How to route a Verilog-A module to the correct simulator based on its domain classification.

> **Capability source of truth:** `references/evas-capabilities.manifest`
> Read that file first — it defines exactly which constructs the voltage-domain simulator
> (EVAS) currently supports. The lists below are derived from it. If they conflict,
> the manifest wins.

---

## Voltage-Domain Simulator (EVAS)

**Repository:** https://github.com/Arcadia-1/EVAS
**Status:** In development — capabilities may change between syncs.

The EVAS simulator's supported and unsupported constructs are declared in
`references/evas-capabilities.manifest`. Read that file to get the current list.
Do NOT rely on the summary below if the manifest has been updated more recently.

**Supported constructs (snapshot):** `V() <+`, `@(cross())`, `transition()`, `genvar`,
arrays, `@(initial_step)`, `$abstime`, `$bound_step()`, `$fopen`/`$fdisplay`/`$fclose`.

**Not supported (snapshot):** `I() <+`, `ddt()`, `idt()`, `idtmod()`, `laplace_nd()`,
`laplace_zp()`, `flicker_noise()`, `white_noise()`, KCL-based solving.

### Module Preparation Checklist

Before sending a module to EVAS, verify against the manifest's `[unsupported]` section:

1. No constructs from the `[unsupported]` list appear in the module
2. All outputs use `V(node) <+ transition(...)` or `V(node) <+ expression`
3. Edge detection uses `@(cross(...))` with explicit direction (`+1` or `-1`)
4. All state is initialized in `@(initial_step)`

### Invocation

EVAS CLI interface is under development. Check `references/customize.md` for the
configured `voltage_simulator_cmd`. If not configured, inform the user that the module
is voltage-domain and ready for EVAS once its CLI is available.

---

## Current-Domain (OpenVAF + ngspice)

**Supported constructs:** `I() <+`, `V() <+` (as voltage source), `ddt()`, `idt()`,
`idtmod()`, `laplace_nd()`, `laplace_zp()`, `flicker_noise()`, `white_noise()`,
`$bound_step()`, `$temperature`, `$vt`.

**Not supported:** `@(cross())`, `transition()`, `genvar`, arrays, `@(initial_step)`,
`$abstime`, `$fopen`/`$fdisplay`/`$fclose`.

### Delegation to openvaf Skill

Current-domain modules are compiled and simulated via the `openvaf` companion skill.
The workflow is:

1. **Compile:** OpenVAF compiles the `.va` file into an OSDI shared library
2. **Load:** ngspice loads the OSDI library at startup
3. **Simulate:** Standard SPICE simulation (DC, AC, tran, noise)

### Adaptation Checklist

If a module was originally written with voltage-domain constructs and needs to be
converted to current-domain:

1. Replace `@(cross(...))` edge detection with continuous-time threshold comparisons
2. Replace `transition()` output smoothing with `ddt()`-based slew limiting or
   `tanh()`-based smooth switching
3. Replace `genvar` loops with unrolled statements or parameter-computed expressions
4. Replace array indexing with explicit variable naming
5. Move initialization from `@(initial_step)` to parameter-based initial conditions

---

## Mixed Domain — Reject and Split

A module that contains **both** voltage-domain constructs (from the manifest's
`[supported]` list that are NOT in OpenVAF's supported set) **and** current-domain
constructs (`I() <+`, `ddt()`, `laplace_nd()`) cannot run on either simulator.
Do NOT attempt simulation.

### How to Identify the Split Boundary

1. **Find the interface signals** — which nodes carry information between the two domains?
2. **Draw the boundary** — voltage-domain logic on one side, current-domain analog on the other
3. **Define the interface** — the boundary becomes port connections between the two sub-modules

### Splitting Strategy

Create two separate `.va` files:

- **Sub-module A (voltage-domain):** Contains all `@(cross())`, `transition()`, state machines,
  counters, digital logic. Outputs digital control signals via `V(node) <+ transition(...)`.
- **Sub-module B (current-domain):** Contains all `I() <+`, `ddt()`, `laplace_nd()` constructs.
  Reads control signals as `V(node)` inputs.

### Common Split Examples

| Original Module | Voltage-Domain Sub-module | Current-Domain Sub-module |
|---|---|---|
| Charge pump (PFD + current source) | PFD: edge detection, UP/DOWN pulses | CP core: `I() <+` current steering |
| LDO (digital controller + analog regulator) | Controller: comparator, FSM, trim logic | Regulator: error amp, pass device, `laplace_nd()` loop |
| SAR ADC (logic + CDAC) | SAR logic: bit-cycling FSM, comparator interface | CDAC: charge redistribution via `I() <+ ddt(C*V)` |
| VCO with digital divider | Divider: counter, modulus control | VCO core: `idtmod()` phase, `I() <+` tank |

### Interface Conventions

When splitting a module:

- Use simple `V(node)` signals at the boundary (no `I() <+` across the interface)
- The voltage-domain sub-module drives digital signals with `transition()`
- The current-domain sub-module reads those signals as continuous `V(node)` inputs
- Document the interface in both sub-module headers with matching port names

---

## Syncing with EVAS Development

EVAS is an event-driven voltage-domain simulator. Its `[unsupported]` constructs
(`I() <+`, `ddt()`, `idt()`, etc.) are **permanent architectural exclusions** — EVAS
will never add KCL-based solving. The `[unsupported]` list in the manifest should not
change.

What may change as EVAS develops:

1. **New voltage-domain constructs** — if EVAS adds support for a new system function
   or behavioral construct, add it to `[supported]` in the manifest.
2. **CLI interface** — update `voltage_simulator_cmd` in `customize.md` when the EVAS
   CLI stabilizes. Change `evas_status` from `in-development` to `ready`.
3. **Bug fixes in construct support** — if EVAS tightens or loosens how it handles an
   existing `[supported]` construct, update the Module Preparation Checklist above.
