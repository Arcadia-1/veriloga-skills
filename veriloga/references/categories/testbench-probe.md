# Testbench & Probe
<!-- domain: voltage -->

Patterns for testbench wrappers, stimulus drivers, measurement probes, and output monitors.

## Typical Ports

| Block | Ports |
|---|---|
| **Probe** | `input: signal` (observe only) → `output: result` (measured value) |
| **Stimulus** | `output: stim_out` (drive) + `input: ctrl` (optional) |
| **TB Wrapper** | `input: DIN[N:0]` → `output: VOUT` (reconstruct analog from digital) |

## Measurement Probe

Observes a signal and outputs a processed measurement:

```
module voltage_probe(VDD, VSS, sig_i, meas_o);
    inout electrical VDD, VSS;
    input electrical sig_i;
    output electrical meas_o;

    parameter real gain = 1.0;

    real vh, vl;

    analog begin
        vh = V(VDD); vl = V(VSS);
        V(meas_o) <+ gain * V(sig_i);
    end
endmodule
```

## Digital-to-Analog Reconstruction (TB Helper)

Testbenches often need to reconstruct an analog voltage from digital bus outputs:

```
module tb_reconstruct(VDD, VSS, DIN, VOUT);
    inout electrical VDD, VSS;
    input electrical [7:0] DIN;
    output electrical VOUT;

    parameter real vth = 0.45;
    parameter integer Nbits = 8;

    real vh, vl, accum, lsb;
    genvar i;

    analog begin
        vh = V(VDD); vl = V(VSS);
        lsb = (vh - vl) / (1 << Nbits);

        accum = 0.0;
        for (i = 0; i < Nbits; i = i + 1)
            accum = accum + ((V(DIN[i]) > vth) ? (1 << i) : 0);

        V(VOUT) <+ vl + accum * lsb;
    end
endmodule
```

## Bit Error Monitor

Compares two signals and flags errors:

```
module bit_error_probe(VDD, VSS, expected_i, actual_i, error_o);
    inout electrical VDD, VSS;
    input electrical expected_i, actual_i;
    output electrical error_o;

    parameter real vth = 0.45;

    real vh, vl;
    integer exp_bit, act_bit, err;

    analog begin
        vh = V(VDD); vl = V(VSS);
        vth_mid = (vh + vl) / 2.0;

        exp_bit = (V(expected_i) > vth_mid) ? 1 : 0;
        act_bit = (V(actual_i) > vth_mid) ? 1 : 0;
        err = (exp_bit != act_bit) ? 1 : 0;

        V(error_o) <+ transition(err ? vh : vl, 0, 10e-12, 10e-12);
    end
endmodule
```

## Stimulus Driver

```
module data_driver(VDD, VSS, clk_i, dout_o);
    inout electrical VDD, VSS;
    input electrical clk_i;
    output electrical dout_o;

    parameter real trise = 10e-12;
    parameter real tfall = 10e-12;

    real vh, vl, vth;
    integer out_val;

    analog begin
        vh = V(VDD); vl = V(VSS);
        vth = (vh + vl) / 2.0;

        @(initial_step)
            out_val = 0;

        @(cross(V(clk_i) - vth, +1))
            out_val = 1 - out_val;   // toggle, or use $random

        V(dout_o) <+ transition(out_val ? vh : vl, 0, trise, tfall);
    end
endmodule
```

## Key Idioms

- Testbench modules are NOT synthesized — they exist only for simulation
- Direct output (`V(out) <+ value` without `transition()`) is acceptable in probes
  since they don't drive real loads
- `$strobe("msg %f", value)` — print debug info to simulator log
- `$abstime` — timestamp for logging
- Bit accumulation loop: standard pattern for reconstructing integer from digital bus

## Design Notes

- TB modules typically have relaxed timing — no need for precise `transition()` delays
- Probes should be high-impedance (don't source/sink current on the observed signal)
- For file-based stimulus: Verilog-A has `$fopen`, `$fgets`, `$fscanf` for reading
  test vectors from a file, though support varies by simulator
- Empty TB modules (just port declarations, no body) are placeholder stubs —
  they exist to satisfy netlister connectivity requirements
