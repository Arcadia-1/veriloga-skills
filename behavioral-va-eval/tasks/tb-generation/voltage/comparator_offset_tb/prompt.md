Given a voltage-domain comparator DUT, generate a minimal EVAS-compatible
Spectre-format `.scs` testbench to measure comparator offset behavior.

Requirements:

- provide `VDD`, `VSS`, and a clock if needed
- drive the differential input with a small sweep or stepped offset
- instantiate the DUT by position
- include `tran`
- include explicit `save`
- place `ahdl_include` last
