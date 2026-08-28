module expect_restrict_property_demo(input logic clk, input logic a);
    initial expect (@(posedge clk) a);
endmodule
