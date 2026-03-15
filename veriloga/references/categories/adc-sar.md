# ADC / SAR
<!-- domain: voltage -->

Patterns for successive-approximation register ADCs, pipeline ADCs, and flash sub-ADCs.

## Typical Ports

| Port | Direction | Purpose |
|---|---|---|
| `VDD, VSS` | inout | Power rails |
| `CLK, MCLK, CLKS` | input | Main clock, sample clock |
| `VINP, VINN` | input | Differential analog input |
| `DCOMP, DCOMPB` | input | Comparator decision (from external comparator) |
| `DOUT[N:0]` | output | Digital output word |
| `DP_DAC[N:0], DM_DAC[N:0]` | output | DAC control bits (to CDAC) |
| `CMPCK` | output | Comparator clock |
| `RDY, EOC` | output | Ready / end-of-conversion flag |

## Typical Parameters

```
parameter integer Nbit   = 10;          // resolution
parameter real    vdd    = 0.9;         // nominal supply (for threshold calc)
parameter real    vtrans = 0.45;        // clock threshold
parameter real    vrefp  = 0.9;         // positive reference
parameter real    vrefn  = 0.0;         // negative reference
parameter real    tedge  = 15e-12;      // output transition time
parameter real    td_cmp = 20e-12;      // comparator delay
parameter real    Vhi    = 0.9;         // logic high (use vh from VDD in practice)
parameter real    Vlo    = 0.0;         // logic low (use vl from VSS in practice)
```

## Analog Block Structure

SAR ADCs are event-driven state machines. The typical flow:

```
analog begin
    vh = V(VDD); vl = V(VSS);
    vth = (vh + vl) / 2.0;

    // 1. Initialize
    @(initial_step) begin
        bit = Nbit - 1;
        for (i = 0; i < Nbit; i = i + 1)
            B[i] = 0;
        done = 0;
    end

    // 2. Sample phase — reset on CLKS falling edge
    @(cross(V(CLKS) - vth, -1)) begin
        bit = Nbit - 1;
        for (i = 0; i < Nbit; i = i + 1)
            B[i] = 0;
        done = 0;
    end

    // 3. Bit-cycling — on comparator clock rising edge
    @(cross(V(CLK) - vth, +1)) begin
        if (bit >= 0) begin
            // Read comparator result
            B[bit] = (V(DCOMP) > vth) ? 1 : 0;
            bit = bit - 1;
        end
        if (bit < 0)
            done = 1;
    end

    // 4. Drive DAC control outputs
    for (i = 0; i < Nbit; i = i + 1)
        V(DOUT[i]) <+ transition(B[i] ? vh : vl, tedge, tedge);

    V(RDY) <+ transition(done ? vh : vl, tedge, tedge);
end
```

## Key Variables

- `integer B[N:0]` — bit decision array (module level)
- `integer bit` — current bit pointer, counts down from Nbit-1
- `integer done` — end-of-conversion flag
- `genvar i` — loop index for output drive

## Pipeline ADC Variant

Pipeline stages use MDAC (multiplying DAC) with sub-ADC:
- Sample input, compare against reference levels
- Compute residue: `residue = gain * (Vin - Vdac)`
- Pass residue to next stage
- Each stage has its own clock phase

## Design Notes

- SAR modules often have multiple clock domains (sample clock, comparator clock, main clock)
- The bit pointer decrements each cycle — conversion takes Nbit clock cycles
- CDAC control signals are complementary pairs (DP/DM) for differential topologies
- For redundant SAR: bits may overlap (e.g., 1.5-bit/stage) — adjust decision thresholds
