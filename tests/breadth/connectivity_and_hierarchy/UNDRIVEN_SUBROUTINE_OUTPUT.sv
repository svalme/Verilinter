// breadth: reports | A task output argument that is never assigned is reported.
// pair: task-output-assignment
module top;
  task t(output logic out);
  endtask
endmodule

// breadth: clean | A task output argument that is assigned in the body is not reported.
// pair: task-output-assignment
module top;
  task t(output logic out);
    out = 1'b1;
  endtask
endmodule

// breadth: reports | A non-void function that never assigns its return value is reported.
// pair: function-return-assignment
module top;
  function automatic logic [7:0] f(input logic [7:0] in);
  endfunction
endmodule

// breadth: clean | A non-void function that returns a value via return statement is not reported.
// pair: function-return-assignment
module top;
  function automatic logic [7:0] f(input logic [7:0] in);
    return in;
  endfunction
endmodule

// breadth: reports | A function output argument that is never assigned is reported even when return is used.
// pair: function-output-argument
module top;
  function automatic logic [7:0] f(input logic [7:0] in, output logic flag);
    return in;
  endfunction
endmodule

// breadth: clean | A function assigning both its return value and its output argument is not reported.
// pair: function-output-argument
module top;
  function automatic logic [7:0] f(input logic [7:0] in, output logic flag);
    flag = 1'b1;
    return in;
  endfunction
endmodule

// breadth: reports | A task output argument passed only to an input parameter of a helper is reported.
// pair: subroutine-call-argument
module top;
  task helper(input logic i);
  endtask
  task t(output logic out);
    helper(out);
  endtask
endmodule

// breadth: clean | A task output argument passed to an output parameter of a helper is not reported.
// pair: subroutine-call-argument
module top;
  task helper(output logic o);
    o = 1'b1;
  endtask
  task t(output logic out);
    helper(out);
  endtask
endmodule

// breadth: reports | A task output argument never assigned before or after an early return is reported.
module top;
  task t(input logic cond, output logic out);
    if (cond) return;
  endtask
endmodule

// breadth: clean | A task inout argument is not reported by the undriven output rule.
module top;
  task t(inout logic io);
  endtask
endmodule

// breadth: clean | A task ref argument is not reported by the undriven output rule.
module top;
  task t(ref logic r);
  endtask
endmodule

// breadth: clean | A void function with no output argument is not reported.
module top;
  function automatic void f(input logic a);
  endfunction
endmodule

// breadth: clean | A function assigning its return value by assigning to the function name is not reported.
module top;
  function automatic logic [7:0] f(input logic [7:0] in);
    f = in;
  endfunction
endmodule

// breadth: clean | A task output argument driven via bit-select assignment is not reported.
module top;
  task t(output logic [3:0] out);
    out[0] = 1'b1;
  endtask
endmodule

// breadth: clean | A task output argument assigned in only one branch is not reported by the symbol-level rule.
module top;
  task t(input logic cond, output logic out);
    if (cond) out = 1'b1;
  endtask
endmodule
