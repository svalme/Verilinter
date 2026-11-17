// breadth: reports | Two separate if generates that give blocks the same label redefine that label, even when their conditions exclude each other.
// pair: if-branches-vs-separate-ifs
module separate_ifs_same_label #(
    parameter int P = 1
);
  generate
    if (P == 1) begin : gen_mode
      wire mode_one;
    end
    if (P != 1) begin : gen_mode
      wire mode_other;
    end
  endgenerate
endmodule

// breadth: clean | The if and else branches of one generate may share a label because only one branch is elaborated.
// pair: if-branches-vs-separate-ifs
module if_else_duplicate_label #(
    parameter int MODE = 0
);
  generate
    if (MODE == 0) begin : gen_mode
      wire mode_zero;
    end else begin : gen_mode
      wire mode_nonzero;
    end
  endgenerate
endmodule

// breadth: clean | Distinct labels on the if and else branches of one generate are not reported.
module if_else_distinct_labels #(
    parameter int MODE = 0
);
  generate
    if (MODE == 0) begin : gen_mode_zero
      wire mode_zero;
    end else begin : gen_mode_other
      wire mode_nonzero;
    end
  endgenerate
endmodule

// breadth: reports | A case generate and an if generate in one scope that use the same label redefine it.
// pair: case-items-vs-case-and-if
module case_and_if_same_label #(
    parameter int SEL = 0
);
  generate
    case (SEL)
      0: begin : gen_bus
        wire [7:0] bus_a;
      end
      default: begin : gen_other
        wire [7:0] bus_default;
      end
    endcase
    if (SEL == 0) begin : gen_bus
      wire [7:0] bus_b;
    end
  endgenerate
endmodule

// breadth: clean | Two items of one case generate may share a label because only one item is elaborated.
// pair: case-items-vs-case-and-if
module case_generate_duplicate_label #(
    parameter int SEL = 0
);
  generate
    case (SEL)
      0: begin : gen_bus
        wire [7:0] bus_a;
      end
      1: begin : gen_bus
        wire [7:0] bus_b;
      end
      default: begin : gen_bus_def
        wire [7:0] bus_default;
      end
    endcase
  endgenerate
endmodule

// breadth: clean | A case item and the default item of one case generate may share a label.
module case_default_duplicate_label #(
    parameter int P = 0
);
  generate
    case (P)
      0: begin : gen_common
        wire a;
      end
      default: begin : gen_common
        wire b;
      end
    endcase
  endgenerate
endmodule

// breadth: clean | Distinct labels on the items of one case generate are not reported.
module case_generate_distinct_labels #(
    parameter int SEL = 0
);
  generate
    case (SEL)
      0: begin : gen_bus_zero
        wire [7:0] bus_a;
      end
      1: begin : gen_bus_one
        wire [7:0] bus_b;
      end
      default: begin : gen_bus_def
        wire [7:0] bus_default;
      end
    endcase
  endgenerate
endmodule

// breadth: clean | The same label on two items of a case generate nested in an if generate is not reported.
module nested_case_generate_duplicate #(
    parameter int OUTER = 1,
    parameter int INNER = 0
);
  generate
    if (OUTER == 1) begin : gen_outer
      case (INNER)
        0: begin : gen_inner
          wire a;
        end
        1: begin : gen_inner
          wire b;
        end
        default: begin : gen_inner_def
          wire c;
        end
      endcase
    end
  endgenerate
endmodule

// breadth: reports | An else-if chain and a separate if generate that use the same label redefine it.
// pair: else-if-chain-vs-chain-and-other-if
module else_if_chain_and_other_if #(
    parameter int P = 1,
    parameter int Q = 1
);
  if (P == 1) begin : gen_width
    wire a;
  end else if (Q == 1) begin : gen_width
    wire b;
  end
  if (Q == 1) begin : gen_width
    wire c;
  end
endmodule

