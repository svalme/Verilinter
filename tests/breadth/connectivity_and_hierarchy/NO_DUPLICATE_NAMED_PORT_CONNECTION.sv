// breadth: reports | An instance connecting the same port name twice is reported.
// pair: duplicate-named-port-in-instance
module child(input a, output b);
endmodule
module top;
  logic x, y, z;
  child u(.a(x), .a(y), .b(z));
endmodule

// breadth: clean | An instance connecting distinct named ports without duplicates is not reported.
// pair: duplicate-named-port-in-instance
module child(input a, output b);
endmodule
module top;
  logic x, y;
  child u(.a(x), .b(y));
endmodule

// breadth: reports | An instance specifying duplicate connections for a named port is reported.
// pair: same-instance-vs-different-instances
module child(input a);
endmodule
module top;
  logic x, y;
  child u(.a(x), .a(y));
endmodule

// breadth: clean | Two distinct instances each connecting the same declared port name are not reported.
// pair: same-instance-vs-different-instances
module child(input a);
endmodule
module top;
  logic x, y;
  child u1(.a(x));
  child u2(.a(y));
endmodule

// breadth: reports | An instance specifying duplicate connections with exact matching casing is reported.
// pair: case-sensitive-port-names
module child(input a);
endmodule
module top;
  logic x, y;
  child u(.a(x), .a(y));
endmodule

// breadth: clean | An instance connecting distinct ports whose names differ only in case is not reported.
// pair: case-sensitive-port-names
module child(input a, input A);
endmodule
module top;
  logic x, y;
  child u(.a(x), .A(y));
endmodule

// breadth: reports | An instance specifying duplicate connections for a named port using empty parentheses is reported.
// pair: empty-parentheses-duplicate
module child(input a);
endmodule
module top;
  child u(.a(), .a());
endmodule

// breadth: clean | An instance connecting distinct named ports using empty parentheses is not reported.
// pair: empty-parentheses-duplicate
module child(input a, output b);
endmodule
module top;
  child u(.a(), .b());
endmodule

// breadth: reports | An instance duplicating multiple different named ports is reported.
module child(input a, output b);
endmodule
module top;
  logic x;
  child u(.a(x), .a(x), .b(x), .b(x));
endmodule

// breadth: clean | An instance using positional ordered port connections is not reported by the duplicate named port rule.
module child(input a, output b);
endmodule
module top;
  logic x, y;
  child u(x, y);
endmodule

// breadth: clean | An instance using wildcard dot-star connection is not reported by the duplicate named port rule.
module child(input a, output b);
endmodule
module top;
  logic a, b;
  child u(.*);
endmodule
