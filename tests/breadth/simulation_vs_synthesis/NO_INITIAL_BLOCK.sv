// Breadth tests for NO_INITIAL_BLOCK.
// Tests the prohibition of initial procedural blocks.

// breadth: reports | Banned initial block initializing signals
// pair: initial_vs_always
module b_rep_initial (output logic q);
    initial begin
        q = 1'b0;
    end
endmodule

// breadth: clean | Continuous assignment replacing initial block
// pair: initial_vs_always
module b_clean_assign (output logic q);
    assign q = 1'b0;
endmodule

// breadth: clean | Word initial in comment or string literal
module b_clean_comment (input logic a, output logic b);
    // initial blocks are not synthesizable
    assign b = a;
    localparam string MSG = "initial block banned";
endmodule

// breadth: reports | Banned initial block nested in generate block
module b_rep_generate (output logic q);
    generate
        if (1) begin : g_init
            initial begin
                q = 1'b1;
            end
        end
    endgenerate
endmodule

// breadth: reports | Banned initial block with multiple statements
module b_rep_multi_stmt (output logic [1:0] y);
    initial begin
        y[0] = 1'b0;
        y[1] = 1'b1;
    end
endmodule

// breadth: reports | Multiple initial procedural blocks in module
// expect: 2
module b_rep_count (output logic a, b);
    initial begin
        a = 1'b0;
    end

    initial begin
        b = 1'b1;
    end
endmodule

// breadth: clean | Always_comb procedural block instead of initial block
module b_clean_neighbor_always (input logic a, output logic b);
    always_comb begin
        b = ~a;
    end
endmodule
