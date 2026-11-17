// Breadth test suite for NO_ASSERTION_CONTROL_TASK
// Category: assertions_and_verification
//
// Tests detection of simulation-only assertion control tasks ($assertoff, $asserton, $assertkill),
// contrasting with other system tasks and comments.

// breadth: reports | Assertion control task $assertoff call is reported.
// pair: assert_ctrl_vs_display
module m;
  initial begin
    $assertoff(0);
  end
endmodule

// breadth: clean | Standard display system task call is not reported by NO_ASSERTION_CONTROL_TASK.
// pair: assert_ctrl_vs_display
module m;
  initial begin
    $display("msg");
  end
endmodule

// breadth: clean | Words $assertoff and $asserton inside comments are not reported.
module m;
  // $assertoff $asserton $assertkill
  wire w = 1'b0;
endmodule

// breadth: reports | Assertion control task $assertkill call in function is reported.
module m;
  function void kill_checks();
    $assertkill(0);
  endfunction
endmodule

// breadth: reports | Multiple assertion control task calls trigger multiple reports.
// expect: 2
module m;
  initial begin
    $assertoff(0);
    $asserton(0);
  end
endmodule

// breadth: clean | Simulation control task $finish is not reported by NO_ASSERTION_CONTROL_TASK.
module m;
  initial begin
    $finish;
  end
endmodule
