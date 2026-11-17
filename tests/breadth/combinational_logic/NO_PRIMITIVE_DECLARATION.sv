// Breadth test suite for NO_PRIMITIVE_DECLARATION
// Category: combinational_logic
//
// Tests detection of user-defined primitive (UDP) declarations (primitive ... endprimitive),
// contrasting with behavioral functions and standard module declarations.

// breadth: reports | Combinational user-defined primitive declaration is reported.
// pair: udp_vs_function
primitive udp_mux(output y, input sel, a, b);
  table
    0 1 ? : 1;
    0 0 ? : 0;
    1 ? 1 : 1;
    1 ? 0 : 0;
  endtable
endprimitive

// breadth: clean | Function implementing equivalent logic is not reported.
// pair: udp_vs_function
module m;
  function automatic logic func_mux(input sel, a, b);
    func_mux = sel ? b : a;
  endfunction
endmodule

// breadth: clean | Word primitive inside comments is not reported.
module m;
  // primitive udp_not
  wire w;
endmodule

// breadth: reports | Sequential user-defined primitive declaration with state table is reported.
primitive udp_dff(output reg q, input clk, d);
  initial q = 1'b0;
  table
    (01) 0 : ? : 0;
    (01) 1 : ? : 1;
    (?0) ? : ? : -;
  endtable
endprimitive

// breadth: reports | Multiple user-defined primitive declarations trigger multiple reports.
// expect: 2
primitive udp_inv(output y, input a);
  table
    0 : 1;
    1 : 0;
  endtable
endprimitive

primitive udp_buf(output y, input a);
  table
    0 : 0;
    1 : 1;
  endtable
endprimitive

// breadth: clean | Standard module declaration is not reported.
module standard_mod(input a, output y);
  assign y = ~a;
endmodule

// breadth: clean | Module declaration with gate primitive instead of UDP declaration
module b_clean_neighbor_udp_alt (input logic a, b, output logic y);
    and g1 (y, a, b);
endmodule
