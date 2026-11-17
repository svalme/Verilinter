// Breadth test suite for NO_WAND_WOR
// Category: declarations_and_types
//
// Tests detection of wand (wired AND) and wor (wired OR) net declarations,
// contrasting with explicit logic gates and standard wire nets.

// breadth: reports | Net declared with wand is reported.
// pair: wired_net_vs_explicit_gate
module m;
  wand wand_net;
endmodule

// breadth: clean | Wire net driven by explicit AND logic is not reported.
// pair: wired_net_vs_explicit_gate
module m(input a, input b, output wire y);
  assign y = a & b;
endmodule

// breadth: clean | Words wand and wor inside comments are not reported.
module m;
  // wand and wor
  wire w;
endmodule

// breadth: reports | Net declared with wor is reported.
module m;
  wor wor_net;
endmodule

// breadth: reports | Both wand and wor declared in the same module trigger multiple reports.
// expect: 2
module m;
  wand a;
  wor b;
endmodule

// breadth: clean | Standard wire and tri declarations are not reported.
module m;
  wire w;
  tri t;
endmodule
