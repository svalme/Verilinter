// Breadth tests for CLOCK_SIGNAL_NAMING
// Rule: Flags synchronous procedural blocks whose clock signal is not named 'clk' or suffixed with '_clk'.

// breadth: reports | Synchronous always block clocked by clock is reported because it is not named clk or suffixed with _clk.
// pair: bare_name
module sync_clock_bare_clock(input clock, output reg q);
  always @(posedge clock) begin
    q <= 1'b0;
  end
endmodule

// breadth: clean | Synchronous always block clocked by clk is not reported.
// pair: bare_name
module sync_clock_bare_clk(input clk, output reg q);
  always @(posedge clk) begin
    q <= 1'b0;
  end
endmodule

// breadth: reports | Clock signal clk_sys with clk prefix rather than _clk suffix is reported.
// pair: suffix_convention
module sync_clock_prefix_only(input clk_sys, output reg q);
  always @(posedge clk_sys) begin
    q <= 1'b0;
  end
endmodule

// breadth: clean | Clock signal sys_clk ending with _clk suffix is not reported.
// pair: suffix_convention
module sync_clock_suffixed_clk(input sys_clk, output reg q);
  always @(posedge sys_clk) begin
    q <= 1'b0;
  end
endmodule

// breadth: reports | Synchronous always_ff block clocked by single-letter signal c is reported.
// pair: always_ff_clock
module sync_always_ff_single_letter(input c, output logic q);
  always_ff @(posedge c) begin
    q <= 1'b0;
  end
endmodule

// breadth: clean | Synchronous always_ff block clocked by clk is not reported.
// pair: always_ff_clock
module sync_always_ff_clk(input clk, output logic q);
  always_ff @(posedge clk) begin
    q <= 1'b0;
  end
endmodule

// breadth: reports | Negedge synchronous clock ck without clk name or _clk suffix is reported.
// pair: negedge_clock
module sync_clock_negedge_ck(input ck, output reg q);
  always @(negedge ck) begin
    q <= 1'b0;
  end
endmodule

// breadth: clean | Negedge synchronous clock bus_clk with _clk suffix is not reported.
// pair: negedge_clock
module sync_clock_negedge_clk(input bus_clk, output reg q);
  always @(negedge bus_clk) begin
    q <= 1'b0;
  end
endmodule

// breadth: clean | Asynchronous block with two edge events is not reported because clock cannot be uniquely distinguished.
module async_reset_block_ignored(input clock, input rst_n, output reg q);
  always @(posedge clock or negedge rst_n) begin
    if (!rst_n) q <= 1'b0;
    else q <= 1'b1;
  end
endmodule

// breadth: clean | Combinational always_comb block without edge events is not reported.
module comb_always_ignored(input a, output reg y);
  always_comb begin
    y = a;
  end
endmodule
