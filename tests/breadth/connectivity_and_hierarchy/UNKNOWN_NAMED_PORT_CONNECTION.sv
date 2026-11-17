// breadth: reports | An instance connecting a port name that does not exist on the child module is reported.
// pair: known-vs-unknown-named-port
module child(input a);
endmodule
module top;
  logic x, y;
  child u(.a(x), .bad_port(y));
endmodule

// breadth: clean | An instance connecting existing declared ports by name is not reported.
// pair: known-vs-unknown-named-port
module child(input a);
endmodule
module top;
  logic x;
  child u(.a(x));
endmodule

// breadth: reports | An instance connecting a misspelled port name is reported.
// pair: misspelled-port-name
module child(input data_in);
endmodule
module top;
  logic x;
  child u(.data_inn(x));
endmodule

// breadth: clean | An instance connecting the correctly spelled port name is not reported.
// pair: misspelled-port-name
module child(input data_in);
endmodule
module top;
  logic x;
  child u(.data_in(x));
endmodule

// breadth: reports | An instance connecting a port name that exists only on another module is reported.
// pair: sibling-module-port-name
module child1(input a);
endmodule
module child2(input b);
endmodule
module top;
  logic x;
  child1 u(.b(x));
endmodule

// breadth: clean | Two separate instances connecting valid ports to their respective child modules are not reported.
// pair: sibling-module-port-name
module child1(input a);
endmodule
module child2(input b);
endmodule
module top;
  logic x, y;
  child1 u1(.a(x));
  child2 u2(.b(y));
endmodule

// breadth: reports | An instance explicitly connecting an unknown port name alongside valid ports is reported.
// pair: wildcard-vs-invalid-named-port
module child(input a, output b);
endmodule
module top;
  logic a, b, extra;
  child u(.a(a), .b(b), .extra(extra));
endmodule

// breadth: clean | An instance using wildcard dot-star connection to bind matching ports is not reported.
// pair: wildcard-vs-invalid-named-port
module child(input a, output b);
endmodule
module top;
  logic a, b;
  child u(.*);
endmodule

// breadth: reports | An instance with empty parentheses on an unknown port name is reported.
module child(input a);
endmodule
module top;
  child u(.a(), .bad());
endmodule

// breadth: reports | An instance specifying multiple unknown port names is reported.
module child(input a);
endmodule
module top;
  logic x, y, z;
  child u(.a(x), .bad1(y), .bad2(z));
endmodule

// breadth: clean | An instance of an undefined module with named connections is not reported by the known-child named port rule.
module top;
  logic x;
  unknown_child u(.some_port(x));
endmodule

// breadth: clean | An instance using positional ordered port connections is not reported by the named port rule.
module child(input a, output b);
endmodule
module top;
  logic x, y;
  child u(x, y);
endmodule
