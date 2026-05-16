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

### Split-Supply Control vs Core Mapping

When a project uses separate control and analog-core supplies, use the control
domain for thresholding digital-like control pins and the analog-core domain for
the comparator's analog behavior, unless project customization says otherwise.

```verilog
module comp_split_supply (
    input  electrical CLK,
    input  electrical EN,
    input  electrical AZ,
    input  electrical VINP,
    input  electrical VINN,
    inout  electrical VDD_DIG,
    inout  electrical VSS_DIG,
    inout  electrical VDD_ANA,
    inout  electrical VSS_ANA,
    output electrical OUTP,
    output electrical OUTN
);

real vh_dig, vl_dig, vth_ctrl;
real vh_ana, vl_ana;
integer outp_q, outn_q;

analog begin
    vh_dig = V(VDD_DIG); vl_dig = V(VSS_DIG);
    vh_ana = V(VDD_ANA); vl_ana = V(VSS_ANA);
    vth_ctrl = (vh_dig + vl_dig) / 2.0;

    @(initial_step) begin
        outp_q = 0;
        outn_q = 0;
    end

    @(cross(V(CLK) - vth_ctrl, +1)) begin
        if ((V(EN) > vth_ctrl) && (V(AZ) < vth_ctrl)) begin
            if ((V(VINP) - V(VINN)) > 0.0) begin
                outp_q = 1;
                outn_q = 0;
            end else begin
                outp_q = 0;
                outn_q = 1;
            end
        end
    end

    V(OUTP) <+ transition(outp_q ? vh_dig : vl_dig, 0, tedge, tedge);
    V(OUTN) <+ transition(outn_q ? vh_dig : vl_dig, 0, tedge, tedge);
end
endmodule
```

Default policy:

- `CLK`, `EN`, `AZ`, reset, and ready/handshake thresholds use the digital/control domain
- Analog comparison and analog bias/state reference the analog-core domain
- If top-level wiring intentionally uses a different threshold domain, follow the wiring and document the exception

## Design Notes

- Always provide complementary outputs (DCMPP/DCMPN) — SAR logic needs both
- The reset phase (falling edge) is essential for latching comparators; without it,
  outputs hold stale values and cause meta-stability in downstream logic
- Offset `Vos` models random mismatch — typically swept via Monte Carlo
- For StrongARM: propagation delay is input-dependent in real circuits; for behavioral
  model, a fixed `td_cmp` parameter is usually sufficient
- Output is differential and rail-to-rail (swings between VDD and VSS)
- For split-supply projects, threshold control pins with the digital/control domain by default and keep the analog decision path on the analog-core domain unless `customize.md` overrides that policy
