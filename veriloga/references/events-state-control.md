# Events, State, And Control Flow

## Initial State

Use `@(initial_step)` for state that needs a defined value before the first ordinary analog
evaluation:

```verilog
integer count;
real held;

analog begin
    @(initial_step) begin
        count = 0;
        held = 0.0;
    end
end
```

## Threshold Events

`cross(expr, dir)` triggers when `expr` crosses zero. Use `dir` of `+1`, `-1`, or `0`:

```verilog
analog begin
    @(cross(V(clk) - vth, +1)) begin
        held = V(in);
    end

    V(out) <+ transition(held, 0, tt);
end
```

Do not put the only output contribution inside the event. The event updates state; the
contribution outside the event continuously drives the branch from that state.

## Timer Events

`timer(t0, period)` creates scheduled event times:

```verilog
analog begin
    @(timer(start, period)) begin
        phase_index = phase_index + 1;
    end
end
```

## Loops And Arrays

Use integer indices for procedural loops:

```verilog
integer i;
real state[0:3];

analog begin
    @(initial_step) begin
        for (i = 0; i < 4; i = i + 1)
            state[i] = 0.0;
    end
end
```

Keep state updates inside explicit events. Do not create self-referential assignments that run
on every continuous analog evaluation.

Use `genvar` for elaboration-style repeated analog contributions:

```verilog
genvar k;
analog begin
    for (k = 0; k < 4; k = k + 1)
        V(out[k]) <+ transition(state[k], 0, tt);
end
```

## Functions

Place helper functions before the `analog` block:

```verilog
analog function real clamp;
    input x, lo, hi;
    real x, lo, hi;
    begin
        clamp = max(min(x, hi), lo);
    end
endfunction
```
