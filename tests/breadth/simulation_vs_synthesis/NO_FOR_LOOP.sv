// Breadth tests for NO_FOR_LOOP.
// Tests the prohibition of procedural for loops.

// breadth: reports | Banned procedural for loop in always_comb
// pair: for_vs_generate_for
module b_rep_for_loop (input logic [3:0] in, output logic [3:0] out);
    always_comb begin
        for (int i = 0; i < 4; i++) begin
            out[i] = in[i];
        end
    end
endmodule

// breadth: clean | Generate for loop outside procedural context
// pair: for_vs_generate_for
module b_clean_gen_for (input logic [3:0] in, output logic [3:0] out);
    for (genvar i = 0; i < 4; i++) begin : g_loop
        assign out[i] = in[i];
    end
endmodule

// breadth: clean | Word for in comment or string literal
module b_clean_comment (input logic a, output logic b);
    // for loop is avoided here
    assign b = a;
    localparam string MSG = "for statement banned";
endmodule

// breadth: reports | Banned procedural for loop inside function
module b_rep_func (input logic [3:0] in, output logic [3:0] out);
    function automatic logic [3:0] rev(logic [3:0] val);
        for (int i = 0; i < 4; i++) begin
            rev[i] = val[3 - i];
        end
    endfunction
    assign out = rev(in);
endmodule

// breadth: reports | Banned procedural for loop nested in generate block
module b_rep_gen_nested (input logic [3:0] in, output logic [3:0] out);
    generate
        if (1) begin : g_blk
            always_comb begin
                for (int i = 0; i < 4; i++) begin
                    out[i] = in[i];
                end
            end
        end
    endgenerate
endmodule

// breadth: reports | Multiple procedural for loops in block
// expect: 2
module b_rep_count (input logic [3:0] in, output logic [3:0] out1, out2);
    always_comb begin
        for (int i = 0; i < 4; i++) begin
            out1[i] = in[i];
        end
        for (int j = 0; j < 4; j++) begin
            out2[j] = in[j];
        end
    end
endmodule
