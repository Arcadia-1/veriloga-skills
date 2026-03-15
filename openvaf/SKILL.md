---
name: openvaf
description: >
  Compile Verilog-A device models with OpenVAF and simulate them in ngspice via OSDI.
  Use this skill whenever the user wants to: compile a .va file, run a Verilog-A model
  in ngspice, use OpenVAF, load an OSDI model, test a compact device model, or set up
  the OpenVAF + ngspice toolchain. Also use when the user mentions OSDI, compact models,
  BSIM, PSP, HICUM, or wants to simulate custom MOSFET/BJT/diode/varactor models
  written in Verilog-A. Complements the `veriloga` writing skill and the `ngspice`
  simulation skill.
---

# OpenVAF + ngspice: Compile and Simulate Verilog-A Models

This skill covers the full flow: write a Verilog-A compact model → compile it with
OpenVAF → load the compiled `.osdi` plugin in ngspice → run simulations.

## Scope: What OpenVAF Can and Cannot Compile

OpenVAF implements the **analog subset** of the Verilog-AMS LRM 2.4.0. It is designed
for **compact device models** (MOSFETs, BJTs, diodes, varactors, resistors, capacitors)
— the kind of models that define I-V and C-V relationships.

### Supported features
- `analog begin` / `end` blocks
- `I()`, `V()` branch access, `<+` contributions
- `ddt()`, `idt()`, `idtmod()`, `ddx()`
- `$vt`, `$temperature`, `$abstime`
- `@(initial_step)`, `@(final_step)`
- `$strobe`, `$display`, `$bound_step`
- `limexp()`, `ln()`, `exp()`, `sqrt()`, `pow()`, `abs()`, `min()`, `max()`
- `$param_given()`, parameter ranges
- Noise: `white_noise()`, `flicker_noise()`
- All math from `constants.vams`

### NOT supported (will cause compile errors)
| Feature | Why |
|---|---|
| `@(cross(...))` | Event monitoring — behavioral, not compact-model |
| `@(above(...))` | Same reason |
| Named events, `or`-combined events | Same reason |
| Arrays inside modules (`integer A[0:7]`) | Not implemented |
| `genvar` / generate loops | Not implemented |
| Arithmetic shift (`<<<`, `>>>`) | Not implemented, no plans to add |
| Digital / mixed-signal constructs | Analog subset only |

**Bottom line:** If your `.va` file uses `@(cross)`, arrays, or `genvar`, it is a
behavioral model and cannot be compiled with OpenVAF. Use a full Verilog-AMS simulator
(Cadence AMS, Synopsys HSPICE, Mentor AFS) instead. The `veriloga` skill covers
writing both behavioral blocks and compact models; this skill covers compiling and
simulating the compact-model subset.

---

## 1. Installation

### OpenVAF (the compiler)

Read `references/install.md` for detailed step-by-step instructions for Windows and
Linux. The short version:

1. **Download** the prebuilt binary from https://openvaf.semimod.de/download/
   - Windows: rename the downloaded file to `openvaf.exe`
   - Linux: make executable with `chmod +x`
