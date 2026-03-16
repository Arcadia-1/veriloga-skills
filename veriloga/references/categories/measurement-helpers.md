# Measurement Helpers & Probes
<!-- domain: voltage -->

Reusable Verilog-A modules for measurement, stimulus generation, and data reconstruction
**within Spectre netlists**. These are behavioral modules, **not testbenches** — testbenches are
`.scs` files (see `testbench-spectre.md`).

## ⚠️ Important Distinction

- **This file** → Verilog-A modules (`.va`) for probes, helpers, stimulus drivers
- **NOT this** → Testbenches (`.scs` netlists with `include`, `.tran`, probe statements)

See `testbench-spectre.md` for how to instantiate these modules in a real `.scs` testbench.

---

## Typical Patterns

| Pattern | Ports | Purpose |
|---|---|---|
| **Voltage Probe** | `input: signal` → `output: measured` | Observe signal with optional gain/filtering |
| **DAC Reconstructor** | `input: digital_bus[N:0]` → `output: analog` | Convert digital output to analog for feedback/measurement |
| **Bit Error Monitor** | `input: expected, actual` → `output: error_flag` | Compare and flag mismatches |
| **Stimulus Source** | `input: clk` → `output: stimulus` | Generate test patterns (clock-driven, internal counters) |

---

## Voltage Probe with Gain

Observes and scales a signal:

```verilog
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

**Usage in `.scs`:**
```spectre
Xprobe (signal net, probe_out, VDD, VSS) voltage_probe gain=2.0
meas_probe_out probe_out VSS DC
```

---

## DAC Reconstructor

Converts an N-bit digital output to an analog voltage. Used to feed back ADC/DAC outputs
for verification measurements.

```verilog
module dac_reconstructor(VDD, VSS, DIN, VOUT);
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

**Usage in `.scs`:**
```spectre
Xdac_recon (dac_out[7:0], dac_analog, VDD, VSS) dac_reconstructor Nbits=8
meas_dac dac_analog VSS DC
```

---

## Bit Error Monitor

Compares expected vs. actual digital signals and outputs a flag:

```verilog
module bit_error_probe(VDD, VSS, expected_i, actual_i, error_o);
    inout electrical VDD, VSS;
    input electrical expected_i, actual_i;
    output electrical error_o;

    parameter real vth = 0.45;

    real vh, vl, vth_mid;
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

**Usage in `.scs`:**
```spectre
Xerr (expected_sig, actual_sig, error_flag, VDD, VSS) bit_error_probe
meas_error error_flag VSS DC
```

---

## Stimulus Driver (Clock-Synchronized)

Generates data patterns synchronized to a clock input:

```verilog
module stimulus_driver(VDD, VSS, clk_i, dout_o);
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
            out_val = 1 - out_val;   // Toggle pattern

        V(dout_o) <+ transition(out_val ? vh : vl, 0, trise, tfall);
    end
endmodule
```

**Usage in `.scs`:**
```spectre
Xstim (clock, stimulus_out, VDD, VSS) stimulus_driver trise=5p tfall=5p
```

---

## Key Design Points

- **These are modules, not testbenches** — instantiate them in a `.scs` netlist
- **Not synthesized** — only for simulation verification
- **Port naming** — use `_i` / `_o` suffixes (consistent with behavioral module conventions)
- **Threshold detection** — always use `(vh + vl) / 2.0` for digital thresholds
- **No `transition()` in probes** — only in drivers/stimulus (probes are read-only)
- **Vector support** — use `[N:0]` for multi-bit buses and `genvar` for loops

---

## Spectre Netlist Integration

To use these modules in a `.scs` testbench:

1. **Include the module definition:**
   ```spectre
   include "path/to/measurement_helpers.va"
   ```

2. **Instantiate:**
   ```spectre
   Xprobe (input_net, output_net, VDD, VSS) measurement_module_name param=value
   ```

3. **Probe the output:**
   ```spectre
   meas output_net VSS DC   // or AC, transient, etc.
   ```

For full `.scs` testbench workflow, see `testbench-spectre.md`.
