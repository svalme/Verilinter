// Breadth tests for NO_FINAL_BLOCK.
// Tests the prohibition of final procedural blocks.

// breadth: reports | Banned final block executing at end of simulation
// pair: final_vs_assign
module b_rep_final (input logic clk);
    final begin
        $display("Simulation ended");
    end
endmodule

// breadth: clean | Continuous assignment instead of final block
// pair: final_vs_assign
module b_clean_assign (input logic clk, output logic q);
    assign q = clk;
endmodule

// breadth: clean | Word final in comment or string literal
module b_clean_comment (input logic a, output logic b);
    // final blocks are non-synthesizable
    assign b = a;
    localparam string MSG = "final block disallowed";
endmodule

// breadth: reports | Banned final block nested in generate block
module b_rep_generate (input logic clk);
    generate
        if (1) begin : g_fin
            final begin
                $display("Generate final");
            end
        end
    endgenerate
endmodule

// breadth: reports | Banned final block with variable assignment
module b_rep_assign (output int cnt);
    final begin
        cnt = 100;
    end
endmodule

// breadth: reports | Multiple final procedural blocks in module
// expect: 2
module b_rep_count (input logic clk);
    final begin
        $display("Final block 1");
    end

    final begin
        $display("Final block 2");
    end
endmodule

// breadth: clean | Initial block and always_comb instead of final block
module b_clean_neighbor_blocks (input logic clk, d, output logic q);
    initial begin
        q = 1'b0;
    end
    always_comb begin
        q = d;
    end
endmodule
