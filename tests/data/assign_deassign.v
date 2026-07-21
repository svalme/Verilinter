module assign_deassign_demo;
    reg a;

    initial begin
        assign a = 1'b1;
        deassign a;
    end
endmodule
