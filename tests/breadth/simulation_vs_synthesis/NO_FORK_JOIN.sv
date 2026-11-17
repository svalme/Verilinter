// Breadth tests for NO_FORK_JOIN.
// Tests the prohibition of fork..join parallel blocks.

// breadth: reports | Banned fork..join parallel block in initial block
// pair: fork_join_vs_begin_end
module b_rep_fork_join (output logic a, b);
    initial begin
        fork
            a = 1'b1;
            b = 1'b0;
        join
    end
endmodule

// breadth: clean | Sequential begin..end block instead of fork..join
// pair: fork_join_vs_begin_end
module b_clean_begin_end (output logic a, b);
    initial begin
        a = 1'b1;
        b = 1'b0;
    end
endmodule

// breadth: clean | Word fork join in comment or string literal
module b_clean_comment (input logic a, output logic b);
    // fork and join are unsupported in synthesis
    assign b = a;
    localparam string MSG = "fork join banned";
endmodule

// breadth: reports | Banned fork..join_any block
module b_rep_join_any (output logic a, b);
    initial begin
        fork
            a = 1'b1;
            b = 1'b0;
        join_any
    end
endmodule

// breadth: reports | Banned fork..join_none block nested in generate
module b_rep_join_none (output logic a, b);
    generate
        if (1) begin : g_blk
            initial begin
                fork
                    a = 1'b1;
                    b = 1'b0;
                join_none
            end
        end
    endgenerate
endmodule

// breadth: reports | Multiple fork..join blocks in initial block
// expect: 2
module b_rep_count (output logic x, y);
    initial begin
        fork
            x = 1'b1;
        join
        fork
            y = 1'b0;
        join
    end
endmodule
