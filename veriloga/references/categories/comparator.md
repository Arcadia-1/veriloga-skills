# Comparator
<!-- domain: voltage -->

Patterns for clocked comparators: StrongARM, dynamic, latching, and continuous-time.

## Typical Ports

| Port | Direction | Purpose |
|---|---|---|
| `VDD, VSS` | inout | Power rails |
| `VINP, VIP` | input | Positive analog input |
| `VINN, VIN` | input | Negative analog input |
| `CLK` | input | Comparison clock |
| `EN` | input | Enable (optional) |
| `DCMPP, DOUTP` | output | Positive decision output |
| `DCMPN, DOUTN` | output | Negative / complementary output |
| `RDY` | output | Ready flag (optional) |

## Typical Parameters

```
parameter real td_cmp  = 20e-12;       // propagation delay
parameter real Vos     = 0.0;          // input offset voltage
parameter real tedge   = 15e-12;       // output transition time
parameter real vdd_nom = 0.9;          // nominal supply (for reference only)
```

## Analog Block Pattern

Comparators are edge-triggered with a reset phase. The canonical structure:

```
analog begin
    vh = V(VDD); vl = V(VSS);
    vth = (vh + vl) / 2.0;

    @(initial_step) begin
        xoutp = 0;
        xoutn = 0;
    end

    // Sense: rising clock edge triggers comparison
    @(cross(V(CLK) - vth, +1)) begin
        if ((V(VINP) - V(VINN) + Vos) > 0.0) begin
            xoutp = 1;
            xoutn = 0;
        end else begin
            xoutp = 0;
            xoutn = 1;
        end
    end

    // Reset: falling clock edge clears outputs
    @(cross(V(CLK) - vth, -1)) begin
        xoutp = 0;
        xoutn = 0;
    end

    // Drive complementary outputs
    V(DCMPP) <+ transition(xoutp ? vh : vl, td_cmp, tedge, tedge);
    V(DCMPN) <+ transition(xoutn ? vh : vl, td_cmp, tedge, tedge);
end
```

## Key Variables

- `integer xoutp, xoutn` — latch flags (complementary pair)
- `real Vos` — models input-referred offset (add to differential input)

## Variants

### Continuous-Time (No Clock)
```
// No cross() events — purely combinational
vdiff = V(VINP) - V(VINN) + Vos;
V(DOUT) <+ transition((vdiff > 0) ? vh : vl, td_cmp, tedge, tedge);
```

### With Hysteresis
```
@(cross(V(VINP) - V(VINN) - vhyst/2, +1))
    xout = 1;
@(cross(V(VINP) - V(VINN) + vhyst/2, -1))
    xout = 0;
```

### With Enable
```
@(cross(V(CLK) - vth, +1)) begin
    if (V(EN) > vth) begin
        // Compare only when enabled
        ...
    end
end
```

## Design Notes

- Always provide complementary outputs (DCMPP/DCMPN) — SAR logic needs both
- The reset phase (falling edge) is essential for latching comparators; without it,
  outputs hold stale values and cause meta-stability in downstream logic
- Offset `Vos` models random mismatch — typically swept via Monte Carlo
- For StrongARM: propagation delay is input-dependent in real circuits; for behavioral
  model, a fixed `td_cmp` parameter is usually sufficient
- Output is differential and rail-to-rail (swings between VDD and VSS)
