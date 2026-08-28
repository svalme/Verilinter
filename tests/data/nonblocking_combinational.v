module nonblocking_combinational_demo(input a, input b, output y);
    always @(*) begin
        y <= a & b;
    end
endmodule
