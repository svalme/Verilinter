// Breadth tests for NO_PLUSARGS_SYSTEM_FUNCTION.
// Tests the prohibition of plusargs system functions ($test$plusargs, $value$plusargs).

// breadth: reports | Banned $test$plusargs system function checking runtime flag
// pair: plusargs_vs_parameter
module b_rep_test_plusargs (output logic dbg_en);
    initial begin
        dbg_en = $test$plusargs("DEBUG");
    end
endmodule

// breadth: clean | Design parameter used instead of command-line plusargs
// pair: plusargs_vs_parameter
module b_clean_parameter #(parameter bit DEBUG = 0) (output logic dbg_en);
    assign dbg_en = DEBUG;
endmodule

// breadth: clean | Word $test$plusargs in comment or string literal
module b_clean_comment (input logic a, output logic b);
    // $test$plusargs reads simulation command-line switches
    assign b = a;
    localparam string MSG = "$test$plusargs is banned";
endmodule

// breadth: reports | Banned $value$plusargs system function reading string argument
module b_rep_value_plusargs (output int timeout);
    initial begin
        void'($value$plusargs("TIMEOUT=%d", timeout));
    end
endmodule

// breadth: reports | Banned $test$plusargs nested in generate block
module b_rep_gen_plusargs (output logic cfg_flag);
    generate
        if (1) begin : g_blk
            initial begin
                cfg_flag = $test$plusargs("FAST_SIM");
            end
        end
    endgenerate
endmodule

// breadth: reports | Multiple plusargs system function calls
// expect: 2
module b_rep_count (output logic f1, f2);
    initial begin
        f1 = $test$plusargs("MODE_A");
        f2 = $test$plusargs("MODE_B");
    end
endmodule

// breadth: clean | System functions clog2 and display instead of plusargs query
module b_clean_neighbor_funcs;
    localparam int SZ = $clog2(16);
    initial begin
        $display("Buffer size: %0d", SZ);
    end
endmodule
