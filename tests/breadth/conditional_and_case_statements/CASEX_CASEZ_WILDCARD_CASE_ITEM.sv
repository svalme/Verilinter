// breadth: reports | An all-x literal case item in a casex statement is reported.
// pair: all-x-in-casex-vs-plain-case
module top(input [3:0] sel, output logic y);
  always_comb begin
    casex (sel)
      4'bxxxx: y = 1'b1;
      default: y = 1'b0;
    endcase
  end
endmodule

// breadth: clean | An all-x literal case item in a standard case statement is not reported.
// pair: all-x-in-casex-vs-plain-case
module top(input [3:0] sel, output logic y);
  always_comb begin
    case (sel)
      4'bxxxx: y = 1'b1;
      default: y = 1'b0;
    endcase
  end
endmodule

// breadth: reports | An all-z literal case item in a casez statement is reported.
// pair: all-z-in-casez-vs-partial-wildcard
module top(input [3:0] sel, output logic y);
  always_comb begin
    casez (sel)
      4'bzzzz: y = 1'b1;
      default: y = 1'b0;
    endcase
  end
endmodule

// breadth: clean | A partial wildcard case item with fixed bits in a casez statement is not reported.
// pair: all-z-in-casez-vs-partial-wildcard
module top(input [3:0] sel, output logic y);
  always_comb begin
    casez (sel)
      4'b0???: y = 1'b1;
      default: y = 1'b0;
    endcase
  end
endmodule

// breadth: reports | An all-question-mark wildcard case item in a casez statement is reported.
// pair: all-qmark-in-casez-vs-all-x-in-casez
module top(input [3:0] sel, output logic y);
  always_comb begin
    casez (sel)
      4'b????: y = 1'b1;
      default: y = 1'b0;
    endcase
  end
endmodule

// breadth: clean | An all-x literal in a casez statement is not reported as an all-wildcard item.
// pair: all-qmark-in-casez-vs-all-x-in-casez
module top(input [3:0] sel, output logic y);
  always_comb begin
    casez (sel)
      4'bxxxx: y = 1'b1;
      default: y = 1'b0;
    endcase
  end
endmodule

// breadth: reports | An all-wildcard case item in a case branch is reported.
// pair: wildcard-item-vs-wildcard-expression
module top(input [3:0] sel, output logic y);
  always_comb begin
    casez (sel)
      4'b????: y = 1'b1;
      default: y = 1'b0;
    endcase
  end
endmodule

// breadth: clean | A wildcard literal used in the case expression rather than an item is not reported.
// pair: wildcard-item-vs-wildcard-expression
module top(input [3:0] a, output logic y);
  always_comb begin
    casez (4'b????)
      a: y = 1'b1;
      default: y = 1'b0;
    endcase
  end
endmodule

// breadth: reports | An all-z literal case item in a casex statement is reported.
module top(input [3:0] sel, output logic y);
  always_comb begin
    casex (sel)
      4'bzzzz: y = 1'b1;
      default: y = 1'b0;
    endcase
  end
endmodule

// breadth: clean | A deterministic constant case item in a casez statement is not reported.
module top(input [3:0] sel, output logic y);
  always_comb begin
    casez (sel)
      4'd2: y = 1'b1;
      default: y = 1'b0;
    endcase
  end
endmodule

// breadth: clean | A standard case statement with integer literals is not reported.
module top(input [3:0] sel, output logic y);
  always_comb begin
    case (sel)
      4'd1: y = 1'b1;
      default: y = 1'b0;
    endcase
  end
endmodule
