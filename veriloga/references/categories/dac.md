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
analog begin
    vh = V(VDD); vl = V(VSS);
    lsb = (vh - vl) / (1 << Nbit);

    accum = 0.0;
    for (i = 0; i < Nbit; i = i + 1)
        accum = accum + ((V(DIN[i]) > vth) ? (1 << i) : 0);

    V(VOUT) <+ transition(vl + accum * lsb, tdc, tt);
end
```

### Latching (updates on clock/strobe edge)

```
analog begin
    vh = V(VDD); vl = V(VSS);
    vth_clk = (vh + vl) / 2.0;

    @(initial_step)
        held_value = 0.0;

    @(cross(V(RDY) - vth_clk, +1)) begin
        decimal = 0;
        for (i = 0; i < Nbit; i = i + 1)
            decimal = decimal + ((V(DIN[i]) > vth) ? (1 << i) : 0);
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
for (i = 0; i < Nbit; i = i + 1)
    state = state + Cw[i] / Ctotal * ((V(DIN[i]) > vth) ? 1.0 : 0.0);

V(VOUT) <+ transition(state * (vrefp - vrefn) + vrefn, tdc, tt);
```

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
