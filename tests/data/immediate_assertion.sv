module immediate_assertion_demo(input a);
    always_comb begin
        assert (a);
    end
endmodule
