# Calibration & Trim
<!-- domain: voltage -->

Patterns for trim DACs, calibration logic, foreground/background calibration, and code generators.

## Typical Ports

| Port | Direction | Purpose |
|---|---|---|
| `VDD, VSS` | inout | Power rails |
| `AIN` | input | Analog input to calibrate against |
| `CLK` | input | Calibration clock |
| `EN, START` | input | Enable / start calibration |
| `DOUT[N:0]` | output | Trim code (digital) |
| `DONE` | output | Calibration complete flag |

## Typical Parameters

```
parameter integer Nbits = 8;          // trim resolution
parameter real    vth   = 0.45;       // digital threshold [V]
parameter real    trise = 10e-12;     // output transition [s]
```

## Trim Code Generator (Combinational)

Converts an analog voltage into a binary trim code:

```
real vh, vl, lsb, scaled;
integer code;
genvar i;

analog begin
    vh = V(VDD); vl = V(VSS);
    lsb = (vh - vl) / (1 << Nbits);

    // Quantize input
    scaled = (V(AIN) - vl) / lsb;
    code = (scaled < 0) ? 0 : (scaled > ((1 << Nbits) - 1)) ? ((1 << Nbits) - 1) : scaled;

    // Output bits
    for (i = 0; i < Nbits; i = i + 1)
        V(DOUT[i]) <+ transition(((code >> i) & 1) ? vh : vl, 0, trise, trise);
end
```

## SAR-Based Foreground Calibration

Iteratively finds optimal trim code using binary search:

```
integer cal_code, bit_under_test, cal_done;

analog begin
    vh = V(VDD); vl = V(VSS);
    vth_clk = (vh + vl) / 2.0;

    @(initial_step) begin
        cal_code = 0;
        bit_under_test = Nbits - 1;
        cal_done = 0;
    end

    @(cross(V(CLK) - vth_clk, +1)) begin
        if (!cal_done && bit_under_test >= 0) begin
            // Set trial bit
            cal_code = cal_code | (1 << bit_under_test);

            // Compare (assume AIN reflects the effect of current trim code)
            if (V(AIN) < V(REF))
                cal_code = cal_code & ~(1 << bit_under_test);  // clear bit

            bit_under_test = bit_under_test - 1;

            if (bit_under_test < 0)
                cal_done = 1;
        end
    end

    for (i = 0; i < Nbits; i = i + 1)
        V(DOUT[i]) <+ transition(((cal_code >> i) & 1) ? vh : vl, 0, trise, trise);

    V(DONE) <+ transition(cal_done ? vh : vl, 0, trise, trise);
end
```

## Background Calibration (Accumulator-Based)

Runs continuously, adjusting trim code by small steps:

```
parameter integer step = 1;           // adjustment step size
parameter integer code_max = 255;     // max trim code
parameter integer code_min = 0;       // min trim code

integer cal_code;

analog begin
    vh = V(VDD); vl = V(VSS);
    vth_clk = (vh + vl) / 2.0;

    @(initial_step)
        cal_code = (code_max + code_min) / 2;   // start at midpoint

    @(cross(V(CLK) - vth_clk, +1)) begin
        if (V(ERROR) > 0 && cal_code < code_max)
            cal_code = cal_code + step;
        else if (V(ERROR) < 0 && cal_code > code_min)
            cal_code = cal_code - step;
    end

    // Output code
    for (i = 0; i < Nbits; i = i + 1)
        V(DOUT[i]) <+ transition(((cal_code >> i) & 1) ? vh : vl, 0, trise, trise);
end
```

## Key Idioms

- `code | (1 << bit)` — set bit (trial)
- `code & ~(1 << bit)` — clear bit (reject)
- `(code >> i) & 1` — extract bit i
- Binary search: MSB-first, one bit per clock cycle (like SAR ADC logic)

## Design Notes

- Foreground calibration runs once at startup, holds result (SAR-style binary search)
- Background calibration runs continuously, tracks drift with small adjustments
- Trim code output is always a bus of digital signals driven with `transition()`
- Calibration modules often need a `DONE` or `RDY` flag so downstream logic knows
  when the code is valid
- The analog input (`AIN` or `ERROR`) typically comes from a measurement block that
  senses the quantity being calibrated (offset, gain, linearity, etc.)
