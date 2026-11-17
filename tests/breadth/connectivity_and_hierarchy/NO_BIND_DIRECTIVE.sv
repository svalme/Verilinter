// Breadth tests for NO_BIND_DIRECTIVE.
// Tests the prohibition of bind directives.

// breadth: reports | Banned bind directive binding module to target
// pair: bind_vs_instantiation
module target_dev (input logic clk);
endmodule

module assertion_ip (input logic clk);
endmodule

module b_rep_bind;
    bind target_dev assertion_ip u_assert (clk);
endmodule

// breadth: clean | Direct module instantiation instead of bind directive
// pair: bind_vs_instantiation
module b_clean_direct_inst (input logic clk);
    assertion_ip u_direct (clk);
endmodule

// breadth: clean | Word bind in comment or string literal
module b_clean_comment (input logic a, output logic b);
    // bind directives inject assertions or checkers into target scopes
    assign b = a;
    localparam string MSG = "bind directive banned";
endmodule

// breadth: reports | Banned bind directive targeting instance scope
module sub_target (input logic clk);
endmodule

module sub_mon (input logic clk);
endmodule

module b_rep_inst_bind (input logic clk);
    sub_target u_sub (clk);
    bind u_sub sub_mon u_mon (clk);
endmodule

// breadth: reports | Banned bind directive with named port connections
module b_rep_named_bind;
    bind target_dev assertion_ip u_chk (.clk(clk));
endmodule

// breadth: reports | Multiple bind directives
// expect: 2
module b_rep_count;
    bind target_dev assertion_ip u_chk1 (clk);
    bind target_dev assertion_ip u_chk2 (clk);
endmodule

// breadth: clean | Ordinary direct module instantiation instead of bind directive
module child_device (input logic clk);
endmodule

module b_clean_neighbor_inst (input logic clk);
    child_device u_child (clk);
endmodule
