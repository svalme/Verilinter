// Breadth tests for NO_FORCE_RELEASE.
// Tests the prohibition of force and release statements.

// breadth: reports | Banned force statement in procedural block
// pair: force_vs_assign
module b_rep_force (input logic sig, output logic net_out);
    initial begin
        force net_out = sig;
    end
endmodule

// breadth: clean | Continuous assignment instead of force statement
// pair: force_vs_assign
module b_clean_assign (input logic sig, output logic net_out);
    assign net_out = sig;
endmodule

// breadth: clean | Word force or release in comment or string literal
module b_clean_comment (input logic a, output logic b);
    // force and release statements are simulation-only
    assign b = a;
    localparam string MSG = "force release prohibited";
endmodule

// breadth: reports | Banned release statement in procedural block
module b_rep_release (output logic net_out);
    initial begin
        release net_out;
    end
endmodule

// breadth: reports | Banned force statement inside task
module b_rep_task (input logic override_val, output logic target_net);
    task automatic apply_override();
        force target_net = override_val;
    endtask
endmodule

// breadth: reports | Multiple force and release statements in block
// expect: 2
module b_rep_count (input logic val, output logic net_out);
    initial begin
        force net_out = val;
        release net_out;
    end
endmodule
