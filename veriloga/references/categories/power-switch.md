# Power & Switch
<!-- domain: either | voltage-when: digital switch control | current-when: conductance model, I() <+ -->

Patterns for switches, bootstrap drivers, ESD clamps, and switched-capacitor circuits.

## Typical Ports

| Block | Ports |
|---|---|
| **Switch** | `inout: IN, OUT` (signal path) + `input: C` (control/gate) |
| **Bootstrap** | `input: clk, vin` → `output: clkbs` (boosted clock) |
| **ESD** | `inout: HI, LO` (stress nodes) |

## Ideal Switch (Conductance Model)

```
parameter real VTH  = 0.6;            // switch threshold [V]
parameter real Ron  = 1.0;            // on-resistance [Ohm]
parameter real Roff = 1.0e9;          // off-resistance [Ohm]

integer closed;

analog begin
    closed = (V(C) > VTH) ? 1 : 0;
    V(IN, OUT) <+ I(IN, OUT) * transition(closed ? Ron : Roff, 0, 10e-12);
end
```

## CMOS Transmission Gate

```
parameter real Ron_n  = 500.0;        // NMOS on-resistance [Ohm]
parameter real Ron_p  = 800.0;        // PMOS on-resistance [Ohm]
parameter real Roff   = 1.0e12;       // off-resistance [Ohm]

real r_eff;
integer n_on, p_on;

analog begin
    vh = V(VDD); vl = V(VSS);
    vth = (vh + vl) / 2.0;

    n_on = (V(en)  > vth) ? 1 : 0;
    p_on = (V(enb) < vth) ? 1 : 0;

    if (n_on && p_on)
        r_eff = 1.0 / (1.0/Ron_n + 1.0/Ron_p);  // parallel
    else if (n_on)
        r_eff = Ron_n;
    else if (p_on)
        r_eff = Ron_p;
    else
        r_eff = Roff;

    V(IN, OUT) <+ I(IN, OUT) * transition(r_eff, 0, 10e-12);
end
```

## Bootstrap Switch Driver

```
parameter real tde = 50e-12;
parameter real tdc = 50e-12;

real state;

analog begin
    vh = V(VDD); vl = V(VSS);
    vth = (vh + vl) / 2.0;

    @(initial_step)
        state = 0.0;

    @(cross(V(clk) - vth, +1))
        state = V(vin) + vh;          // boosted: Vin + VDD

    @(cross(V(clk) - vth, -1))
        state = 0.0;                  // off

    V(clkbs) <+ transition(state, tde, tdc);
end
```

## Switched-Capacitor Integrator

```
parameter real cap_in = 1.0e-12;      // input cap [F]
parameter real cap_fb = 2.0e-12;      // feedback cap [F]

real vout_held;
integer crossed;

analog begin
    vh = V(VDD); vl = V(VSS);
    vth = (vh + vl) / 2.0;

    @(initial_step) begin
        vout_held = 0.0;
        crossed = 0;
    end

    @(cross(V(phi1) - vth, +1))
        crossed = 1;

    if (crossed) begin
        vout_held = (cap_in * V(vin) + cap_fb * vout_held) / (cap_in + cap_fb);
        crossed = 0;
    end

    V(vout) <+ vout_held;
end
```

## Key Idioms

- `V(a, b) <+ I(a, b) * R` — resistive branch (switch model)
- `transition(R, ...)` on resistance — smooths on/off transitions to help convergence
- `branch (IN, OUT) sw;` — named branch for readability (optional)
- Conductance-based: `1.0` (on) vs `1.0e-9` (off) ratio sets on/off contrast

## Design Notes

- Switch models use resistance, not conductance — `V = I × R` is more intuitive
- Always add a finite off-resistance (`Roff`), never use infinity — simulators need a
  finite path for DC operating point
- `transition()` on the resistance itself (not just the output) prevents instantaneous
  impedance jumps that cause convergence failures
- For charge injection modeling: add a small capacitor from control to signal path
- ESD models use `$abstime` and exponential decay for human body / machine / charged
  device model waveforms — these are specialized and rarely needed in standard design
