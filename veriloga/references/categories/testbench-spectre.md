# Spectre Testbench Netlists (.scs)

How to write proper `.scs` testbench files for simulating Verilog-A behavioral modules.
This is the **correct place** for testbenches, stimulus, and measurement commands.

---

## Key Concepts

| Artifact | File Type | Purpose |
|---|---|---|
| **Behavioral Module** | `.va` | Verilog-A code; implements circuit behavior |
| **Testbench Netlist** | `.scs` | Spectre netlist; instantiates the module, drives inputs, measures outputs |
| **Measurement Helper** | `.va` | Optional Verilog-A module for probes, DAC reconstructors, etc. |

---

## Basic `.scs` Testbench Structure

```spectre
// ────────────────────────────────────────────────────────────
// Testbench: adder_simple
// Description: Test 4-bit full adder behavioral model
// ────────────────────────────────────────────────────────────

simulator lang=spectre

// Include the Verilog-A behavioral module
include "path/to/adder_4bit.va"

// Global options
global 0

// Power supply definition
Vdd vdd 0 dc=3.3

// Test stimulus: voltage sources or pulse sources
Va a[0] 0 pwl(0 0 10n 0 11n 3.3 20n 3.3 21n 0)
Vb b[0] 0 pwl(0 0 10n 0 11n 0 20n 3.3 21n 3.3)
Vin_c cin 0 dc=0

// Module instantiation
Xadd (a[0] b[0] cin sum s[0] vdd 0) adder_4bit vth=1.65

// Transient simulation
tran tran start=0 stop=30n step=10p

// Measurements
meas tran sum_at_15n FIND V(s[0]) AT=15n
meas tran sum_rise TRIG V(s[0]) VAL=1.65 RISE=1 TARG V(s[0]) VAL=2.97 RISE=1
```

---

## Stimulus Sources in Spectre

### DC Voltage Source
```spectre
Vdc net 0 dc=1.5   // constant 1.5V
```

### AC Voltage Source
```spectre
Vac net 0 ac=1.0 phase=45   // AC analysis only
```

### Pulse/PWL Sources

**Pulse (periodic square wave):**
```spectre
Vpulse clk 0 pulse(initial_val pulse_val delay rise_time fall_time pulse_width period)
// Example: 0V → 3.3V, 100ps delay, 10ps rise, 10ps fall, 500ps width, 1ns period
Vpulse clk 0 pulse(0 3.3 100p 10p 10p 500p 1ns)
```

**PWL (piecewise linear):**
```spectre
Vpwl sig 0 pwl(time1 value1 time2 value2 time3 value3 ...)
// Example: ramp 0→3.3V over 100ns, stay 3.3V, ramp down 3.3→0V
Vpwl sig 0 pwl(0 0 100n 3.3 200n 3.3 300n 0)
```

### Current Source
```spectre
Idc net 0 dc=10u   // 10 μA current source
```

---

## Module Instantiation

```spectre
// Instance name    Net connections           Module name    Parameters
X<instance_name> ( net1 net2 net3 ... ) <module_name> <param1>=<value1> <param2>=<value2>
```

**Example:**
```spectre
// Instantiate adder_4bit with 4 input bits, carry in/out, power
Xdut (a[3:0] b[3:0] cin sum[3:0] cout vdd vss) adder_4bit vth=1.65 trise=5p
```

---

## Analysis Types

### Transient Analysis (Time-domain)
```spectre
tran tran start=0 stop=<time> step=<timestep>
// Example: 0 to 100ns with 1ps steps
tran tran start=0 stop=100n step=1p
```

### AC Analysis (Frequency-domain)
```spectre
ac ac start=1Hz stop=1MHz dec=10
// dec=N: N points per decade
// lin=N: N points linearly spaced
// log: logarithmic sweep
```

### DC Analysis
```spectre
dc sweep_var=<net> start=<v1> stop=<v2> step=<dv>
// Example: sweep V(vin) from 0 to 3.3V in 100mV steps
dc sweep_var=vin start=0 stop=3.3 step=100m
```

---

## Measurements

### Transient Measurements

