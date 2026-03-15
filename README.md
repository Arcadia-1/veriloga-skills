# veriloga-skills

Agent skill package for writing Verilog-A behavioral modules.

## The Skill: `veriloga/`

A complete skill package that teaches any coding agent to write production-quality Verilog-A. Covers 12 circuit categories with patterns extracted from 1,638 real-world designs.

**Install:** Point your agent at `veriloga/SKILL.md`.

**Customize:** Edit `veriloga/references/customize.md` to override port naming, supply voltage, file headers, and simulator-specific settings.

### What's Inside

```
veriloga/
├── SKILL.md                        # 8 mandatory rules, category index, common pitfalls
├── assets/
│   ├── template.va                 # Starter module skeleton
│   └── examples/                   # 31 representative .va files across 12 categories
│       ├── adc-sar/                #   SAR behavioral, CDAC, comparator, sync/async logic
│       ├── dac/                    #   Binary-weighted, single-ended, differential
│       ├── comparator/             #   Latching, noise-aware with offset modeling
│       ├── pll-clock/              #   Frequency divider, phase-frequency detector
│       ├── sample-hold/            #   Minimal S&H, multi-bit edge sampler
│       ├── amplifier-filter/       #   Differential amplifier, 1st-order LPF
│       ├── digital-logic/          #   AND gate with jitter, DFF with set/reset
│       ├── signal-source/          #   Data generator, swept sine source
│       ├── passive-model/          #   RLC network, Shockley diode
│       ├── testbench-probe/        #   Timing probe, comparator offset search
│       ├── power-switch/           #   Conductance switch, current clamp
│       └── calibration/            #   SPI trim register, DAC code generator
└── references/
    ├── customize.md                # Your project-specific overrides
    └── categories/                 # Per-category patterns & code examples
        ├── adc-sar.md              #   SAR logic, pipeline, CDAC
        ├── dac.md                  #   Binary-weighted, thermometer, current-steering
        ├── comparator.md           #   StrongARM, dynamic, hysteresis
        ├── pll-clock.md            #   VCO, divider, charge pump, PFD
        ├── sample-hold.md          #   Ideal S&H, bottom-plate, bootstrap
        ├── amplifier-filter.md     #   Opamp, OTA, LPF/BPF/HPF
        ├── digital-logic.md        #   Gates, DFF, counter, shift register, FSM
        ├── signal-source.md        #   AM/FM modulator, pulse gen, ramp
        ├── passive-model.md        #   R/C/L, mismatch, tempco, controlled sources
        ├── testbench-probe.md      #   TB wrappers, probes, measurement
        ├── power-switch.md         #   Ideal switch, T-gate, bootstrap, switched-cap
        └── calibration.md          #   Trim code gen, foreground/background cal
```

## Companion Skill: `openvaf/`

Teaches agents to compile Verilog-A modules with OpenVAF and simulate them via ngspice/OSDI. Covers the compile-load-simulate flow, supported features, and troubleshooting.

**Install:** Point your agent at `openvaf/SKILL.md`.

## Other Docs

- [Agent Skill Format](./agent-skill-format.md) — General template for documenting any agent skill

## License

This repository is intended for educational and reference purposes.
