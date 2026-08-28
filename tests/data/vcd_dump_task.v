module vcd_dump_task_demo;
    initial begin
        $dumpfile("waves.vcd");
        $dumpvars;
    end
endmodule
