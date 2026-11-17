// Breadth tests for NO_PROGRAM_DECLARATION.
// Tests the prohibition of program block declarations.

// breadth: reports | Banned program declaration for testbench execution
// pair: program_vs_module
program b_rep_prog (input logic clk);
    initial begin
        $display("Test started");
    end
endprogram

// breadth: clean | Module declaration instead of program construct
// pair: program_vs_module
module b_clean_module (input logic clk);
    initial begin
        $display("Module initialized");
    end
endmodule

// breadth: clean | Word program in comment or string literal
module b_clean_comment (input logic a, output logic b);
    // program blocks create reactive region testbenches
    assign b = a;
    localparam string MSG = "program construct banned";
endmodule

// breadth: reports | Banned automatic program declaration
program automatic b_rep_auto_prog;
    initial begin
        $display("Automatic testbench");
    end
endprogram

// breadth: reports | Banned program declaration with ports
program b_rep_port_prog (input logic clk, input logic rst_n);
    initial begin
        $display("Program with ports");
    end
endprogram

// breadth: reports | Multiple program declarations
// expect: 2
program b_rep_prog_1;
    initial $display("Prog 1");
endprogram

program b_rep_prog_2;
    initial $display("Prog 2");
endprogram
