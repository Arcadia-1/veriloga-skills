The following voltage-domain Verilog-A DUT drives a digital-style output with an
instantaneous assignment. Fix it without changing the intended function.

```verilog
module comp_flag (VDD, VSS, VIN, FLAG);
    inout VDD, VSS;
    input VIN;
    output FLAG;
    electrical VDD, VSS, VIN, FLAG;
    parameter real vth = 0.45;
    analog begin
        if (V(VIN) > vth)
            V(FLAG) <+ V(VDD);
        else
            V(FLAG) <+ V(VSS);
    end
endmodule
```
