module function_declaration_demo;
    function automatic int add_one(input int x);
        add_one = x + 1;
    endfunction

    task automatic do_work;
    endtask
endmodule
