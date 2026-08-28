module multiple_nonblocking_writes_demo(
    input wire clk,
    input wire a,
    input wire b,
    output reg y
);
    always @(posedge clk) begin
        y <= a;
        y <= b;
    end
endmodule
