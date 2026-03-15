# Digital Logic
<!-- domain: voltage -->

Patterns for gates, flip-flops, latches, MUX, decoders, encoders, counters, shift registers, and state machines.

## Typical Ports

| Block | Ports |
|---|---|
| **Gate** | `in: vin1, vin2` → `out: vout` |
| **Flip-flop** | `in: d_i, clk_i, rst_i` → `out: q_o, qb_o` |
| **Counter** | `in: clk_i, rst_i` → `out: [N:0] count_o` |
| **MUX** | `in: [N:0] din, sel_i` → `out: vout` |
| **Decoder** | `in: [M:0] addr_i` → `out: [N:0] sel_o` |
| All blocks | `inout: VDD, VSS` |

## Typical Parameters

```
parameter real trise = 10e-12;         // output rise time [s]
parameter real tfall = 10e-12;         // output fall time [s]
parameter real tdel  = 0.0;           // propagation delay [s]
```

## Combinational Gate (AND example)

```
integer logic1, logic2;

analog begin
    vh = V(VDD); vl = V(VSS);
    vth = (vh + vl) / 2.0;

    // Track input levels via cross() for event-driven efficiency
    @(cross(V(vin1) - vth, +1)) logic1 = 1;
    @(cross(V(vin1) - vth, -1)) logic1 = 0;
    @(cross(V(vin2) - vth, +1)) logic2 = 1;
    @(cross(V(vin2) - vth, -1)) logic2 = 0;

    V(vout) <+ transition((logic1 && logic2) ? vh : vl, tdel, trise, tfall);
end
```

For simple gates, you can also use continuous threshold comparison without `cross()`:
```
V(vout) <+ transition(((V(vin1) > vth) && (V(vin2) > vth)) ? vh : vl, tdel, trise, tfall);
```
The `cross()` approach is more simulator-efficient for large netlists.

## D Flip-Flop

```
integer q_val;

analog begin
    vh = V(VDD); vl = V(VSS);
    vth = (vh + vl) / 2.0;

    @(initial_step)
        q_val = 0;

    // Async reset (active high)
    @(cross(V(rst_i) - vth, +1))
        q_val = 0;

    // Clock rising edge — capture D
    @(cross(V(clk_i) - vth, +1))
        if (V(rst_i) < vth)
            q_val = (V(d_i) > vth) ? 1 : 0;

    V(q_o)  <+ transition(q_val ? vh : vl, tdel, trise, tfall);
    V(qb_o) <+ transition(q_val ? vl : vh, tdel, trise, tfall);
end
```

## N-Bit Counter

```
parameter integer Nbits = 8;

integer count;
genvar i;

analog begin
    vh = V(VDD); vl = V(VSS);
    vth = (vh + vl) / 2.0;

    @(initial_step)
        count = 0;

    @(cross(V(rst_i) - vth, +1))
        count = 0;

    @(cross(V(clk_i) - vth, +1))
        if (V(rst_i) < vth)
            count = (count + 1) % (1 << Nbits);

    for (i = 0; i < Nbits; i = i + 1)
        V(count_o[i]) <+ transition(((count >> i) & 1) ? vh : vl, tdel, trise, tfall);
end
```

## Shift Register

```
parameter integer Nbits = 4;

integer sr[0:3];                       // one element per stage
genvar i;

analog begin
    vh = V(VDD); vl = V(VSS);
    vth = (vh + vl) / 2.0;

    @(initial_step)
        for (i = 0; i < Nbits; i = i + 1)
            sr[i] = 0;

    @(cross(V(clk_i) - vth, +1)) begin
        for (i = Nbits - 1; i > 0; i = i - 1)
            sr[i] = sr[i-1];
        sr[0] = (V(din_i) > vth) ? 1 : 0;
    end

    for (i = 0; i < Nbits; i = i + 1)
        V(dout_o[i]) <+ transition(sr[i] ? vh : vl, tdel, trise, tfall);
end
```

## State Machine (FSM)

```
parameter integer S_IDLE = 0, S_RUN = 1, S_DONE = 2;

integer state;

analog begin
    vh = V(VDD); vl = V(VSS);
    vth = (vh + vl) / 2.0;

    @(initial_step)
        state = S_IDLE;

    @(cross(V(clk_i) - vth, +1)) begin
        case (state)
            S_IDLE: if (V(start_i) > vth) state = S_RUN;
            S_RUN:  if (/* done condition */) state = S_DONE;
            S_DONE: state = S_IDLE;
        endcase
    end

    V(busy_o) <+ transition((state == S_RUN) ? vh : vl, tdel, trise, tfall);
    V(done_o) <+ transition((state == S_DONE) ? vh : vl, tdel, trise, tfall);
end
```

## Design Notes

- Digital logic in Verilog-A is behavioral — no gate-level synthesis
- Use `case` statements for FSMs with >3 states — cleaner than nested if-else
- Bit extraction: `(count >> i) & 1` extracts bit `i` from an integer
- Shift registers shift *backwards* through the array (MSB first) to avoid overwriting
- For async reset: place the reset `@(cross())` *before* the clock event — the simulator
  processes events in order of appearance
