// breadth: reports | An instance providing more positional connections than the child module has ports is reported.
// pair: ordered-connection-count
module child(input a, output b);
endmodule
module top;
  logic x, y, z;
  child u(x, y, z);
endmodule

// breadth: clean | An instance providing exactly as many positional connections as the child module has ports is not reported.
// pair: ordered-connection-count
module child(input a, output b);
endmodule
module top;
  logic x, y;
  child u(x, y);
endmodule

// breadth: reports | An instance providing three positional connections to a two-port module is reported.
// pair: extra-vs-fewer-ordered
module child(input a, output b);
endmodule
module top;
  logic x, y, z;
  child u(x, y, z);
endmodule

// breadth: clean | An instance providing fewer positional connections than the child module has ports is not reported by the extra connection rule.
// pair: extra-vs-fewer-ordered
module child(input a, output b);
endmodule
module top;
  logic x;
  child u(x);
endmodule

// breadth: reports | An instance with a trailing empty positional connection slot beyond declared ports is reported.
// pair: trailing-empty-slot
module child(input a, output b);
endmodule
module top;
  logic x, y;
  child u(x, y, );
endmodule

// breadth: clean | An instance with an empty positional connection slot within the declared port range is not reported by the extra connection rule.
// pair: trailing-empty-slot
module child(input a, input b, output c);
endmodule
module top;
  logic x, z;
  child u(x, , z);
endmodule

// breadth: reports | An instance providing a positional connection to a module with no declared ports is reported.
// pair: zero-port-child
module child;
endmodule
module top;
  logic x;
  child u(x);
endmodule

// breadth: clean | An instance connecting no ports to a module with no declared ports is not reported.
// pair: zero-port-child
module child;
endmodule
module top;
  child u();
endmodule

// breadth: reports | An instance providing multiple extra positional connections beyond declared ports is reported.
module child(input a);
endmodule
module top;
  logic x, y, z;
  child u(x, y, z);
endmodule

// breadth: clean | An instance using named port connections is not reported by the positional ordered port rule.
module child(input a, output b);
endmodule
module top;
  logic x, y;
  child u(.a(x), .b(y));
endmodule

// breadth: clean | An instance of an undefined module is not reported by the extra ordered connection rule.
module top;
  logic x, y, z;
  unknown_child u(x, y, z);
endmodule
