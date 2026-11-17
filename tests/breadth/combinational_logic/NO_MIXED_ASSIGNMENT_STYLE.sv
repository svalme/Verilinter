// Breadth test suite for NO_MIXED_ASSIGNMENT_STYLE
// Category: combinational_logic
//
// Tests detection of mixed blocking and non-blocking assignments within the same
// procedural block, contrasting with purely blocking or purely non-blocking blocks,
// separate procedural blocks, and for-loop idioms.

// breadth: reports | Mixed blocking and nonblocking assignments to the same signal in one block are reported.
// pair: p1
module mixed_same_signal (
    input  wire clk,
    input  wire d,
    output reg  q
);
  always_ff @(posedge clk) begin
    q = d;
    q <= ~d;
  end
endmodule

// breadth: clean | Multiple blocking assignments to the same signal in a combinational block are not reported.
// pair: p1
module blocking_same_signal (
    input  wire [3:0] in_val,
    output reg  [3:0] out_val
);
  always_comb begin
    out_val = in_val;
    out_val = out_val + 4'd1;
  end
endmodule

// breadth: reports | Mixed blocking and nonblocking assignments to different signals in one block are reported.
// pair: p2
module mixed_different_signals (
    input  wire clk,
    input  wire a,
    input  wire b,
    output reg  x,
    output reg  y
);
  always_ff @(posedge clk) begin
    x = a;
    y <= b;
  end
endmodule

// breadth: clean | Purely nonblocking assignments to different signals in a sequential block are not reported.
// pair: p2
module nonblocking_different_signals (
    input  wire clk,
    input  wire a,
    input  wire b,
    output reg  x,
    output reg  y
);
  always_ff @(posedge clk) begin
    x <= a;
    y <= b;
  end
endmodule

// breadth: reports | Nonblocking assignment followed by blocking assignment in one block is reported.
// pair: p3
module nonblocking_first_then_blocking (
    input  wire clk,
    input  wire a,
    input  wire b,
    output reg  x,
    output reg  y
);
  always_ff @(posedge clk) begin
    x <= a;
    y = b;
  end
endmodule

// breadth: clean | Purely blocking assignments in a combinational block are not reported.
// pair: p3
module all_blocking_combinational (
    input  wire a,
    input  wire b,
    output reg  x,
    output reg  y
);
  always_comb begin
    x = a;
    y = b;
  end
endmodule

// breadth: reports | Compound assignment += mixed with nonblocking assignment in one block is reported.
// pair: p4
module compound_mixed_with_nonblocking (
    input  wire       clk,
    input  wire [3:0] in_val,
    output reg  [3:0] a,
    output reg  [3:0] b
);
  always_ff @(posedge clk) begin
    a += in_val;
    b <= in_val;
  end
endmodule

// breadth: clean | Compound assignment with blocking assignment in a combinational block is not reported.
// pair: p4
module compound_with_blocking (
    input  wire [3:0] in_val,
    output reg  [3:0] a,
    output reg  [3:0] b
);
  always_comb begin
    a = in_val;
    b += 4'd2;
  end
endmodule

// breadth: reports | For-loop blocking step assignment mixed with nonblocking body assignment in always_ff is reported.
// pair: p5
module for_loop_mixed_with_nonblocking (
    input  wire clk,
    output reg  [3:0] arr [0:3]
);
  always_ff @(posedge clk) begin
    for (int i = 0; i < 4; i = i + 1) begin
      arr[i] <= 4'd0;
    end
  end
endmodule

// breadth: clean | For-loop step assignment with blocking body in a combinational block is not reported.
// pair: p5
module for_loop_blocking_body (
    input  wire [3:0] in_val,
    output reg  [3:0] arr [0:3]
);
  always_comb begin
    for (int i = 0; i < 4; i = i + 1) begin
      arr[i] = in_val;
    end
  end
endmodule

// breadth: clean | Separate procedural blocks with distinct assignment styles are not reported.
module separate_blocks_distinct_styles (
    input  wire clk,
    input  wire in_a,
    input  wire in_b,
    output reg  out_a,
    output reg  out_b
);
  always_comb begin
    out_a = in_a;
  end

  always_ff @(posedge clk) begin
    out_b <= in_b;
  end
endmodule

// breadth: clean | Continuous assignment outside procedural blocks is not reported.
module continuous_assignment_clean (
    input  wire a,
    output wire y
);
  assign y = a;
endmodule
