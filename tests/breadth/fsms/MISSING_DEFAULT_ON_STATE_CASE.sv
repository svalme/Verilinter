// Breadth test suite for MISSING_DEFAULT_ON_STATE_CASE
// Category: fsms
//
// Tests detection of state-machine case statements missing a default branch,
// covering one-process and two-process FSM styles, enum state types,
// contrasting with FSMs having default branches and ordinary non-state multiplexers.

// breadth: reports | One-process FSM case on state variable missing default branch is reported.
// pair: p1
module one_process_fsm_missing_default (
    input  wire clk,
    input  wire rst_n,
    output reg  out_val
);
  localparam [1:0] S_IDLE = 2'b00;
  localparam [1:0] S_RUN  = 2'b01;
  reg [1:0] state;

  always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      state   <= S_IDLE;
      out_val <= 1'b0;
    end else begin
      case (state)
        S_IDLE: begin
          state   <= S_RUN;
          out_val <= 1'b0;
        end
        S_RUN: begin
          state   <= S_IDLE;
          out_val <= 1'b1;
        end
      endcase
    end
  end
endmodule

// breadth: clean | One-process FSM case on state variable with default branch is not reported.
// pair: p1
module one_process_fsm_with_default (
    input  wire clk,
    input  wire rst_n,
    output reg  out_val
);
  localparam [1:0] S_IDLE = 2'b00;
  localparam [1:0] S_RUN  = 2'b01;
  reg [1:0] state;

  always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      state   <= S_IDLE;
      out_val <= 1'b0;
    end else begin
      case (state)
        S_IDLE: begin
          state   <= S_RUN;
          out_val <= 1'b0;
        end
        S_RUN: begin
          state   <= S_IDLE;
          out_val <= 1'b1;
        end
        default: begin
          state   <= S_IDLE;
          out_val <= 1'b0;
        end
      endcase
    end
  end
endmodule

// breadth: reports | Two-process FSM next-state combinational case missing default branch is reported.
// pair: p2
module two_process_fsm_missing_default (
    input  wire clk,
    input  wire rst_n,
    output reg  active
);
  reg [1:0] state, next_state;

  always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) state <= 2'b00;
    else        state <= next_state;
  end

  always_comb begin
    active = 1'b0;
    case (state)
      2'b00: begin
        next_state = 2'b01;
        active = 1'b0;
      end
      2'b01: begin
        next_state = 2'b00;
        active = 1'b1;
      end
    endcase
  end
endmodule

// breadth: clean | Two-process FSM next-state combinational case with default branch is not reported.
// pair: p2
module two_process_fsm_with_default (
    input  wire clk,
    input  wire rst_n,
    output reg  active
);
  reg [1:0] state, next_state;

  always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) state <= 2'b00;
    else        state <= next_state;
  end

  always_comb begin
    active = 1'b0;
    case (state)
      2'b00: begin
        next_state = 2'b01;
        active = 1'b0;
      end
      2'b01: begin
        next_state = 2'b00;
        active = 1'b1;
      end
      default: begin
        next_state = 2'b00;
        active = 1'b0;
      end
    endcase
  end
endmodule

// breadth: reports | Enum-typed state machine case statement missing default branch is reported.
// pair: p3
module enum_state_fsm_missing_default (
    input  wire clk,
    input  wire rst_n,
    output reg  busy
);
  typedef enum logic [1:0] {
    ST_RESET = 2'b00,
    ST_WORK  = 2'b01
  } state_t;

  state_t current_state, future_state;

  always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) current_state <= ST_RESET;
    else        current_state <= future_state;
  end

  always_comb begin
    busy = 1'b0;
    case (current_state)
      ST_RESET: begin
        future_state = ST_WORK;
        busy = 1'b0;
      end
      ST_WORK: begin
        future_state = ST_RESET;
        busy = 1'b1;
      end
    endcase
  end
endmodule

// breadth: clean | Enum-typed state machine case statement with default branch is not reported.
// pair: p3
module enum_state_fsm_with_default (
    input  wire clk,
    input  wire rst_n,
    output reg  busy
);
  typedef enum logic [1:0] {
    ST_RESET = 2'b00,
    ST_WORK  = 2'b01
  } state_t;

  state_t current_state, future_state;

  always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) current_state <= ST_RESET;
    else        current_state <= future_state;
  end

  always_comb begin
    busy = 1'b0;
    case (current_state)
      ST_RESET: begin
        future_state = ST_WORK;
        busy = 1'b0;
      end
      ST_WORK: begin
        future_state = ST_RESET;
        busy = 1'b1;
      end
      default: begin
        future_state = ST_RESET;
        busy = 1'b0;
      end
    endcase
  end
endmodule

// breadth: reports | One-process FSM using fsm_state naming missing default branch is reported.
// pair: p4
module one_process_state_case_missing_default (
    input  wire clk,
    input  wire rst,
    output reg  led
);
  reg [1:0] fsm_state;

  always_ff @(posedge clk) begin
    if (rst) fsm_state <= 2'b00;
    else begin
      case (fsm_state)
        2'b00: begin
          fsm_state <= 2'b01;
          led <= 1'b0;
        end
        2'b01: begin
          fsm_state <= 2'b00;
          led <= 1'b1;
        end
      endcase
    end
  end
endmodule

// breadth: clean | Multiplexer case on non-state variable is not reported by MISSING_DEFAULT_ON_STATE_CASE.
// pair: p4
module ordinary_mux_missing_default (
    input  wire [1:0] mux_sel,
    output reg  [7:0] data_out
);
  // Pure multiplexer on non-state signal: handled by NO_DEFAULT_CASE_STATEMENT, not this rule
  always_comb begin
    case (mux_sel)
      2'b00: data_out = 8'hAA;
      2'b01: data_out = 8'h55;
    endcase
  end
endmodule

// breadth: clean | Two-process FSM case with default branch placed first is not reported.
module two_process_fsm_default_first (
    input  wire clk,
    input  wire rst_n,
    output reg  ready
);
  reg [1:0] state, next_state;

  always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) state <= 2'b00;
    else        state <= next_state;
  end

  always_comb begin
    case (state)
      default: begin
        next_state = 2'b00;
        ready = 1'b0;
      end
      2'b00: begin
        next_state = 2'b01;
        ready = 1'b1;
      end
    endcase
  end
endmodule

// breadth: clean | Non-state control mode case within sequential block with default is not reported.
module non_state_case_in_sequential_block (
    input  wire       clk,
    input  wire [1:0] mode,
    output reg  [3:0] count
);
  always_ff @(posedge clk) begin
    case (mode)
      2'd0:    count <= count + 4'd1;
      2'd1:    count <= count - 4'd1;
      default: count <= 4'd0;
    endcase
  end
endmodule
