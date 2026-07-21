module tran_rtran_demo (
    inout wire a,
    inout wire b,
    inout wire c,
    inout wire d
);
    tran t0(a, b);
    rtran t1(c, d);
endmodule
