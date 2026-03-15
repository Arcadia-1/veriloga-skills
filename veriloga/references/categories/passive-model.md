# Passive & Device Model
<!-- domain: current -->

Patterns for behavioral resistors, capacitors, inductors, MOSFET models, BJTs, diodes, and controlled sources.

## Typical Ports

| Block | Ports |
|---|---|
| **2-terminal** | `inout: vp, vn` (positive, negative) |
| **MOSFET** | `inout: d, g, s, b` (drain, gate, source, bulk) |
| **Controlled source** | `in: ctrl_p, ctrl_n` → `out: vp, vn` |

## Basic Resistor

```
parameter real r_val = 1.0e3 from (0:inf);    // resistance [Ohm]

analog begin
    V(vp, vn) <+ r_val * I(vp, vn);
end
```

## Basic Capacitor

```
parameter real c_val = 1.0e-12 from (0:inf);  // capacitance [F]

analog begin
    I(vp, vn) <+ c_val * ddt(V(vp, vn));
end
```

## Basic Inductor

```
parameter real l_val = 1.0e-9 from (0:inf);   // inductance [H]

analog begin
    V(vp, vn) <+ l_val * ddt(I(vp, vn));
end
```

## Resistor with Mismatch (Gaussian)

Models process variation using Box-Muller transform:

```
parameter real r_mean = 10.0e3;        // mean resistance [Ohm]
parameter real r_dev  = 1.0e3;         // std deviation [Ohm]
parameter integer seed1 = 0;
parameter integer seed2 = 13;

real r_actual;

analog begin
    @(initial_step) begin
        // Box-Muller: two uniform randoms → one Gaussian
        u1 = $rdist_uniform(seed1, 0.0, 1.0);
        u2 = $rdist_uniform(seed2, 0.0, 1.0);
        r_actual = r_mean + r_dev * sqrt(-2.0 * ln(u1)) * cos(2.0 * `M_PI * u2);
    end

    V(vp, vn) <+ r_actual * I(vp, vn);
end
```

## Temperature-Dependent Resistor

```
parameter real r_nom = 1.0e3;          // nominal resistance at tnom [Ohm]
parameter real tnom  = 27.0;           // nominal temperature [°C]
parameter real tc1   = 0.0;            // 1st-order tempco [1/°C]
parameter real tc2   = 0.0;            // 2nd-order tempco [1/°C²]

real dt, r_eff;

analog begin
    dt = $temperature - (tnom + 273.15);
    r_eff = r_nom * (1.0 + tc1 * dt + tc2 * dt * dt);
    V(vp, vn) <+ r_eff * I(vp, vn);
end
```

## Voltage-Controlled Voltage Source (VCVS)

```
parameter real gain = 1.0;

analog begin
    V(vp, vn) <+ gain * V(ctrl_p, ctrl_n);
end
```

## Voltage-Controlled Current Source (VCCS)

```
parameter real gm = 1.0e-3;           // transconductance [S]

analog begin
    I(vp, vn) <+ gm * V(ctrl_p, ctrl_n);
end
```

## Key Idioms

- `V(a, b) <+ R * I(a, b)` — resistor (Ohm's law, branch form)
- `I(a, b) <+ C * ddt(V(a, b))` — capacitor (current = C × dV/dt)
- `V(a, b) <+ L * ddt(I(a, b))` — inductor (voltage = L × dI/dt)
- `$temperature` — simulator temperature in Kelvin
- `$rdist_uniform(seed, lo, hi)` — uniform random (for mismatch modeling)
- `parameter ... from (lo:hi)` — range constraint, checked at elaboration

## Design Notes

- Passive models are purely algebraic — no `@(cross())` or `@(initial_step)` needed
  (except for mismatch initialization)
- For Monte Carlo: seed parameters let the testbench sweep different random instances
- Always use `from (0:inf)` for R, C, L values to catch negative-value errors early
- Controlled sources (VCVS, VCCS, CCVS, CCCS) are one-liners — gain/gm parameter only
- For nonlinear capacitance (varactor): `I(a,b) <+ ddt(Q(V(a,b)))` where Q is a function of voltage
