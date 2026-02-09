# Verilog-A Guidelines

## Module Template

```verilog
module <module_name> (
    inout electrical VDD,
    inout electrical VSS,
    input electrical signal_i,
    output electrical [7:0] data_o
);
    // ALL variable declarations at module level
    parameter real vth = 0.5;
    integer state, signal_val, data_val;
    real vh_actual, vl_actual;
    genvar i;
    
    analog begin
        // Read supply voltages
        vh_actual = V(VDD);
        vl_actual = V(VSS);
        
        // Initialize state
        @(initial_step) state = 0;
        
        // Read inputs
        signal_val = (V(signal_i) > vth) ? 1 : 0;
        
        // Edge-triggered logic
        @(cross(V(signal_i) - vth, +1)) begin
            state = state + 1;
        end
        
        // Output assignment
        for (i = 0; i < 8; i = i + 1) begin
            V(data_o[i]) <+ transition((data_val & (1 << i)) ? vh_actual : vl_actual);
        end
    end
endmodule
```

## Key Rules

1. **All signals**: Use `electrical` type for all ports
2. **Power ports**: Always include VDD/VSS ports as `inout` (not `input`)
3. **Read supply**: `vh = V(VDD, VSS)` or `vh = V(VDD); vl = V(VSS);`
4. **Read inputs**: `val = (V(sig) > vth) ? 1 : 0`
5. **Output**: `V(out) <+ transition(val ? vh : vl)`
6. **Loop variables**: Use `genvar` (not `integer`) for loop indices
7. **Variable declarations**: ALL variables must be declared at module level, BEFORE `analog begin`

## Variable Declaration Rules

```verilog
module example (
    input electrical clk_i,
    output electrical out_o
);
    // ✓ All declarations at module level
    parameter real vth = 0.5;
    integer counter, state, tmp_val;
    real voltage;
    genvar i;
    
    analog begin
        // ✗ NEVER declare variables here!
        // integer tmp;  // ERROR!
        
        // ✓ Only assignments and logic here
        tmp_val = 0;
        counter = counter + 1;
    end
endmodule
```

## Loop Variables

```verilog
genvar i, j;  // Declare loop variables as genvar

analog begin
    // Use genvar in for loops
    for (i = 0; i < 8; i = i + 1) begin
        if (V(bus[i]) > vth)
            value = value + (1 << i);
    end
end
```

## Edge Detection

```verilog
@(cross(V(clk_i) - vth, +1))  // Rising edge
@(cross(V(clk_i) - vth, -1))  // Falling edge
@(cross(V(clk_i) - vth))      // Both edges
```

## Common Pitfalls

❌ **Macros in transition()**: `V(out) <+ transition(vh, 0, \`macro);` → Use literals  
❌ **Missing VDD/VSS**: Always include power ports  
❌ **SystemVerilog constructs**: No `always_ff`, `logic`, etc.  
❌ **Uninitialized variables**: Use `@(initial_step)`  
❌ **Wrong cross direction**: `+1` for rising, `-1` for falling  
❌ **Loop variables as integer**: Use `genvar` for loop indices, not `integer`  
❌ **Variables in analog block**: Declare ALL variables at module level, NOT inside `analog begin`

## Best Practices

1. **Consistent naming**: Use suffixes like `_i` for inputs, `_o` for outputs
2. **Parameter naming**: Use lowercase with underscores (e.g., `vth`, `delay_time`)
3. **State initialization**: Always initialize state variables with `@(initial_step)`
4. **Transition function**: Always use `transition()` for outputs to ensure smooth transitions
5. **Supply voltage handling**: Always read and use actual supply voltages from VDD/VSS ports

## Example: Complete Counter Module

```verilog
module counter_8bit (
    inout electrical VDD,
    inout electrical VSS,
    input electrical clk_i,
    input electrical reset_i,
    output electrical [7:0] count_o
);
    // All variable declarations at module level
    parameter real vth = 0.5;
    integer count, clk_val, reset_val;
    real vh_actual, vl_actual;
    genvar i;
    
    analog begin
        // Read supply voltages
        vh_actual = V(VDD);
        vl_actual = V(VSS);
        
        // Initialize counter
        @(initial_step) begin
            count = 0;
        end
        
        // Read inputs
        clk_val = (V(clk_i) > vth) ? 1 : 0;
        reset_val = (V(reset_i) > vth) ? 1 : 0;
        
        // Reset logic
        if (reset_val) begin
            count = 0;
        end
        
        // Clock edge detection
        @(cross(V(clk_i) - vth, +1)) begin
            if (!reset_val) begin
                count = (count + 1) % 256;
            end
        end
        
        // Output assignment
        for (i = 0; i < 8; i = i + 1) begin
            V(count_o[i]) <+ transition((count & (1 << i)) ? vh_actual : vl_actual);
        end
    end
endmodule
```
