// breadth: reports | A module header port list with a trailing comma is reported.
// pair: module-header-trailing-comma
module top(a,);
  input a;
endmodule

// breadth: clean | A module header port list with declared ports and no trailing comma is not reported.
// pair: module-header-trailing-comma
module top(a);
  input a;
endmodule

// breadth: reports | An instance positional port list with an empty slot between commas is reported.
// pair: instance-ordered-empty-slot
module sub(input a, input b, output c);
endmodule
module top;
  logic x, z;
  sub u(x, , z);
endmodule

// breadth: clean | An instance providing expressions for all positional port connections is not reported.
// pair: instance-ordered-empty-slot
module sub(input a, input b, output c);
endmodule
module top;
  logic x, y, z;
  sub u(x, y, z);
endmodule

// breadth: reports | An instance positional port list with a trailing comma is reported.
// pair: instance-trailing-comma
module sub(input a, output b);
endmodule
module top;
  logic x;
  sub u(x, );
endmodule

// breadth: clean | An instance providing positional port connections without a trailing comma is not reported.
// pair: instance-trailing-comma
module sub(input a, output b);
endmodule
module top;
  logic x, y;
  sub u(x, y);
endmodule

// breadth: reports | An instance with an empty positional connection slot is reported.
// pair: named-empty-parens-vs-empty-positional
module sub(input a, output b);
endmodule
module top;
  logic x;
  sub u(x, );
endmodule

// breadth: clean | An instance using named port connection with empty parentheses is not reported by the nullport rule.
// pair: named-empty-parens-vs-empty-positional
module sub(input a, output b);
endmodule
module top;
  logic x;
  sub u(.a(x), .b());
endmodule

// breadth: reports | A module header port list with an empty slot between consecutive commas is reported.
module top(a, , b);
  input a, b;
endmodule

// breadth: reports | A module header port list with a leading comma is reported.
module top(, a);
  input a;
endmodule

// breadth: clean | A module header declared with an empty port list is not reported.
module top();
endmodule

// breadth: clean | A module declared without parentheses in its header is not reported.
module top;
endmodule
