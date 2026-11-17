// Breadth test suite for NO_TRAN_RTRAN
// Category: combinational_logic
//
// Tests detection of unconditional bidirectional switches (tran, rtran),
// contrasting with unidirectional continuous assignments and controlled tranif switches.

// breadth: reports | Unconditional bidirectional tran switch instantiation is reported.
// pair: tran_vs_continuous_assign
module m(inout a, b);
  tran t1(a, b);
endmodule

// breadth: clean | Unidirectional continuous assignment is not reported.
// pair: tran_vs_continuous_assign
module m(input a, output b);
  assign b = a;
endmodule

// breadth: clean | Words tran and rtran inside comments are not reported.
module m;
  // tran rtran
  wire w = 1'b0;
endmodule

// breadth: reports | Resistive bidirectional rtran switch instantiation is reported.
module m(inout a, b);
  rtran rt1(a, b);
endmodule

// breadth: reports | Multiple tran switch instantiations trigger multiple reports.
// expect: 2
module m(inout a, b, c);
  tran t1(a, b);
  tran t2(b, c);
endmodule

// breadth: clean | Controlled tranif1 primitive is clean for NO_TRAN_RTRAN.
module m(inout a, b, input en);
  tranif1 t1(a, b, en);
endmodule
