module mixed_assignment_style_demo(input clk);
    reg a, b;
    always @(posedge clk) begin
        a = 1;
        b <= 1;
    end
endmodule
