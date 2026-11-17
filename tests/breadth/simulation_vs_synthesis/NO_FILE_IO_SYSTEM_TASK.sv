// Breadth tests for NO_FILE_IO_SYSTEM_TASK.
// Tests the prohibition of file I/O system tasks ($fopen, $fclose, $fdisplay, etc.).

// breadth: reports | Banned $fopen system task opening file handle
// pair: fopen_vs_internal_regs
module b_rep_fopen;
    int fd;
    initial begin
        fd = $fopen("log.txt", "w");
    end
endmodule

// breadth: clean | Hardware registers without file I/O operations
// pair: fopen_vs_internal_regs
module b_clean_regs (input logic clk, input logic [7:0] in, output logic [7:0] out);
    always_ff @(posedge clk) begin
        out <= in;
    end
endmodule

// breadth: clean | Word $fopen in comment or string literal
module b_clean_comment (input logic a, output logic b);
    // $fopen and $fclose are simulation-only file operations
    assign b = a;
    localparam string MSG = "$fopen is disallowed in synthesizable RTL";
endmodule

// breadth: reports | Banned $fdisplay system task inside generate block
module b_rep_gen_fdisplay;
    int fd;
    generate
        if (1) begin : g_blk
            initial begin
                $fdisplay(fd, "Data line");
            end
        end
    endgenerate
endmodule

// breadth: reports | Banned $fclose system task in initial block
module b_rep_fclose;
    int fd;
    initial begin
        $fclose(fd);
    end
endmodule

// breadth: reports | Multiple file I/O system tasks in initial block
// expect: 2
module b_rep_count;
    int fd;
    initial begin
        fd = $fopen("test.dat", "r");
        $fclose(fd);
    end
endmodule

// breadth: clean | Constant system function clog2 and display instead of file io
module b_clean_neighbor_funcs;
    localparam int DEPTH = $clog2(64);
    initial begin
        $display("Depth calculated: %0d", DEPTH);
    end
endmodule
