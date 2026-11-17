// Breadth tests for NO_DELAY_CONTROL.
// Tests the prohibition of delay control constructs.

// breadth: reports | Banned delay control in procedural statement
// pair: delay_control_vs_clocked
module b_rep_delay (output logic clk);
    initial begin
        #10 clk = 1'b1;
    end
endmodule

// breadth: clean | Clock-edge sensitivity instead of delay control
// pair: delay_control_vs_clocked
module b_clean_clocked (input logic clk, d, output logic q);
    always_ff @(posedge clk) begin
        q <= d;
    end
endmodule

// breadth: clean | Word hash delay in comment or string literal
module b_clean_comment (input logic a, output logic b);
    // delay control #n is not synthesizable in RTL
    assign b = a;
    localparam string MSG = "#10 delay control banned";
endmodule

// breadth: reports | Banned delay control inside continuous assignment
module b_rep_continuous_delay (input logic in, output logic out);
    assign #5 out = in;
endmodule

// breadth: reports | Banned delay control inside task
module b_rep_task (output logic tick);
    task automatic pulse();
        tick = 1'b1;
        #2 tick = 1'b0;
    endtask
endmodule

// breadth: reports | Multiple delay control constructs in procedural block
// expect: 2
module b_rep_count (output logic sig);
    initial begin
        #5 sig = 1'b1;
        #10 sig = 1'b0;
    end
endmodule

// breadth: clean | Event control and wait statement instead of delay control
module b_clean_neighbor_event (input logic clk, ready, d, output logic q);
    always @(posedge clk) begin
        q <= d;
    end
    initial begin
        wait (ready);
    end
endmodule
