// Breadth test suite for MISSING_STATE_REGISTER_RESET
// Category: fsms
//
// Tests detection of state registers in async-reset procedural blocks where the
// state register is not assigned inside the reset branch, contrasting with
// fully reset state registers, synchronous reset blocks, and non-state registers.

// breadth: reports | State register in async-reset block omitted from reset branch is reported.
// pair: p1
module async_reset_missing_state_assignment (
    input  wire clk,
    input  wire rst_n,
    output reg  z
);
  localparam [1:0] IDLE = 2'b00;
  localparam [1:0] RUN  = 2'b01;
  reg [1:0] state;

  always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      z <= 1'b0; // Resets output z, but omits state
    end else begin
      case (state)
        IDLE:    state <= RUN;
        RUN:     state <= IDLE;
        default: state <= IDLE;
      endcase
    end
  end
endmodule

// breadth: clean | State register in async-reset block initialized inside reset branch is not reported.
// pair: p1
module async_reset_covering_state (
    input  wire clk,
    input  wire rst_n,
    output reg  z
);
  localparam [1:0] IDLE = 2'b00;
  localparam [1:0] RUN  = 2'b01;
  reg [1:0] state;

  always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      state <= IDLE;
      z     <= 1'b0;
    end else begin
      case (state)
        IDLE:    state <= RUN;
        RUN:     state <= IDLE;
        default: state <= IDLE;
      endcase
    end
  end
endmodule

// breadth: reports | Active-high async-reset block omitting current_state register assignment is reported.
// pair: p2
module active_high_async_reset_missing_state (
    input  wire clk,
    input  wire rst_high,
    output reg  flag
);
  localparam [1:0] S0 = 2'b00;
  localparam [1:0] S1 = 2'b01;
  reg [1:0] current_state;

  always_ff @(posedge clk or posedge rst_high) begin
    if (rst_high) begin
      flag <= 1'b0;
    end else begin
      case (current_state)
        S0:      current_state <= S1;
        S1:      current_state <= S0;
        default: current_state <= S0;
      endcase
    end
  end
endmodule

// breadth: clean | Active-high async-reset block initializing current_state register is not reported.
// pair: p2
module active_high_async_reset_covering_state (
    input  wire clk,
    input  wire rst_high,
    output reg  flag
);
  localparam [1:0] S0 = 2'b00;
  localparam [1:0] S1 = 2'b01;
  reg [1:0] current_state;

  always_ff @(posedge clk or posedge rst_high) begin
    if (rst_high) begin
      current_state <= S0;
      flag          <= 1'b0;
    end else begin
      case (current_state)
        S0:      current_state <= S1;
        S1:      current_state <= S0;
        default: current_state <= S0;
      endcase
    end
  end
endmodule

// breadth: reports | Two-process FSM state register omitted from async-reset branch is reported.
// pair: p3
module two_process_async_missing_state (
    input  wire clk,
    input  wire rst_n,
    output reg  out_sig
);
  reg [1:0] state, next_state;

  always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      out_sig <= 1'b0; // State is missing from reset branch
    end else begin
      state <= next_state;
    end
  end

  always_comb begin
    case (state)
      2'b00:   next_state = 2'b01;
      2'b01:   next_state = 2'b00;
      default: next_state = 2'b00;
    endcase
  end
endmodule

// breadth: clean | Two-process FSM state register properly assigned in async-reset branch is not reported.
// pair: p3
module two_process_async_covering_state (
    input  wire clk,
    input  wire rst_n,
    output reg  out_sig
);
  reg [1:0] state, next_state;

  always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      state   <= 2'b00;
      out_sig <= 1'b0;
    end else begin
      state <= next_state;
    end
  end

  always_comb begin
    case (state)
      2'b00:   next_state = 2'b01;
      2'b01:   next_state = 2'b00;
      default: next_state = 2'b00;
    endcase
  end
endmodule

// breadth: reports | Empty async-reset branch leaving state register uninitialized is reported.
// pair: p4
module empty_reset_branch_missing_state (
    input  wire clk,
    input  wire rst_n
);
  reg [1:0] state;

  always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      // Empty reset branch: state unassigned
    end else begin
      case (state)
        2'b00:   state <= 2'b01;
        2'b01:   state <= 2'b00;
        default: state <= 2'b00;
      endcase
    end
  end
endmodule

// breadth: clean | Synchronous reset sequential block is not reported by MISSING_STATE_REGISTER_RESET.
// pair: p4
module sync_reset_block_clean_for_this_rule (
    input  wire clk,
    input  wire rst
);
  // Synchronous reset has no structural sensitivity marker: rule is async-only
  reg [1:0] state;

  always_ff @(posedge clk) begin
    if (rst) state <= 2'b00;
    else case (state)
      2'b00:   state <= 2'b01;
      2'b01:   state <= 2'b00;
      default: state <= 2'b00;
    endcase
  end
endmodule

// breadth: clean | Non-state datapath register without case statement is not reported.
module non_state_register_missing_reset (
    input  wire       clk,
    input  wire       rst_n,
    input  wire [7:0] d,
    output reg  [7:0] q
);
  // Pure datapath register without case statement is not an FSM state register
  always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      // q not assigned
    end else begin
      q <= d;
    end
  end
endmodule

// breadth: clean | Enum-typed state register properly assigned in async-reset branch is not reported.
module enum_state_async_reset_covered (
    input  wire clk,
    input  wire rst_n
);
  typedef enum logic [1:0] {
    ST_0 = 2'b00,
    ST_1 = 2'b01
  } fsm_t;

  fsm_t st;

  always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) st <= ST_0;
    else case (st)
      ST_0:    st <= ST_1;
      ST_1:    st <= ST_0;
      default: st <= ST_0;
    endcase
  end
endmodule
