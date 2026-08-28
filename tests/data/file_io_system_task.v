module file_io_system_task_demo;
    integer fd;
    initial begin
        fd = $fopen("out.txt", "w");
        $fdisplay(fd, "hi");
        $fclose(fd);
    end
endmodule
