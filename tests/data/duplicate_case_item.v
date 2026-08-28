module duplicate_case_item_demo(
    input wire [1:0] sel,
    output reg y
);
    always @(*) begin
        case (sel)
            2'b00: y = 1'b0;
            2'b00: y = 1'b1;
            default: y = 1'b0;
        endcase
    end
endmodule
