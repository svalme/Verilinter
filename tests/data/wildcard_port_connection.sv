module child_wildcard(
    input logic a,
    input logic b,
    output logic y
);
    assign y = a & b;
endmodule

module top_wildcard(
    input logic a,
    input logic b,
    output logic y
);
    child_wildcard u_wild(.*);
endmodule
