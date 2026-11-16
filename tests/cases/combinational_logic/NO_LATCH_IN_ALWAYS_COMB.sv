// case: reports | An output assigned only when a condition holds keeps its old value otherwise.
// pair: output-versus-scratch
module top(input logic a, output logic y);
  always_comb begin
    if (a) y = 1'b1;
  end
endmodule

// case: clean | A scratch variable that only this block uses, written before each read, holds nothing between evaluations.
// pair: output-versus-scratch
module top #(parameter KEEP = 1) (input logic a, input logic [3:0] k, output logic [3:0] o);
  integer i, bit_cnt;
  always @* begin
    o = 0;
    if (a) begin
      if (KEEP) begin
        bit_cnt = 0;
        for (i = 0; i < 4; i = i + 1) if (k[i]) bit_cnt = i;
        o = o + bit_cnt;
      end
    end
  end
endmodule

// case: reports | A scratch variable that another statement reads outside the block is observed there.
module top(input logic a, input logic [3:0] k, output logic [3:0] o);
  reg [3:0] seen;
  always_comb begin
    if (a) seen = k;
  end
  assign o = seen;
endmodule

// case: reports | A variable read before it is written in the block carries the previous value.
module top(input logic a, output logic [3:0] o);
  reg [3:0] t;
  always_comb begin
    o = t;
    if (a) t = 4'd1;
  end
endmodule

// case: clean | A default assignment before the condition covers every path.
module top(input logic a, input logic b, output logic y);
  always_comb begin
    y = 1'b0;
    if (a) y = b;
  end
endmodule

// case: reports | A case without a default leaves the output unassigned for other values.
module top(input logic [1:0] s, output logic y);
  always_comb begin
    case (s)
      2'd0: y = 1'b0;
      2'd1: y = 1'b1;
    endcase
  end
endmodule
