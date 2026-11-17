// Breadth tests for NO_WILDCARD_PORT_CONNECTION.
// Tests the prohibition of wildcard (.*) port connections.

// breadth: reports | Banned wildcard port connection (.*) on instance
// pair: wildcard_ports_vs_explicit_named
module leaf_mod (input logic clk, d, output logic q);
    always_ff @(posedge clk) q <= d;
endmodule

module b_rep_wildcard (input logic clk, d, output logic q);
    leaf_mod u_leaf (.*);
endmodule

// breadth: clean | Explicit named port bindings without wildcard
// pair: wildcard_ports_vs_explicit_named
module b_clean_named (input logic clk, d, output logic q);
    leaf_mod u_leaf (.clk(clk), .d(d), .q(q));
endmodule

// breadth: clean | Word .* wildcard port in comment or string literal
module b_clean_comment (input logic a, output logic b);
    // wildcard port connection .* hides connectivity details
    assign b = a;
    localparam string MSG = "wildcard .* connections banned";
endmodule

// breadth: reports | Banned wildcard connection with explicit override
module b_rep_wildcard_with_named (input logic clk, in_d, output logic q);
    logic d;
    assign d = in_d;
    leaf_mod u_leaf (.*, .d(d));
endmodule

// breadth: reports | Banned wildcard port connection inside generate block
module b_rep_gen_wildcard (input logic clk, d, output logic q);
    generate
        if (1) begin : g_blk
            leaf_mod u_leaf (.*);
        end
    endgenerate
endmodule

// breadth: reports | Multiple instances using wildcard port connections
// expect: 2
module b_rep_count (input logic clk, d, output logic q);
    leaf_mod u_leaf1 (.*);
    leaf_mod u_leaf2 (.*);
endmodule
