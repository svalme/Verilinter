// Breadth test suite for NO_FULL_PARALLEL_CASE
// Category: conditional_and_case_statements
//
// Tests detection of full_case and parallel_case synthesis pragmas preceding
// case statements, contrasting with clean case statements, SystemVerilog unique/priority
// keywords, pragma strings, and comments not directly preceding case keywords.

// breadth: reports | Case statement preceded by synopsys full_case pragma comment is reported.
// pair: p1
module full_case_pragma_preceding (
    input  wire [1:0] sel,
    output reg        y
);
  always_comb begin
    // synopsys full_case
    case (sel)
      2'd0:    y = 1'b0;
      default: y = 1'b1;
    endcase
  end
endmodule

// breadth: clean | Case statement without preceding synthesis pragmas is not reported.
// pair: p1
module clean_case_no_pragmas (
    input  wire [1:0] sel,
    output reg        y
);
  always_comb begin
    case (sel)
      2'd0:    y = 1'b0;
      default: y = 1'b1;
    endcase
  end
endmodule

// breadth: reports | Case statement preceded by synopsys parallel_case pragma comment is reported.
// pair: p2
module parallel_case_pragma_preceding (
    input  wire [1:0] sel,
    output reg        y
);
  always_comb begin
    // synopsys parallel_case
    case (sel)
      2'd0:    y = 1'b0;
      2'd1:    y = 1'b1;
      default: y = 1'b0;
    endcase
  end
endmodule

// breadth: clean | Case statement qualified with standard SystemVerilog unique keyword is not reported.
// pair: p2
module unique_case_keyword_clean (
    input  wire [1:0] sel,
    output reg        y
);
  // SystemVerilog unique keyword is handled by its own rules, not NO_FULL_PARALLEL_CASE
  always_comb begin
    unique case (sel)
      2'd0:    y = 1'b0;
      2'd1:    y = 1'b1;
      default: y = 1'b0;
    endcase
  end
endmodule

// breadth: reports | Case statement preceded by combined synthesis full_case parallel_case comment is reported.
// pair: p3
module both_pragmas_preceding (
    input  wire [1:0] sel,
    output reg        y
);
  always_comb begin
    // synthesis full_case parallel_case
    case (sel)
      2'd0:    y = 1'b0;
      default: y = 1'b1;
    endcase
  end
endmodule

// breadth: clean | Case statement qualified with standard SystemVerilog priority keyword is not reported.
// pair: p3
module priority_case_keyword_clean (
    input  wire [1:0] sel,
    output reg        y
);
  // SystemVerilog priority keyword is clean for this rule
  always_comb begin
    priority case (sel)
      2'd0:    y = 1'b0;
      default: y = 1'b1;
    endcase
  end
endmodule

// breadth: clean | Pragma text contained within a string literal is not a comment and is not reported.
// pair: p4
module pragma_text_inside_string (
    output wire [7:0] dummy
);
  // String literal containing pragma text is not a case-preceding comment
  wire [127:0] msg;
  assign msg = "full_case parallel_case";
  assign dummy = msg[7:0];
endmodule

// breadth: reports | Casez statement preceded by synthesis full_case pragma comment is reported.
// pair: p4
module casez_with_full_case_pragma (
    input  wire [3:0] opcode,
    output reg        valid
);
  always_comb begin
    // synthesis full_case
    casez (opcode)
      4'b1???: valid = 1'b1;
      default: valid = 1'b0;
    endcase
  end
endmodule

// breadth: clean | Pragma separated from case keyword by blank line is not attached trivia and is not reported.
module pragma_separated_by_blank_line (
    input  wire [1:0] sel,
    output reg        y
);
  always_comb begin
    // synopsys full_case

    case (sel)
      2'd0:    y = 1'b0;
      default: y = 1'b1;
    endcase
  end
endmodule

// breadth: clean | Standard if-else statement without case constructs is not reported.
module standard_if_no_case (
    input  wire a,
    output reg  y
);
  always_comb begin
    if (a) begin
      y = 1'b1;
    end else begin
      y = 1'b0;
    end
  end
endmodule
