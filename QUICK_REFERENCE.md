# Verilog-A Quick Reference Card

## Port Declarations

```verilog
inout electrical VDD, VSS;      // ✓ Power ports (always inout)
input electrical clk_i, data_i;  // ✓ Input signals
output electrical [7:0] out_o;   // ✓ Output bus
```

## Variable Declarations (Module Level Only!)

```verilog
module example (...);
    // Parameters
    parameter real vth = 0.5;
    parameter real tdelay = 1n;
    
    // Variables - ALL at module level
    integer state, count, tmp;
    real vh_actual, vl_actual, voltage;
    genvar i, j;  // For loops only
    
    analog begin
        // NO declarations here!
    end
endmodule
```

## Reading Supply Voltages

```verilog
// Always read actual supply voltages
vh_actual = V(VDD);
vl_actual = V(VSS);

// Or differential
vh_actual = V(VDD, VSS);
```

## Reading Digital Inputs

```verilog
// Threshold comparison
signal_val = (V(signal_i) > vth) ? 1 : 0;

// For bus inputs
for (i = 0; i < 8; i = i + 1) begin
    if (V(bus_i[i]) > vth)
        value = value | (1 << i);
end
```

## Writing Digital Outputs

```verilog
// Single bit
V(out_o) <+ transition(signal_val ? vh_actual : vl_actual, 0, tdelay);

// Bus output
for (i = 0; i < 8; i = i + 1) begin
    V(data_o[i]) <+ transition((data_val & (1 << i)) ? vh_actual : vl_actual, 0, tdelay);
end
```

## Edge Detection

```verilog
// Rising edge (+1)
@(cross(V(clk_i) - vth, +1)) begin
    count = count + 1;
end

// Falling edge (-1)
@(cross(V(clk_i) - vth, -1)) begin
    state = 0;
end

// Both edges (no direction)
@(cross(V(clk_i) - vth)) begin
    toggle = !toggle;
end
```

## Initialization

```verilog
// Always initialize state variables
@(initial_step) begin
    state = 0;
    count = 0;
    shift_reg = 0;
end
```

## Timer Events

```verilog
// One-time timer
@(timer(10n)) begin
    pulse = 0;
end

// Periodic timer
@(timer(0, 10n)) begin
    periodic_flag = !periodic_flag;
end
```

## Loops

```verilog
// Declare genvar at module level
genvar i;

analog begin
    // Use in for loops
    for (i = 0; i < 8; i = i + 1) begin
        V(out[i]) <+ transition(...);
    end
end
```

## Common Patterns

### Synchronous Counter

```verilog
@(initial_step) count = 0;

@(cross(V(clk_i) - vth, +1)) begin
    if (reset_val)
        count = 0;
    else
        count = (count + 1) % MAX_COUNT;
end
```

### Shift Register

```verilog
@(initial_step) shift_reg = 0;

@(cross(V(clk_i) - vth, +1)) begin
    shift_reg = ((shift_reg << 1) | data_val) & MASK;
end
```

### State Machine

```verilog
@(initial_step) state = IDLE;

@(cross(V(clk_i) - vth, +1)) begin
    case (state)
        IDLE: state = enable ? ACTIVE : IDLE;
        ACTIVE: state = done ? IDLE : ACTIVE;
    endcase
end
```

## Do's and Don'ts

### ✓ DO

- Declare ALL variables at module level
- Use `genvar` for loop indices
- Use `inout` for VDD/VSS ports
- Read actual supply voltages
- Initialize state variables with `@(initial_step)`
- Use correct `@(cross())` direction

### ✗ DON'T

- Declare variables inside `analog begin`
- Use `integer` for loop variables
- Use `input` for power ports
- Hardcode supply voltages (1.8, 0.0, etc.)
- Leave state variables uninitialized
- Mix up cross directions (+1 vs -1)
- Use SystemVerilog constructs (`always_ff`, `logic`)
- Use macros in `transition()` third parameter

## Transition Function

```verilog
// Basic form
V(out) <+ transition(value);

// With delay (literal only, no macros)
V(out) <+ transition(value, 0, 1n);

// With rise/fall times
V(out) <+ transition(value, 0, 1n, 2n);
```

## Complete Module Checklist

When writing a Verilog-A module, ensure:

- [ ] VDD/VSS ports declared as `inout electrical`
- [ ] All signals declared as `electrical`
- [ ] All variables declared at module level (before `analog begin`)
- [ ] Loop variables declared as `genvar`
- [ ] State variables initialized with `@(initial_step)`
- [ ] Supply voltages read with `V(VDD)` and `V(VSS)`
- [ ] Inputs read with threshold comparison
- [ ] Outputs use `transition()` with actual supply voltages
- [ ] Edge detection uses correct `@(cross())` direction
- [ ] No SystemVerilog constructs used
