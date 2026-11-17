// Breadth test suite for NO_RANDSEQUENCE
// Category: assertions_and_verification
//
// Tests detection of verification randsequence statements,
// contrasting with procedural case statements and loops.

// breadth: reports | Randsequence statement inside initial block is reported.
// pair: randsequence_vs_case
module m;
  initial begin
    randsequence(main)
      main : first second;
      first : { };
      second : { };
    endsequence
  end
endmodule

// breadth: clean | Procedural case statement is not reported.
// pair: randsequence_vs_case
module m(input [1:0] sel, output reg y);
  always_comb begin
    case (sel)
      2'd0:    y = 1'b0;
      default: y = 1'b1;
    endcase
  end
endmodule

// breadth: clean | Word randsequence inside comments is not reported.
module m;
  // randsequence
  wire w = 1'b0;
endmodule

// breadth: reports | Randsequence statement inside function body is reported.
module m;
  function void run_seq();
    randsequence(top_seq)
      top_seq : s1 s2;
      s1 : { };
      s2 : { };
    endsequence
  endfunction
endmodule

// breadth: reports | Multiple randsequence statements trigger multiple reports.
// expect: 2
module m;
  initial begin
    randsequence(seq_a)
      seq_a : a1;
      a1 : { };
    endsequence
    randsequence(seq_b)
      seq_b : b1;
      b1 : { };
    endsequence
  end
endmodule

// breadth: clean | Standard for-loop is clean for NO_RANDSEQUENCE.
module m;
  initial begin
    for (int i = 0; i < 4; i++) begin
    end
  end
endmodule

// breadth: clean | Procedural case statement instead of randsequence construct
module b_clean_neighbor_case (input logic [1:0] state, output logic [1:0] next_s);
    always_comb begin
        case (state)
            2'b00: next_s = 2'b01;
            2'b01: next_s = 2'b10;
            default: next_s = 2'b00;
        endcase
    end
endmodule
