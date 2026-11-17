// breadth: reports | An explicit sized X literal used as an assigned value is reported.
// pair: sized-x-literal
module top(output logic o);
  assign o = 1'bx;
endmodule

// breadth: clean | A sized numeric literal used as an assigned value is not reported.
// pair: sized-x-literal
module top(output logic o);
  assign o = 1'b0;
endmodule

// breadth: reports | An explicit sized Z literal used as an assigned value is reported.
// pair: sized-z-literal
module top(output logic o);
  assign o = 1'bz;
endmodule

// breadth: clean | A sized numeric one literal used as an assigned value is not reported.
// pair: sized-z-literal
module top(output logic o);
  assign o = 1'b1;
endmodule

// breadth: reports | An unbased unsized X literal used as an assigned value is reported.
// pair: unbased-x-literal
module top(output logic [3:0] o);
  assign o = 'x;
endmodule

// breadth: clean | An unbased unsized 0 literal used as an assigned value is not reported.
// pair: unbased-x-literal
module top(output logic [3:0] o);
  assign o = '0;
endmodule

// breadth: clean | Wildcard question-mark pattern in wildcard equality is not an explicit value literal.
module top(input logic [3:0] a, output logic o);
  assign o = (a ==? 4'b1???);
endmodule

// breadth: clean | A multi-bit binary value with known binary digits is not reported.
// pair: partial-x-digits
module top(output logic [3:0] o);
  assign o = 4'b1010;
endmodule

// breadth: reports | A sized literal with some x digits among known digits is an explicit X value and is reported.
// pair: partial-x-digits
module top(output logic [3:0] o);
  assign o = 4'bx0x0;
endmodule

// breadth: reports | An x literal assigned in the default arm of a case statement is reported.
// pair: x-in-case-default
module top(input logic [3:0] a, input logic [3:0] b, output logic [3:0] o);
  always_comb begin
    case (a)
      4'd0: o = b;
      default: o = 4'bx;
    endcase
  end
endmodule

// breadth: clean | A known value in the default arm of a case statement is not reported.
// pair: x-in-case-default
module top(input logic [3:0] a, input logic [3:0] b, output logic [3:0] o);
  always_comb begin
    case (a)
      4'd0: o = b;
      default: o = 4'd0;
    endcase
  end
endmodule

// breadth: reports | A hexadecimal literal with x digits is reported.
module top(output logic [7:0] o);
  assign o = 8'hxx;
endmodule

// breadth: reports | An unbased unsized z literal is reported.
module top(output logic [3:0] o);
  assign o = 'z;
endmodule

// breadth: reports | An x literal used as an operand of case equality is a value and is reported.
module top(input logic [3:0] a, output logic o);
  assign o = (a === 4'bx);
endmodule

// breadth: reports | An x literal connected to an instance port is reported.
module child(input logic [3:0] p);
endmodule
module top(output logic o);
  child u(.p(4'bx));
  assign o = 1'b0;
endmodule

// breadth: reports | An x literal used as a declaration initializer is reported.
module top(output logic [3:0] o);
  logic [3:0] v = 4'bx;
  assign o = v;
endmodule

// breadth: clean | Question-mark digits in a casez item are pattern wildcards, not values.
module top(input logic [3:0] a, input logic [3:0] b, output logic [3:0] o);
  always_comb begin
    casez (a)
      4'b1???: o = b;
      default: o = 4'd0;
    endcase
  end
endmodule

// breadth: clean | An x digit in a casex item is a pattern wildcard, not a value.
module top(input logic [3:0] a, input logic [3:0] b, output logic [3:0] o);
  always_comb begin
    casex (a)
      4'b1xxx: o = b;
      default: o = 4'd0;
    endcase
  end
endmodule

// breadth: gap | The z of an enable-guarded tri-state driver releases the net and is synthesizable, but the rule reports it as an unsynthesizable value.
// expect: 0
module top(input logic d, input logic en, output wire o);
  assign o = en ? d : 1'bz;
endmodule
