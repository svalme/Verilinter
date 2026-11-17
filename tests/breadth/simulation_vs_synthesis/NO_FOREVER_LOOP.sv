// Breadth tests for NO_FOREVER_LOOP.
// Tests the prohibition of forever loops.

// breadth: reports | Banned forever loop in initial block
// pair: forever_vs_always
module b_rep_forever (output logic clk);
    initial begin
        clk = 1'b0;
        forever begin
            #5 clk = ~clk;
        end
    end
endmodule

// breadth: clean | Standard always block instead of forever loop
// pair: forever_vs_always
module b_clean_always (input logic clk, d, output logic q);
    always_ff @(posedge clk) begin
        q <= d;
    end
endmodule

// breadth: clean | Word forever in comment or string literal
module b_clean_comment (input logic a, output logic b);
    // forever loop is non-synthesizable
    assign b = a;
    localparam string MSG = "forever statement prohibited";
endmodule

// breadth: reports | Banned forever loop nested in generate block
module b_rep_generate (output logic clk);
    generate
        if (1) begin : g_blk
            initial begin
                clk = 1'b0;
                forever begin
                    #10 clk = ~clk;
                end
            end
        end
    endgenerate
endmodule

// breadth: reports | Banned forever loop inside task
module b_rep_task (output logic sig);
    task automatic run_toggle();
        forever begin
            #2 sig = ~sig;
        end
    endtask
endmodule

// breadth: reports | Multiple forever loops in block
// expect: 2
module b_rep_count (output logic c1, c2);
    initial begin
        fork
            forever #5 c1 = ~c1;
            forever #10 c2 = ~c2;
        join
    end
endmodule
