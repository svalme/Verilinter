// breadth: reports | An always_latch block with an unconditional assignment is reported.
// pair: unconditional-vs-conditional-latch
module top(input a, output logic y);
  always_latch begin
    y = a;
  end
endmodule

// breadth: clean | An always_latch block with an enable condition and no else branch is not reported.
// pair: unconditional-vs-conditional-latch
module top(input en, input d, output logic q);
  always_latch begin
    if (en) q = d;
  end
endmodule

// breadth: reports | An always_latch block with a complete if-else statement is reported.
// pair: complete-if-else-vs-single-branch-if
module top(input en, input a, input b, output logic y);
  always_latch begin
    if (en) y = a;
    else y = b;
  end
endmodule

// breadth: clean | An always_latch block with a single-branch if statement is not reported.
// pair: complete-if-else-vs-single-branch-if
module top(input en, input a, output logic y);
  always_latch begin
    if (en) y = a;
  end
endmodule

// breadth: reports | An always_latch block with a complete case statement with a default branch is reported.
// pair: complete-case-vs-incomplete-case
module top(input [1:0] sel, input a, input b, output logic q);
  always_latch begin
    case (sel)
      2'b00: q = a;
      default: q = b;
    endcase
  end
endmodule

// breadth: clean | An always_latch block with an incomplete case statement without a default branch is not reported.
// pair: complete-case-vs-incomplete-case
module top(input [1:0] sel, input d, output logic q);
  always_latch begin
    case (sel)
      2'b00: q = d;
    endcase
  end
endmodule

// breadth: reports | An always_latch block describing purely combinational logic is reported.
// pair: always-latch-vs-always-comb
module top(input a, input b, output logic y);
  always_latch begin
    y = a & b;
  end
endmodule

// breadth: clean | An always_comb block describing purely combinational logic is not reported.
// pair: always-latch-vs-always-comb
module top(input a, input b, output logic y);
  always_comb begin
    y = a & b;
  end
endmodule

// breadth: reports | An always_latch block with a complete ternary assignment is reported.
module top(input en, input a, input b, output logic y);
  always_latch begin
    y = en ? a : b;
  end
endmodule

// breadth: clean | An always_latch block with an incomplete nested if structure is not reported.
module top(input en1, input en2, input d, output logic q);
  always_latch begin
    if (en1) begin
      if (en2) q = d;
    end
  end
endmodule

// breadth: clean | An always_latch block with constant enable condition and no else branch is not reported.
module top(input d, output logic q);
  always_latch begin
    if (1'b1) q = d;
  end
endmodule
