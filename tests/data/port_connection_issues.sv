module child(
    input logic clk,
    input logic [7:0] data,
    input logic signed [7:0] sdata,
    output logic [3:0] y
);
endmodule

module top;
    logic clk;
    logic [3:0] narrow;
    logic [7:0] wide;
    logic signed [7:0] signed_bus;
    logic [7:0] unsigned_bus;

    child u_unconn(.clk(clk), .data(wide), .sdata(signed_bus));
    child u_dup(.clk(clk), .data(wide), .data(narrow), .sdata(signed_bus), .y(narrow));
    child u_mixed(.clk(clk), wide, signed_bus, narrow);
    child u_width(.clk(clk), .data(narrow), .sdata(unsigned_bus), .y(wide));
endmodule
