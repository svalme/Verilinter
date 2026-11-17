// breadth: reports | The exact same constant item written twice in separate case branches is reported.
// pair: identical-constant-twice-vs-distinct
module top(input [3:0] sel, output logic y);
  always_comb begin
    case (sel)
      4'd2: y = 1'b1;
      4'd2: y = 1'b0;
      default: y = 1'b0;
    endcase
  end
endmodule

// breadth: clean | Distinct constant items in separate case branches are not reported.
// pair: identical-constant-twice-vs-distinct
module top(input [3:0] sel, output logic y);
  always_comb begin
    case (sel)
      4'd1: y = 1'b1;
      4'd2: y = 1'b0;
      default: y = 1'b0;
    endcase
  end
endmodule

// breadth: reports | The exact same constant repeated in the same comma-separated case branch list is reported.
// pair: same-constant-same-list-vs-distinct-list
module top(input [3:0] sel, output logic y);
  always_comb begin
    case (sel)
      4'd2, 4'd2: y = 1'b1;
      default: y = 1'b0;
    endcase
  end
endmodule

// breadth: clean | Distinct constants in the same comma-separated case branch list are not reported.
// pair: same-constant-same-list-vs-distinct-list
module top(input [3:0] sel, output logic y);
  always_comb begin
    case (sel)
      4'd1, 4'd2: y = 1'b1;
      default: y = 1'b0;
    endcase
  end
endmodule

// breadth: reports | The same constant repeated in the same case statement is reported.
// pair: same-case-vs-different-case-statements
module top(input [3:0] sel, output logic y);
  always_comb begin
    case (sel)
      4'hA: y = 1'b1;
      4'hA: y = 1'b0;
      default: y = 1'b0;
    endcase
  end
endmodule

// breadth: clean | The same constant used across two separate case statements is not reported.
// pair: same-case-vs-different-case-statements
module top(input [3:0] a, input [3:0] b, output logic y, output logic z);
  always_comb begin
    case (a)
      4'hA: y = 1'b1;
      default: y = 1'b0;
    endcase
    case (b)
      4'hA: z = 1'b1;
      default: z = 1'b0;
    endcase
  end
endmodule

// breadth: reports | The exact same literal token repeated twice in a case statement is reported.
// pair: exact-text-duplicate-vs-different-spelling-same-value
module top(input [3:0] sel, output logic y);
  always_comb begin
    case (sel)
      2'b10: y = 1'b1;
      2'b10: y = 1'b0;
      default: y = 1'b0;
    endcase
  end
endmodule

// breadth: clean | Semantically equal values written with different lexical spellings are not reported by the syntactic duplicate rule.
// pair: exact-text-duplicate-vs-different-spelling-same-value
module top(input [3:0] sel, output logic y);
  always_comb begin
    case (sel)
      2: y = 1'b1;
      2'b10: y = 1'b0;
      default: y = 1'b0;
    endcase
  end
endmodule

// breadth: reports | The exact same parameter identifier repeated in separate case branches is reported.
// pair: parameter-identifier-duplicate
module top #(parameter P = 2) (input [3:0] sel, output logic y);
  always_comb begin
    case (sel)
      P: y = 1'b1;
      P: y = 1'b0;
      default: y = 1'b0;
    endcase
  end
endmodule

// breadth: clean | A parameter identifier and a constant literal evaluating to the same value are not reported by the syntactic duplicate rule.
// pair: parameter-identifier-duplicate
module top #(parameter P = 2) (input [3:0] sel, output logic y);
  always_comb begin
    case (sel)
      P: y = 1'b1;
      2: y = 1'b0;
      default: y = 1'b0;
    endcase
  end
endmodule

// breadth: reports | The same wildcard literal repeated in a casez statement is reported.
module top(input [2:0] sel, output logic y);
  always_comb begin
    casez (sel)
      3'b0??: y = 1'b1;
      3'b0??: y = 1'b0;
      default: y = 1'b0;
    endcase
  end
endmodule

// breadth: clean | A case statement with a single unique item and a default branch is not reported.
module top(input [3:0] sel, output logic y);
  always_comb begin
    case (sel)
      4'd1: y = 1'b1;
      default: y = 1'b0;
    endcase
  end
endmodule
