module property_declaration_demo(input clk, input a);
    property p1;
        @(posedge clk) a;
    endproperty
    assert property (p1);
endmodule
