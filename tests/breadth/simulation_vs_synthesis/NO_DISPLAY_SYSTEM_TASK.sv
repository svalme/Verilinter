// Breadth tests for NO_DISPLAY_SYSTEM_TASK.
// Tests the prohibition of display system tasks ($display, $write, $strobe, $monitor).

// breadth: reports | Banned $display system task in procedural block
// pair: display_vs_assign
module b_rep_display (input logic clk, d);
    always_ff @(posedge clk) begin
        if (d)
            $display("Signal d asserted at time %0t", $time);
    end
endmodule

// breadth: clean | Module logic without display system tasks
// pair: display_vs_assign
module b_clean_no_display (input logic clk, d, output logic q);
    always_ff @(posedge clk) begin
        q <= d;
    end
endmodule

// breadth: clean | Word $display in comment or string literal
module b_clean_comment (input logic a, output logic b);
    // $display system task is for simulation output only
    assign b = a;
    localparam string MSG = "$display is banned in synthesizable RTL";
endmodule

// breadth: reports | Banned $write system task in generate block
module b_rep_generate_write (input logic clk, in);
    generate
        if (1) begin : g_blk
            always_ff @(posedge clk) begin
                if (in)
                    $write("Bit received\n");
            end
        end
    endgenerate
endmodule

// breadth: reports | Banned $strobe system task in initial block
module b_rep_strobe;
    initial begin
        $strobe("Initial strobe event");
    end
endmodule

// breadth: reports | Multiple display tasks in procedural block
// expect: 2
module b_rep_count (input logic clk);
    initial begin
        $display("Header line");
        $display("Footer line");
    end
endmodule

// breadth: clean | Constant system functions clog2 and bits instead of display task
module b_clean_neighbor_sysfuncs;
    localparam int W = $clog2(32);
    localparam int B = $bits(logic [7:0]);
endmodule
