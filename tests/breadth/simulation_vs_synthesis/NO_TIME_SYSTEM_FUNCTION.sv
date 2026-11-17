// Breadth tests for NO_TIME_SYSTEM_FUNCTION.
// Tests the prohibition of time system functions ($time, $realtime, $stime).

// breadth: reports | Banned $time system function sampling simulation time
// pair: time_vs_cycle_counter
module b_rep_time (input logic clk, output time cur_t);
    always_ff @(posedge clk) begin
        cur_t <= $time;
    end
endmodule

// breadth: clean | Cycle counter tracking elapsed clock periods
// pair: time_vs_cycle_counter
module b_clean_cycle_counter (input logic clk, output int cycles);
    always_ff @(posedge clk) begin
        cycles <= cycles + 1;
    end
endmodule

// breadth: clean | Word $time in comment or string literal
module b_clean_comment (input logic a, output logic b);
    // $time and $realtime query simulation engine clock
    assign b = a;
    localparam string MSG = "$time function banned";
endmodule

// breadth: reports | Banned $realtime system function
module b_rep_realtime (input logic clk, output real rt);
    always_ff @(posedge clk) begin
        rt = $realtime;
    end
endmodule

// breadth: reports | Banned $stime system function nested in generate
module b_rep_gen_stime (output int st);
    generate
        if (1) begin : g_blk
            initial begin
                st = $stime;
            end
        end
    endgenerate
endmodule

// breadth: reports | Multiple time system functions in module
// expect: 2
module b_rep_count (output time t1, t2);
    initial begin
        t1 = $time;
        t2 = $time;
    end
endmodule

// breadth: clean | Constant system function clog2 instead of time function
module b_clean_neighbor_clog2;
    localparam int PERIODS = $clog2(256);
endmodule
