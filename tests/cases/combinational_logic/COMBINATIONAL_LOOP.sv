// case: reports | Two continuous assignments that feed each other.
module top(input logic a, b, output logic x, y);
  assign x = y | a;
  assign y = x | b;
endmodule

// case: reports | A swap attempt inside one block: the final value of q depends on the value q had before the block.
// pair: swap-versus-reuse
module top(input logic a, output logic p, q);
  always_comb begin
    p = q;
    q = p;
  end
endmodule

// case: clean | A variable overwritten after it was used: the later read sees the new value, so the chain never returns to the old one.
// pair: swap-versus-reuse
module top(input logic a, b, output logic [7:0] o);
  logic [7:0] r, rev;
  always_comb begin
    r = {8{a}};
    for (int unsigned i = 0; i < 8; i++) rev[i] = r[7-i];
    r = b ? rev : r;
    o = r;
  end
endmodule

// case: clean | Edges in different branches of one generate construct are never active together.
// pair: exclusive-versus-same-branch
module top #(parameter bit BUF = 1) (input logic a, b, output logic x, y);
  if (BUF) begin : g_buf
    assign x = y | a;
  end else begin : g_no
    assign y = x | b;
  end
endmodule

// case: reports | The same two assignments in one generate branch do form a loop.
// pair: exclusive-versus-same-branch
module top #(parameter bit BUF = 1) (input logic a, b, output logic x, y);
  if (BUF) begin : g_buf
    assign x = y | a;
    assign y = x | b;
  end
endmodule

// case: clean | An accumulator written and read inside one for loop is an unrolled chain, not feedback.
module top(input logic [3:0] a, output logic [3:0] o);
  logic [3:0] next_rd, next_rdt;
  always_comb begin
    next_rd = 4'd0;
    for (int i = 0; i < 4; i++) begin
      next_rdt = next_rd ^ a;
      next_rd = next_rdt;
    end
    o = next_rd;
  end
endmodule
