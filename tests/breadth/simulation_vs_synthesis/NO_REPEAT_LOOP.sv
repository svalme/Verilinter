// Breadth tests for NO_REPEAT_LOOP.
// Tests the prohibition of repeat loops.

// breadth: reports | Banned repeat loop in procedural block
// pair: repeat_vs_for
module b_rep_repeat (input logic clk, output int cnt);
    initial begin
        cnt = 0;
        repeat (10) begin
            cnt = cnt + 1;
        end
    end
endmodule

// breadth: clean | Procedural for loop replacing repeat construct
// pair: repeat_vs_for
module b_clean_for (input logic clk, output int cnt);
    always_comb begin
        cnt = 0;
        for (int i = 0; i < 10; i++) begin
            cnt = cnt + 1;
        end
    end
endmodule

// breadth: clean | Word repeat in comment or string literal
module b_clean_comment (input logic a, output logic b);
    // repeat loop is not allowed in synthesis
    assign b = a;
    localparam string MSG = "repeat statement banned";
endmodule

// breadth: reports | Banned repeat loop nested in generate block
module b_rep_generate (output int cnt);
    generate
        if (1) begin : g_blk
            initial begin
                cnt = 0;
                repeat (5) begin
                    cnt++;
                end
            end
        end
    endgenerate
endmodule

// breadth: reports | Banned repeat loop inside task
module b_rep_task (input logic clk, output logic done);
    task automatic wait_cycles(int n);
        repeat (n) @(posedge clk);
        done = 1'b1;
    endtask
endmodule

// breadth: reports | Multiple repeat loops in procedural block
// expect: 2
module b_rep_count (output int a, b);
    initial begin
        repeat (4) begin
            a++;
        end
        repeat (8) begin
            b++;
        end
    end
endmodule
