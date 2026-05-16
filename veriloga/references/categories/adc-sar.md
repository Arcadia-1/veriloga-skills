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

## System-Level Decomposition

Do not treat an ADC prompt as one opaque behavior. Split it into mechanism
blocks, then connect those blocks with observable relations:

| Block | Typical observable | Contract-style check |
|---|---|---|
| Sample / hold | `vin_sh`, `clks`, `phi1`, `phi2` | The sample/update clock has edges; sampled value follows input at the requested phase |
| Quantizer / flash sub-ADC | `DOUT[*]`, `dout_*`, `dout_code` | Codes cover the expected range and are not stuck |
| SAR control | `DP_DAC[*]`, `DM_DAC[*]`, `CMPCK`, `RDY`, `EOC` | Bit trial/control signals move; ready/end flag asserts after conversion |
| CDAC / DAC reconstruction | `vout`, `VDAC_P`, `VDAC_N` | Output span is non-trivial and matches the same bit order/reference as the code |
| Pipeline residue / MDAC | `vres`, `residue` | Residue changes across decision regions and stays bounded |
| Calibration / trim | `TRIM_code`, `CAL*`, trim buses | Trim/control code converges or at least moves under the calibration stimulus |

For an ADC-DAC round trip, the useful chain is:

```
sample clock -> sampled input -> quantizer code -> DAC reconstruction
```

The repair loop should therefore look at a vector of mechanism failures:
missing clock edges, stuck code, wrong bit order, wrong reference scale,
flat reconstruction output, missing ready flag, flat residue, or static
calibration control. This is more useful than a single note such as "ADC
failed", because it points to the broken internal relation.

### Gold-Derived Robustness Lessons

Gold sweeps should be non-mutating: copy the gold testbench/DUT to a result
folder, perturb public stimulus parameters, and record the mechanism metrics.
For `sar_adc_dac_weighted_8b_smoke`, sweeping input sine frequency showed:

- `fin=50k..500k` passes the existing checker.
- Code coverage drops from 224 unique codes at `100k` to 57 at `500k`.
- Average reconstruction error rises from about `2.2mV` to `8.2mV`.
- `fin=1M` became a timeout/error boundary in the local EVAS run, with only
  partial metrics available.

This tells the generator that input speed versus sampling cadence is part of
the ADC contract. A repair that only toggles outputs is not enough; it must
preserve sampling phase, bit order, reference scale, and reconstruction timing.

## Design Notes

- SAR modules often have multiple clock domains (sample clock, comparator clock, main clock)
- The bit pointer decrements each cycle — conversion takes Nbit clock cycles
- CDAC control signals are complementary pairs (DP/DM) for differential topologies
- For redundant SAR: bits may overlap (e.g., 1.5-bit/stage) — adjust decision thresholds
