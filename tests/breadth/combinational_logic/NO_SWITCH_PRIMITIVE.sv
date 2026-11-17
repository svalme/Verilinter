// Breadth test suite for NO_SWITCH_PRIMITIVE
// Category: combinational_logic
//
// Tests detection of switch-level primitives (nmos, pmos, cmos, rnmos, rpmos, rcmos),
// contrasting with tri-state continuous assignments and gate-level primitives.

// breadth: reports | Built-in nmos switch primitive instantiation is reported.
// pair: switch_vs_assign
module m(inout d, s, input g);
  nmos n1(d, s, g);
endmodule

// breadth: clean | Tri-state continuous assignment modeling switch is not reported.
// pair: switch_vs_assign
module m(inout d, input s, g);
  assign d = g ? s : 1'bz;
endmodule

// breadth: clean | Switch primitive names inside comments are not reported.
module m;
  // nmos pmos
  wire w = 1'b0;
endmodule

// breadth: reports | Built-in pmos switch primitive inside generate block is reported.
module m(inout d, s, input g);
  generate
    if (1) begin : gen_sw
      pmos p1(d, s, g);
    end
  endgenerate
endmodule

// breadth: reports | Multiple switch primitive instantiations trigger multiple reports.
// expect: 2
module m(inout d, s, input g, g_bar);
  cmos  c1(d, s, g, g_bar);
  rnmos r1(d, s, g);
endmodule

// breadth: clean | Standard gate primitive is not reported by NO_SWITCH_PRIMITIVE.
module m(input a, b, output y);
  and g1(y, a, b);
endmodule
