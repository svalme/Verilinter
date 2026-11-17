// Breadth test suite for NO_SUPPLY0_SUPPLY1
// Category: declarations_and_types
//
// Tests detection of supply0 and supply1 net declarations,
// contrasting with explicit constant drivers and standard wire nets.

// breadth: reports | Net declared with supply0 is reported.
// pair: supply_vs_constant_driver
module m;
  supply0 gnd_net;
endmodule

// breadth: clean | Wire net driven to constant zero is not reported.
// pair: supply_vs_constant_driver
module m;
  wire gnd_net = 1'b0;
endmodule

// breadth: clean | Words supply0 and supply1 inside comments are not reported.
module m;
  // supply0 and supply1
  wire vdd_net = 1'b1;
endmodule

// breadth: reports | Net declared with supply1 is reported.
module m;
  supply1 vdd_net;
endmodule

// breadth: reports | Both supply0 and supply1 nets declared in the same module trigger multiple reports.
// expect: 2
module m;
  supply0 vss;
  supply1 vcc;
endmodule

// breadth: clean | Standard wire and tri net declarations are not reported.
module m;
  wire a;
  tri b;
endmodule
