// Breadth tests for NO_LET_DECLARATION.
// Tests the prohibition of let declarations.

// breadth: reports | Banned let declaration defining macro expression
// pair: let_vs_assign
module b_rep_let (input logic [3:0] in, output logic [3:0] out);
    let inv(x) = ~x;
    assign out = inv(in);
endmodule

// breadth: clean | Inline continuous assignment without let
// pair: let_vs_assign
module b_clean_assign (input logic [3:0] in, output logic [3:0] out);
    assign out = ~in;
endmodule

// breadth: clean | Word let in comment or string literal
module b_clean_comment (input logic a, output logic b);
    // let declarations create parameterized expressions
    assign b = a;
    localparam string MSG = "let declaration banned";
endmodule

// breadth: reports | Banned let declaration in package
package b_pkg_let;
    let add_one(x) = x + 1;
endpackage

// breadth: reports | Banned let declaration with multiple arguments
module b_rep_multi_arg (input logic [3:0] a, b, output logic [3:0] y);
    let masked(val, mask) = val & mask;
    assign y = masked(a, b);
endmodule

// breadth: reports | Multiple let declarations in module
// expect: 2
module b_rep_count (input logic a, b, output logic y1, y2);
    let op_and(x, y) = x & y;
    let op_or(x, y) = x | y;
    assign y1 = op_and(a, b);
    assign y2 = op_or(a, b);
endmodule

// breadth: clean | Localparam and function declaration instead of let declaration
module b_clean_neighbor_let_alt (input logic [3:0] in, output logic [3:0] out);
    localparam int MASK = 4'hF;
    function automatic logic [3:0] apply_mask(logic [3:0] v);
        return v & MASK;
    endfunction
    assign out = apply_mask(in);
endmodule
