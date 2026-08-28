module if_without_begin_end_example;
  reg x;

  always @(*) begin
    if (1'b1)
      x = 1'b0;
    else
      x = 1'b1;
  end
endmodule
