// Breadth tests for NO_DEFPARAM.
// Tests the prohibition of defparam statements.

// breadth: reports | Banned defparam statement overriding sub-module parameter
// pair: defparam_vs_param_inst
module sub_cell;
    parameter int WIDTH = 8;
endmodule

module b_rep_defparam;
    sub_cell u_sub ();
    defparam u_sub.WIDTH = 16;
endmodule

// breadth: clean | Explicit parameter override at instance site
// pair: defparam_vs_param_inst
module b_clean_param_inst;
    sub_cell #(.WIDTH(16)) u_sub ();
endmodule

// breadth: clean | Word defparam in comment or string literal
module b_clean_comment (input logic a, output logic b);
    // defparam statements are obsolete and hinder modular hierarchy
    assign b = a;
    localparam string MSG = "defparam statement banned";
endmodule

// breadth: reports | Banned defparam overriding nested hierarchical parameter
module leaf_cell;
    parameter int WIDTH = 8;
endmodule

module mid_cell;
    leaf_cell u_leaf ();
endmodule

module b_rep_hier_defparam;
    mid_cell u_mid ();
    defparam u_mid.u_leaf.WIDTH = 32;
endmodule

// breadth: reports | Banned defparam with multiple parameter assignments
module b_rep_multi_assign;
    sub_cell u_sub1 ();
    sub_cell u_sub2 ();
    defparam u_sub1.WIDTH = 4, u_sub2.WIDTH = 8;
endmodule

// breadth: reports | Multiple defparam statements in module
// expect: 2
module b_rep_count;
    sub_cell u_sub ();
    defparam u_sub.WIDTH = 24;
    defparam u_sub.WIDTH = 32;
endmodule
