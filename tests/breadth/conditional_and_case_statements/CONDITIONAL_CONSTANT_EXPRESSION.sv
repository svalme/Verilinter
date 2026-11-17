// breadth: reports | An if statement with a constant integer literal condition 1 is reported.
// pair: if-literal-constant-vs-variable-condition
module top(input a, output logic y);
  always_comb begin
    if (1) y = a;
    else y = 1'b0;
  end
endmodule

// breadth: clean | An if statement with a runtime signal condition is not reported.
// pair: if-literal-constant-vs-variable-condition
module top(input en, input a, output logic y);
  always_comb begin
    if (en) y = a;
    else y = 1'b0;
  end
endmodule

// breadth: reports | An if statement with a constant expression condition 1 + 1 == 2 is reported.
// pair: if-binary-constant-expr-vs-variable-comparison
module top(input a, output logic y);
  always_comb begin
    if (1 + 1 == 2) y = a;
    else y = 1'b0;
  end
endmodule

// breadth: clean | An if statement with a variable comparison condition is not reported.
// pair: if-binary-constant-expr-vs-variable-comparison
module top(input [3:0] a, output logic y);
  always_comb begin
    if (a == 4'd2) y = 1'b1;
    else y = 1'b0;
  end
endmodule

// breadth: reports | A procedural if statement with constant false condition 0 is reported.
// pair: procedural-if-constant-vs-generate-if
module top(input a, output logic y);
  always_comb begin
    if (0) y = a;
    else y = 1'b0;
  end
endmodule

// breadth: clean | A generate if statement evaluating a parameter condition is not reported.
// pair: procedural-if-constant-vs-generate-if
module top #(parameter EN = 1) (input a, output logic y);
  generate
    if (EN) begin
      assign y = a;
    end else begin
      assign y = 1'b0;
    end
  endgenerate
endmodule

// breadth: reports | A procedural if statement with sized literal 1'b1 is reported.
// pair: procedural-if-constant-vs-ternary-operator
module top(input a, output logic y);
  always_comb begin
    if (1'b1) y = a;
    else y = 1'b0;
  end
endmodule

// breadth: clean | A continuous assignment ternary conditional expression is not reported.
// pair: procedural-if-constant-vs-ternary-operator
module top(input a, output logic y);
  assign y = 1'b1 ? a : 1'b0;
endmodule

// breadth: reports | An if statement with unbased unsized constant '0 is reported.
module top(input a, output logic y);
  always_comb begin
    if ('0) y = a;
    else y = 1'b0;
  end
endmodule

// breadth: reports | A nested if statement with constant predicate 1'b0 is reported.
module top(input en, input a, output logic y);
  always_comb begin
    if (en) begin
      if (1'b0) y = a;
      else y = 1'b0;
    end else begin
      y = 1'b0;
    end
  end
endmodule

// breadth: clean | A procedural if statement conditioned on an overridable parameter name is not reported.
module top #(parameter EN = 1) (input a, output logic y);
  always_comb begin
    if (EN) y = a;
    else y = 1'b0;
  end
endmodule

// breadth: clean | A procedural if statement conditioned on a localparam identifier is not reported.
module top(input a, output logic y);
  localparam EN = 1;
  always_comb begin
    if (EN) y = a;
    else y = 1'b0;
  end
endmodule
