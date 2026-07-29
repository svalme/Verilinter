module top;
  logic [3:0] arr;
  initial foreach (arr[i]) arr[i] = 1'b0;
endmodule
