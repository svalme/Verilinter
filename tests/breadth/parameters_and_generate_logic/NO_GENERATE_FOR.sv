// Breadth tests for NO_GENERATE_FOR.
// Tests the prohibition of loop generate constructs (generate for).

// breadth: reports | Banned loop generate construct replicating logic
// pair: generate_for_vs_unrolled
module b_rep_gen_for (input logic [3:0] in, output logic [3:0] out);
    for (genvar i = 0; i < 4; i++) begin : g_bits
        assign out[i] = in[i];
    end
endmodule

// breadth: clean | Unrolled continuous assignments without loop generate
// pair: generate_for_vs_unrolled
module b_clean_unrolled (input logic [3:0] in, output logic [3:0] out);
    assign out[0] = in[0];
    assign out[1] = in[1];
    assign out[2] = in[2];
    assign out[3] = in[3];
endmodule

// breadth: clean | Word generate for in comment or string literal
module b_clean_comment (input logic a, output logic b);
    // generate for loops are discouraged in flat RTL
    assign b = a;
    localparam string MSG = "generate for loop banned";
endmodule

// breadth: reports | Banned loop generate inside explicit generate block
module b_rep_explicit_gen (input logic [1:0] a, output logic [1:0] y);
    generate
        for (genvar k = 0; k < 2; k++) begin : g_loop
            assign y[k] = ~a[k];
        end
    endgenerate
endmodule

// breadth: reports | Banned loop generate instantiating sub-modules
module child_cell (input logic d, output logic q);
    assign q = d;
endmodule

module b_rep_inst_loop (input logic [1:0] d, output logic [1:0] q);
    for (genvar j = 0; j < 2; j++) begin : g_insts
        child_cell u_cell (.d(d[j]), .q(q[j]));
    end
endmodule

// breadth: reports | Multiple loop generate constructs in module
// expect: 2
module b_rep_count (input logic [1:0] a, b, output logic [1:0] ya, yb);
    for (genvar i = 0; i < 2; i++) begin : g_a
        assign ya[i] = a[i];
    end

    for (genvar j = 0; j < 2; j++) begin : g_b
        assign yb[j] = b[j];
    end
endmodule

// breadth: clean | Procedural for loop in always_comb instead of loop generate
module b_clean_neighbor_proc_for (input logic [3:0] in, output logic [3:0] out);
    always_comb begin
        for (int i = 0; i < 4; i++) begin
            out[i] = in[i];
        end
    end
endmodule
