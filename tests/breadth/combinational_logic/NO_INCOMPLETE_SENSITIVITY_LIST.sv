// breadth: reports | A signal read in the block body but missing from the explicit sensitivity list is reported.
// pair: missing-vs-listed-signal
module top(input a, input b, output logic y);
  always @(a) begin
    y = a & b;
  end
endmodule

// breadth: clean | All signals read in the block body explicitly listed in the sensitivity list is not reported.
// pair: missing-vs-listed-signal
module top(input a, input b, output logic y);
  always @(a or b) begin
    y = a & b;
  end
endmodule

// breadth: reports | An explicit sensitivity list missing a read operand is reported.
// pair: explicit-list-vs-at-star
module top(input a, input b, output logic y);
  always @(a) begin
    y = a | b;
  end
endmodule

// breadth: clean | An always block using wildcard at-star sensitivity is not reported.
// pair: explicit-list-vs-at-star
module top(input a, input b, output logic y);
  always @* begin
    y = a | b;
  end
endmodule

// breadth: reports | An always block with a missing read variable is reported.
// pair: explicit-list-vs-always-comb
module top(input a, input b, output logic y);
  always @(a) begin
    y = a ^ b;
  end
endmodule

// breadth: clean | An always_comb block with implicit sensitivity is not reported.
// pair: explicit-list-vs-always-comb
module top(input a, input b, output logic y);
  always_comb begin
    y = a ^ b;
  end
endmodule

// breadth: reports | An index variable used in a select expression and missing from the sensitivity list is reported.
// pair: index-expression-missing-vs-listed
module top(input [3:0] a, input [1:0] sel, output logic y);
  always @(a) begin
    y = a[sel];
  end
endmodule

// breadth: clean | Both the indexed array and the selecting index variable explicitly listed in the sensitivity list is not reported.
// pair: index-expression-missing-vs-listed
module top(input [3:0] a, input [1:0] sel, output logic y);
  always @(a or sel) begin
    y = a[sel];
  end
endmodule

// breadth: reports | A signal read in an expression and missing from the sensitivity list is reported.
// pair: signal-read-vs-written-only
module top(input a, input b, output logic y);
  always @(a) begin
    y = b;
  end
endmodule

// breadth: clean | A signal that is only assigned in the block is not reported when omitted from the sensitivity list.
// pair: signal-read-vs-written-only
module top(input a, output logic y, output logic z);
  always @(a) begin
    z = 1'b0;
    y = a;
  end
endmodule

// breadth: reports | Multiple signals read in the block and missing from the sensitivity list are reported.
// expect: 2
module top(input a, input b, input c, output logic y);
  always @(a) begin
    y = a & b & c;
  end
endmodule

// breadth: clean | A clocked sequential block with posedge clk is not reported for data inputs read inside the block.
module top(input clk, input d, output logic q);
  always @(posedge clk) begin
    q <= d;
  end
endmodule

// breadth: clean | A sensitivity list using comma separation listing all read signals is not reported.
module top(input a, input b, output logic y);
  always @(a, b) begin
    y = a & b;
  end
endmodule
