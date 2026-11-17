// Breadth test suite for NO_SEQUENCE_DECLARATION
// Category: assertions_and_verification
//
// Tests detection of sequence declarations (sequence ... endsequence),
// contrasting with behavioral functions and property declarations.

// breadth: reports | Sequence declaration inside module is reported.
// pair: sequence_vs_function
module m(input clk, a);
  sequence s;
    @(posedge clk) a;
  endsequence
endmodule

// breadth: clean | Function declaration is not reported.
// pair: sequence_vs_function
module m(input a);
  function automatic logic check_val(input val);
    check_val = val;
  endfunction
endmodule

// breadth: clean | Word sequence inside comments is not reported.
module m;
  // sequence s_step
  wire w = 1'b0;
endmodule

// breadth: reports | Sequence declaration with arguments is reported.
module m(input clk, req, ack);
  sequence s_handshake(r, a);
    @(posedge clk) r ##1 a;
  endsequence
endmodule

// breadth: reports | Multiple sequence declarations trigger multiple reports.
// expect: 2
module m(input clk, a, b);
  sequence s1; @(posedge clk) a; endsequence
  sequence s2; @(posedge clk) b; endsequence
endmodule

// breadth: clean | Property declaration is clean for NO_SEQUENCE_DECLARATION.
module m(input clk, a);
  property p;
    @(posedge clk) a;
  endproperty
endmodule

// breadth: clean | Property declaration instead of sequence declaration
module b_clean_neighbor_prop (input logic clk, req, gnt);
    property p_handshake;
        @(posedge clk) req |-> gnt;
    endproperty
endmodule
