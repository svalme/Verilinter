// Breadth tests for NO_ORDERED_PARAMETER_OVERRIDES.
// Tests the prohibition of positional ordered parameter overrides on instances.

// breadth: reports | Banned ordered parameter override on instance
// pair: ordered_params_vs_named_params
module param_cell #(parameter int WIDTH = 8, parameter int DEPTH = 16) (input logic clk);
endmodule

module b_rep_ordered_params (input logic clk);
    param_cell #(16, 32) u_cell (clk);
endmodule

// breadth: clean | Named parameter override on instance
// pair: ordered_params_vs_named_params
module b_clean_named_params (input logic clk);
    param_cell #(.WIDTH(16), .DEPTH(32)) u_cell (.clk(clk));
endmodule

// breadth: clean | Word ordered parameter override in comment or string literal
module b_clean_comment (input logic a, output logic b);
    // positional parameter overrides #(val) are fragile
    assign b = a;
    localparam string MSG = "ordered parameter override banned";
endmodule

// breadth: reports | Banned single ordered parameter override
module b_rep_single_param (input logic clk);
    param_cell #(64) u_cell (clk);
endmodule

// breadth: reports | Banned ordered parameter override in generate block
module b_rep_gen_ordered_param (input logic clk);
    generate
        if (1) begin : g_blk
            param_cell #(128) u_cell (clk);
        end
    endgenerate
endmodule

// breadth: reports | Multiple instances with ordered parameter overrides
// expect: 2
module b_rep_count (input logic clk);
    param_cell #(4) u_cell1 (clk);
    param_cell #(8) u_cell2 (clk);
endmodule