2. **Place on PATH** (e.g., `C:\tools\` on Windows, `/usr/local/bin/` on Linux)
3. **Windows only:** install Microsoft Visual C++ Build Tools
   ("Desktop development with C++" workload) — OpenVAF needs the MSVC linker
4. **Verify:** `openvaf --help` should print usage info

### ngspice (the simulator)

Requires **ngspice 39 or later** for OSDI support. Read the `ngspice` skill for
general ngspice setup, or see `references/install.md` for the OSDI-specific parts.

---

## 2. The Workflow

```
  .va file ──→ openvaf ──→ .osdi file ──→ ngspice loads it ──→ simulation
```

### Step 1: Compile

On **Linux** (or if MSVC is in PATH):
```bash
openvaf mymodel.va
```

On **Windows**, the MSVC linker environment must be loaded first. Use this
one-liner from any shell:
```bash
cmd.exe /c "call \"C:\Program Files (x86)\Microsoft Visual Studio\<ver>\BuildTools\VC\Auxiliary\Build\vcvarsall.bat\" x64 >nul 2>&1 & openvaf.exe mymodel.va"
```
Replace `<ver>` with your VS version (e.g., `18`, `2022`). Without this,
OpenVAF crashes because it can't find the MSVC `link.exe`.

Produces `mymodel.osdi` in the same directory. Compilation typically takes
under 1 second for simple models.

### Step 2: Write an ngspice netlist that loads the model

```spice
* Test circuit for mymodel
V1 in 0 DC 1.0

.control
pre_osdi mymodel.osdi
dc V1 0 5 0.01
plot -i(V1)
.endc

.model m1 mymodel paramA=1.0 paramB=2.0
Nr1 in 0 m1

.end
```

### Step 3: Run

```bash
ngspice test.spice
```

---

## 3. Netlist Rules for OSDI Models

These rules are specific to OSDI-loaded models in ngspice. Getting any of them wrong
causes cryptic errors.

### Rule 1: Use `pre_osdi`, not `osdi`

The `pre_` prefix tells ngspice to load the model **before** parsing the netlist.
Without it, ngspice won't recognize the model type and will fail.

```spice
.control
pre_osdi mymodel.osdi
.endc
```

### Rule 2: Instance names start with `N`

All OSDI device instances must have names beginning with the letter **N**:

```spice
Nr1 in out mymod            ✓ correct
Nq1 col base emit sub mymod ✓ correct
R1  in out mymod            ✗ wrong — ngspice treats it as a built-in resistor
M1  d g s b mymod           ✗ wrong — ngspice treats it as a built-in MOSFET
```

### Rule 3: `.model` uses the exact Verilog-A module name

The `.model` statement must reference the **exact module name** from the `.va` source:

```verilog
// In myresistor.va:
module myresistor(p, n);    // ← this name
```

```spice
.model r1k myresistor r=1000    ✓ matches module name
.model r1k resistor r=1000      ✗ wrong — conflicts with ngspice built-in
```

### Rule 4: Avoid module names that clash with ngspice built-ins

Do NOT name your module `resistor`, `capacitor`, `inductor`, `diode`, `nmos`, `pmos`,
`npn`, `pnp`, or other ngspice built-in type names. Use a unique name like
`myresistor`, `custom_diode`, `nmos_sq`, etc.

### Rule 5: Path resolution for `.osdi` files

| Path style | Resolves from |
|---|---|
| `pre_osdi mymodel.osdi` | ngspice's `lib/ngspice/` directory |
| `pre_osdi ./mymodel.osdi` | Netlist directory |
| `pre_osdi /abs/path/mymodel.osdi` | Absolute path |

For portable projects, keep the `.osdi` file next to the netlist and use `./`.

---

## 4. Complete Examples

### Example A: Simple resistor

See `assets/example_resistor.va` and `assets/test_resistor.spice` for the complete
files. This is the simplest possible round-trip: a two-terminal resistor model.

### Example B: Square-law MOSFET

See `assets/example_mosfet.va` and `assets/test_mosfet.spice` for a basic MOSFET
with linear/saturation regions and body effect — demonstrates a 4-terminal device.

### Example C: Voltage-dependent capacitor (varactor)

See `assets/example_varactor.va` and `assets/test_varactor.spice` for a C(V) model
using `ddt()` — demonstrates dynamic (charge-based) modeling.

---

## 5. Troubleshooting

Read `references/troubleshooting.md` for a comprehensive list. The most common issues:

| Symptom | Cause | Fix |
|---|---|---|
| `Library couldn't be loaded` | Wrong path to `.osdi` | Use `./mymodel.osdi` for relative path |
| `unrecognized parameter` | `pre_osdi` missing or after netlist | Move `pre_osdi` into `.control` block |
| Instance ignored silently | Name doesn't start with `N` | Rename to `N...` prefix |
| `LINK: fatal error` on compile | Missing MSVC Build Tools (Windows) | Install "Desktop development with C++" |
| Crash / `Illegal instruction` | Missing VC++ runtime | Install "Microsoft Visual C++ Redistributable" |
| Module name conflict | Module named `resistor` etc. | Rename to unique name |

---

## 6. Pre-compiled Model Library

The [VA-Models repository](https://github.com/dwarning/VA-Models) provides
pre-compiled `.osdi` files for standard compact models (BSIM-CMG, PSP, HICUM, EKV,
MEXTRAM, etc.) for both Windows and Linux, ready for ngspice 39+. Consider using
these instead of compiling from source when working with standard models.

---

## Further Reading

- `references/install.md` — Detailed installation instructions
- `references/troubleshooting.md` — Extended troubleshooting guide
- `references/supported_features.md` — Full feature support table
- `assets/` — Complete example files ready to compile and run
