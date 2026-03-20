Given a voltage-domain clock divider DUT, generate a minimal Spectre-format
`.scs` testbench suitable for EVAS.

Requirements:

- provide `VDD`, `VSS`, input clock, and reset stimulus
- instantiate the DUT by position
- include `tran`
- include explicit `save`
- place `ahdl_include` last
