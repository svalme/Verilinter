// breadth: reports | An equality comparison comparing a signal with itself is reported.
// pair: equality-self-vs-distinct-operands
module top(input [3:0] a, output logic y);
  assign y = (a == a);
endmodule

// breadth: clean | An equality comparison between two distinct signals is not reported.
// pair: equality-self-vs-distinct-operands
module top(input [3:0] a, input [3:0] b, output logic y);
  assign y = (a == b);
endmodule

// breadth: reports | A relational less-than comparison comparing a signal with itself is reported.
// pair: relational-less-than-self-vs-distinct
module top(input [3:0] a, output logic y);
  assign y = (a < a);
endmodule

// breadth: clean | A relational less-than comparison between distinct signals is not reported.
// pair: relational-less-than-self-vs-distinct
module top(input [3:0] a, input [3:0] b, output logic y);
  assign y = (a < b);
endmodule

// breadth: reports | An inequality comparison comparing a signal with itself is reported.
// pair: inequality-self-vs-distinct
module top(input [3:0] a, output logic y);
  assign y = (a != a);
endmodule

// breadth: clean | An inequality comparison between distinct signals is not reported.
// pair: inequality-self-vs-distinct
module top(input [3:0] a, input [3:0] b, output logic y);
  assign y = (a != b);
endmodule

// breadth: reports | A comparison between a parenthesized signal and itself is reported.
// pair: parenthesized-self-vs-distinct
module top(input [3:0] a, output logic y);
  assign y = ((a) == a);
endmodule

// breadth: clean | A parenthesized signal compared with a distinct signal is not reported.
// pair: parenthesized-self-vs-distinct
module top(input [3:0] a, input [3:0] b, output logic y);
  assign y = ((a) == b);
endmodule

// breadth: reports | A case-equality comparison comparing a signal with itself is reported.
module top(input [3:0] a, output logic y);
  assign y = (a === a);
endmodule

// breadth: reports | A real variable compared with itself is reported.
module top(output logic y);
  real r;
  assign y = (r == r);
endmodule

// breadth: clean | Two distinct parameters holding the same constant value compared together are not reported.
module top(output logic y);
  localparam int A = 5;
  localparam int B = 5;
  assign y = (A == B);
endmodule

// breadth: clean | An equality comparison between two function invocations is not reported by the signal self-comparison rule.
module top(input [3:0] a, output logic y);
  function automatic int f(int x);
    return x;
  endfunction
  assign y = (f(a) == f(a));
endmodule