// breadth: clean | Every branch of one else-if chain may use the same label because only one branch is elaborated.
// pair: else-if-chain-vs-chain-and-other-if
module if_elseif_duplicate_label #(
    parameter int WIDTH = 8
);
  generate
    if (WIDTH == 8) begin : blk_width
      wire [7:0] data;
    end else if (WIDTH == 16) begin : blk_width
      wire [15:0] data;
    end else begin : blk_other
      wire [31:0] data;
    end
  endgenerate
endmodule

// breadth: reports | A loop generate and an if generate that use the same label redefine it.
module loop_and_if_same_label #(
    parameter int N = 2
);
  for (genvar i = 0; i < N; i = i + 1) begin : gen_lane
    wire lane;
  end
  if (N == 2) begin : gen_lane
    wire two_lanes;
  end
endmodule

// breadth: reports | A bare generate block and an if generate that use the same label redefine it.
module bare_block_and_if_same_label #(
    parameter int P = 1
);
  begin : gen_part
    wire a;
  end
  if (P == 1) begin : gen_part
    wire b;
  end
endmodule

// breadth: reports | Constructs written in two separate generate regions of one module share one scope, so the same label in both is reported.
module two_generate_regions_same_label #(
    parameter int P1 = 0,
    parameter int P2 = 1
);
  generate
    if (P1 == 0) begin : gen_common
      wire sig_a;
    end
  endgenerate

  generate
    if (P2 == 1) begin : gen_common
      wire sig_b;
    end
  endgenerate
endmodule

// breadth: reports | Every later construct that reuses a label is reported, so three constructs with one label give two findings.
// expect: 2
module three_ifs_same_label #(
    parameter int P = 1
);
  if (P == 1) begin : gen_x
    wire a;
  end
  if (P == 1) begin : gen_x
    wire b;
  end
  if (P == 1) begin : gen_x
    wire c;
  end
endmodule

// breadth: reports | Two constructs that use the same label inside one generate block are in the same scope and are reported.
// pair: same-scope-vs-nested-scope
module separate_ifs_inside_a_block #(
    parameter int P = 1
);
  if (P == 1) begin : gen_outer
    if (P == 1) begin : gen_part
      wire a;
    end
    if (P == 1) begin : gen_part
      wire b;
    end
  end
endmodule

// breadth: clean | A label reused inside a generate block of that label is in a nested scope, so it is not a redefinition.
// pair: same-scope-vs-nested-scope
module label_reused_in_nested_scope #(
    parameter int P = 1
);
  if (P == 1) begin : gen_outer
    if (P == 1) begin : gen_outer
      wire a;
    end
  end
endmodule

// breadth: clean | The same label in generate constructs of two different modules is not reported.
module generate_label_in_first_module #(
    parameter int P = 1
);
  if (P == 1) begin : gen_common
    wire a;
  end
endmodule

module generate_label_in_second_module #(
    parameter int P = 1
);
  if (P == 1) begin : gen_common
    wire b;
  end
endmodule

// breadth: clean | A labeled loop generate block with no other construct of that label is not reported.
module loop_generate_labeled_clean #(
    parameter int N = 4
);
  generate
    for (genvar i = 0; i < N; i = i + 1) begin : gen_lanes
      wire [7:0] lane_data;
    end
  endgenerate
endmodule

// breadth: clean | Unlabeled blocks have no label to share; they belong to MISSING_GENERATE_BLOCK_LABEL.
module unlabeled_generate_constructs #(
    parameter int P = 1
);
  if (P == 1) begin
    wire a;
  end
  if (P == 1) begin
    wire b;
  end
endmodule

// breadth: clean | Constructs written without begin and end have no label to share.
module unwrapped_generate_statements #(
    parameter int P = 0
);
  generate
    if (P == 0)
      wire a;
    else
      wire b;
  endgenerate
endmodule

// breadth: gap | A generate block label that equals the name of a net in the same scope is also a redefinition, but the rule compares labels only with other generate constructs.
// expect: 1
module label_equals_net_name #(
    parameter int P = 1
);
  wire gen_part;
  if (P == 1) begin : gen_part
    wire a;
  end
endmodule
