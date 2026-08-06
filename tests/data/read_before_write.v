module read_before_write_demo;
    real x;
    real y;
    initial begin
        y = x;
        x = 1;
    end
endmodule
