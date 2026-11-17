// breadth: reports | Two case items with the same numeric value are reported.
// pair: two-items-same-value-vs-disjoint
module top(input [3:0] sel, output logic y);
  always_comb begin
    case (sel)
      4'd2: y = 1'b1;
      4'b0010: y = 1'b0;
      default: y = 1'b0;
    endcase
  end
endmodule

// breadth: clean | Case items with disjoint numeric values are not reported.
// pair: two-items-same-value-vs-disjoint
module top(input [3:0] sel, output logic y);
  always_comb begin
    case (sel)
      4'd1: y = 1'b1;
      4'd2: y = 1'b0;
      default: y = 1'b0;
    endcase
  end
endmodule

// breadth: reports | Overlapping wildcard patterns in casez are reported.
// pair: casez-overlapping-wildcards-vs-disjoint
module top(input [2:0] sel, output logic y);
  always_comb begin
    casez (sel)
      3'b00?: y = 1'b1;
      3'b001: y = 1'b0;
      default: y = 1'b0;
    endcase
  end
endmodule

// breadth: clean | Mutually disjoint wildcard patterns in casez are not reported.
// pair: casez-overlapping-wildcards-vs-disjoint
module top(input [2:0] sel, output logic y);
  always_comb begin
    casez (sel)
      3'b00?: y = 1'b1;
      3'b01?: y = 1'b0;
      default: y = 1'b0;
    endcase
  end
endmodule

// breadth: reports | Two case items with the same numeric value differing only by width are reported.
// pair: same-value-different-widths-vs-distinct
module top(input [3:0] sel, output logic y);
  always_comb begin
    case (sel)
      4'd2: y = 1'b1;
      2'd2: y = 1'b0;
      default: y = 1'b0;
    endcase
  end
endmodule

// breadth: clean | Distinct case items with different declared widths are not reported.
// pair: same-value-different-widths-vs-distinct
module top(input [3:0] sel, output logic y);
  always_comb begin
    case (sel)
      4'd2: y = 1'b1;
      2'd3: y = 1'b0;
      default: y = 1'b0;
    endcase
  end
endmodule

// breadth: reports | Duplicate items in the same comma-separated case branch are reported.
// pair: duplicate-in-same-branch-vs-distinct-items
module top(input [3:0] sel, output logic y);
  always_comb begin
    case (sel)
      4'd2, 4'd2: y = 1'b1;
      default: y = 1'b0;
    endcase
  end
endmodule

// breadth: clean | Distinct items in a comma-separated case item list are not reported.
// pair: duplicate-in-same-branch-vs-distinct-items
module top(input [3:0] sel, output logic y);
  always_comb begin
    case (sel)
      4'd2, 4'd3: y = 1'b1;
      default: y = 1'b0;
    endcase
  end
endmodule

// breadth: reports | A casez statement with a wildcard item that covers an earlier specific constant is reported.
module top(input [2:0] sel, output logic y);
  always_comb begin
    casez (sel)
      3'b11?, 3'b???: y = 1'b1;
      default: y = 1'b0;
    endcase
  end
endmodule

// breadth: gap | Overlapping range items in a case inside statement are reported.
module top(input [3:0] sel, output logic y);
  always_comb begin
    case (sel) inside
      [4'd0:4'd4]: y = 1'b1;
      [4'd2:4'd6]: y = 1'b0;
      default: y = 1'b0;
    endcase
  end
endmodule

// breadth: clean | A case statement with a default branch and distinct items is not reported.
module top(input [3:0] sel, output logic y);
  always_comb begin
    case (sel)
      4'd1: y = 1'b1;
      default: y = 1'b0;
    endcase
  end
endmodule

// breadth: clean | A casez statement with non-overlapping bit patterns is not reported.
module top(input [3:0] sel, output logic y);
  always_comb begin
    casez (sel)
      4'b10??: y = 1'b1;
      4'b01??: y = 1'b0;
      default: y = 1'b0;
    endcase
  end
endmodule
