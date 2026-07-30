module concurrent_assertion_demo(input clk, input a);
    assert property (@(posedge clk) a);
endmodule
