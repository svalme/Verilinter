module child_adv(
    input logic [3:0] p,
    input logic [5:0] q,
    input logic [3:0] r,
    input logic [7:0] u,
    output logic [3:0] y
);
endmodule

module child_param #(parameter W = 8) (
    input logic [W-1:0] data
);
endmodule

module child_unresolved #(parameter WIDTH) (
    input logic [WIDTH-1:0] data
);
endmodule

module child_two_params #(parameter A = 1, parameter B = 2) (
    input logic x,
    output logic y
);
    assign y = x;
endmodule

module top;
    logic [7:0] bus8;
    logic [3:0] nibble;
    logic [1:0] pair;
    logic [3:0] out_unused;
    logic [31:0] idx;
    logic single;

    child_adv u_slice_mismatch(.p(bus8[5:0]), .q({nibble, pair}), .r({2{pair}}), .u(bus8), .y(out_unused));
    child_adv u_rep_mismatch(.p(bus8[3:0]), .q({nibble, pair}), .r({3{pair}}), .u(5), .y(nibble));
    child_adv u_bad_port(.p(nibble), .qq({nibble, pair}), .r({2{pair}}), .u(bus8), .y(nibble));
    child_adv u_indexed_ok(.p(bus8[idx +: 4]), .q({bus8[2:0], pair, 1'b0}), .r(bus8[1 +: 4]), .u(bus8), .y(nibble));
    child_unresolved u_unknown(.data(bus8));
    child_adv u_extra_ordered(bus8[3:0], bus8[5:0], bus8[3:0], bus8, nibble, idx);
    child_param #(.W(8), .BOGUS_PARAM(4)) u_bad_param_override(.data(bus8));
    child_param #(.W(8), .W(4)) u_dup_param_override(.data(bus8));
    child_two_params #(3, .B(4)) u_mixed_param_override(.x(single), .y(single));
endmodule
