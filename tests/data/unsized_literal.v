module unsized_literal_example;
  reg [7:0] x;

  always @(*) begin
    x = 5;
  end
endmodule
