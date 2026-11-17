// breadth: reports | An instance of a module type not defined anywhere in the source is reported.
// pair: undefined-vs-defined-module
module top;
  missing_child u();
endmodule

// breadth: clean | An instance of a module declared earlier in the source is not reported.
// pair: undefined-vs-defined-module
module child;
endmodule
module top;
  child u();
endmodule

// breadth: reports | An instance of a module type that has no declaration in the file is reported.
// pair: undefined-vs-defined-later
module top;
  nonexistent_sub u();
endmodule

// breadth: clean | An instance of a module declared later in the same file is not reported.
// pair: undefined-vs-defined-later
module top;
  child u();
endmodule
module child;
endmodule

// breadth: reports | An instance of an unrecognized identifier as a module is reported.
// pair: undefined-vs-primitive-gate
module top(input a, input b, output y);
  custom_gate g1(y, a, b);
endmodule

// breadth: clean | An instantiation of a built-in gate primitive is not reported as an undefined module.
// pair: undefined-vs-primitive-gate
module top(input a, input b, output y);
  and g1(y, a, b);
endmodule

// breadth: reports | An instance of an undefined target name is reported.
// pair: undefined-vs-interface-instantiation
module top;
  missing_if ifc();
endmodule

// breadth: clean | An instantiation of a declared SystemVerilog interface is not reported as an undefined module.
// pair: undefined-vs-interface-instantiation
interface my_if;
  logic clk;
endinterface
module top;
  my_if ifc();
endmodule

// breadth: reports | An instance of a misspelled macro-generated module name is reported.
// pair: undefined-vs-macro-built-module
`define TARGET_MOD worker_sub
module `TARGET_MOD;
endmodule
module top;
  worker_sub_wrong u();
endmodule

// breadth: clean | An instantiation of a module declared using a preprocessor macro is not reported.
// pair: undefined-vs-macro-built-module
`define TARGET_MOD worker_sub
module `TARGET_MOD;
endmodule
module top;
  `TARGET_MOD u();
endmodule

// breadth: reports | Multiple instances of different undefined modules are reported.
// expect: 2
module top;
  bad_mod_a u1();
  bad_mod_b u2();
endmodule

// breadth: clean | An instantiation of a declared SystemVerilog program block is not reported.
program my_prog;
endprogram
module top;
  my_prog p();
endmodule

// breadth: clean | An instantiation of a declared user-defined primitive is not reported.
primitive udp(output o, input a, input b);
  table
    0 0 : 0;
    1 0 : 1;
    0 1 : 1;
    1 1 : 1;
  endtable
endprimitive
module top(input a, input b, output y);
  udp u1(y, a, b);
endmodule
