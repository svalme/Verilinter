// Breadth tests for NO_EVENT_TRIGGER.
// Tests the prohibition of named event triggers.

// breadth: reports | Banned named event trigger operator
// pair: event_trigger_vs_logic_signal
module b_rep_event_trigger (input logic clk);
    event done_ev;
    initial begin
        -> done_ev;
    end
endmodule

// breadth: clean | Logic signal toggle replacing event trigger
// pair: event_trigger_vs_logic_signal
module b_clean_logic_signal (input logic clk, output logic done_sig);
    always_ff @(posedge clk) begin
        done_sig <= 1'b1;
    end
endmodule

// breadth: clean | Word event trigger in comment or string literal
module b_clean_comment (input logic a, output logic b);
    // named event trigger operator -> is non-synthesizable
    assign b = a;
    localparam string MSG = "event trigger banned";
endmodule

// breadth: reports | Banned nonblocking event trigger
module b_rep_nonblocking_trigger (input logic clk);
    event tick_ev;
    initial begin
        ->> tick_ev;
    end
endmodule

// breadth: reports | Banned event trigger nested in generate block
module b_rep_generate (input logic clk);
    event g_ev;
    generate
        if (1) begin : g_blk
            initial begin
                -> g_ev;
            end
        end
    endgenerate
endmodule

// breadth: reports | Multiple event triggers in procedural block
// expect: 2
module b_rep_count (input logic clk);
    event e1, e2;
    initial begin
        -> e1;
        -> e2;
    end
endmodule
