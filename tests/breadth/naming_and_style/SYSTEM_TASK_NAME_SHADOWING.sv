// Breadth tests for SYSTEM_TASK_NAME_SHADOWING
// Rule: Flags declared identifiers whose names match built-in system task/function names without '$'.

// breadth: reports | A net named display matches the system task name $display without its dollar sign and is reported.
// pair: signal_display
module wire_named_display;
  wire display;
endmodule

// breadth: clean | Net declared with display_sig not matching any system task is not reported.
// pair: signal_display
module wire_normal_name;
  wire display_sig;
endmodule

// breadth: reports | A variable named finish matches the system task name $finish without its dollar sign and is reported.
// pair: signal_finish
module reg_named_finish;
  reg finish;
endmodule

// breadth: clean | Variable declared with finish_flag not matching any system task is not reported.
// pair: signal_finish
module reg_normal_name;
  reg finish_flag;
endmodule

// breadth: reports | A logic variable named random matches the system function name $random without its dollar sign and is reported.
// pair: signal_random
module logic_named_random;
  logic random;
endmodule

// breadth: clean | Logic variable declared with random_val is not reported.
// pair: signal_random
module logic_normal_name;
  logic random_val;
endmodule

// breadth: reports | A variable local to a function and named monitor matches the system task name $monitor and is reported.
// pair: local_scope_shadow
module local_variable_in_function_named_monitor;
  function void log_msg();
    logic monitor;
  endfunction
endmodule

// breadth: clean | Subroutine-local variable declared with identifier monitor_en is not reported.
// pair: local_scope_shadow
module local_variable_in_function_normal_name;
  function void log_msg();
    logic monitor_en;
  endfunction
endmodule

// breadth: clean | Calling system task with leading dollar sign is not a declarator and is not reported.
module calling_system_task_itself;
  initial begin
    $finish;
  end
endmodule

// breadth: reports | A function named display matches the system task name $display without its dollar sign and is reported.
// pair: subroutine-name
module user_function_named_like_system_task;
  function void display();
  endfunction
endmodule

// breadth: clean | A function whose name only starts with a system task name (display_state) does not match it and is not reported.
// pair: subroutine-name
module function_named_display_state;
  function void display_state();
  endfunction
endmodule

// breadth: reports | A task named finish matches the system task name $finish without its dollar sign and is reported.
// pair: task-name
module task_named_like_system_task;
  task finish;
  endtask
endmodule

// breadth: clean | A task whose name only contains a system task name (finish_now) does not match it and is not reported.
// pair: task-name
module task_named_finish_now;
  task finish_now;
  endtask
endmodule
