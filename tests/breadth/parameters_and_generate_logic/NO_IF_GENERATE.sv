// Breadth tests for NO_IF_GENERATE.
// Tests the prohibition of if generate constructs.

// breadth: reports | Banned conditional generate if statement
// pair: if_generate_vs_continuous
module b_rep_if_gen #(parameter bit FAST = 1) (input logic [3:0] d, output logic [3:0] q);
    generate
        if (FAST) begin : g_fast
            assign q = d;
        end else begin : g_slow
            assign q = ~d;
        end
    endgenerate
endmodule

// breadth: clean | Ternary operator in continuous assignment instead of generate if
// pair: if_generate_vs_continuous
module b_clean_ternary #(parameter bit FAST = 1) (input logic [3:0] d, output logic [3:0] q);
    assign q = FAST ? d : ~d;
endmodule

// breadth: clean | Word generate if in comment or string literal
module b_clean_comment (input logic a, output logic b);
    // if generate statements create conditional architecture variants
    assign b = a;
    localparam string MSG = "generate if construct banned";
endmodule

// breadth: reports | Banned if generate without else branch
module b_rep_no_else #(parameter bit ENABLED = 1) (output logic sig);
    generate
        if (ENABLED) begin : g_opt
            assign sig = 1'b1;
        end
    endgenerate
endmodule

// breadth: reports | Banned if generate with complex boolean condition
module b_rep_complex_cond #(parameter int VER = 2) (output logic [1:0] code);
    generate
        if (VER > 0 && VER < 4) begin : g_v
            assign code = 2'b01;
        end else begin : g_def
            assign code = 2'b00;
        end
    endgenerate
endmodule

// breadth: reports | Multiple if generate constructs in module
// expect: 2
module b_rep_count #(parameter bit EN1 = 1, parameter bit EN2 = 0) (output logic o1, o2);
    generate
        if (EN1) begin : g_one
            assign o1 = 1'b1;
        end

        if (EN2) begin : g_two
            assign o2 = 1'b1;
        end
    endgenerate
endmodule

// breadth: clean | Procedural if statement and ternary expression instead of if generate
module b_clean_neighbor_if (input logic sel, a, b, output logic y1, y2);
    always_comb begin
        if (sel)
            y1 = a;
        else
            y1 = b;
    end
    assign y2 = sel ? a : b;
endmodule
