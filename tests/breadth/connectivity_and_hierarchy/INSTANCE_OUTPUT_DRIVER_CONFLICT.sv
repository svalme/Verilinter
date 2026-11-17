// breadth: reports | An instance output connecting to a net also written by a continuous assign is reported.
// pair: instance-output-and-continuous-assign
module sub(output logic out);
endmodule
module top;
  logic x, a;
  assign x = a;
  sub u_sub(.out(x));
endmodule

// breadth: clean | An instance output connecting to a net that is not written elsewhere in the module is not reported.
// pair: instance-output-and-continuous-assign
module sub(output logic out);
endmodule
module top;
  logic x;
  sub u_sub(.out(x));
endmodule

// breadth: reports | An instance output connecting to a net driven by a continuous assign is reported.
// pair: instance-port-direction-conflict
module sub_out(output logic out);
endmodule
module top;
  logic a;
  assign a = 1'b1;
  sub_out u_sub(.out(a));
endmodule

// breadth: clean | An instance input connecting to a net driven by a continuous assign is not reported.
// pair: instance-port-direction-conflict
module sub_in(input logic in);
endmodule
module top;
  logic a;
  assign a = 1'b1;
  sub_in u_sub(.in(a));
endmodule

// breadth: reports | An instance output and a continuous assign driving the same bit slice of a vector are reported.
// pair: instance-output-disjoint-bits
module sub(output logic out);
endmodule
module top;
  logic [1:0] x;
  assign x[0] = 1'b0;
  sub u_sub(.out(x[0]));
endmodule

// breadth: clean | An instance output and a continuous assign driving provably disjoint bit slices of a vector are not reported.
// pair: instance-output-disjoint-bits
module sub(output logic out);
endmodule
module top;
  logic [1:0] x;
  assign x[0] = 1'b0;
  sub u_sub(.out(x[1]));
endmodule

// breadth: reports | An instance output connecting to a net also written by a clocked procedural block is reported.
// pair: instance-output-procedural-write
module sub(output logic out);
endmodule
module top(input logic clk);
  logic x;
  always_ff @(posedge clk) x <= 1'b1;
  sub u_sub(.out(x));
endmodule

// breadth: clean | An instance output connecting to a net that is read by a clocked procedural block is not reported.
// pair: instance-output-procedural-write
module sub(output logic out);
endmodule
module top(input logic clk, output logic q);
  logic x;
  always_ff @(posedge clk) q <= x;
  sub u_sub(.out(x));
endmodule

// breadth: reports | An instance output and a continuous assign driving the same member of a packed struct are reported.
// pair: instance-output-struct-members
typedef struct packed { logic a; logic b; } pair_t;
module sub(output logic out);
endmodule
module top;
  pair_t p;
  assign p.a = 1'b0;
  sub u_sub(.out(p.a));
endmodule

// breadth: clean | An instance output and a continuous assign driving different members of a packed struct are not reported.
// pair: instance-output-struct-members
typedef struct packed { logic a; logic b; } pair_t;
module sub(output logic out);
endmodule
module top;
  pair_t p;
  assign p.a = 1'b0;
  sub u_sub(.out(p.b));
endmodule

// breadth: reports | An instance inout port connected to a net driven by a continuous assign is reported.
module sub(inout wire io);
endmodule
module top;
  wire x;
  assign x = 1'b0;
  sub u_sub(.io(x));
endmodule

// breadth: clean | An instance output in a generate-if branch and a continuous assign in the mutually exclusive else branch are not reported.
module sub(output logic out);
endmodule
module top #(parameter EN = 1);
  logic x;
  generate
    if (EN) begin
      sub u_sub(.out(x));
    end else begin
      assign x = 1'b0;
    end
  endgenerate
endmodule

// breadth: clean | An instance output connecting to a net that is only read by another instance input port is not reported.
module producer(output logic out);
endmodule
module consumer(input logic in);
endmodule
module top;
  logic x;
  producer u_prod(.out(x));
  consumer u_cons(.in(x));
endmodule
