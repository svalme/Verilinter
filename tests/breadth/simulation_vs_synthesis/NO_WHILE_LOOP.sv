// Breadth tests for NO_WHILE_LOOP.
// Tests the prohibition of while loops.

// breadth: reports | Banned while loop in procedural block
// pair: while_vs_for
module b_rep_while (input logic clk, output int val);
    always_comb begin
        val = 0;
        while (val < 10) begin
            val++;
        end
    end
endmodule

// breadth: clean | Procedural for loop instead of while loop
// pair: while_vs_for
module b_clean_for (input logic clk, output int val);
    always_comb begin
        val = 0;
        for (int i = 0; i < 10; i++) begin
            val++;
        end
    end
endmodule

// breadth: clean | Word while in comment or string literal
module b_clean_comment (input logic a, output logic b);
    // while loop can cause infinite loops in synthesis
    assign b = a;
    localparam string MSG = "while statement disallowed";
endmodule

// breadth: reports | Banned while loop nested in generate block
module b_rep_generate (output int val);
    generate
        if (1) begin : g_blk
            always_comb begin
                val = 0;
                while (val < 5) begin
                    val++;
                end
            end
        end
    endgenerate
endmodule

// breadth: reports | Banned while loop inside function
module b_rep_func (input int limit, output int res);
    function automatic int count_to(int lim);
        int cur;
        cur = 0;
        while (cur < lim) begin
            cur++;
        end
        return cur;
    endfunction
    assign res = count_to(limit);
endmodule

// breadth: reports | Multiple while loops in block
// expect: 2
module b_rep_count (output int x, y);
    always_comb begin
        x = 0;
        while (x < 4) begin
            x++;
        end
        y = 0;
        while (y < 8) begin
            y++;
        end
    end
endmodule
