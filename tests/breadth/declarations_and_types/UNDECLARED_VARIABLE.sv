// breadth: reports | An undeclared identifier used in an expression under default_nettype none is reported.
// pair: undeclared-vs-declared-wire
`default_nettype none
module top(input wire a, output wire y);
  assign y = a & missing_sig;
endmodule
`default_nettype wire

// breadth: clean | A declared wire used in an expression under default_nettype none is not reported.
// pair: undeclared-vs-declared-wire
`default_nettype none
module top(input wire a, output wire y);
  wire sig;
  assign y = a & sig;
endmodule
`default_nettype wire

// breadth: gap | An identifier used before its declaration later in the same scope under default_nettype none is reported.
`default_nettype none
module top(input wire a, output wire y);
  assign y = a & sig_later;
  wire sig_later;
endmodule
`default_nettype wire

// breadth: clean | A declared wire placed before its use under default_nettype none is not reported.
`default_nettype none
module top(input wire a, output wire y);
  wire sig_first;
  assign y = a & sig_first;
endmodule
`default_nettype wire

// breadth: reports | A local variable declared in a sibling block referenced without qualification is reported.
// pair: sibling-block-local
`default_nettype none
module top(input wire a, output logic y);
  initial begin : b1
    logic local_sig;
    local_sig = a;
  end
  initial begin : b2
    y = local_sig;
  end
endmodule
`default_nettype wire

// breadth: clean | A local variable referenced within its own declaring block is not reported.
// pair: sibling-block-local
`default_nettype none
module top(input wire a, output logic y);
  initial begin : b1
    logic local_sig;
    local_sig = a;
    y = local_sig;
  end
endmodule
`default_nettype wire

// breadth: reports | An unresolved identifier in a procedural block under default_nettype none is reported.
`default_nettype none
module top(input wire a, output logic y);
  always_comb begin
    y = a & unk_var;
  end
endmodule
`default_nettype wire

// breadth: clean | A loop variable declared with genvar under default_nettype none is not reported.
`default_nettype none
module top #(parameter N = 2) (input wire a, output wire y);
  genvar i;
  for (i = 0; i < N; i = i + 1) begin : gen
    wire w;
  end
  assign y = a;
endmodule
`default_nettype wire

// breadth: clean | An iterator declared in a for-loop header under default_nettype none is not reported.
`default_nettype none
module top(input wire a, output logic [3:0] y);
  always_comb begin
    for (int i = 0; i < 4; i = i + 1) begin
      y[i] = a;
    end
  end
endmodule
`default_nettype wire

// breadth: clean | An implicit net without default_nettype none belongs to NO_IMPLICIT_NET and is not reported here.
module top(input wire a, output wire y);
  assign y = a & implicit_wire;
endmodule
