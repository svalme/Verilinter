module sequence_declaration_demo(input clk, input a);
    sequence s1;
        @(posedge clk) a;
    endsequence
endmodule
