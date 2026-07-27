module top;
  initial fork
    a = 1'b0;
    b = 1'b1;
  join

  initial fork
    c = 1'b0;
  join_any

  initial fork
    d = 1'b1;
  join_none
endmodule
