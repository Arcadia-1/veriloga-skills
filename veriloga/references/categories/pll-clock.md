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

## Closed-Loop PLL Repair Order

When repairing a failing behavioral PLL, do not start by forcing the `lock`
output. Treat the loop as a staged mechanism and keep already-working stages
intact.

### Preserve The Verifier Interface

Behavior repair must keep the public testbench interface stable. If the
Spectre harness passes parameters on the DUT instance, the Verilog-A module
must declare those exact parameter names even when it also uses internal helper
variables.

Common PLL verifier parameters include:

- `div_ratio`
- `ratio_min`, `ratio_max`
- `f_center`, `freq_step_hz`, `f_min`, `f_max`
- `code_min`, `code_max`, `code_center`, `code_init`
- `tedge`
- `lock_tol`
- `lock_count_target`

It is fine to derive internal variables such as `ndiv`, `t_half`, `freq`, or
`lock_threshold` from those public parameters, but do not replace the public
parameter names with private-only names. The repair may be behaviorally closer
and still be rejected if the harness parameter interface is broken.

### Stage 1: Feedback Edge Liveness

If `ref_clk` has edges but `fb_clk` has none, the feedback generator is dead.
Repair the oscillator/DCO and divider path first.

- Use a held oscillator state plus an absolute `t_next` timer.
- Initialize `t_next` in `@(initial_step)`.
- In every `@(timer(t_next))` event, toggle the oscillator state and advance
  `t_next` by a strictly positive half-period.
- For CPPLL-style tasks, derive `fb_clk` from generated `dco_clk` edges through
  a divider counter.
- For ADPLL-style tasks without a separate `dco_clk`, the feedback output may
  be the generated divided DCO clock.
- Drive public clock pins from held states with unconditional `transition()`
  contributions.

### Stage 2: Feedback/Reference Ratio

If feedback edges exist but the ratio is wrong, preserve edge liveness and
repair cadence.

- Keep one divider counter connected to oscillator/DCO edges.
- Toggle or pulse `fb_clk` only from that counter.
- Latch public ratio or hop controls on safe clock edges.
- Be explicit about half-period versus full-period counting. If the DCO timer
  fires on every half-cycle toggle and `fb_clk` toggles after `N` timer fires,
  then one full `fb_clk` period is `2*N` timer intervals.
- For ADPLL-style divided feedback, the common locked relation is
  `f_dco ~= 2 * div_ratio * f_ref` when `fb_clk` toggles once per divider
  count. If `div_ratio` changes without a matching nominal DCO frequency, the
  late-window feedback/reference edge ratio will move high or low.
- Choose `N` or the DCO period so late-window feedback and reference rising-edge
  counts align. For a 50 MHz reference, `fb_clk` should have a near-20 ns
  rising-edge period in the locked window.
- Do not ignore public `f_center`, `freq_step_hz`, `f_min`, `f_max`, or
  `div_ratio` and replace them with a fixed private oscillator.
- Tune the nominal oscillator/DCO cadence and divider ratio so late-window
  feedback and reference edge counts align.
- Do not make `lock` pass while the ratio check is failing.

### Stage 3: Control Movement

If `vctrl_mon` or a control monitor is stuck, add a bounded loop-control state
instead of a cosmetic waveform.

- REF-leading error should move the control in the direction that speeds up the
  feedback clock.
- FB-leading error should move the control in the direction that slows down the
  feedback clock.
- A lightweight behavioral loop filter can accumulate bounded UP/DN corrections
  into one real control variable.
- Drive `vctrl_mon` from that same held control variable.
- Use the same control variable to influence oscillator/DCO frequency so the
  monitor movement is causally connected to feedback cadence.

### Stage 4: Lock And Reacquire

Assert `lock` only after earlier stages are plausible.

- Maintain a stability counter over consecutive reference edges or comparison
  windows with close reference/feedback cadence.
- Use public `lock_tol` as a time or period tolerance and
  `lock_count_target` as the required number of consecutive stable observations.
- Treat `lock_count_target` as a lock-latency parameter, not a frequency-ratio
  fix. Reducing it may assert lock earlier, but it does not repair a wrong
  feedback cadence.
- Do not use code-near-center as the only lock condition. The lock flag should
  summarize observed ref/fb timing stability.
- Assert `lock` after the stable count reaches the required window.
- Clear or lower `lock` after reset, ratio hop, or a large frequency step.
- For reacquire tasks, allow lock to drop during the disturbance and assert
  again only after the post-step ratio restabilizes.
- Never use a constant-high `lock` flag to hide a dead feedback path.

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
