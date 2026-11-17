// Breadth tests for NO_ALWAYS_FF.
// Tests the prohibition of always_ff procedural blocks.

// breadth: reports | Banned always_ff block for clocked register
// pair: always_ff_vs_plain_always
module b_rep_always_ff (input logic clk, d, output logic q);
    always_ff @(posedge clk) begin
        q <= d;
    end
endmodule

// breadth: clean | Plain always block with sensitivity list
// pair: always_ff_vs_plain_always
module b_clean_plain_always (input logic clk, d, output logic q);
    always @(posedge clk) begin
        q <= d;
    end
endmodule

// breadth: clean | Word always_ff in comment or string literal
module b_clean_comment (input logic a, output logic b);
    // always_ff block is not used here
    assign b = a;
    localparam string MSG = "always_ff is avoided";
endmodule

// breadth: reports | Banned always_ff block nested in generate block
module b_rep_generate (input logic clk, d, output logic q);
    generate
        if (1) begin : g_reg
            always_ff @(posedge clk) begin
                q <= d;
            end
        end
    endgenerate
endmodule

// breadth: reports | Banned always_ff block with asynchronous reset
module b_rep_async_reset (input logic clk, rst_n, d, output logic q);
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            q <= 1'b0;
        else
            q <= d;
    end
endmodule

// breadth: reports | Multiple always_ff procedural blocks in module
// expect: 2
module b_rep_count (input logic clk, d1, d2, output logic q1, q2);
    always_ff @(posedge clk) begin
        q1 <= d1;
    end

    always_ff @(posedge clk) begin
        q2 <= d2;
    end
endmodule
