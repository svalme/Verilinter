// Breadth tests for SIGNAL_NAME_CASING
// Rule: Flags signal declarations whose names are not lower_snake_case. Excludes parameters and enum members.

// breadth: reports | CamelCase wire identifier is reported.
// pair: wire_naming
module wire_camel_case;
  wire dataReady;
endmodule

// breadth: clean | Lowercase snake_case wire identifier is not reported.
// pair: wire_naming
module wire_lower_snake_case;
  wire data_ready;
endmodule

// breadth: reports | ALL_CAPS reg identifier is reported.
// pair: reg_naming
module reg_upper_case;
  reg STATUS_REG;
endmodule

// breadth: clean | Lowercase snake_case reg identifier is not reported.
// pair: reg_naming
module reg_lower_snake_case;
  reg status_reg;
endmodule

// breadth: reports | PascalCase logic identifier is reported.
// pair: logic_naming
module logic_pascal_case;
  logic PacketHeader;
endmodule

// breadth: clean | Lowercase snake_case logic identifier is not reported.
// pair: logic_naming
module logic_lower_snake_case;
  logic packet_header;
endmodule

// breadth: reports | Struct member with PascalCase identifier is reported.
// pair: struct_member_casing
module struct_member_bad_casing;
  typedef struct {
    logic BadField;
  } packet_t;
endmodule

// breadth: clean | Struct member with lower_snake_case identifier is not reported.
// pair: struct_member_casing
module struct_member_lower_casing;
  typedef struct {
    logic good_field;
  } packet_t;
endmodule

// breadth: reports | For-loop index variable with PascalCase identifier is reported.
// pair: loop_var_casing
module loop_variable_bad_casing;
  initial begin
    for (int IterCount = 0; IterCount < 4; IterCount++) begin
    end
  end
endmodule

// breadth: clean | For-loop index variable with lower_snake_case identifier is not reported.
// pair: loop_var_casing
module loop_variable_lower_casing;
  initial begin
    for (int iter_count = 0; iter_count < 4; iter_count++) begin
    end
  end
endmodule

// breadth: clean | Parameter declarations and enum members are not reported because they are not signals.
module parameter_and_enum_ignored;
  parameter UPPER_PARAM = 1;
  localparam LOCAL_VAL = 2;
  typedef enum { ST_IDLE, ST_BUSY } state_t;
endmodule
