# Amplifier & Filter
<!-- domain: current -->

Patterns for opamps, OTAs, transconductance stages, and analog filters (LPF, BPF, HPF).

## Typical Ports

| Port | Direction | Purpose |
|---|---|---|
| `VDD, VSS` | inout | Power rails |
| `inp, inm` or `vin_p, vin_n` | input | Differential input pair |
| `vout, out` | output | Single-ended output |
| `voutp, voutn` | output | Differential output (fully-differential) |
| `vref` | input | Reference / common-mode feedback (optional) |

## Amplifier Parameters

```
parameter real gain          = 1000.0;     // DC gain [V/V]
parameter real freq_unitygain = 1.0e6;     // unity-gain bandwidth [Hz]
parameter real rin           = 1.0e6;      // input resistance [Ohm]
parameter real rout          = 80.0;       // output resistance [Ohm]
parameter real slew_rate     = 0.5e6;      // slew rate [V/s]
parameter real vin_offset    = 0.0;        // input offset [V]
parameter real ibias         = 0.0;        // input bias current [A]
parameter real iin_max       = 100e-6;     // max internal current [A]
parameter real vsoft         = 0.2;        // soft clipping margin [V]
```

## Opamp (Single-Pole with Slew Limiting)

```
real c1, gm_nom, r1, vmax_in, vin_val;

analog begin
    vh = V(VDD); vl = V(VSS);

    @(initial_step) begin
        c1 = iin_max / slew_rate;
        gm_nom = 2.0 * `M_PI * freq_unitygain * c1;
        r1 = gain / gm_nom;
        vmax_in = iin_max / gm_nom;
    end

    // Input stage
    vin_val = V(inp, inm) + vin_offset;
    I(inp, inm) <+ vin_val / rin;

    // Gm stage with slew limiting
    if (vin_val > vmax_in)
        I(vref, int_node) <+ iin_max;
    else if (vin_val < -vmax_in)
        I(vref, int_node) <+ -iin_max;
    else
        I(vref, int_node) <+ gm_nom * vin_val;

    // Dominant pole (RC)
    I(int_node, vref) <+ ddt(c1 * V(int_node, vref));
    I(int_node, vref) <+ V(int_node, vref) / r1;

    // Output stage
    V(vout) <+ V(int_node) / rout;
end
```

## Simple OTA (Transconductor)

```
parameter real gm   = 500e-6;          // transconductance [S]
parameter real iref = 10e-6;           // tail current (output limit) [A]
parameter real cout = 1e-12;           // output cap [F]

analog begin
    // Saturating transconductor
    vin_diff = V(inm, inp) * gm;
    if (vin_diff > iref)
        I(out) <+ -iref;
    else if (vin_diff < -iref)
        I(out) <+ iref;
    else
        I(out) <+ -vin_diff;

    // Load capacitance
    I(out) <+ cout * ddt(V(out));
end
```

## First-Order LPF

```
parameter real bandwidth = 1.0e3;      // -3dB frequency [Hz]
parameter real r_val     = 1.0e3;      // resistance [Ohm]

real c_val;

analog begin
    @(initial_step)
        c_val = 1.0 / (2.0 * `M_PI * r_val * bandwidth);

    V(vout, vin) <+ r_val * I(vout, vin);       // resistor
    I(vout)      <+ ddt(c_val * V(vout));        // capacitor to ground
end
```

## Key Idioms

- `ddt(C * V(node))` — capacitor current (derivative of charge)
- `I(a, b) <+ V(a, b) / R` — resistor between nodes a and b
- `V(inp, inm)` — differential input voltage (shorthand for `V(inp) - V(inm)`)
- Slew limiting: clamp internal current to `±iin_max`
- For Laplace-domain filters: `laplace_nd(V(in), {num_coeffs}, {den_coeffs})`

## Design Notes

- Amplifiers model with *current contributions* (`I() <+`), not voltage — this lets the
  simulator properly load the output
- Always add a leakage path (`V(node)/1e12`) to any internal node that could float
- Soft clipping near rails: `tanh()` or conditional clamping prevents convergence issues
- For fully-differential: drive both `voutp` and `voutn` symmetrically around `vcm`
