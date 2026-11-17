// Breadth tests for NO_VCD_DUMP_TASK.
// Tests the prohibition of VCD dump system tasks ($dumpfile, $dumpvars, etc.).

// breadth: reports | Banned $dumpfile system task opening trace file
// pair: dump_vs_probe
module b_rep_dumpfile;
    initial begin
        $dumpfile("waves.vcd");
    end
endmodule

// breadth: clean | Direct debug probe port without VCD dump tasks
// pair: dump_vs_probe
module b_clean_probe (input logic clk, d, output logic probe_sig);
    assign probe_sig = d;
endmodule

// breadth: clean | Word $dumpfile in comment or string literal
module b_clean_comment (input logic a, output logic b);
    // $dumpfile and $dumpvars configure simulation waveform dumps
    assign b = a;
    localparam string MSG = "$dumpfile is banned in synthesizable RTL";
endmodule

// breadth: reports | Banned $dumpvars system task enabling signal tracing
module b_rep_dumpvars;
    initial begin
        $dumpvars(0, b_rep_dumpvars);
    end
endmodule

// breadth: reports | Banned $dumpall task inside generate block
module b_rep_gen_dumpall;
    generate
        if (1) begin : g_blk
            initial begin
                $dumpall;
            end
        end
    endgenerate
endmodule

// breadth: reports | Multiple VCD dump tasks in initial block
// expect: 2
module b_rep_count;
    initial begin
        $dumpfile("test.vcd");
        $dumpvars;
    end
endmodule

// breadth: clean | Display system task and clog2 instead of vcd dump task
module b_clean_neighbor_display;
    localparam int W = $clog2(64);
    initial begin
        $display("Width: %0d", W);
    end
endmodule
