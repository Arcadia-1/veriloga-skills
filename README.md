# veriloga-skills

Agent skills for veriloga

## Documentation

- [Agent Skill Format](./agent-skill-format.md) - Standard format for documenting agent skills

## About

This repository contains agent skills for the veriloga project. Each skill is documented following a standardized markdown format to ensure consistency and ease of use.

## Getting Started

To add a new skill:

1. Read the [Agent Skill Format](./agent-skill-format.md) documentation
2. Create a new markdown file following the template
3. Document all required sections
4. Submit your skill for review

## Structure

```
veriloga-skills/
├── agent-skill-format.md    # Format specification and template
├── README.md                 # This file
└── skills/                   # Individual skill files (to be added)
```
# Verilog-A Skills

Agent skills and reference examples for Verilog-A hardware description language.

## Overview

This repository contains comprehensive guidelines, examples, and best practices for writing proper Verilog-A code. It serves as a reference for developers and AI agents working with Verilog-A modules.

## Contents

### 📚 Documentation

- **[VERILOG_A_GUIDELINES.md](VERILOG_A_GUIDELINES.md)** - Complete guidelines for Verilog-A coding standards

### ✅ Correct Examples (`examples/correct/`)

Working examples that follow all Verilog-A guidelines:

- **counter_8bit.va** - 8-bit counter with proper variable declarations and edge detection
- **shift_register.va** - 4-bit shift register demonstrating data shifting
- **buffer.va** - Simple buffer with supply voltage tracking
- **edge_detector.va** - Rising and falling edge detection patterns
- **state_machine_example.va** - Complete state machine with multiple outputs and comprehensive documentation

### ❌ Incorrect Examples (`examples/incorrect/`)

Common mistakes to avoid, with explanations:

- **wrong_var_location.va** - Variables declared inside `analog begin` (WRONG)
- **wrong_loop_var.va** - Using `integer` instead of `genvar` for loops
- **wrong_power_ports.va** - Incorrect power port declarations
- **wrong_edge_direction.va** - Wrong cross direction for edge detection
- **uninitialized_vars.va** - Missing variable initialization

## Key Guidelines

### Essential Rules

1. **All signals**: Use `electrical` type
2. **Power ports**: Always include VDD/VSS as `inout` (not `input`)
3. **Variable declarations**: ALL variables at module level, BEFORE `analog begin`
4. **Loop variables**: Use `genvar` (not `integer`) for loop indices
5. **Initialization**: Always initialize state variables with `@(initial_step)`
6. **Edge detection**: Use `@(cross(V(sig) - vth, +1))` for rising, `-1` for falling

### Module Template

```verilog
module example (
    inout electrical VDD,
    inout electrical VSS,
    input electrical in_i,
    output electrical out_o
);
    // ALL declarations at module level
    parameter real vth = 0.5;
    integer state;
    real vh_actual, vl_actual;
    genvar i;
    
    analog begin
        // Read supply voltages
        vh_actual = V(VDD);
        vl_actual = V(VSS);
        
        // Initialize
        @(initial_step) state = 0;
        
        // Logic here...
    end
endmodule
```

## Usage

### For Developers

Use this repository as a reference when writing Verilog-A modules. Check the correct examples for patterns and the incorrect examples to avoid common mistakes.

### For AI Agents

This repository provides structured guidelines and examples for generating or validating Verilog-A code. Follow the patterns in `examples/correct/` and avoid the pitfalls shown in `examples/incorrect/`.

## Common Pitfalls

❌ Variables inside `analog begin`  
❌ `integer` for loop variables (use `genvar`)  
❌ VDD/VSS as `input` (use `inout`)  
❌ Missing `@(initial_step)` initialization  
❌ Wrong `@(cross())` direction (+1 = rising, -1 = falling)  

## License

This repository is intended for educational and reference purposes.
