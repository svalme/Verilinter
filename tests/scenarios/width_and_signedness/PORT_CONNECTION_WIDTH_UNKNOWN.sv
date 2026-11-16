// scenario: reports | A connected name that is not declared has no width, so the analysis cannot compare it with the port.
module child(input [7:0] a);
endmodule
module top;
  child u1(.a(missing_name));
endmodule

// scenario: reports | A port typed by a type parameter has a width that depends on the instantiating module.
module child #(parameter type data_t = logic) (input data_t [3:0] d);
endmodule
module top;
  logic [15:0] x;
  child #(.data_t(logic [3:0])) u1(.d(x));
endmodule

// scenario: reports | A port sized by a parameter with no default and no override has no knowable width.
// pair: parameter-without-value
module child #(parameter int Width) (input [Width-1:0] d);
endmodule
module top;
  logic [5:0] x;
  child u1(.d(x));
endmodule

// scenario: clean | The same port with a parameter that has a value is sized.
// pair: parameter-without-value
module child #(parameter int Width = 6) (input [Width-1:0] d);
endmodule
module top;
  logic [5:0] x;
  child u1(.d(x));
endmodule

// scenario: clean | An unbased unsized literal fills the port, so there is no width to size.
module child(input [7:0] a);
endmodule
module top;
  child u1(.a('0));
endmodule

// scenario: clean | An unsized decimal literal fits the port.
module child(input b, input [4:0] c);
endmodule
module top;
  child u1(.b(0), .c(1));
endmodule

// scenario: clean | A named empty connection is left open on purpose; the unconnected-port rule covers it.
module child(input [3:0] a, output [3:0] y);
endmodule
module top;
  logic [3:0] p;
  child u1(.a(p), .y());
endmodule

// scenario: clean | A variable declared with a typedef has the typedef width.
module child(input [4:0] d, input [3:0] h);
endmodule
module top;
  typedef struct packed { logic [3:0] a; logic b; } s_t;
  s_t sv;
  child u0(.d(sv), .h(sv.a));
endmodule

// scenario: clean | A logical or bitwise expression of one-bit operands is one bit.
module child(input a, input b);
endmodule
module top;
  logic v, iso;
  child u1(.a(v & !iso), .b(v && !iso));
endmodule

// scenario: clean | A port sized by a package parameter keeps its width when an unrelated override is unknown.
package p_pkg;
  localparam int unsigned IdxW = 3;
endpackage
module child import p_pkg::*; #(parameter int Width = 32, parameter int Other = 1) (input [Width-1:0] d, input [IdxW-1:0] idx);
endmodule
module top;
  logic [5:0] x;
  logic [2:0] i;
  child #(.Width(6), .Other($bits(missing_t))) u0(.d(x), .idx(i));
endmodule
