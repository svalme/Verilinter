// Breadth test suite for NO_PROPERTY_DECLARATION
// Category: assertions_and_verification
//
// Tests detection of property declarations (property ... endproperty),
// contrasting with behavioral functions and sequence declarations.

// breadth: reports | Property declaration inside module is reported.
// pair: property_vs_function
module m(input clk, a);
  property p;
    @(posedge clk) a;
  endproperty
endmodule

// breadth: clean | Function declaration is not reported.
// pair: property_vs_function
module m(input a);
  function automatic logic check_val(input val);
    check_val = val;
  endfunction
endmodule

// breadth: clean | Word property inside comments is not reported.
module m;
  // property p_req_ack
  wire w = 1'b0;
endmodule

// breadth: reports | Property declaration with formal arguments is reported.
module m(input clk, req, ack);
  property p_handshake(r, a);
    @(posedge clk) r |-> a;
  endproperty
endmodule

// breadth: reports | Multiple property declarations trigger multiple reports.
// expect: 2
module m(input clk, a, b);
  property p1; @(posedge clk) a; endproperty
  property p2; @(posedge clk) b; endproperty
endmodule

// breadth: clean | Sequence declaration is clean for NO_PROPERTY_DECLARATION.
module m(input clk, a);
  sequence s;
    @(posedge clk) a;
  endsequence
endmodule

// breadth: clean | Sequence declaration instead of property declaration
module b_clean_neighbor_seq (input logic clk, a, b);
    sequence s_ab;
        @(posedge clk) a ##1 b;
    endsequence
endmodule
