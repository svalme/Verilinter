// Breadth tests for NO_ALIAS_STATEMENT.
// Tests the prohibition of alias statements.

// breadth: reports | Banned alias statement joining two net names
// pair: alias_vs_continuous
module b_rep_alias (input wire in_sig);
    wire a, b;
    assign a = in_sig;
    alias a = b;
endmodule

// breadth: clean | Unidirectional continuous assignment instead of bidirectional alias
// pair: alias_vs_continuous
module b_clean_assign (input wire in_sig, output wire b);
    wire a;
    assign a = in_sig;
    assign b = a;
endmodule

// breadth: clean | Word alias in comment or string literal
module b_clean_comment (input logic a, output logic b);
    // alias statements create bidirectional net synonymies
    assign b = a;
    localparam string MSG = "alias statement banned";
endmodule

// breadth: reports | Banned multi-way alias statement
module b_rep_multi_alias;
    wire x, y, z;
    alias x = y = z;
endmodule

// breadth: reports | Banned alias statement inside generate block
module b_rep_generate;
    wire net1, net2;
    generate
        if (1) begin : g_blk
            alias net1 = net2;
        end
    endgenerate
endmodule

// breadth: reports | Multiple alias statements in module
// expect: 2
module b_rep_count;
    wire p1, p2, q1, q2;
    alias p1 = p2;
    alias q1 = q2;
endmodule

// breadth: clean | Unidirectional continuous assign between nets instead of alias
module b_clean_neighbor_assign (input wire a, output wire b);
    assign b = a;
endmodule
