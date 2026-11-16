// scenario: reports | A bit-select past the end of a vector.
module top(input logic [7:0] r, output logic o);
  assign o = r[8];
endmodule

// scenario: reports | The outer index of a two-dimensional packed vector past its outer dimension.
module top(output logic o);
  logic [2:0][7:0] a;
  assign o = a[3][0];
endmodule

// scenario: reports | The inner index past the inner dimension.
// pair: inner-index
module top(output logic o);
  logic [2:0][7:0] a;
  assign o = a[1][8];
endmodule

// scenario: clean | The same selector shape with an inner index inside its own dimension.
// pair: inner-index
module top(output logic o);
  logic [2:0][7:0] a;
  assign o = a[1][7];
endmodule

// scenario: clean | Each selector of a two-dimensional packed vector is checked against its own dimension, not the outer one.
module top(output logic [15:0] o1);
  logic [2:0][15:0] a;
  assign o1 = a[2][15:0];
endmodule

// scenario: reports | An indexed part-select wider than the inner dimension.
module top(output logic o);
  logic [2:0][7:0] a;
  assign o = a[0][0 +: 9];
endmodule

// scenario: clean | A part-select of the declared range.
module top(input logic [7:0] r, output logic [3:0] o);
  assign o = r[7:4];
endmodule

// scenario: gap | An index past the end of an unpacked array dimension is not checked yet.
module top(output logic [3:0] o);
  logic [3:0] arr [4];
  assign o = arr[4];
endmodule
