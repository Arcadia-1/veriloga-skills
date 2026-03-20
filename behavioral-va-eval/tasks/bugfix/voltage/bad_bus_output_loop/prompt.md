The following voltage-domain DUT intends to drive a 4-bit bus, but the output
assignment is incorrect. Fix it without changing the module intent.

```verilog
module bin4_out (VDD, VSS, CODE, DOUT);
    inout VDD, VSS;
    input [3:0] CODE;
    output [3:0] DOUT;
    electrical VDD, VSS;
    electrical [3:0] CODE, DOUT;
    integer i;
    analog begin
        for (i = 0; i < 4; i = i + 1)
            V(DOUT) <+ ((V(CODE[i]) > 0.45) ? V(VDD) : V(VSS));
    end
endmodule
```
