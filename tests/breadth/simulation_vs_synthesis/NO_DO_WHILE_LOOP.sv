// Breadth tests for NO_DO_WHILE_LOOP.
// Tests the prohibition of do..while loops.

// breadth: reports | Banned do..while loop in procedural block
// pair: do_while_vs_while
module b_rep_do_while (input logic clk, output int val);
    always_comb begin
        val = 0;
        do begin
            val++;
        end while (val < 10);
    end
endmodule

// breadth: clean | Plain for loop instead of do..while loop
// pair: do_while_vs_while
module b_clean_for (input logic clk, output int val);
    always_comb begin
        val = 0;
        for (int i = 0; i < 10; i++) begin
            val++;
        end
    end
endmodule

// breadth: clean | Word do while in comment or string literal
module b_clean_comment (input logic a, output logic b);
    // do while loops are non-synthesizable
    assign b = a;
    localparam string MSG = "do while statement banned";
endmodule

// breadth: reports | Banned do..while loop nested in generate block
module b_rep_generate (output int val);
    generate
        if (1) begin : g_blk
            always_comb begin
                val = 0;
                do begin
                    val++;
                end while (val < 5);
            end
        end
    endgenerate
endmodule

// breadth: reports | Banned do..while loop inside function
module b_rep_func (input int limit, output int res);
    function automatic int calc(int lim);
        int cur;
        cur = 0;
        do begin
            cur++;
        end while (cur < lim);
        return cur;
    endfunction
    assign res = calc(limit);
endmodule

// breadth: reports | Multiple do..while loops in block
// expect: 2
module b_rep_count (output int x, y);
    always_comb begin
        x = 0;
        do begin
            x++;
        end while (x < 4);
        y = 0;
        do begin
            y++;
        end while (y < 8);
    end
endmodule
