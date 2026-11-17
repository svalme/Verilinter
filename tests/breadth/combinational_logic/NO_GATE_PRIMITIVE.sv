// Breadth test suite for NO_GATE_PRIMITIVE
// Category: combinational_logic
//
// Tests detection of built-in gate-level primitive instantiations (and, or, xor, nand, nor, xnor, not, buf),
// contrasting with continuous assignments, user submodule instantiations, and comments.

// breadth: reports | Built-in and gate primitive instantiation is reported.
// pair: gate_vs_assign
module m(input a, b, output y);
  and g1(y, a, b);
endmodule

// breadth: clean | Continuous assign statement with bitwise operator is not reported.
// pair: gate_vs_assign
module m(input a, b, output y);
  assign y = a & b;
endmodule

// breadth: clean | Gate primitive names inside comments are not reported.
module m;
  // and or xor
  wire sig = 1'b0;
endmodule

// breadth: reports | Built-in nor gate primitive inside a generate block is reported.
module m(input a, b, output y);
  generate
    if (1) begin : gen_gate
      nor g_nor(y, a, b);
    end
  endgenerate
endmodule

// breadth: reports | Multiple gate primitive instantiations trigger multiple reports.
// expect: 2
module m(input a, b, c, output y1, y2);
  or  g_or(y1, a, b);
  xor g_xor(y2, b, c);
endmodule

// breadth: clean | User-defined submodule instantiation is not reported.
module sub_gate(input a, output y);
  assign y = ~a;
endmodule

module m(input in_sig, output out_sig);
  sub_gate u_sub(.a(in_sig), .y(out_sig));
endmodule
