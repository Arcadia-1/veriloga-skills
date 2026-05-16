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

For EVAS-first or EVAS+Spectre parity workflows, prefer a non-idt baseline first.
Use `idtmod()` only after parity-gate A/B evidence (see `../evas-parity-gate.md`).

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

## EVAS-friendly Alternative (No idtmod)

Use timer-driven toggling with frequency updates in the event block:

- For variable-period VCO/DCO/CPPLL clocks, prefer a single-argument absolute-time timer:
  `@(timer(t_next))`
- Do not use `@(timer(0.0, t_half))` with a time-varying `t_half` for oscillator scheduling.
  In event-driven simulators this commonly schedules the next edge using the old period, so the
  frequency update takes effect one edge late.

```
parameter real fo = 1.0e9;
parameter real Kvco = 100.0e6;
parameter real tedge = 10p;

real vh, vl, vcm, inst_freq, t_next, t_half;
integer state;

analog begin
    vh = V(VDD); vl = V(VSS); vcm = (vh + vl) / 2.0;

    @(initial_step) begin
        state = 0;
        inst_freq = fo;
        t_half = 0.5 / inst_freq;
        t_next = $abstime + t_half;
    end

    @(timer(t_next)) begin
        inst_freq = fo + Kvco * (V(vctr) - vcm);
        if (inst_freq < 1.0) inst_freq = 1.0;
        $bound_step(1.0 / (64.0 * inst_freq));
        state = 1 - state;
        t_half = 0.5 / inst_freq;
        t_next = t_next + t_half;
    end

    V(vout) <+ vl + (vh - vl) * transition(state ? 1.0 : 0.0, 0, tedge, tedge);
end
```

This pattern is usually easier to align between EVAS and Spectre than direct phase integration.
It also avoids one-edge-late period application when the oscillation period changes over time.

## Differential VCO Output Topology

Do not over-constrain a differential VCO output with three independent ideal
voltage branches. Spectre treats these as ideal branch equations, so this shape
can create a rigid-branch topology fatal even when EVAS accepts it:

```verilog
// Unsafe: OUTP, OUTN, and VSS are tied by three ideal voltage constraints.
V(OUTP, VSS) <+ vcm + vdiff;
V(OUTN, VSS) <+ vcm - vdiff;
V(OUTP, OUTN) <+ 2.0 * vdiff + noise_v;
```

General rule: if two pin pairs already share a reference, such as
`OUTP-VSS` and `OUTN-VSS`, do not add a third ideal `V(OUTP, OUTN) <+`
constraint across the same two output pins. Add differential perturbations to
the existing output targets before the single-ended contributions, or use a
current-domain perturbation path.

Preferred shapes:

```verilog
// Voltage-domain target style: add perturbation before the two output drives.
outp_target = vcm + vdiff + 0.5 * noise_v;
outn_target = vcm - vdiff - 0.5 * noise_v;
V(OUTP, VSS) <+ transition(outp_target, 0, tedge, tedge);
V(OUTN, VSS) <+ transition(outn_target, 0, tedge, tedge);
```

```verilog
// Current-domain style: inject differential noise without an ideal voltage loop.
I(OUTP, OUTN) <+ noise_i;
```

For finite-output-impedance models, use a Norton-style path with conductance
and current injection rather than a third ideal differential voltage source.
EVAS does not solve the same KCL/KVL topology as Spectre, so EVAS-only passing
does not prove that an ideal voltage-branch topology is Spectre-portable.

## Monitor Node Unit Discipline

Monitor pins are voltages. Do not drive a monitor node with an unscaled physical
quantity whose numeric value is far outside a reasonable voltage range. A common
failure is:

```verilog
// Unsafe at GHz operation: this drives about 1e9 V onto freq_mon.
V(freq_mon) <+ freq;
```

Use an explicit scale parameter so the monitor voltage has documented units:

```verilog
parameter real freq_mon_scale = 1e-9;  // GHz on freq_mon
V(freq_mon) <+ freq * freq_mon_scale;
```

Apply the same discipline to other PLL monitors:

- Frequency monitors: scale Hz to GHz/MHz/kHz on the voltage node.
- Phase monitors: document rad-to-V scaling, for example `phase_mon_scale`.
- Control-voltage monitors: no scale is needed when the state is already volts.
- Divider-ratio or code monitors: dimensionless values may be driven directly
  only when their range is small; otherwise add a scale parameter.

Passing in EVAS is not enough for monitor nodes because EVAS may not expose DC
or initial-condition blowup the way Spectre does. If a monitor can reach
hundreds of volts or more, scale it before using it as a voltage contribution.

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
- For variable-period oscillators, schedule the next edge with an explicit `t_next` state rather
  than a two-argument periodic `timer(start, period)`
