The following Verilog-A DUT is wrong for Cadence Spectre. Fix it without changing its intended function.

```verilog
module and2_gate (VDD, VSS, A, B, Y);
    inout electrical VDD, VSS;
    input electrical A, B;
    output electrical Y;
    analog begin
        V(Y) <+ transition((V(A) > 0.5 && V(B) > 0.5) ? V(VDD) : V(VSS), 0, 10p);
    end
endmodule
```
