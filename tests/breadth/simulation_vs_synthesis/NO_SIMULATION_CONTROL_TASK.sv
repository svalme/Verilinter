// Breadth tests for NO_SIMULATION_CONTROL_TASK.
// Tests the prohibition of simulation control tasks ($stop, $finish).

// breadth: reports | Banned $finish system task terminating simulation
// pair: finish_vs_error_signal
module b_rep_finish (input logic clk, err);
    always_ff @(posedge clk) begin
        if (err)
            $finish;
    end
endmodule

// breadth: clean | Error status flag instead of simulation termination task
// pair: finish_vs_error_signal
module b_clean_error_flag (input logic clk, err, output logic err_flag);
    always_ff @(posedge clk) begin
        if (err)
            err_flag <= 1'b1;
    end
endmodule

// breadth: clean | Word $finish in comment or string literal
module b_clean_comment (input logic a, output logic b);
    // $finish and $stop are simulation control primitives
    assign b = a;
    localparam string MSG = "$finish task banned in synthesizable RTL";
endmodule

// breadth: reports | Banned $stop system task pausing simulation
module b_rep_stop (input logic clk, break_cond);
    always_ff @(posedge clk) begin
        if (break_cond)
            $stop;
    end
endmodule

// breadth: reports | Banned $finish task nested in generate block
module b_rep_gen_finish (input logic clk, bad_state);
    generate
        if (1) begin : g_blk
            always_ff @(posedge clk) begin
                if (bad_state)
                    $finish();
            end
        end
    endgenerate
endmodule

// breadth: reports | Multiple simulation control tasks in procedural code
// expect: 2
module b_rep_count (input logic clk, e1, e2);
    always_ff @(posedge clk) begin
        if (e1)
            $stop;
        if (e2)
            $finish;
    end
endmodule

// breadth: clean | Display system task instead of simulation control task
module b_clean_neighbor_display (input logic clk);
    initial begin
        $display("Simulation running normally");
    end
endmodule
