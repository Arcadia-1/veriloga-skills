# Modules, Ports, And Disciplines

## Module Shape

Use this structure for a complete Verilog-A source file:

```verilog
`include "constants.vams"
`include "disciplines.vams"

module module_name (
    input  electrical in,
    output electrical out,
    inout  electrical ref
);
    parameter real gain = 1.0;

    analog begin
        V(out, ref) <+ gain * V(in, ref);
    end
endmodule
```

## Port Declarations

ANSI-style declarations keep direction and discipline beside each port:

```verilog
module m (
    input  electrical a,
    input  electrical b,
    output electrical y
);
```

Old-style declarations are also valid when the declarations are complete:

```verilog
module m(a, b, y);
    input a, b;
    output y;
    electrical a, b, y;
```

For buses, declare a range on the discipline:

```verilog
input  electrical [3:0] din;
output electrical [3:0] dout;
```

## Disciplines, Natures, And Branches

`electrical` is the usual discipline for voltage/current branch quantities. Custom natures and
disciplines belong near the top of the file when they are needed:

```verilog
nature temperature;
    units = "K";
    access = Temp;
    abstol = 1u;
endnature

discipline thermal;
    potential temperature;
enddiscipline
```

Declare named branches when repeated branch access clarifies intent:

```verilog
branch (p, n) path;

analog begin
    V(path) <+ value;
    I(path) <+ current_value;
end
```

## Parameters

Use typed parameters and constrain ranges where the language form supports it:

```verilog
parameter real vh = 1.0;
parameter real tr = 1n from [0:inf);
parameter integer width = 4 from [1:64];
```
