// Breadth tests for NO_SPECIFY_BLOCK.
// Tests the prohibition of specify timing blocks.

// breadth: reports | Banned specify block defining module pin-to-pin delays
// pair: specify_vs_logic
module b_rep_specify (input wire in_sig, output wire out_sig);
    specify
        (in_sig => out_sig) = 5;
    endspecify
endmodule

// breadth: clean | Module logic without pin delay specify block
// pair: specify_vs_logic
module b_clean_no_specify (input wire in_sig, output wire out_sig);
    assign out_sig = in_sig;
endmodule

// breadth: clean | Word specify in comment or string literal
module b_clean_comment (input logic a, output logic b);
    // specify blocks are used for gate-level SDF back-annotation
    assign b = a;
    localparam string MSG = "specify block banned in RTL";
endmodule

// breadth: reports | Banned specify block with conditional path
module b_rep_cond_specify (input wire a, b, output wire y);
    specify
        if (a) (b => y) = 2;
    endspecify
endmodule

// breadth: reports | Banned specify block with timing checks
module b_rep_setup_specify (input wire clk, d, output wire q);
    specify
        $setup(d, posedge clk, 3);
    endspecify
endmodule

// breadth: reports | Multiple specify blocks in module
// expect: 2
module b_rep_count (input wire a, b, output wire y1, y2);
    specify
        (a => y1) = 1;
    endspecify

    specify
        (b => y2) = 2;
    endspecify
endmodule

// breadth: clean | Parameter override and continuous assign instead of specify block
module b_clean_neighbor_assign #(parameter int DELAY = 2) (input wire a, output wire b);
    assign b = a;
endmodule
