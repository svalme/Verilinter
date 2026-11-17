// Breadth tests for PORT_DIRECTION_SUFFIX
// Rule: Flags port declarations missing expected direction suffix (_i for input, _o for output, _io for inout).

// breadth: reports | Input port missing expected _i suffix is reported.
// pair: input_suffix
module input_missing_suffix(input logic data);
endmodule

// breadth: clean | Input port with _i suffix is not reported.
// pair: input_suffix
module input_correct_suffix(input logic data_i);
endmodule

// breadth: reports | Output port missing expected _o suffix is reported.
// pair: output_suffix
module output_missing_suffix(output logic result);
endmodule

// breadth: clean | Output port with _o suffix is not reported.
// pair: output_suffix
module output_correct_suffix(output logic result_o);
endmodule

// breadth: reports | Inout port missing expected _io suffix is reported.
// pair: inout_suffix
module inout_missing_suffix(inout wire bus);
endmodule

// breadth: clean | Inout port with _io suffix is not reported.
// pair: inout_suffix
module inout_correct_suffix(inout wire bus_io);
endmodule

// breadth: reports | Input port incorrectly ending with output suffix _o instead of _i is reported.
// pair: cross_direction_suffix
module input_with_output_suffix(input logic data_o);
endmodule

// breadth: clean | Input port ending with proper _i suffix is not reported.
// pair: cross_direction_suffix
module input_with_proper_input_suffix(input logic data_i);
endmodule

// breadth: reports | Grouped ANSI port sharing preceding input direction keyword and omitting suffix is reported.
// pair: grouped_ports
module grouped_ansi_port_missing_suffix(input logic clk_i, enable);
endmodule

// breadth: clean | Grouped ANSI port sharing preceding input direction keyword with _i suffix is not reported.
// pair: grouped_ports
module grouped_ansi_port_correct_suffix(input logic clk_i, enable_i);
endmodule

// breadth: clean | Subroutine argument without direction suffix is not reported because subroutines are excluded.
module subroutine_input_not_flagged;
  function void calculate(input logic val);
  endfunction
endmodule
