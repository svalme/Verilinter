// Breadth tests for NO_UNIQUE_IF.
// Tests the prohibition of unique if statements.

// breadth: reports | Banned unique if statement in procedural block
// pair: unique_if_vs_plain
module b_rep_unique_if (input logic [1:0] sel, output logic [1:0] y);
    always_comb begin
        unique if (sel == 2'b00)
            y = 2'b01;
        else if (sel == 2'b01)
            y = 2'b10;
        else
            y = 2'b00;
    end
endmodule

// breadth: clean | Plain if statement without unique qualifier
// pair: unique_if_vs_plain
module b_clean_plain_if (input logic [1:0] sel, output logic [1:0] y);
    always_comb begin
        if (sel == 2'b00)
            y = 2'b01;
        else if (sel == 2'b01)
            y = 2'b10;
        else
            y = 2'b00;
    end
endmodule

// breadth: clean | Word unique if in comment or string literal
module b_clean_comment (input logic a, output logic b);
    // unique if qualifier is avoided here
    assign b = a;
    localparam string MSG = "unique if is disallowed";
endmodule

// breadth: reports | Banned unique if nested in generate block
module b_rep_generate (input logic [1:0] sel, output logic [1:0] y);
    generate
        if (1) begin : g_blk
            always_comb begin
                unique if (sel == 2'b00)
                    y = 2'b01;
                else
                    y = 2'b00;
            end
        end
    endgenerate
endmodule

// breadth: reports | Banned unique if without else branch
module b_rep_no_else (input logic a, output logic b);
    always_comb begin
        b = 1'b0;
        unique if (a)
            b = 1'b1;
    end
endmodule

// breadth: reports | Multiple unique if statements in procedural code
// expect: 2
module b_rep_count (input logic a, b, output logic y1, y2);
    always_comb begin
        unique if (a)
            y1 = 1'b1;
        else
            y1 = 1'b0;

        unique if (b)
            y2 = 1'b1;
        else
            y2 = 1'b0;
    end
endmodule
