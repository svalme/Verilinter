module latch_in_always_comb (
    input logic a,
    input logic b,
    output logic y,
    output logic z
);
    always_comb begin
        if (a) begin
            y = b;
            z = b;
        end
    end
endmodule
