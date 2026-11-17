// Breadth tests for NO_MODPORT_DECLARATION.
// Tests the prohibition of modport declarations.

// breadth: reports | Banned modport declaration inside interface
// pair: modport_vs_plain_interface
interface b_rep_modport (input logic clk);
    logic req;
    modport master (output req);
endinterface

// breadth: clean | Interface without modport declarations
// pair: modport_vs_plain_interface
interface b_clean_no_modport (input logic clk);
    logic req;
endinterface

// breadth: clean | Word modport in comment or string literal
module b_clean_comment (input logic a, output logic b);
    // modport declarations restrict interface signal access
    assign b = a;
    localparam string MSG = "modport construct is banned";
endmodule

// breadth: reports | Banned slave modport declaration
interface b_rep_slave_modport (input logic clk);
    logic ack;
    modport slave (input ack);
endinterface

// breadth: reports | Banned modport with clocking block reference
interface b_rep_cb_modport (input logic clk, d);
    clocking cb @(posedge clk);
        input d;
    endclocking
    modport client (clocking cb);
endinterface

// breadth: reports | Multiple modport declarations in interface
// expect: 2
interface b_rep_count (input logic clk);
    logic req, ack;
    modport master_mp (output req, input ack);
    modport slave_mp (input req, output ack);
endinterface

// breadth: clean | Interface with discrete signals and no modport declarations
interface b_clean_neighbor_raw_itf (input logic clk);
    logic [7:0] data;
    logic valid;
endinterface
