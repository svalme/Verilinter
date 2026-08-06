module covergroup_declaration_demo(input clk);
    covergroup cg @(posedge clk);
        coverpoint clk;
    endgroup
endmodule
