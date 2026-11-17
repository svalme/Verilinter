// Breadth tests for NO_RANDOM_SYSTEM_FUNCTION.
// Tests the prohibition of random system functions ($random, $urandom, $urandom_range).

// breadth: reports | Banned $urandom system function generating random word
// pair: random_vs_lfsr
module b_rep_urandom (output int rand_val);
    always_comb begin
        rand_val = $urandom();
    end
endmodule

// breadth: clean | Synthesizable counter instead of pseudo-random generator
// pair: random_vs_lfsr
module b_clean_counter (input logic clk, output logic [7:0] cnt);
    always_ff @(posedge clk) begin
        cnt <= cnt + 1'b1;
    end
endmodule

// breadth: clean | Word $urandom in comment or string literal
module b_clean_comment (input logic a, output logic b);
    // $urandom and $random are non-synthesizable simulation functions
    assign b = a;
    localparam string MSG = "$urandom function banned";
endmodule

// breadth: reports | Banned $random legacy system function
module b_rep_random (output int val);
    always_comb begin
        val = $random();
    end
endmodule

// breadth: reports | Banned $urandom_range system function nested in generate
module b_rep_gen_urandom_range (output int seed);
    generate
        if (1) begin : g_blk
            initial begin
                seed = $urandom_range(1, 100);
            end
        end
    endgenerate
endmodule

// breadth: reports | Multiple random system functions in procedural block
// expect: 2
module b_rep_count (output int r1, r2);
    always_comb begin
        r1 = $urandom();
        r2 = $urandom();
    end
endmodule

// breadth: clean | Constant system function clog2 instead of random function
module b_clean_neighbor_clog2;
    localparam int STEPS = $clog2(128);
endmodule
