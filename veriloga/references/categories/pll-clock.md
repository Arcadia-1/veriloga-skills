# PLL / Clock
<!-- domain: either | voltage-when: PFD, divider, TDC | current-when: VCO, charge pump with I() <+ -->

Patterns for phase-locked loop building blocks: VCO, DCO, PFD, charge pump, frequency dividers, TDC, and DTC.

## Typical Ports

| Block | Ports |
|---|---|
| **VCO** | `in: vctr (control voltage)` → `out: vout (oscillation)` |
| **PFD** | `in: ref_clk, fb_clk` → `out: up, down` |
| **Charge Pump** | `in: up, down` → `out: iout (to loop filter)` |
| **Divider** | `in: clk_in` → `out: clk_out` + `parameter: div_ratio` |
| All blocks | `inout: VDD, VSS` |

## VCO — Voltage-Controlled Oscillator

The most common PLL block. Uses phase accumulation:

```
parameter real fo   = 1.0e9;           // free-running frequency [Hz]
parameter real Kvco = 100.0e6;         // VCO gain [Hz/V]
parameter real amp  = 0.4;             // output amplitude [V]
parameter integer step_size_num = 80;  // min points per period

real vh, vl, vcm, inst_freq, phase;

analog begin
    vh = V(VDD); vl = V(VSS);
    vcm = (vh + vl) / 2.0;

    // Instantaneous frequency
    inst_freq = fo + Kvco * (V(vctr) - vcm);

    // Force simulator time-step for waveform accuracy
    $bound_step(1.0 / (step_size_num * inst_freq));

    // Phase accumulation with wrap-around
    phase = idtmod(inst_freq, 0.0, 1.0);

    // Sinusoidal output
    V(vout) <+ vcm + amp * sin(2.0 * `M_PI * phase);
end
```

### Key Idioms
- `idtmod(freq, init, modulus)` — integrates frequency, wraps at modulus (avoids overflow)
- `$bound_step()` — forces max time-step so oscillation is sampled correctly
- For square-wave output: `V(vout) <+ transition((phase < 0.5) ? vh : vl, ...)`
- For noise: add `flicker_noise(Kf, exp, "vco_fn")` and `white_noise(Kw, "vco_wn")`

## Frequency Divider

```
parameter integer div_ratio = 2;
parameter real    tedge     = 10e-12;

integer count;
integer out_state;

analog begin
    vh = V(VDD); vl = V(VSS);
    vth = (vh + vl) / 2.0;

    @(initial_step) begin
        count = 0;
        out_state = 0;
    end

    @(cross(V(clk_in) - vth, +1)) begin
        count = count + 1;
        if (count >= div_ratio) begin
            count = 0;
            out_state = 1 - out_state;   // toggle
        end
    end

    V(clk_out) <+ transition(out_state ? vh : vl, 0, tedge, tedge);
end
```

## Charge Pump

```
parameter real Icp = 100e-6;           // pump current [A]
parameter real td  = 50e-12;           // switching delay

real up_val, dn_val;

analog begin
    vh = V(VDD); vl = V(VSS);
    vth = (vh + vl) / 2.0;

    up_val = (V(up) > vth) ? 1.0 : 0.0;
    dn_val = (V(down) > vth) ? 1.0 : 0.0;

    I(VDD, iout) <+ transition(Icp * up_val, td, tedge);
    I(iout, VSS) <+ transition(Icp * dn_val, td, tedge);
end
```

## Design Notes

- VCO `$bound_step` is critical — without it, the simulator takes large steps and
  misses oscillation cycles entirely
- Dividers need `@(initial_step)` — an uninitialized counter may never reach `div_ratio`
- Charge pump current is sourced from VDD and sunk to VSS — model both paths
- PFD outputs (up/down) are pulse-width-modulated — their overlap (dead zone) matters
  for lock-in behavior
- For DCO (digitally controlled oscillator): replace continuous `vctr` with a digital
  frequency word and discrete frequency steps
