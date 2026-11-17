// Breadth tests for NO_TASK_DECLARATION.
// Tests the prohibition of task declarations.

// breadth: reports | Banned task declaration inside module
// pair: task_vs_always
module b_rep_task (input logic clk, in, output logic out);
    task automatic set_out(input logic val);
        out = val;
    endtask
endmodule

// breadth: clean | Procedural assignment block without task
// pair: task_vs_always
module b_clean_always (input logic clk, in, output logic out);
    always_comb begin
        out = in;
    end
endmodule

// breadth: clean | Word task in comment or string literal
module b_clean_comment (input logic a, output logic b);
    // task declarations are non-synthesizable routines
    assign b = a;
    localparam string MSG = "task declaration is banned";
endmodule

// breadth: reports | Banned task declaration inside package
package b_pkg_task;
    task automatic log_msg(input string s);
        $display("%s", s);
    endtask
endpackage

// breadth: reports | Banned task declaration inside interface
interface b_itf_task (input logic clk);
    task automatic wait_cycle();
        @(posedge clk);
    endtask
endinterface

// breadth: reports | Multiple task declarations in module
// expect: 2
module b_rep_count (output logic a, b);
    task automatic clear_a();
        a = 1'b0;
    endtask

    task automatic clear_b();
        b = 1'b0;
    endtask
endmodule

// breadth: clean | Function declaration instead of task declaration
module b_clean_neighbor_func (input logic [3:0] in, output logic [3:0] out);
    function automatic logic [3:0] compute(logic [3:0] v);
        return v + 1'b1;
    endfunction
    assign out = compute(in);
endmodule
