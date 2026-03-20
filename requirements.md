# Requirements

## veriloga skill

**No external dependencies.** Pure documentation/reference skill — any Agent can use it directly.

## Local Verification (Optional)

Finished modules can be verified locally. There are two verification paths depending on the constructs used in the module:

### Voltage-Domain Verification — EVAS

Applies to modules that use `V() <+` + `@(cross())` / `transition()` (SAR logic, DFF, counter, etc.).

```bash
uv tool install evas-sim
```

| Tool | Purpose | How to get |
|------|---------|------------|
| [EVAS](https://evas.tokenzhang.com/) | Event-driven Verilog-A simulator | `uv tool install evas-sim` |
| **evas-sim skill** | Complete instructions for Agent-driven EVAS simulation | `evas-sim/SKILL.md` in this repo |

### Current-Domain Verification — OpenVAF + ngspice

Applies to modules that use `I() <+` / `ddt()` / `laplace_nd()` (Opamp, RLC, VCO, etc.).

> **Installation is more involved**: you need to install the OpenVAF compiler and ngspice (≥ 38, with OSDI support) separately; on Windows, Visual C++ Build Tools are also required. See [`openvaf/references/install.md`](./openvaf/references/install.md) for details.
