// Breadth test suite for DEEPLY_NESTED_BLOCK
// Category: maintainability_and_complexity
//
// Tests detection of procedural blocks exceeding maximum nesting depth (_MAX_NESTING_DEPTH = 4),
// covering mixed if/case/block hierarchies, contrasting with blocks within depth limits,
// loop statements (which do not count toward depth), and flat else-if chains.

// breadth: reports | Nested if-statements exceeding maximum procedural depth of 4 are reported.
// pair: p1
module nested_if_exceeds_depth (
    input  wire a,
    input  wire b,
    output reg  y
);
  always_comb begin // 1
    if (a) begin // 2, 3
      if (b) begin // 4, 5: Exceeds 4 levels of nesting
        y = 1'b1;
      end
    end
  end
endmodule

// breadth: clean | Single nested if-statement within depth 3 is not reported.
// pair: p1
module nested_if_within_depth (
    input  wire a,
    output reg  y
);
  always_comb begin // 1
    if (a) begin // 2, 3: Depth 3 is within the limit of 4
      y = 1'b1;
    end
  end
endmodule

// breadth: reports | If-statement nested inside a case branch exceeding maximum depth is reported.
// pair: p2
module mixed_case_and_if_deep (
    input  wire [1:0] sel,
    input  wire       cond,
    output reg        y
);
  always_comb begin // 1
    case (sel) // 2
      2'd0: begin // 3
        if (cond) begin // 4, 5: Exceeds limit
          y = 1'b1;
        end
      end
      default: begin
        y = 1'b0;
      end
    endcase
  end
endmodule

// breadth: clean | Case statement with wrapped branch within depth 3 is not reported.
// pair: p2
module case_within_depth (
    input  wire [1:0] sel,
    output reg        y
);
  always_comb begin // 1
    case (sel) // 2
      2'd0: begin // 3: Within limit
        y = 1'b1;
      end
      default: begin
        y = 1'b0;
      end
    endcase
  end
endmodule

// breadth: reports | Sequential always_ff block with nested conditionals exceeding maximum depth is reported.
// pair: p3
module sequential_nested_ifs_deep (
    input  wire clk,
    input  wire en1,
    input  wire en2,
    output reg  q
);
  always_ff @(posedge clk) begin // 1
    if (en1) begin // 2, 3
      if (en2) begin // 4, 5: Exceeds limit
        q <= 1'b1;
      end
    end
  end
endmodule

// breadth: clean | Sequential always_ff block with single conditional within depth 3 is not reported.
// pair: p3
module sequential_if_within_depth (
    input  wire clk,
    input  wire en,
    output reg  q
);
  always_ff @(posedge clk) begin // 1
    if (en) begin // 2, 3: Within limit
      q <= 1'b1;
    end
  end
endmodule

// breadth: clean | Nested for-loops without conditional blocks do not increment nesting depth counter and are not reported.
// pair: p4
module nested_loops_do_not_add_depth (
    output reg [3:0] matrix [0:1][0:1]
);
  // Loop statements (for/while/repeat) are not counted toward procedural nesting depth
  always_comb begin
    for (int i = 0; i < 2; i = i + 1) begin
      for (int j = 0; j < 2; j = j + 1) begin
        matrix[i][j] = 4'd0;
      end
    end
  end
endmodule

// breadth: reports | Bare begin-end blocks deeply nested to level 5 are reported.
// pair: p4
module bare_blocks_exceed_depth (
    output reg y
);
  always_comb begin // 1
    begin // 2
      begin // 3
        begin // 4
          begin // 5: Exceeds limit
            y = 1'b1;
          end
        end
      end
    end
  end
endmodule

// breadth: clean | Flat else-if chain without nested block statements is not reported.
module long_elseif_chain_clean (
    input  wire [3:0] code_in,
    output reg  [3:0] code_out
);
  // An else-if chain without nested block statements stays flat
  always_comb begin
    if (code_in == 4'd0)
      code_out = 4'd0;
    else if (code_in == 4'd1)
      code_out = 4'd1;
    else if (code_in == 4'd2)
      code_out = 4'd2;
    else
      code_out = 4'd3;
  end
endmodule

// breadth: clean | Function body with simple conditional within depth limits is not reported.
module function_body_within_depth (
    input  wire [3:0] a,
    output wire [3:0] y
);
  function automatic [3:0] clamp(input [3:0] val);
    if (val > 4'd10) begin
      clamp = 4'd10;
    end else begin
      clamp = val;
    end
  endfunction

  assign y = clamp(a);
endmodule
