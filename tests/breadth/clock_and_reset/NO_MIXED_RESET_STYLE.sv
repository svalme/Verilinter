// Breadth test suite for NO_MIXED_RESET_STYLE
// Category: clock_and_reset
//
// Tests detection of mixed synchronous- and asynchronous-reset styles across
// sequential procedural blocks within the same module, contrasting with
// homogeneous reset styles, multi-module separation, and combinational blocks.

// breadth: reports | Synchronous and asynchronous reset blocks combined in the same module are reported.
// pair: p1
module mixed_sync_and_async_in_module (
    input  wire clk,
    input  wire rst_n,
    input  wire d1,
    input  wire d2,
    output reg  q1,
    output reg  q2
);
  // Block 1: synchronous reset style (1 edge event)
  always_ff @(posedge clk) begin
    if (!rst_n) q1 <= 1'b0;
    else        q1 <= d1;
  end

  // Block 2: asynchronous reset style (2 edge events)
  always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) q2 <= 1'b0;
    else        q2 <= d2;
  end
endmodule

// breadth: clean | Module containing only a synchronous reset block is not reported.
// pair: p1
module separate_module_sync_only (
    input  wire clk,
    input  wire rst_n,
    input  wire d,
    output reg  q
);
  always_ff @(posedge clk) begin
    if (!rst_n) q <= 1'b0;
    else        q <= d;
  end
endmodule

// breadth: clean | Module containing only an asynchronous reset block is not reported.
module separate_module_async_only (
    input  wire clk,
    input  wire rst_n,
    input  wire d,
    output reg  q
);
  always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) q <= 1'b0;
    else        q <= d;
  end
endmodule

// breadth: reports | Synchronous block followed by asynchronous block is reported.
// pair: p2
module sync_first_then_async (
    input  wire clk,
    input  wire rst,
    input  wire d1,
    input  wire d2,
    output reg  q1,
    output reg  q2
);
  always @(posedge clk) begin
    if (rst) q1 <= 1'b0;
    else     q1 <= d1;
  end

  always @(posedge clk or posedge rst) begin
    if (rst) q2 <= 1'b0;
    else     q2 <= d2;
  end
endmodule

// breadth: clean | Multiple homogeneous synchronous reset blocks are not reported.
// pair: p2
module homogeneous_sync_blocks (
    input  wire clk,
    input  wire rst,
    input  wire d1,
    input  wire d2,
    output reg  q1,
    output reg  q2
);
  always @(posedge clk) begin
    if (rst) q1 <= 1'b0;
    else     q1 <= d1;
  end

  always @(posedge clk) begin
    if (rst) q2 <= 1'b0;
    else     q2 <= d2;
  end
endmodule

// breadth: reports | Asynchronous block followed by synchronous block is reported.
// pair: p3
module async_first_then_sync (
    input  wire clk,
    input  wire rst_n,
    input  wire d1,
    input  wire d2,
    output reg  q1,
    output reg  q2
);
  always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) q1 <= 1'b0;
    else        q1 <= d1;
  end

  always_ff @(posedge clk) begin
    if (!rst_n) q2 <= 1'b0;
    else        q2 <= d2;
  end
endmodule

// breadth: clean | Multiple homogeneous asynchronous reset blocks are not reported.
// pair: p3
module homogeneous_async_blocks (
    input  wire clk,
    input  wire rst_n,
    input  wire d1,
    input  wire d2,
    output reg  q1,
    output reg  q2
);
  always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) q1 <= 1'b0;
    else        q1 <= d1;
  end

  always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) q2 <= 1'b0;
    else        q2 <= d2;
  end
endmodule

// breadth: reports | Two synchronous blocks followed by an asynchronous third block are reported.
// pair: p4
module three_blocks_with_mismatch (
    input  wire clk,
    input  wire rst_n,
    input  wire d1,
    input  wire d2,
    input  wire d3,
    output reg  q1,
    output reg  q2,
    output reg  q3
);
  always_ff @(posedge clk) begin
    q1 <= d1;
  end

  always_ff @(posedge clk) begin
    q2 <= d2;
  end

  always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) q3 <= 1'b0;
    else        q3 <= d3;
  end
endmodule

// breadth: clean | Different active polarities in asynchronous blocks share the 2-edge style and are not reported.
// pair: p4
module mixed_active_levels_both_async (
    input  wire clk,
    input  wire rst_high,
    input  wire rst_low_n,
    input  wire d1,
    input  wire d2,
    output reg  q1,
    output reg  q2
);
  // Both blocks have 2 edge events (async style), even with different polarities
  always_ff @(posedge clk or posedge rst_high) begin
    if (rst_high) q1 <= 1'b0;
    else          q1 <= d1;
  end

  always_ff @(posedge clk or negedge rst_low_n) begin
    if (!rst_low_n) q2 <= 1'b0;
    else            q2 <= d2;
  end
endmodule

// breadth: clean | Synchronous sequential block mixed with combinational block is not reported.
module sync_with_combinational_block (
    input  wire clk,
    input  wire d,
    output reg  q,
    output reg  comb_out
);
  always_ff @(posedge clk) begin
    q <= d;
  end

  always_comb begin
    comb_out = ~d;
  end
endmodule

// breadth: clean | Single sequential block with reset is not reported.
module single_reset_used_one_style (
    input  wire clk,
    input  wire rst,
    input  wire d,
    output reg  q
);
  always_ff @(posedge clk) begin
    if (rst) q <= 1'b0;
    else     q <= d;
  end
endmodule
