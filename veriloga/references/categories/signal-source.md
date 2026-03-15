# Signal Source
<!-- domain: voltage -->

Patterns for signal generators: AM/FM/QAM modulators, pulse generators, ramp sources, and sinusoidal sources.

## Typical Ports

| Port | Direction | Purpose |
|---|---|---|
| `VDD, VSS` | inout | Power rails |
| `vin` | input | Modulation input (for modulators) |
| `vout` | output | Generated signal |

## Typical Parameters

```
parameter real f_carrier  = 1.0e6;     // carrier frequency [Hz]
parameter real amp        = 1.0;       // output amplitude [V]
parameter real mod_depth  = 0.5;       // modulation depth [0:1]
parameter real vin_max    = 1.0;       // max input range [V]
parameter real vin_min    = -1.0;      // min input range [V]
```

## AM Modulator

```
real w_carrier, vin_offset, vin_scale, vin_val, vin_adj;

analog begin
    @(initial_step) begin
        w_carrier = 2.0 * `M_PI * f_carrier;
        vin_offset = (vin_max + vin_min) / 2.0;
        vin_scale = (vin_max - vin_min) / 2.0;
    end

    // Clip input
    vin_val = min(max(V(vin), vin_min), vin_max);

    // Normalize to [-1, +1]
    vin_adj = (vin_val - vin_offset) / vin_scale;

    // AM output
    V(vout) <+ amp * (1.0 + mod_depth * vin_adj) * cos(w_carrier * $abstime);

    // Ensure adequate time-step sampling
    $bound_step(0.04 / f_carrier);
end
```

## FM Modulator

Uses phase accumulation (like VCO):

```
parameter real f_center = 1.0e6;       // center frequency [Hz]
parameter real f_dev    = 100.0e3;     // frequency deviation [Hz]

real inst_freq, phase;

analog begin
    inst_freq = f_center + f_dev * V(vin);
    phase = idtmod(inst_freq, 0.0, 1.0);
    V(vout) <+ amp * sin(2.0 * `M_PI * phase);
    $bound_step(1.0 / (80 * inst_freq));
end
```

## Pulse Generator

```
parameter real period   = 1.0e-6;     // pulse period [s]
parameter real duty     = 0.5;        // duty cycle [0:1]
parameter real trise    = 1.0e-9;     // rise time [s]
parameter real tfall    = 1.0e-9;     // fall time [s]

real phase;

analog begin
    vh = V(VDD); vl = V(VSS);
    phase = $abstime / period - $floor($abstime / period);  // [0, 1)
    V(vout) <+ transition((phase < duty) ? vh : vl, 0, trise, tfall);
    $bound_step(period / 100.0);
end
```

## Ramp Generator

```
parameter real period = 1.0e-3;       // ramp period [s]
parameter real vmin   = 0.0;
parameter real vmax   = 1.0;

real phase, ramp_val;

analog begin
    phase = $abstime / period - $floor($abstime / period);
    ramp_val = vmin + (vmax - vmin) * phase;
    V(vout) <+ ramp_val;
    $bound_step(period / 100.0);
end
```

## Key Idioms

- `$abstime` — absolute simulation time (read-only, used for carrier generation)
- `$bound_step(dt)` — constrains max simulator step; set to ~1/80th of the highest
  frequency to avoid aliasing
- `idtmod(freq, init, mod)` — frequency-to-phase integrator with modular wrap
- `$floor()` — floor function for phase calculation from time
- Input clipping: `min(max(V(vin), lo), hi)` prevents out-of-range inputs

## Design Notes

- Always pair carrier generation with `$bound_step()` — without it, the simulator
  may take steps larger than the carrier period and produce garbage waveforms
- For QAM/QPSK: combine in-phase (I) and quadrature (Q) channels using
  `cos()` and `sin()` of the same carrier
- Pulse generators can replace a full SPICE voltage source (VPULSE) when you need
  parameterized control or conditional behavior
