// Breadth tests for NO_ALWAYS_LATCH.
// Tests the prohibition of always_latch procedural blocks.

// breadth: reports | Banned always_latch block for transparent latch
// pair: always_latch_vs_plain_always
module b_rep_always_latch (input logic en, d, output logic q);
    always_latch begin
        if (en)
            q <= d;
    end
endmodule

// breadth: clean | Plain always block modeling level-sensitive behavior
// pair: always_latch_vs_plain_always
module b_clean_plain_always (input logic en, d, output logic q);
    always @* begin
        if (en)
            q = d;
    end
endmodule

// breadth: clean | Word always_latch in comment or string literal
module b_clean_comment (input logic a, output logic b);
    // always_latch is prohibited in this design
    assign b = a;
    localparam string MSG = "always_latch is avoided";
endmodule

// breadth: reports | Banned always_latch block nested in generate block
module b_rep_generate (input logic en, d, output logic q);
    generate
        if (1) begin : g_latch
            always_latch begin
                if (en)
                    q <= d;
            end
        end
    endgenerate
endmodule

// breadth: reports | Banned always_latch block with inverted enable
module b_rep_inverted_en (input logic en_n, d, output logic q);
    always_latch begin
        if (!en_n)
            q <= d;
    end
endmodule

// breadth: reports | Multiple always_latch procedural blocks in module
// expect: 2
module b_rep_count (input logic en, d1, d2, output logic q1, q2);
    always_latch begin
        if (en)
            q1 <= d1;
    end

    always_latch begin
        if (en)
            q2 <= d2;
    end
endmodule
