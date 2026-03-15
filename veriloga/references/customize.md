# Customization Guide

Override default conventions to match your project's coding standards. Edit the sections
below — the skill reads this file at the start of every session.

---

## Port Naming Convention

Default suffixes (delete or change as needed):

```
Input ports:   _i     (e.g., clk_i, data_i, rst_i)
Output ports:  _o     (e.g., out_o, done_o, rdy_o)
Power ports:   VDD, VSS  (uppercase, no suffix)
Bus notation:  [N:0]  (e.g., [7:0] data_i)
```

To use a different convention (e.g., no suffix, `_in`/`_out`, `_p`/`_n`), edit above.

---

## Default Parameters

Override the default parameter values used when no spec is given:

```
Supply voltage:     0.9       (change for 1.8V, 3.3V, 5V processes)
Clock threshold:    derived   (always (vh + vl) / 2.0 from supply)
Output rise time:   10e-12    (10 ps)
Output fall time:   10e-12    (10 ps)
Propagation delay:  0         (ideal by default)
```

---

## File Header

Template prepended to every generated .va file. Edit freely:

```
// ────────────────────────────────────────────────────────────
// Module: <auto-filled>
// Description: <auto-filled>
// Author: <your name or team>
// Date: <auto-filled>
// ────────────────────────────────────────────────────────────
```

Set `Author` to your name/team to auto-populate.

---

## Include Directives

Default includes (change if your simulator uses different paths):

```
`include "constants.vams"
`include "disciplines.vams"
```

Some projects use:
```
`include "discipline.h"
`include "constants.h"
```

---

## Simulator-Specific Tweaks

Uncomment the line matching your primary simulator:

```
// simulator: spectre       (Cadence Spectre — most permissive)
// simulator: ams           (Cadence AMS — stricter variable scoping)
// simulator: ads           (Keysight ADS — different noise syntax)
// simulator: hspice        (Synopsys HSPICE — limited Verilog-A subset)
```

When set, the skill avoids constructs known to cause issues in that simulator.

---

## Extra Rules

Add any project-specific rules here. The skill will treat them as mandatory
(same weight as the 8 core rules in SKILL.md).

```
# Example:
# - All modules must include a `version` parameter
# - Use `gnd` instead of `VSS`
# - Maximum 100 lines per module
# - No `$strobe` or `$display` in production code
```

---

## Disabled Categories

If your project doesn't use certain circuit types, list them here to skip
their reference files (saves context):

```
# Example:
# - signal-source
# - testbench-probe
```

---

## Domain Routing Overrides

Override the automatic domain classification and simulator routing behavior.

### Force Domain

Force all modules to a specific domain (bypasses code-level analysis):

```
# force_domain: voltage
# force_domain: current
# force_domain: auto          (default — use code analysis)
```

### Custom Voltage-Domain Simulator

Path and invocation for the EVAS voltage-domain simulator
(https://github.com/Arcadia-1/EVAS — still in development):

```
# voltage_simulator_path: /path/to/evas
# voltage_simulator_cmd: evas run {file}
# evas_status: in-development
```

When `evas_status` is `in-development`, the skill will classify the domain and
confirm the module is EVAS-compatible, but will NOT attempt to invoke the simulator.
Change to `ready` once EVAS CLI is usable.

### Disable Routing

Turn off domain classification and simulation routing entirely (Steps 6-7 are skipped):

```
# disable_domain_routing: true
```
