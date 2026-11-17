// Breadth test suite for ONE_HOT_ENCODING_VIOLATION
// Category: fsms
//
// Tests detection of one-hot state machine encoding violations where the register
// width implies one-hot intent (width == state count >= 3) but one or more states
// have popcount != 1 (e.g. multiple bits set or all-zero), contrasting with valid
// one-hot encodings, binary encodings, and 2-state machines.

// breadth: reports | 3-state one-hot FSM containing a state with two bits set is reported.
// pair: p1
module one_hot_two_bits_set (
    input  wire clk,
    input  wire rst_n,
    output reg  out_sig
);
  localparam [2:0] S0 = 3'b001;
  localparam [2:0] S1 = 3'b010;
  localparam [2:0] S2 = 3'b011; // Violation: 2 bits set in 3-bit one-hot register
  reg [2:0] state;

  always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) state <= S0;
    else case (state)
      S0:      state <= S1;
      S1:      state <= S2;
      S2:      state <= S0;
      default: state <= S0;
    endcase
  end
endmodule

// breadth: clean | Valid 3-state one-hot FSM with exactly one bit set per state is not reported.
// pair: p1
module valid_3bit_one_hot (
    input  wire clk,
    input  wire rst_n,
    output reg  out_sig
);
  localparam [2:0] S0 = 3'b001;
  localparam [2:0] S1 = 3'b010;
  localparam [2:0] S2 = 3'b100;
  reg [2:0] state;

  always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) state <= S0;
    else case (state)
      S0:      state <= S1;
      S1:      state <= S2;
      S2:      state <= S0;
      default: state <= S0;
    endcase
  end
endmodule

// breadth: reports | 4-state one-hot FSM containing an all-zero state is reported.
// pair: p2
module one_hot_all_zero_state (
    input  wire clk,
    input  wire rst_n,
    output reg  done
);
  localparam [3:0] S_INIT = 4'b0000; // Violation: popcount 0 in 4-bit one-hot register
  localparam [3:0] S_WORK = 4'b0010;
  localparam [3:0] S_WAIT = 4'b0100;
  localparam [3:0] S_DONE = 4'b1000;
  reg [3:0] state;

  always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) state <= S_INIT;
    else case (state)
      S_INIT:  state <= S_WORK;
      S_WORK:  state <= S_WAIT;
      S_WAIT:  state <= S_DONE;
      S_DONE:  state <= S_INIT;
      default: state <= S_INIT;
    endcase
  end
endmodule

// breadth: clean | Valid 4-state one-hot FSM with single active bit per state is not reported.
// pair: p2
module valid_4bit_one_hot (
    input  wire clk,
    input  wire rst_n,
    output reg  done
);
  localparam [3:0] S_INIT = 4'b0001;
  localparam [3:0] S_WORK = 4'b0010;
  localparam [3:0] S_WAIT = 4'b0100;
  localparam [3:0] S_DONE = 4'b1000;
  reg [3:0] state;

  always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) state <= S_INIT;
    else case (state)
      S_INIT:  state <= S_WORK;
      S_WORK:  state <= S_WAIT;
      S_WAIT:  state <= S_DONE;
      S_DONE:  state <= S_INIT;
      default: state <= S_INIT;
    endcase
  end
endmodule

// breadth: reports | Enum-based 3-state one-hot FSM with non-one-hot state literal is reported.
// pair: p3
module enum_one_hot_violation (
    input  wire clk,
    input  wire rst_n,
    output reg  busy
);
  typedef enum logic [2:0] {
    ST_A = 3'b001,
    ST_B = 3'b010,
    ST_C = 3'b011 // Violation: two bits set
  } state_t;

  state_t current_state;

  always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) current_state <= ST_A;
    else case (current_state)
      ST_A:    current_state <= ST_B;
      ST_B:    current_state <= ST_C;
      ST_C:    current_state <= ST_A;
      default: current_state <= ST_A;
    endcase
  end
endmodule

// breadth: clean | Enum-based 3-state one-hot FSM with valid one-hot literals is not reported.
// pair: p3
module enum_valid_one_hot (
    input  wire clk,
    input  wire rst_n,
    output reg  busy
);
  typedef enum logic [2:0] {
    ST_A = 3'b001,
    ST_B = 3'b010,
    ST_C = 3'b100
  } state_t;

  state_t current_state;

  always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) current_state <= ST_A;
    else case (current_state)
      ST_A:    current_state <= ST_B;
      ST_B:    current_state <= ST_C;
      ST_C:    current_state <= ST_A;
      default: current_state <= ST_A;
    endcase
  end
endmodule

// breadth: reports | 3-state one-hot FSM containing a state with three bits set is reported.
// pair: p4
module one_hot_three_bits_set (
    input  wire clk,
    input  wire rst_n
);
  localparam [2:0] ST0 = 3'b001;
  localparam [2:0] ST1 = 3'b010;
  localparam [2:0] ST2 = 3'b111; // Violation: 3 bits set
  reg [2:0] st;

  always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) st <= ST0;
    else case (st)
      ST0:     st <= ST1;
      ST1:     st <= ST2;
      ST2:     st <= ST0;
      default: st <= ST0;
    endcase
  end
endmodule

// breadth: clean | 4-state FSM using binary encoding in a 2-bit register is not reported.
// pair: p4
module ordinary_binary_encoding (
    input  wire clk,
    input  wire rst_n
);
  // 4 states in a 2-bit register: width (2) != state count (4), recognized as binary encoding
  localparam [1:0] B_IDLE = 2'b00;
  localparam [1:0] B_LOAD = 2'b01;
  localparam [1:0] B_WORK = 2'b10;
  localparam [1:0] B_DONE = 2'b11;
  reg [1:0] st;

  always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) st <= B_IDLE;
    else case (st)
      B_IDLE:  st <= B_LOAD;
      B_LOAD:  st <= B_WORK;
      B_WORK:  st <= B_DONE;
      B_DONE:  st <= B_IDLE;
      default: st <= B_IDLE;
    endcase
  end
endmodule

// breadth: clean | 2-state machine in 2-bit register is below minimum state count (3) and is not reported.
module two_state_machine_with_2bit_reg (
    input  wire clk,
    input  wire rst_n
);
  // 2 states in 2-bit register: clean because rule requires >= 3 states to avoid false positive on headroom
  localparam [1:0] S_OFF = 2'b00;
  localparam [1:0] S_ON  = 2'b01;
  reg [1:0] st;

  always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) st <= S_OFF;
    else case (st)
      S_OFF:   st <= S_ON;
      S_ON:    st <= S_OFF;
      default: st <= S_OFF;
    endcase
  end
endmodule

// breadth: clean | Combinational case statement on arbitrary selector is not reported.
module non_state_case_statement (
    input  wire [2:0] sel,
    output reg  [7:0] val
);
  always_comb begin
    case (sel)
      3'b000:  val = 8'h01;
      3'b011:  val = 8'h02;
      3'b111:  val = 8'h03;
      default: val = 8'h00;
    endcase
  end
endmodule
