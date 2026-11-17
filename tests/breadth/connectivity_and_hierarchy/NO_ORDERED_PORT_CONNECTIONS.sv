// Breadth tests for NO_ORDERED_PORT_CONNECTIONS.
// Tests the prohibition of ordered positional port connections in module instances.

// breadth: reports | Banned positional port connection in module instance
// pair: ordered_ports_vs_named_ports
module target_sub (input logic a, b, output logic y);
    assign y = a & b;
endmodule

module b_rep_ordered_ports (input logic in1, in2, output logic out_sig);
    target_sub u_sub (in1, in2, out_sig);
endmodule

// breadth: clean | Named port connection in module instance
// pair: ordered_ports_vs_named_ports
module b_clean_named_ports (input logic in1, in2, output logic out_sig);
    target_sub u_sub (.a(in1), .b(in2), .y(out_sig));
endmodule

// breadth: clean | Word ordered port connection in comment or string literal
module b_clean_comment (input logic a, output logic b);
    // ordered port connections are error-prone during refactoring
    assign b = a;
    localparam string MSG = "ordered port connections banned";
endmodule

// breadth: reports | Banned ordered port connection nested in generate block
module b_rep_generate_ordered (input logic in1, in2, output logic out_sig);
    generate
        if (1) begin : g_blk
            target_sub u_sub (in1, in2, out_sig);
        end
    endgenerate
endmodule

// breadth: reports | Banned ordered port connection with mixed expressions
module b_rep_expr_ports (input logic [1:0] sel, output logic out_sig);
    target_sub u_sub (sel[0], sel[1], out_sig);
endmodule

// breadth: reports | Multiple module instances with ordered port connections
// expect: 2
module b_rep_count (input logic a, b, c, output logic y1, y2);
    target_sub u_sub1 (a, b, y1);
    target_sub u_sub2 (b, c, y2);
endmodule
