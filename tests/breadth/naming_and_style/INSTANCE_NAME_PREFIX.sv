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

// breadth: clean | A gate primitive instance is not a module instance and is not reported.
// pair: gate-primitive
module top(input a, input b, output o);
  and a1(o, a, b);
endmodule

// breadth: reports | A module instance in a module that also holds a gate primitive is reported by its own name.
// pair: gate-primitive
module sub;
endmodule
module top(input a, input b, output o);
  and a1(o, a, b);
  sub block_a();
endmodule

// breadth: gap | A user-defined primitive instance is reported because slang parses it as a module instantiation; the rule cannot tell it apart without resolving the name.
// expect: 0
primitive inv(output o, input a);
  table 0 : 1; 1 : 0; endtable
endprimitive
module top(input a, output o);
  inv i1x(o, a);
endmodule
