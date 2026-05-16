# DAC
<!-- domain: either | voltage-when: V() <+ transition() | current-when: I() <+ -->

Patterns for digital-to-analog converters: binary-weighted, thermometer-coded, current-steering, R-string, and CDAC.

## Typical Ports

| Port | Direction | Purpose |
|---|---|---|
| `VDD, VSS` | inout | Power rails |
| `DIN[N:0]` | input | Digital input word |
| `CLK, RDY` | input | Clock or ready strobe (for latching DACs) |
| `VOUT, AOUT` | output | Analog output voltage |
| `VOUTP, VOUTN` | output | Differential analog output (current-steering) |

## Typical Parameters

```
parameter integer Nbit    = 10;         // resolution
parameter real    Vhi     = 0.9;        // output full-scale high
parameter real    Vlo     = 0.0;        // output full-scale low
parameter real    vth     = 0.45;       // input digital threshold
parameter real    tt      = 100e-12;    // output transition time
parameter real    tdc     = 10e-12;     // clock-to-output delay
parameter real    vcm     = 0.45;       // output common-mode
```

## Analog Block Patterns

### Combinational (continuously evaluates inputs)

```
// Example shown for 4 bits. For wider buses, explicitly unroll the electrical-bus
// reads in procedural code; do not use V(DIN[i]) with a runtime index.
analog begin
    vh = V(VDD); vl = V(VSS);
    lsb = (vh - vl) / 16.0;

    accum = 0.0;
    if (V(DIN[0]) > vth) accum = accum + 1;
    if (V(DIN[1]) > vth) accum = accum + 2;
    if (V(DIN[2]) > vth) accum = accum + 4;
    if (V(DIN[3]) > vth) accum = accum + 8;

    V(VOUT) <+ transition(vl + accum * lsb, tdc, tt);
end
```

### Latching (updates on clock/strobe edge)

```
// Example shown for 4 bits. Extend by explicitly unrolling each electrical-bit read.
analog begin
    vh = V(VDD); vl = V(VSS);
    vth_clk = (vh + vl) / 2.0;

    @(initial_step)
        held_value = 0.0;

    @(cross(V(RDY) - vth_clk, +1)) begin
        decimal = 0;
        if (V(DIN[0]) > vth) decimal = decimal + 1;
        if (V(DIN[1]) > vth) decimal = decimal + 2;
        if (V(DIN[2]) > vth) decimal = decimal + 4;
        if (V(DIN[3]) > vth) decimal = decimal + 8;
        held_value = vl + decimal * (vh - vl) / ((1 << Nbit) - 1);
    end

    V(VOUT) <+ transition(held_value, tdc, tt);
end
```

### CDAC (Capacitive DAC for SAR)

Uses weighted capacitor array. Each bit controls a capacitor switch:
```
@(initial_step) begin
    // Weight array (binary or custom)
    Cw[0] = 1.0; Cw[1] = 2.0; Cw[2] = 4.0; ...
    Ctotal = sum of Cw[];
end

// Accumulate charge on each strobe
state = 0.0;
if (V(DIN[0]) > vth) state = state + Cw[0] / Ctotal;
if (V(DIN[1]) > vth) state = state + Cw[1] / Ctotal;
if (V(DIN[2]) > vth) state = state + Cw[2] / Ctotal;
if (V(DIN[3]) > vth) state = state + Cw[3] / Ctotal;

V(VOUT) <+ transition(state * (vrefp - vrefn) + vrefn, tdc, tt);
```

### DWA / Thermometer Pointer (Spectre-safe shape)

For DWA, use integer arrays for internal state and `genvar` for bus contributions.
Read small input buses with fixed indices inside clock events.

This is an instance of the generic multi-output transition target-buffer pattern:
state/event code updates held real targets, and electrical contributions are
unconditional at analog top level. The same pattern applies to any multi-output
digital/analog driver, not only DWA.

```
integer ptr_q, code_q, j;
real cell_en_val[15:0], ptr_val[15:0];
genvar k;

analog begin
    @(initial_step) begin
        ptr_q = 0;
        for (j = 0; j < 16; j = j + 1) begin
            cell_en_val[j] = 0.0;
            ptr_val[j] = (j == ptr_q) ? vhi : vlo;
        end
    end

    @(cross(V(CLK) - vth, +1)) begin
        code_q = 0;
        if (V(CODE[0]) > vth) code_q = code_q + 1;
        if (V(CODE[1]) > vth) code_q = code_q + 2;
        if (V(CODE[2]) > vth) code_q = code_q + 4;
        if (V(CODE[3]) > vth) code_q = code_q + 8;

        ptr_q = (ptr_q + code_q) % 16;
        for (j = 0; j < 16; j = j + 1) begin
            cell_en_val[j] = 0.0;
            ptr_val[j] = (j == ptr_q) ? vhi : vlo;
        end
    end

    for (k = 0; k < 16; k = k + 1) begin
        V(CELL_EN[k]) <+ transition(cell_en_val[k], 0, tt, tt);
        V(PTR[k]) <+ transition(ptr_val[k], 0, tt, tt);
    end
end
```

### Thermometer-Code DAC Count-To-Voltage

Thermometer DACs should map the population count of active input cells to the
analog output. Do not interpret thermometer inputs as a binary-weighted word.

```
integer count;
real vout_target;

analog begin
    count = 0;
    if (V(DIN0) > vth) count = count + 1;
    if (V(DIN1) > vth) count = count + 1;
    if (V(DIN2) > vth) count = count + 1;
    if (V(DIN3) > vth) count = count + 1;
    // Continue explicitly or use genvar/unrolled helpers for wider buses.

    if (V(rst_n) < vth)
        vout_target = 0.0;
    else
        vout_target = count * vstep;

    V(VOUT) <+ transition(vout_target, 0, tt, tt);
end
```

Key points:
- Count asserted cells; do not use `DIN[k] * (1 << k)` for thermometer inputs.
- Keep active-low reset released after startup if the checker observes settled
  output levels.
- If the prompt names scalar stimulus nodes such as `d0..d15`, keep those save
  names visible even when the DUT uses an internal bus.

## Key Variables

- `real accum, held_value, state` — accumulator for weighted sum
- `integer decimal` — integer code from bit accumulation
- `real Cw[N:0]` — capacitor weight array (for CDAC)
- `real lsb` — least significant bit voltage step
- `genvar i` — loop index

## Design Notes

- Binary-weighted: `weight[i] = 1 << i`, simplest but worst DNL for high resolution
- Thermometer-coded: unary weights, better linearity, more ports (`2^N - 1` inputs)
- Segmented: MSBs thermometer-coded, LSBs binary-weighted — common hybrid
- Multiple `V(VOUT) <+` statements *add* contributions — useful for segmented DACs where
  each segment drives the same output node
- For differential outputs: `VOUTP = vcm + signal/2`, `VOUTN = vcm - signal/2`
- Spectre portability rule: do not use runtime-indexed electrical-bus reads such as
  `V(DIN[i])` in procedural/event code; explicitly unroll or restructure them
