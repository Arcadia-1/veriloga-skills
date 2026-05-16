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
| **Encoder (binary)** | `param: din (integer, 0..2^N-1)` → `out: [N-1:0] out` |
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

## Static Binary Encoder

Parameter-only input (no signal ports for data). Use `real` variables for computed voltages so
assignments are stable in the bare `analog begin` block — no `@(initial_step)` needed.

```verilog
`include "constants.vams"
`include "disciplines.vams"

module param_encoder_3bit(out);
    output [2:0] out;
    electrical  [2:0] out;

    parameter integer din   = 0;   // encoded value (0..7)
    parameter real    vhigh = 1.0;
    parameter real    vlow  = 0.0;
    parameter real    trise = 1n;
    parameter real    tfall = 1n;

    real vout0, vout1, vout2;

    analog begin
        vout0 = (din & 1) ? vhigh : vlow;
        vout1 = (din & 2) ? vhigh : vlow;
        vout2 = (din & 4) ? vhigh : vlow;

        V(out[0]) <+ transition(vout0, 0, trise, tfall);
        V(out[1]) <+ transition(vout1, 0, trise, tfall);
        V(out[2]) <+ transition(vout2, 0, trise, tfall);
    end
endmodule
```

Key points:
- `real` (not `integer`) for computed voltage values — stable across timesteps without events
- Bitwise AND on integer parameter selects each output bit
- `transition()` on each bus element drives clean digital edges

## Gray Counter

A Gray counter should keep a normal binary counter internally, then encode the
public outputs as `gray = binary ^ (binary >> 1)`. Incrementing the Gray word
directly often breaks the one-bit-transition property.

```
integer bin_count;
integer gray_count;
genvar k;

analog begin
    @(initial_step) begin
        bin_count = 0;
        gray_count = 0;
    end

    @(cross(V(rst_i) - vth, +1)) begin
        bin_count = 0;
        gray_count = 0;
    end

    @(cross(V(clk_i) - vth, +1)) begin
        if (V(rst_i) > vth) begin
            bin_count = 0;
        end else begin
            bin_count = (bin_count + 1) % (1 << Nbits);
        end
        gray_count = bin_count ^ (bin_count >> 1);
    end

    for (k = 0; k < Nbits; k = k + 1)
        V(gray_o[k]) <+ transition(((gray_count >> k) & 1) ? vh : vl, tdel, trise, tfall);
end
```

## Serializer With Frame Alignment

For parallel-to-serial blocks, latch the parallel word on the load-qualified
clock edge, then shift exactly one bit per clock. If the prompt asks for a
frame marker, assert it only for the first serialized bit of the loaded word.

```
integer word_q;
integer bit_idx;
integer sout_q;
integer frame_q;

analog begin
    @(initial_step) begin
        word_q = 0;
        bit_idx = 0;
        sout_q = 0;
        frame_q = 0;
    end

    @(cross(V(clk_i) - vth, +1)) begin
        if (V(load_i) > vth) begin
            word_q = decoded_parallel_word;
            bit_idx = Nbits - 1;       // MSB first
            frame_q = 1;
        end else begin
            frame_q = 0;
            if (bit_idx > 0)
                bit_idx = bit_idx - 1;
        end
        sout_q = (word_q >> bit_idx) & 1;
    end

    V(sout_o)  <+ transition(sout_q ? vh : vl, tdel, trise, tfall);
    V(frame_o) <+ transition(frame_q ? vh : vl, tdel, trise, tfall);
end
```

## Parameterized Pulse Train

When a task checks parameter overrides, declare the public parameter names
exactly and let the instance line override them. The output behavior should
depend on those parameters, not on hard-coded constants.

```
parameter real    vhi  = 0.5;
parameter integer reps = 2;

integer emitted;
integer out_state;
real t_next;

analog begin
    @(initial_step) begin
        emitted = 0;
        out_state = 0;
        t_next = 1n;
    end

    @(timer(t_next)) begin
        if (emitted < 2 * reps) begin
            out_state = 1 - out_state;
            emitted = emitted + 1;
            t_next = t_next + 2n;
        end
    end

    V(out) <+ transition(out_state ? vhi : 0.0, 0, trise, tfall);
end
```

## Design Notes

- Digital logic in Verilog-A is behavioral — no gate-level synthesis
- Use `case` statements for FSMs with >3 states — cleaner than nested if-else
- Bit extraction: `(count >> i) & 1` extracts bit `i` from an integer
- Shift registers shift *backwards* through the array (MSB first) to avoid overwriting
- For async reset: place the reset `@(cross())` *before* the clock event — the simulator
  processes events in order of appearance
