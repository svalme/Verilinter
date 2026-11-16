// scenario: reports | A plain signal narrower than the port is extended; that is a mismatch the author should see.
// pair: plain-versus-arithmetic
module child(input [4:0] a);
endmodule
module top;
  wire [3:0] p;
  child u1(.a(p));
endmodule

// scenario: clean | A sum narrower than the port is evaluated at the port width, so nothing is lost.
// pair: plain-versus-arithmetic
module child(input [4:0] a);
endmodule
module top;
  wire [3:0] p, q;
  child u1(.a(p + q));
endmodule

// scenario: reports | A product wider than the port loses its upper bits.
module child(input [3:0] a);
endmodule
module top;
  wire [3:0] p, q;
  child u1(.a(p * q));
endmodule

// scenario: reports | A conditional or bitwise expression narrower than the port is the same extension a plain signal gets.
// expect: 2
module child(input [4:0] a, input [4:0] b);
endmodule
module top;
  wire [3:0] p, q;
  wire s;
  child u1(.a(s ? p : q), .b(p | q));
endmodule

// scenario: clean | A parameter override written as $bits of a typedef sizes the child port.
module child #(parameter int Width = 32) (input [Width-1:0] d);
endmodule
module top;
  typedef struct packed { logic [3:0] a; logic b; } s_t;
  s_t sv;
  child #(.Width($bits(s_t))) u0(.d(sv));
endmodule

// scenario: clean | An override that cannot be evaluated leaves the port width unknown instead of using the child default.
module child #(parameter int Width = 32) (input [Width-1:0] d);
endmodule
module top;
  logic [5:0] x;
  child #(.Width($bits(missing_t))) u0(.d(x));
endmodule

// scenario: clean | Whole unpacked arrays are compared by their whole width.
module child (output logic [33:0] d [2], input logic [33:0] q [2]);
endmodule
module top;
  logic [33:0] d [2];
  logic [33:0] q [2];
  child u1 (.d(d), .q);
endmodule
