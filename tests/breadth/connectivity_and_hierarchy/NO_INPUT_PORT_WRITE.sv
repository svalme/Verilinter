// breadth: reports | An input port assigned in an always_comb block is reported.
// pair: input-port-procedural-write
module top(input logic in, output logic out);
  always_comb begin
    in = 1'b0;
    out = in;
  end
endmodule

// breadth: clean | An input port that is only read in an always_comb block is not reported.
// pair: input-port-procedural-write
module top(input logic in, output logic out);
  always_comb begin
    out = in;
  end
endmodule

// breadth: reports | An input port driven by a continuous assign is reported.
// pair: input-port-continuous-assign
module top(input logic in, output logic out);
  assign in = 1'b0;
  assign out = 1'b1;
endmodule

// breadth: clean | An internal net driven by a continuous assign from an input port is not reported.
// pair: input-port-continuous-assign
module top(input logic in, output logic out);
  assign out = in;
endmodule

// breadth: reports | A bit-select of an input port assigned in a procedural block is reported.
// pair: input-port-bit-select-write
module top(input logic [3:0] in, output logic out);
  always_comb begin
    in[0] = 1'b0;
    out = in[1];
  end
endmodule

// breadth: clean | A bit-select of an input port that is only read is not reported.
// pair: input-port-bit-select-write
module top(input logic [3:0] in, output logic out);
  always_comb begin
    out = in[0];
  end
endmodule

// breadth: reports | A module input port assigned inside a task body without a local formal is reported.
// pair: input-port-task-formal-shadow
module top(input logic a, output logic out);
  task t();
    a = 1'b1;
  endtask
  assign out = a;
endmodule

// breadth: clean | A task input argument shadowing a module input port name is not reported when assigned.
// pair: input-port-task-formal-shadow
module top(input logic a, output logic out);
  task t(input logic a);
    a = 1'b1;
  endtask
  assign out = a;
endmodule

// breadth: reports | A part-select slice of an input port assigned in a procedural block is reported.
module top(input logic [3:0] in, output logic out);
  always_comb begin
    in[2:1] = 2'b00;
    out = in[0];
  end
endmodule

// breadth: reports | An input port that is both read and written in a procedural block is reported.
module top(input logic in, output logic out);
  always_comb begin
    out = in;
    in = 1'b0;
  end
endmodule

// breadth: clean | A local variable declared in an inner named block shadowing a module input port name is not reported when written.
module top(input logic in, output logic out);
  initial begin : blk
    logic in;
    in = 1'b1;
  end
  assign out = in;
endmodule

// breadth: clean | A function formal argument shadowing a module input port name is not reported when assigned.
module top(input logic a, output logic out);
  function automatic logic f(input logic a);
    a = 1'b1;
    return a;
  endfunction
  assign out = f(a);
endmodule

// breadth: clean | An inout port driven by a continuous assign is not reported by the input port write rule.
module top(inout wire io, input logic en, input logic d);
  assign io = en ? d : 1'bz;
endmodule
