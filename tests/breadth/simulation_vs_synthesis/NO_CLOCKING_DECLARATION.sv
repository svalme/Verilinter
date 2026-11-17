// Breadth tests for NO_CLOCKING_DECLARATION.
// Tests the prohibition of clocking block declarations.

// breadth: reports | Banned clocking block declaration in module
// pair: clocking_vs_always_ff
module b_rep_clocking (input logic clk, d, output logic q);
    clocking cb @(posedge clk);
        input d;
        output q;
    endclocking
endmodule

// breadth: clean | Clocked always block instead of clocking block
// pair: clocking_vs_always_ff
module b_clean_always (input logic clk, d, output logic q);
    always_ff @(posedge clk) begin
        q <= d;
    end
endmodule

// breadth: clean | Word clocking in comment or string literal
module b_clean_comment (input logic a, output logic b);
    // clocking blocks specify simulation cycle timing
    assign b = a;
    localparam string MSG = "clocking declaration banned";
endmodule

// breadth: reports | Banned default clocking block
module b_rep_default_clocking (input logic clk, d);
    default clocking def_cb @(posedge clk);
        input d;
    endclocking
endmodule

// breadth: reports | Banned global clocking declaration
module b_rep_global_clocking (input logic sys_clk);
    global clocking g_cb @(posedge sys_clk);
    endclocking
endmodule

// breadth: reports | Multiple clocking blocks in module
// expect: 2
module b_rep_count (input logic clk1, clk2, d);
    clocking cb1 @(posedge clk1);
        input d;
    endclocking

    clocking cb2 @(posedge clk2);
        input d;
    endclocking
endmodule

// breadth: clean | Interface with signals and modport instead of clocking block
interface b_clean_neighbor_itf (input logic clk);
    logic req;
    logic ack;
    modport master (input clk, ack, output req);
endinterface
