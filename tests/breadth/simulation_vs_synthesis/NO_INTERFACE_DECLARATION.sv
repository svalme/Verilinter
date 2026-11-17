// Breadth tests for NO_INTERFACE_DECLARATION.
// Tests the prohibition of interface declarations.

// breadth: reports | Banned interface declaration defining bus bundle
// pair: interface_vs_module
interface b_rep_if (input logic clk);
    logic req;
    logic ack;
endinterface

// breadth: clean | Module declaration with discrete ports
// pair: interface_vs_module
module b_clean_module (input logic clk, req, output logic ack);
    assign ack = req;
endmodule

// breadth: clean | Word interface in comment or string literal
module b_clean_comment (input logic a, output logic b);
    // interface declarations bundle signals together
    assign b = a;
    localparam string MSG = "interface construct banned";
endmodule

// breadth: reports | Banned parameterized interface declaration
interface b_rep_param_if #(parameter int WIDTH = 32) (input logic clk);
    logic [WIDTH-1:0] data;
    logic valid;
endinterface

// breadth: reports | Banned interface declaration with modports
interface b_rep_modport_if (input logic clk);
    logic req;
    modport master (output req);
endinterface

// breadth: reports | Multiple interface declarations
// expect: 2
interface b_rep_if1 (input logic clk);
    logic a;
endinterface

interface b_rep_if2 (input logic clk);
    logic b;
endinterface
