// breadth: reports | A plain signal narrower than the port is extended; that is a mismatch the author should see.
// pair: plain-versus-arithmetic
module child(input [4:0] a);
endmodule
module top;
  wire [3:0] p;
  child u1(.a(p));
endmodule

// breadth: clean | A sum narrower than the port is evaluated at the port width, so nothing is lost.
// pair: plain-versus-arithmetic
module child(input [4:0] a);
endmodule
module top;
  wire [3:0] p, q;
  child u1(.a(p + q));
endmodule

// breadth: reports | A product wider than the port loses its upper bits.
module child(input [3:0] a);
endmodule
module top;
  wire [3:0] p, q;
  child u1(.a(p * q));
endmodule

// breadth: reports | A conditional or bitwise expression narrower than the port is the same extension a plain signal gets.
// expect: 2
module child(input [4:0] a, input [4:0] b);
endmodule
module top;
  wire [3:0] p, q;
  wire s;
  child u1(.a(s ? p : q), .b(p | q));
endmodule

// breadth: clean | A parameter override written as $bits of a typedef sizes the child port.
module child #(parameter int Width = 32) (input [Width-1:0] d);
endmodule
module top;
  typedef struct packed { logic [3:0] a; logic b; } s_t;
  s_t sv;
  child #(.Width($bits(s_t))) u0(.d(sv));
endmodule

// breadth: clean | An override that cannot be evaluated leaves the port width unknown instead of using the child default.
module child #(parameter int Width = 32) (input [Width-1:0] d);
endmodule
module top;
  logic [5:0] x;
  child #(.Width($bits(missing_t))) u0(.d(x));
endmodule

// breadth: clean | Whole unpacked arrays are compared by their whole width.
module child (output logic [33:0] d [2], input logic [33:0] q [2]);
endmodule
module top;
  logic [33:0] d [2];
  logic [33:0] q [2];
  child u1 (.d(d), .q);
endmodule

// breadth: reports | A port sized by a package function is compared with the connected signal at the width slang computes.
// pair: package-function-width
package p_pkg;
  function automatic int wide();
    return 8;
  endfunction
endpackage
module child(input logic [p_pkg::wide()-1:0] a);
endmodule
module top;
  logic [3:0] x;
  child u1(.a(x));
endmodule

// breadth: clean | The same port with a connected signal of the computed width.
// pair: package-function-width
package p_pkg;
  function automatic int wide();
    return 8;
  endfunction
endpackage
module child(input logic [p_pkg::wide()-1:0] a);
endmodule
module top;
  logic [7:0] x;
  child u1(.a(x));
endmodule

// breadth: reports | A name that is not declared is a one-bit implicit net, narrower than the port.
// pair: undeclared-name
module child(input [7:0] a);
endmodule
module top;
  child u1(.a(missing_name));
endmodule

// breadth: clean | With implicit nets turned off the name has no width, which the unknown-width rule reports.
// pair: undeclared-name
`default_nettype none
module child(input [7:0] a);
endmodule
module top;
  child u1(.a(missing_name));
endmodule
