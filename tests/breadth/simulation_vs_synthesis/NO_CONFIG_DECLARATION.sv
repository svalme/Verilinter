// Breadth tests for NO_CONFIG_DECLARATION.
// Tests the prohibition of config declarations.

// breadth: reports | Banned config declaration specifying design configuration
// pair: config_vs_module
config b_rep_cfg;
    design work.top;
    default liblist work;
endconfig

// breadth: clean | Top module declaration without config block
// pair: config_vs_module
module b_clean_module (input logic clk, output logic q);
    assign q = clk;
endmodule

// breadth: clean | Word config in comment or string literal
module b_clean_comment (input logic a, output logic b);
    // config declarations specify library binding rules
    assign b = a;
    localparam string MSG = "config construct is banned";
endmodule

// breadth: reports | Banned config declaration with instance rule
config b_rep_inst_cfg;
    design rtl_lib.core;
    instance rtl_lib.core.u_alu use gate_lib.alu_gate;
endconfig

// breadth: reports | Banned config declaration with cell rule
config b_rep_cell_cfg;
    design my_lib.sub;
    cell my_lib.sub use work.sub;
endconfig

// breadth: reports | Multiple config declarations in compilation unit
// expect: 2
config b_rep_cfg_1;
    design work.top1;
endconfig

config b_rep_cfg_2;
    design work.top2;
endconfig

// breadth: clean | Module declaration with local parameters instead of config block
module b_clean_neighbor_mod #(parameter int MODE = 1) (input logic clk, output logic q);
    localparam int CFG_VAL = MODE * 2;
    assign q = clk;
endmodule
