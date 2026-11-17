// breadth: reports | Two distinct instances connecting output ports to the same scalar net are reported.
// pair: two-instances-same-net
module sub(output logic out);
endmodule
module top;
  logic x;
  sub u1(.out(x));
  sub u2(.out(x));
endmodule

// breadth: clean | One instance driving a net and a second instance receiving that net on an input port are not reported.
// pair: two-instances-same-net
module producer(output logic out);
endmodule
module consumer(input logic in);
endmodule
module top;
  logic x;
  producer u1(.out(x));
  consumer u2(.in(x));
endmodule

// breadth: reports | Two distinct instances connecting output ports to the same bit of a vector are reported.
// pair: two-instances-bit-selects
module sub(output logic out);
endmodule
module top;
  logic [1:0] x;
  sub u1(.out(x[0]));
  sub u2(.out(x[0]));
endmodule

// breadth: clean | Two distinct instances connecting output ports to provably disjoint bits of a vector are not reported.
// pair: two-instances-bit-selects
module sub(output logic out);
endmodule
module top;
  logic [1:0] x;
  sub u1(.out(x[0]));
  sub u2(.out(x[1]));
endmodule

// breadth: reports | Two distinct instances driving the same member of a packed struct are reported.
// pair: two-instances-struct-members
typedef struct packed { logic a; logic b; } pair_t;
module sub(output logic out);
endmodule
module top;
  pair_t p;
  sub u1(.out(p.a));
  sub u2(.out(p.a));
endmodule

// breadth: clean | Two distinct instances driving provably disjoint members of a packed struct are not reported.
// pair: two-instances-struct-members
typedef struct packed { logic a; logic b; } pair_t;
module sub(output logic out);
endmodule
module top;
  pair_t p;
  sub u1(.out(p.a));
  sub u2(.out(p.b));
endmodule

// breadth: reports | Two distinct instances in non-exclusive generate blocks driving the same net are reported.
// pair: two-instances-generate-branches
module sub(output logic out);
endmodule
module top;
  logic x;
  generate
    if (1) begin : g1
      sub u1(.out(x));
    end
    if (1) begin : g2
      sub u2(.out(x));
    end
  endgenerate
endmodule

// breadth: clean | Two distinct instances in mutually exclusive generate if-else branches driving the same net are not reported.
// pair: two-instances-generate-branches
module sub(output logic out);
endmodule
module top #(parameter EN = 1);
  logic x;
  generate
    if (EN) begin
      sub u1(.out(x));
    end else begin
      sub u2(.out(x));
    end
  endgenerate
endmodule

// breadth: reports | Two distinct instances driving the same element of an unpacked array are reported.
// pair: two-instances-array-elements
module sub(output logic out);
endmodule
module top;
  logic [1:0] mem [1:0];
  sub u1(.out(mem[0][0]));
  sub u2(.out(mem[0][0]));
endmodule

// breadth: clean | Two distinct instances driving provably disjoint elements of an unpacked array are not reported.
// pair: two-instances-array-elements
module sub(output logic out);
endmodule
module top;
  logic [1:0] mem [1:0];
  sub u1(.out(mem[0][0]));
  sub u2(.out(mem[1][0]));
endmodule

// breadth: reports | Two distinct instances connecting inout ports to the same tri-state wire are reported.
module tri_driver(inout wire bus);
endmodule
module top;
  wire bus;
  tri_driver u1(.bus(bus));
  tri_driver u2(.bus(bus));
endmodule

// breadth: clean | An instance array binding an output port across slice elements is not reported as distinct instance conflict.
module sub(output logic out);
endmodule
module top;
  logic [1:0] x;
  sub u[1:0](.out(x));
endmodule

// breadth: clean | Two distinct instances each driving completely independent signals are not reported.
module sub(output logic out);
endmodule
module top;
  logic a, b;
  sub u1(.out(a));
  sub u2(.out(b));
endmodule
