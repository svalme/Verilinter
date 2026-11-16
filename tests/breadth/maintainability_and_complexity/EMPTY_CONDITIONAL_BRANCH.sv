// breadth: reports | An if branch with an empty begin-end block.
// pair: empty-versus-macro
module top(input logic a, output logic y);
  always_comb begin
    y = 1'b0;
    if (a) begin
    end
  end
endmodule

// breadth: clean | A branch whose only content is a macro that expands to nothing is source code, not an empty branch.
// pair: empty-versus-macro
`define dbg(x)
module top(input logic a, output logic y);
  always_comb begin
    y = 1'b0;
    if (a) begin
      `dbg($display("hi");)
    end
  end
endmodule

// breadth: reports | A case item with an empty begin-end block.
module top(input logic b, output logic y);
  always_comb begin
    y = 1'b0;
    case (b)
      1'b1: begin
      end
      default: y = 1'b1;
    endcase
  end
endmodule

// breadth: reports | An else branch that is a bare semicolon.
module top(input logic a, output logic y);
  always_comb begin
    if (a) y = 1'b1;
    else ;
  end
endmodule

// breadth: clean | Branches that contain statements.
module top(input logic a, output logic y);
  always_comb begin
    if (a) begin
      y = 1'b1;
    end else begin
      y = 1'b0;
    end
  end
endmodule
