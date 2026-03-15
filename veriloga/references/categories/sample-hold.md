# Sample & Hold
<!-- domain: voltage -->

Patterns for track-and-hold, sample-and-hold, and bootstrap switches.

## Typical Ports

| Port | Direction | Purpose |
|---|---|---|
| `VDD, VSS` | inout | Power rails |
| `VIN, IN` | input | Analog input to sample |
| `CLK, VCLK` | input | Sample clock / control |
| `VOUT, OUT` | output | Held analog voltage |

## Typical Parameters

```
parameter real vtrans_clk = 0.45;      // clock threshold [V]
parameter real td         = 50e-12;    // propagation delay [s]
parameter real tt         = 50e-12;    // output transition time [s]
```

## Ideal Sample & Hold

The simplest behavioral module — capture input on clock edge, hold until next:

```
real vh, vl, vth, held;

analog begin
    vh = V(VDD); vl = V(VSS);
    vth = (vh + vl) / 2.0;

    @(initial_step)
        held = 0.0;

    @(cross(V(CLK) - vth, +1))        // sample on rising edge
        held = V(VIN);

    V(VOUT) <+ transition(held, td, tt);
end
```

## Bottom-Plate Sampling Variant

Samples on falling edge (bottom-plate opens first to cancel charge injection):

```
@(cross(V(CLK) - vth, -1))            // sample on falling edge
    held = V(VIN);
```

## Bootstrap Switch

Models a clock-boosted switch for high-linearity sampling:

```
parameter real tde = 50e-12;
parameter real tdc = 50e-12;

real state;

analog begin
    vh = V(VDD); vl = V(VSS);
    vth = (vh + vl) / 2.0;

    @(initial_step)
        state = 0.0;

    @(cross(V(CLK) - vth, +1))
        state = V(VIN) + vh;           // boosted gate voltage

    @(cross(V(CLK) - vth, -1))
        state = 0.0;                   // switch off

    V(clkbs) <+ transition(state, tde, tdc);
end
```

## Design Notes

- S&H modules are the simplest Verilog-A blocks — often just 3 lines of logic
- One `real` variable is all you need for the held voltage
- Clock threshold should be derived from supply: `vth = (vh + vl) / 2.0`
- For differential S&H: use two held variables, sample `V(VINP)` and `V(VINN)` independently
- Bottom-plate sampling (falling edge) is standard in high-performance ADCs
- `transition()` on the output prevents the simulator from seeing an instantaneous voltage jump
