// Breadth tests for NO_ASSIGN_DEASSIGN.
// Tests the prohibition of procedural assign and deassign statements.

// breadth: reports | Banned procedural assign statement in initial block
// pair: procedural_assign_vs_continuous
module b_rep_proc_assign (input logic d, output logic q);
    initial begin
        assign q = d;
    end
endmodule

// breadth: clean | Continuous assignment at module level
// pair: procedural_assign_vs_continuous
module b_clean_continuous (input logic d, output logic q);
    assign q = d;
endmodule

// breadth: clean | Word assign or deassign in comment or string literal
module b_clean_comment (input logic a, output logic b);
    // procedural assign and deassign are obsolete Verilog-1995 features
    assign b = a;
    localparam string MSG = "procedural assign banned";
endmodule

// breadth: reports | Banned procedural deassign statement
module b_rep_deassign (output logic q);
    initial begin
        deassign q;
    end
endmodule

// breadth: reports | Banned procedural assign inside always block
module b_rep_always (input logic clk, d, output logic q);
    always @(posedge clk) begin
        assign q = d;
    end
endmodule

// breadth: reports | Multiple procedural assign and deassign statements
// expect: 2
module b_rep_count (input logic d, output logic q);
    initial begin
        assign q = d;
        deassign q;
    end
endmodule
