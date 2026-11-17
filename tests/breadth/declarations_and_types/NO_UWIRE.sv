// Breadth test suite for NO_UWIRE
// Category: declarations_and_types
//
// Tests detection of uwire (unresolved wire) net declarations,
// contrasting with standard wire and tri declarations.

// breadth: reports | Net declared with uwire is reported.
// pair: uwire_vs_wire
module m;
  uwire u_sig;
endmodule

// breadth: clean | Net declared with standard wire is not reported.
// pair: uwire_vs_wire
module m;
  wire u_sig;
endmodule

// breadth: clean | Word uwire inside comments is not reported.
module m;
  // uwire
  wire w;
endmodule

// breadth: reports | Vector uwire net declaration is reported.
module m;
  uwire [7:0] bus;
endmodule

// breadth: reports | Multiple uwire net declarations trigger multiple reports.
// expect: 2
module m;
  uwire a;
  uwire b;
endmodule

// breadth: clean | Standard logic and tri declarations are not reported.
module m;
  logic l;
  tri t;
endmodule
