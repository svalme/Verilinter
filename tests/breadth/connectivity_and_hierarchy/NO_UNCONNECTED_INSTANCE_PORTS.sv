// breadth: reports | An instance omitting a declared port in its named connection list is reported.
// pair: unconnected-named-port
module child(input a, output b);
endmodule
module top;
  logic x;
  child u_child(.a(x));
endmodule

// breadth: clean | An instance connecting all declared ports by name is not reported.
// pair: unconnected-named-port
module child(input a, output b);
endmodule
module top;
  logic x, y;
  child u_child(.a(x), .b(y));
endmodule

// breadth: reports | An instance explicitly connecting an empty port list is reported.
// pair: empty-parentheses-port
module child(input a, output b);
endmodule
module top;
  logic x;
  child u_child(.a(x), .b());
endmodule

// breadth: clean | An instance connecting an expression to every port is not reported.
// pair: empty-parentheses-port
module child(input a, output b);
endmodule
module top;
  logic x, y;
  child u_child(.a(x), .b(y));
endmodule

// breadth: reports | An instance using positional connections with missing trailing ports is reported.
// pair: unconnected-positional-port
module child(input a, output b);
endmodule
module top;
  logic x;
  child u_child(x);
endmodule

// breadth: clean | An instance providing all positional port connections is not reported.
// pair: unconnected-positional-port
module child(input a, output b);
endmodule
module top;
  logic x, y;
  child u_child(x, y);
endmodule

// breadth: reports | An instance with an empty positional connection slot is reported.
module child(input a, output b);
endmodule
module top;
  logic x;
  child u_child(x, );
endmodule

// breadth: clean | An instance using wildcard dot-star connection satisfies port connections.
module child(input a, output b);
endmodule
module top;
  logic a, b;
  child u_child(.*);
endmodule

// breadth: clean | Instantiating a module with no declared ports is not reported.
module child;
endmodule
module top;
  child u_child();
endmodule

// breadth: reports | An omitted input port is reported: the input floats.
module child(input a, output b);
endmodule
module top;
  logic y;
  child u_child(.b(y));
endmodule

// breadth: reports | An omitted inout port is reported.
module child(inout io, input a);
endmodule
module top;
  logic x;
  child u_child(.a(x));
endmodule

// breadth: reports | An omitted port of an instance array is reported.
module child(input a, output b);
endmodule
module top;
  logic x;
  child u_child [1:0] (.a(x));
endmodule

// breadth: reports | An instance in a generate branch that the default parameters switch off is checked: its port list does not depend on a parameter value.
module child(input a, output b);
endmodule
module top #(parameter W = 4);
  logic x;
  if (W == 1) begin : g
    child u_child(.a(x));
  end
endmodule

// breadth: clean | An instance of a module with no visible definition has unknown ports and is not reported.
module top;
  logic x;
  undefined_mod u_m(.a(x));
endmodule

// breadth: gap | A wildcard connection leaves a port unconnected when the parent has no signal of that name, but the rule treats every port covered by `.*` as connected, so a floating port goes unreported.
module child(input a, output b);
endmodule
module top;
  child u_child(.*);
endmodule

// breadth: gap | A wildcard connection with only some matching signals leaves the others unconnected; the rule does not report them.
module child(input a, output b);
endmodule
module top;
  logic a;
  child u_child(.*);
endmodule

// breadth: gap | An input port that declares a default value is unconnected on purpose: the default is used. The rule reports it anyway.
// expect: 0
module child(input a = 1'b1, output b);
endmodule
module top;
  logic y;
  child u_child(.b(y));
endmodule
