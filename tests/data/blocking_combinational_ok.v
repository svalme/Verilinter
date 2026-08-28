module blocking_combinational_ok_demo(input a, input b, output y);
    always @(*) begin
        y = a & b;
    end
endmodule
