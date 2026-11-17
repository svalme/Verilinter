// Breadth tests for NO_WAIT_STATEMENT.
// Tests the prohibition of wait statements.

// breadth: reports | Banned wait statement with condition
// pair: wait_vs_if
module b_rep_wait (input logic ready, output logic done);
    initial begin
        wait (ready);
        done = 1'b1;
    end
endmodule

// breadth: clean | Procedural if condition with edge sensitivity
// pair: wait_vs_if
module b_clean_if (input logic clk, ready, output logic done);
    always_ff @(posedge clk) begin
        if (ready)
            done <= 1'b1;
    end
endmodule

// breadth: clean | Word wait in comment or string literal
module b_clean_comment (input logic a, output logic b);
    // wait statements are not synthesizable
    assign b = a;
    localparam string MSG = "wait statement banned";
endmodule

// breadth: reports | Banned wait statement nested in generate block
module b_rep_generate (input logic ready, output logic done);
    generate
        if (1) begin : g_blk
            initial begin
                wait (ready);
                done = 1'b1;
            end
        end
    endgenerate
endmodule

// breadth: reports | Banned wait statement inside task
module b_rep_task (input logic ack);
    task automatic wait_for_ack();
        wait (ack == 1'b1);
    endtask
endmodule

// breadth: reports | Multiple wait statements in procedural block
// expect: 2
module b_rep_count (input logic start, done);
    initial begin
        wait (start);
        wait (done);
    end
endmodule
