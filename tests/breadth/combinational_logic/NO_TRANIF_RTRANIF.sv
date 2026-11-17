// Breadth test suite for NO_TRANIF_RTRANIF
// Category: combinational_logic
//
// Tests detection of controlled bidirectional switch primitives (tranif0, tranif1, rtranif0, rtranif1),
// contrasting with explicit directional tri-state bus drivers and unconditional tran switches.

// breadth: reports | Bidirectional pass-switch tranif1 instantiation is reported.
// pair: tranif_vs_tristate_driver
module m(inout a, b, input ctrl);
  tranif1 t1(a, b, ctrl);
endmodule

// breadth: clean | Explicit directional tri-state bus driver is not reported.
// pair: tranif_vs_tristate_driver
module m(inout a, input b, ctrl);
  assign a = ctrl ? b : 1'bz;
endmodule

// breadth: clean | Words tranif and rtranif inside comments are not reported.
module m;
  // tranif0 tranif1
  wire w = 1'b0;
endmodule

// breadth: reports | Bidirectional pass-switch tranif0 inside generate block is reported.
module m(inout a, b, input ctrl);
  generate
    if (1) begin : gen_sw
      tranif0 t0(a, b, ctrl);
    end
  endgenerate
endmodule

// breadth: reports | Both rtranif0 and rtranif1 instantiations trigger multiple reports.
// expect: 2
module m(inout a, b, c, input c1, c2);
  rtranif0 rt0(a, b, c1);
  rtranif1 rt1(b, c, c2);
endmodule

// breadth: clean | Unconditional bidirectional tran primitive is clean for NO_TRANIF_RTRANIF.
module m(inout a, b);
  tran t1(a, b);
endmodule
