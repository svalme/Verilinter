// breadth: reports | A while loop with constant true condition and no exit or delay is reported.
// pair: while-1-no-exit-vs-break
module top;
  logic [7:0] count;
  initial begin
    while (1) count = count + 1;
  end
endmodule

// breadth: clean | A while (1) loop containing a conditional break statement is not reported.
// pair: while-1-no-exit-vs-break
module top;
  logic [7:0] count;
  initial begin
    while (1) begin
      count = count + 1;
      if (count == 10) break;
    end
  end
endmodule

// breadth: reports | A forever loop with no timing control or delay is reported.
// pair: forever-no-delay-vs-with-delay
module top;
  logic [7:0] count;
  initial begin
    forever count = count + 1;
  end
endmodule

// breadth: clean | A forever loop containing a timing delay statement is not reported.
// pair: forever-no-delay-vs-with-delay
module top;
  logic clk;
  initial begin
    forever #5 clk = ~clk;
  end
endmodule

// breadth: reports | A for loop with an omitted condition expression is reported.
// pair: for-omitted-condition-vs-standard-for
module top;
  logic [7:0] count;
  initial begin
    for (int i = 0; ; i = i + 1) begin
      count = count + 1;
    end
  end
endmodule

// breadth: clean | A for loop with a standard variable termination condition is not reported.
// pair: for-omitted-condition-vs-standard-for
module top;
  logic [7:0] count;
  initial begin
    for (int i = 0; i < 10; i = i + 1) begin
      count = count + 1;
    end
  end
endmodule

// breadth: reports | A while loop with true condition and no exit statement is reported.
// pair: while-1-no-exit-vs-finish
module top;
  logic [7:0] count;
  initial begin
    while (1) count = count + 1;
  end
endmodule

// breadth: clean | A while (1) loop containing a system finish call is not reported.
// pair: while-1-no-exit-vs-finish
module top;
  logic [7:0] count;
  initial begin
    while (1) begin
      count = count + 1;
      if (count == 10) $finish;
    end
  end
endmodule

// breadth: reports | A do-while loop with constant true condition and no exit statement is reported.
// pair: do-while-no-exit-vs-break
module top;
  logic [7:0] count;
  initial begin
    do count = count + 1; while (1);
  end
endmodule

// breadth: clean | A do-while (1) loop containing a conditional break statement is not reported.
// pair: do-while-no-exit-vs-break
module top;
  logic [7:0] count;
  initial begin
    do begin
      count = count + 1;
      if (count == 10) break;
    end while (1);
  end
endmodule

// breadth: reports | A while loop with sized literal true condition without exit is reported.
module top;
  logic [7:0] count;
  initial begin
    while (1'b1) count = count + 1;
  end
endmodule

// breadth: clean | A while loop whose condition expression is modified within the loop body is not reported.
module top;
  logic [7:0] count;
  initial begin
    count = 0;
    while (count < 10) begin
      count = count + 1;
    end
  end
endmodule
