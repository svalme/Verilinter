module force_release_demo;
    logic a;

    initial begin
        force a = 1'b1;
        release a;
    end
endmodule