**Find value at specific time:**
```spectre
meas tran <meas_name> FIND V(<net>) AT=<time>
// Example: measure voltage at t=50ns
meas tran v_at_50n FIND V(out) AT=50n
```

**Rise time (low-to-high transition):**
```spectre
meas tran <meas_name> TRIG V(<net>) VAL=<low> RISE=1 TARG V(<net>) VAL=<high> RISE=1
// Example: measure time from 10% to 90% of swing (1.65V to 2.97V at 3.3V supply)
meas tran rise_time TRIG V(out) VAL=0.33 RISE=1 TARG V(out) VAL=2.97 RISE=1
```

**Fall time (high-to-low transition):**
```spectre
meas tran <meas_name> TRIG V(<net>) VAL=<high> FALL=1 TARG V(<net>) VAL=<low> FALL=1
```

**Propagation delay:**
```spectre
meas tran <meas_name> TRIG V(<in>) VAL=<threshold> RISE=1 TARG V(<out>) VAL=<threshold> RISE=1
```

### AC Measurements

**Magnitude at specific frequency:**
```spectre
meas ac <meas_name> FIND VDB(<net>) AT=<frequency>
// Example: find magnitude at 1 MHz
meas ac mag_at_1MHz FIND VDB(out) AT=1MHz
```

**Cutoff frequency (-3dB):**
```spectre
meas ac f_3dB TRIG VDB(out) VAL=<max-3> FALL=1
```

---

## Complete Example: ADC Behavioral Model Testbench

```spectre
// ────────────────────────────────────────────────────────────
// Testbench: adc_sar_tb
// Description: SAR ADC 10-bit behavioral model verification
// ────────────────────────────────────────────────────────────

simulator lang=spectre

// Include behavioral modules
include "adc_sar_10bit.va"
include "dac_reconstructor.va"

global 0

// Power supplies
Vdd vdd 0 dc=3.3
Vss vss 0 dc=0

// Test input: 1 kHz sine wave, 1.65V DC offset, 0.5V amplitude
Vin vin 0 pwl(0 1.65 1m 1.65)
sin_source (vin 0) vsource dc=1.65 ac=0.5 freq=1k

// Clock: 100 kHz
Vclk clk 0 pulse(0 3.3 0 10p 10p 5u 10u)

// Module instantiation
Xadc (vin clk vdd vss dout[9:0] eoc) adc_sar_10bit vth=1.65

// Optional: DAC reconstructor to view digital output as analog
Xdac_recon (dout[9:0] dout_analog vdd vss) dac_reconstructor Nbits=10

// Transient simulation: capture 10 conversion cycles at 100 kHz = 100 μs
tran tran start=0 stop=100u step=10n

// Measurements
meas tran dout_at_10u FIND V(dout[0]) AT=10u
meas tran eoc_first TRIG V(eoc) VAL=1.65 RISE=1
meas tran eoc_period TRIG V(eoc) VAL=1.65 RISE=2 TARG V(eoc) VAL=1.65 RISE=3
```

---

## Common Pitfalls

| Pitfall | Solution |
|---|---|
| Forgetting `include` statement | Always include the `.va` module file at the top |
| Wrong net names in instantiation | Use the exact port names from the `.va` module definition |
| No power connections | Always connect `vdd` and `vss` to the module |
| Measurement time outside simulation range | Use `AT=` or `TRIG/TARG` within the simulated timespan |
| Threshold voltage too low/high | Use `(vdd + vss) / 2` as the reference (usually 1.65V for 3.3V supply) |

---

## Integration with Measurement Helpers

See `measurement-helpers.md` for reusable Verilog-A modules (probes, reconstructors, error monitors).

To use them in `.scs`:

```spectre
include "path/to/measurement_helpers.va"

// Instantiate a probe
Xprobe (measured_signal, probe_output, vdd, vss) voltage_probe gain=1.0

// Instantiate a DAC reconstructor
Xdac_recon (digital_bus[7:0], analog_out, vdd, vss) dac_reconstructor Nbits=8

// Measure the output
meas tran probe_val FIND V(probe_output) AT=50n
```
