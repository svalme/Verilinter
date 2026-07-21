module child #(parameter WIDTH = 1) ();
endmodule

module top;
    child u_child();
    defparam u_child.WIDTH = 8;
endmodule
