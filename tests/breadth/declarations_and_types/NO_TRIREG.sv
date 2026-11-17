// Breadth test suite for NO_TRIREG
// Category: declarations_and_types
//
// Tests detection of trireg net declarations,
// contrasting with standard tri and wire nets.

// breadth: reports | Net declared with trireg is reported.
// pair: trireg_vs_tri
module m;
  trireg tr_net;
endmodule

// breadth: clean | Tri-state net declared with tri is not reported.
// pair: trireg_vs_tri
module m;
  tri tr_net;
endmodule

// breadth: clean | Word trireg inside comments is not reported.
module m;
  // trireg
  wire bus;
endmodule

// breadth: reports | Vector trireg net declaration is reported.
module m;
  trireg [7:0] data_bus;
endmodule

// breadth: reports | Multiple trireg net declarations trigger multiple reports.
// expect: 2
module m;
  trireg tr1;
  trireg tr2;
endmodule

// breadth: clean | Regular reg and logic storage declarations are not reported.
module m;
  reg r;
  logic l;
endmodule
