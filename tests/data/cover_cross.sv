module cover_cross_demo(input logic [1:0] x, input logic [1:0] y);
    covergroup cg;
        cpx: coverpoint x;
        cpy: coverpoint y;
        crs: cross cpx, cpy;
    endgroup
endmodule
