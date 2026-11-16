// breadth: reports | A target assigned to itself.
// pair: same-element-versus-neighbour
module top(input logic clk, output logic [7:0] q);
  always_ff @(posedge clk) q <= q;
endmodule

// breadth: reports | An array element assigned to itself.
module top(input logic clk);
  logic [7:0] a [4];
  always_ff @(posedge clk) a[2] <= a[2];
endmodule

// breadth: clean | An array element assigned from its neighbour is a shift, not a self-assignment.
// pair: same-element-versus-neighbour
module top(input logic clk);
  logic [7:0] a [4];
  always_ff @(posedge clk) begin
    a[0] <= a[1];
    a[1] <= a[2];
  end
endmodule

// breadth: clean | A bit-slice assigned from another slice of the same vector.
module top(input logic clk);
  logic [3:0] v;
  always_ff @(posedge clk) begin
    v[0] <= v[1];
    v[1:0] <= v[3:2];
  end
endmodule

// breadth: reports | A single bit assigned to itself.
module top(input logic clk);
  logic [3:0] v;
  always_ff @(posedge clk) v[3] <= v[3];
endmodule
