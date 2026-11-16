// breadth: reports | An instance name not prefixed with u_ or i_ is reported.
// pair: u-prefix
module sub;
endmodule
module top;
  sub dut();
endmodule

// breadth: clean | An instance name prefixed with u_ is not reported.
// pair: u-prefix
module sub;
endmodule
module top;
  sub u_dut();
endmodule

// breadth: reports | An instance named without a prefix is reported.
// pair: i-prefix
module sub;
endmodule
module top;
  sub block_a();
endmodule

// breadth: clean | An instance name prefixed with i_ is not reported.
// pair: i-prefix
module sub;
endmodule
module top;
  sub i_block_a();
endmodule

// breadth: reports | An instance named u0 without an underscore separator is reported.
// pair: bare-u-digit
module sub;
endmodule
module top;
  sub u0();
endmodule

// breadth: clean | An instance named u_0 with the underscore separator is not reported.
// pair: bare-u-digit
module sub;
endmodule
module top;
  sub u_0();
endmodule

// breadth: reports | An instance array named without a u_ or i_ prefix is reported.
// pair: array-of-instances
module sub;
endmodule
module top;
  sub arr[1:0]();
endmodule

// breadth: clean | An instance array with a u_ prefix is not reported.
// pair: array-of-instances
module sub;
endmodule
module top;
  sub u_arr[1:0]();
endmodule

// breadth: gap | Gate primitive instantiations are reported although primitive gates are not module instances.
// expect: 0
module top(input a, input b, output o);
  and a1(o, a, b);
endmodule
