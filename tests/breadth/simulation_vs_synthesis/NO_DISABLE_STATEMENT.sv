// Breadth tests for NO_DISABLE_STATEMENT.
// Tests the prohibition of disable statements.

// breadth: reports | Banned disable statement targeting named block
// pair: disable_vs_break
module b_rep_disable (input logic clk, in, output logic out);
    always_comb begin : blk
        out = in;
        if (in)
            disable blk;
    end
endmodule

// breadth: clean | Break statement replacing block disable
// pair: disable_vs_break
module b_clean_break (input logic clk, in, output logic out);
    always_comb begin
        out = in;
        for (int i = 0; i < 4; i++) begin
            if (in)
                break;
        end
    end
endmodule

// breadth: clean | Word disable in comment or string literal
module b_clean_comment (input logic a, output logic b);
    // disable statement is not supported in synthesis
    assign b = a;
    localparam string MSG = "disable statement banned";
endmodule

// breadth: reports | Banned disable fork statement
module b_rep_disable_fork (output logic a);
    initial begin
        fork
            #10 a = 1'b1;
        join_any
        disable fork;
    end
endmodule

// breadth: reports | Banned disable statement inside task
module b_rep_task (input logic stop);
    task automatic do_work();
        begin : work_blk
            if (stop)
                disable work_blk;
        end
    endtask
endmodule

// breadth: reports | Multiple disable statements in block
// expect: 2
module b_rep_count (input logic a, b);
    initial begin : main_blk
        if (a)
            disable main_blk;
        if (b)
            disable main_blk;
    end
endmodule
