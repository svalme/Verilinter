module self_assignment_demo(
    input wire clk,
    output reg y
);
    reg tmp;

    always @(posedge clk) begin
        tmp <= tmp;
        y <= tmp;
    end
endmodule
