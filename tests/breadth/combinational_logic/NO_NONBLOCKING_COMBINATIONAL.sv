// breadth: reports | Nonblocking assignment in an always_comb block is reported.
// pair: nonblocking-vs-blocking-in-always-comb
module top(input a, output logic y);
  always_comb begin
    y <= a;
  end
endmodule

// breadth: clean | Blocking assignment in an always_comb block is not reported.
// pair: nonblocking-vs-blocking-in-always-comb
module top(input a, output logic y);
  always_comb begin
    y = a;
  end
endmodule

// breadth: reports | Nonblocking assignment in an always @* block is reported.
// pair: nonblocking-at-star-vs-clocked-always
module top(input a, output logic y);
  always @* begin
    y <= a;
  end
endmodule

// breadth: clean | Nonblocking assignment in an always @(posedge clk) block is not reported.
// pair: nonblocking-at-star-vs-clocked-always
module top(input clk, input d, output logic q);
  always @(posedge clk) begin
    q <= d;
  end
endmodule

// breadth: reports | Nonblocking assignment in an always block with explicit combinational sensitivity is reported.
// pair: nonblocking-explicit-comb-vs-always-ff
module top(input a, output logic y);
  always @(a) begin
    y <= a;
  end
endmodule

// breadth: clean | Nonblocking assignment in an always_ff @(posedge clk) block is not reported.
// pair: nonblocking-explicit-comb-vs-always-ff
module top(input clk, input d, output logic q);
  always_ff @(posedge clk) begin
    q <= d;
  end
endmodule

// breadth: reports | Nonblocking assignment with intra-assignment delay in an always_comb block is reported.
// pair: intra-assignment-delay-comb-vs-seq
module top(input a, output logic y);
  always_comb begin
    y <= #1 a;
  end
endmodule

// breadth: clean | Nonblocking assignment with intra-assignment delay in an always_ff block is not reported.
// pair: intra-assignment-delay-comb-vs-seq
module top(input clk, input d, output logic q);
  always_ff @(posedge clk) begin
    q <= #1 d;
  end
endmodule

// breadth: reports | Nonblocking assignment inside a conditional branch of an always_comb block is reported.
module top(input en, input a, output logic y);
  always_comb begin
    if (en) y <= a;
    else y = 1'b0;
  end
endmodule

// breadth: reports | Multiple nonblocking assignments in an always_comb block are reported.
// expect: 2
module top(input a, input b, output logic y, output logic z);
  always_comb begin
    y <= a;
    z <= b;
  end
endmodule

// breadth: clean | Blocking assignment in an always @* block is not reported.
module top(input a, output logic y);
  always @* begin
    y = a;
  end
endmodule

// breadth: clean | A clocked block with mixed clock and combinational event list is not reported by the combinational nonblocking rule.
module top(input clk, input a, output logic q);
  always @(posedge clk or a) begin
    q <= a;
  end
endmodule
