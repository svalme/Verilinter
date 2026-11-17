// Breadth tests for NO_DPI_IMPORT_EXPORT.
// Tests the prohibition of DPI-C import and export declarations.

// breadth: reports | Banned DPI-C function import declaration
// pair: dpi_vs_pure_verilog
module b_rep_dpi_import;
    import "DPI-C" function int c_math(input int val);
endmodule

// breadth: clean | Native SystemVerilog function instead of foreign DPI import
// pair: dpi_vs_pure_verilog
module b_clean_native_func (input int in_val, output int out_val);
    function automatic int sv_math(input int val);
        return val + 1;
    endfunction
    assign out_val = sv_math(in_val);
endmodule

// breadth: clean | Word DPI-C in comment or string literal
module b_clean_comment (input logic a, output logic b);
    // DPI-C import and export are non-synthesizable foreign interfaces
    assign b = a;
    localparam string MSG = "DPI-C import export banned";
endmodule

// breadth: reports | Banned DPI-C function export declaration
module b_rep_dpi_export;
    function automatic int get_status();
        return 0;
    endfunction
    export "DPI-C" function get_status;
endmodule

// breadth: reports | Banned DPI-C task import
module b_rep_dpi_task;
    import "DPI-C" task c_log_event(input string msg);
endmodule

// breadth: reports | Multiple DPI declarations in module
// expect: 2
module b_rep_count;
    import "DPI-C" function int c_calc1(input int a);
    import "DPI-C" function int c_calc2(input int b);
endmodule

// breadth: clean | Native package import instead of DPI-C foreign import
package b_clean_native_pkg;
    localparam int VER = 1;
endpackage

module b_clean_neighbor_pkg_import;
    import b_clean_native_pkg::*;
endmodule
