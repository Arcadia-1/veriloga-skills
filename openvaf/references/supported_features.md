# OpenVAF Supported Verilog-A Features

Based on the Verilog-AMS LRM 2.4.0 analog subset.

## Fully Supported

### Data types and declarations
- `parameter real`, `parameter integer` with ranges (`from`, `exclude`)
- `real`, `integer` variables
- `electrical` discipline (from `disciplines.vams`)
- `inout`, `input`, `output` port directions
- Internal nodes (undeclared ports used as internal)

### Analog block
- `analog begin` / `end`
- `if` / `else` / `else if`
- `for` loops (with integer loop variable)
- `while` loops
- `case` statements
- `begin` / `end` blocks

### Branch access and contributions
- `V(a)`, `V(a, b)` — voltage access
- `I(a)`, `I(a, b)` — current access
- `V(a) <+` and `I(a) <+` — contributions

### Calculus operators
- `ddt(expr)` — time derivative
- `idt(expr, ic)` — time integral
- `idtmod(expr, ic, mod)` — modular integral
- `ddx(expr, unknown)` — partial derivative (including `$temperature`)

### Math functions
- `ln()`, `log()`, `exp()`, `sqrt()`, `pow()`, `abs()`
- `min()`, `max()`
- `sin()`, `cos()`, `tan()`, `asin()`, `acos()`, `atan()`, `atan2()`
- `sinh()`, `cosh()`, `tanh()`
- `hypot()`, `ceil()`, `floor()`
- `limexp()` — limited exponential (for convergence)

### Noise functions
- `white_noise(pwr)` — thermal/shot noise
- `flicker_noise(pwr, exp)` — 1/f noise

### System functions
- `$vt` / `$vt(temp)` — thermal voltage
- `$temperature` — simulation temperature
- `$abstime` — absolute simulation time
- `$param_given(param)` — check if parameter was specified
- `$bound_step(step)` — limit simulator time step
- `$strobe()`, `$display()` — print output
- `$limit()` — convergence aid

### Events
- `@(initial_step)` — runs once at simulation start
- `@(final_step)` — runs once at simulation end

### Preprocessor
- `` `include "file" ``
- `` `define ``, `` `ifdef ``, `` `ifndef ``, `` `else ``, `` `endif ``
- Constants from `constants.vams` (`M_PI`, `P_Q`, `P_K`, etc.)

---

## NOT Supported

| Feature | Notes |
|---|---|
| `@(cross(expr, dir))` | Monitored analog events |
| `@(above(expr))` | Threshold crossing events |
| Named events (`-> evt`, `@(evt)`) | Digital event semantics |
| `or`-combined events | E.g., `@(evt1 or evt2)` |
| `integer A[0:N]` (arrays) | Array declarations inside modules |
| `genvar` / generate constructs | Generate loops |
| `<<<`, `>>>` | Arithmetic shift operators |
| `transition()` | Piecewise-linear smoothing |
| `last_crossing()` | Time of last threshold crossing |
| `laplace_nd()`, `laplace_zp()` | Laplace transfer functions |
| `zi_nd()`, `zi_zp()` | Z-domain transfer functions |
| `absdelay()` | Absolute transport delay |
| `slew()` | Slew-rate limiting |
| Digital constructs | `always`, `assign`, `wire`, `reg`, etc. |
| `$fopen`, `$fclose`, `$fdisplay` | File I/O |
| `$random` | Random number generation |

### Impact on model types

| Model type | OpenVAF compatible? |
|---|---|
| MOSFET (BSIM, PSP, EKV) | Yes |
| BJT (HICUM, MEXTRAM, Gummel-Poon) | Yes |
| Diode (JUNCAP, simple exponential) | Yes |
| Varactor (C-V with ddt) | Yes |
| Resistor (linear, nonlinear) | Yes |
| VCO, PLL blocks | No — uses `@(cross)`, `idtmod` |
| SAR logic, digital blocks | No — uses `@(cross)`, arrays, genvar |
| Filters (Butterworth, etc.) | No — uses `laplace_nd` |
| Signal sources (PRBS, multitone) | No — uses `$abstime` patterns + arrays |
| Testbench probes | No — uses `$fopen`, `@(final_step)` I/O |
