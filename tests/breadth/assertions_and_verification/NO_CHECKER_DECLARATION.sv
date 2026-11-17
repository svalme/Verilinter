// Breadth test suite for NO_CHECKER_DECLARATION
// Category: assertions_and_verification
//
// Tests detection of checker declarations (checker ... endchecker),
// contrasting with standard modules, interfaces, and comments.

// breadth: reports | Checker declaration inside module is reported.
// pair: checker_vs_module
module m;
  checker chk;
  endchecker
endmodule

// breadth: clean | Declaration of standard module is not reported.
// pair: checker_vs_module
module standard_mod;
  wire w;
endmodule

// breadth: clean | Word checker inside comments is not reported.
module m;
  // checker chk_unit
  wire w = 1'b0;
endmodule

// breadth: reports | Checker declaration with port arguments is reported.
module m;
  checker param_chk (logic clk);
  endchecker
endmodule

// breadth: reports | Multiple checker declarations trigger multiple reports.
// expect: 2
module m;
  checker c1;
  endchecker
  checker c2;
  endchecker
endmodule

// breadth: clean | Interface declaration is clean for NO_CHECKER_DECLARATION.
interface iface_bus;
  logic clk;
endinterface

// breadth: clean | Standard module declaration with property instead of checker
module b_clean_neighbor_module (input logic clk, req);
    property p_req;
        @(posedge clk) req;
    endproperty
endmodule
