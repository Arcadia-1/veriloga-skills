Given a voltage-domain DAC DUT, generate a minimal EVAS-compatible Spectre-format
`.scs` testbench that verifies a monotonic ramp response.

Requirements:

- provide `VDD` and `VSS`
- create a simple code stimulus that steps through several DAC codes
- instantiate the DUT by position
- include `tran`
- include explicit `save`
- place `ahdl_include` last
