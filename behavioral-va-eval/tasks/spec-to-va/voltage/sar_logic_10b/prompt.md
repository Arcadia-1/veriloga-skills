Write a Verilog-A 10-bit SAR ADC logic block.

Requirements:

- Inputs: `VDD`, `VSS`, `CLKS`, `DCOMP`
- Outputs: `DP_DAC[9:0]`, `RDY`
- Voltage-domain only
- Use clock-edge-driven SAR state sequencing
- Outputs must be driven with supply-referenced `transition()`
- No current contributions
- No testbench content
