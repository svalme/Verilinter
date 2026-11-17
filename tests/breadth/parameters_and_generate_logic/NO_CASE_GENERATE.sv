// Breadth tests for NO_CASE_GENERATE.
// Tests the prohibition of case generate constructs.

// breadth: reports | Banned case generate statement selecting architecture
// pair: case_generate_vs_if_generate
module b_rep_case_gen #(parameter int MODE = 0) (input logic a, output logic y);
    generate
        case (MODE)
            0: begin : g_direct
                assign y = a;
            end
            default: begin : g_inv
                assign y = ~a;
            end
        endcase
    endgenerate
endmodule

// breadth: clean | If generate statement instead of case generate
// pair: case_generate_vs_if_generate
module b_clean_if_gen #(parameter int MODE = 0) (input logic a, output logic y);
    generate
        if (MODE == 0) begin : g_direct
            assign y = a;
        end else begin : g_inv
            assign y = ~a;
        end
    endgenerate
endmodule

// breadth: clean | Word case generate in comment or string literal
module b_clean_comment (input logic a, output logic b);
    // case generate constructs are banned by style guidelines
    assign b = a;
    localparam string MSG = "case generate construct banned";
endmodule

// breadth: reports | Banned case generate nested in generate if
module b_rep_nested_case_gen #(parameter int CFG = 1, parameter int SUB = 0) (output logic out_sig);
    generate
        if (CFG == 1) begin : g_outer
            case (SUB)
                0: assign out_sig = 1'b0;
                default: assign out_sig = 1'b1;
            endcase
        end
    endgenerate
endmodule

// breadth: reports | Banned case generate with multiple branch values
module b_rep_multi_branch #(parameter int SEL = 2) (output logic val);
    generate
        case (SEL)
            1, 2: assign val = 1'b1;
            default: assign val = 1'b0;
        endcase
    endgenerate
endmodule

// breadth: reports | Multiple case generate constructs in module
// expect: 2
module b_rep_count #(parameter int A = 0, parameter int B = 1) (output logic y1, y2);
    generate
        case (A)
            0: assign y1 = 1'b0;
            default: assign y1 = 1'b1;
        endcase

        case (B)
            0: assign y2 = 1'b0;
            default: assign y2 = 1'b1;
        endcase
    endgenerate
endmodule

// breadth: clean | Procedural case statement in always_comb instead of case generate
module b_clean_neighbor_case (input logic [1:0] sel, output logic [1:0] y);
    always_comb begin
        case (sel)
            2'b00: y = 2'b01;
            default: y = 2'b00;
        endcase
    end
endmodule
