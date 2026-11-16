// breadth: reports | A case statement qualified with the unique keyword is reported.
// pair: unique-case-modifier
module top(input [1:0] sel, output logic [1:0] y);
  always_comb begin
    unique case (sel)
      2'b00: y = 2'b01;
      default: y = 2'b00;
    endcase
  end
endmodule

// breadth: clean | An unqualified standard case statement is not reported.
// pair: unique-case-modifier
module top(input [1:0] sel, output logic [1:0] y);
  always_comb begin
    case (sel)
      2'b00: y = 2'b01;
      default: y = 2'b00;
    endcase
  end
endmodule

// breadth: reports | A case statement qualified with the priority keyword is reported.
// pair: priority-case-modifier
module top(input [1:0] sel, output logic [1:0] y);
  always_comb begin
    priority case (sel)
      2'b00: y = 2'b01;
      default: y = 2'b00;
    endcase
  end
endmodule

// breadth: clean | An unqualified case statement is clean against the priority-case check.
// pair: priority-case-modifier
module top(input [1:0] sel, output logic [1:0] y);
  always_comb begin
    case (sel)
      2'b00: y = 2'b01;
      default: y = 2'b00;
    endcase
  end
endmodule

// breadth: reports | A casez statement qualified with unique is reported.
module top(input [1:0] sel, output logic [1:0] y);
  always_comb begin
    unique casez (sel)
      2'b0?: y = 2'b01;
      default: y = 2'b00;
    endcase
  end
endmodule

// breadth: reports | A casex statement qualified with priority is reported.
module top(input [1:0] sel, output logic [1:0] y);
  always_comb begin
    priority casex (sel)
      2'b0x: y = 2'b01;
      default: y = 2'b00;
    endcase
  end
endmodule

// breadth: clean | The unique keyword qualifying an if-statement is excluded from this rule.
// pair: case-vs-if
module top(input [1:0] sel, output logic [1:0] y);
  always_comb begin
    unique if (sel == 2'b00) y = 2'b01;
    else y = 2'b00;
  end
endmodule

// breadth: reports | The unique keyword qualifying a case statement is reported.
// pair: case-vs-if
module top(input [1:0] sel, output logic [1:0] y);
  always_comb begin
    unique case (sel == 2'b00)
      1'b1: y = 2'b01;
      default: y = 2'b00;
    endcase
  end
endmodule

// breadth: clean | A unique0 case statement is excluded from the unique/priority check.
module top(input [1:0] sel, output logic [1:0] y);
  always_comb begin
    unique0 case (sel)
      2'b00: y = 2'b01;
      default: y = 2'b00;
    endcase
  end
endmodule
