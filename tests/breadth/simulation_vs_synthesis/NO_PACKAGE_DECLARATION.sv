// Breadth tests for NO_PACKAGE_DECLARATION.
// Tests the prohibition of package declarations.

// breadth: reports | Banned package declaration containing shared definitions
// pair: package_vs_module
package b_rep_pkg;
    parameter int WIDTH = 16;
endpackage

// breadth: clean | Module declaration with local parameters
// pair: package_vs_module
module b_clean_module (input logic clk, output logic q);
    localparam int WIDTH = 16;
    assign q = clk;
endmodule

// breadth: clean | Word package in comment or string literal
module b_clean_comment (input logic a, output logic b);
    // package declarations group common types and constants
    assign b = a;
    localparam string MSG = "package declaration banned";
endmodule

// breadth: reports | Banned package declaration with functions
package b_rep_math_pkg;
    function automatic int square(int val);
        return val * val;
    endfunction
endpackage

// breadth: reports | Banned package declaration with typedef
package b_rep_types_pkg;
    typedef logic [31:0] word_t;
endpackage

// breadth: reports | Multiple package declarations
// expect: 2
package b_rep_pkg_one;
    parameter int P1 = 1;
endpackage

package b_rep_pkg_two;
    parameter int P2 = 2;
endpackage
