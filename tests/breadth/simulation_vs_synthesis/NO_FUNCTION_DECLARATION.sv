// Breadth tests for NO_FUNCTION_DECLARATION.
// Tests the prohibition of function declarations.

// breadth: reports | Banned function declaration in module
// pair: function_vs_continuous
module b_rep_func (input logic [3:0] in, output logic [3:0] out);
    function automatic logic [3:0] invert(logic [3:0] val);
        return ~val;
    endfunction
    assign out = invert(in);
endmodule

// breadth: clean | Inline bitwise expression instead of function
// pair: function_vs_continuous
module b_clean_expr (input logic [3:0] in, output logic [3:0] out);
    assign out = ~in;
endmodule

// breadth: clean | Word function in comment or string literal
module b_clean_comment (input logic a, output logic b);
    // function declarations are disallowed by coding standard
    assign b = a;
    localparam string MSG = "function declaration banned";
endmodule

// breadth: reports | Banned function declaration in package
package b_pkg_func;
    function automatic int double_val(int x);
        return x * 2;
    endfunction
endpackage

// breadth: reports | Banned void function declaration
module b_rep_void_func (input logic clk);
    int cnt;
    function automatic void reset_cnt();
        cnt = 0;
    endfunction
endmodule

// breadth: reports | Multiple function declarations in module
// expect: 2
module b_rep_count (input logic a, b, output logic y1, y2);
    function automatic logic f_and(logic x, logic y);
        return x & y;
    endfunction

    function automatic logic f_or(logic x, logic y);
        return x | y;
    endfunction

    assign y1 = f_and(a, b);
    assign y2 = f_or(a, b);
endmodule

// breadth: clean | Task declaration instead of function declaration
module b_clean_neighbor_task (input logic clk, in, output logic out);
    task automatic update_val(input logic v);
        out = v;
    endtask
endmodule
