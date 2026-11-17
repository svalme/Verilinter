// Breadth tests for NO_FOREACH_LOOP.
// Tests the prohibition of foreach loops.

// breadth: reports | Banned foreach loop iterating over array
// pair: foreach_vs_for
module b_rep_foreach (input logic clk, output int sum);
    int arr [4];
    always_comb begin
        sum = 0;
        foreach (arr[i]) begin
            sum += arr[i];
        end
    end
endmodule

// breadth: clean | Procedural index loop instead of foreach loop
// pair: foreach_vs_for
module b_clean_for (input logic clk, output int sum);
    int arr [4];
    always_comb begin
        sum = 0;
        for (int i = 0; i < 4; i++) begin
            sum += arr[i];
        end
    end
endmodule

// breadth: clean | Word foreach in comment or string literal
module b_clean_comment (input logic a, output logic b);
    // foreach loop is not supported in synthesis
    assign b = a;
    localparam string MSG = "foreach statement banned";
endmodule

// breadth: reports | Banned foreach loop nested in generate block
module b_rep_generate (output int sum);
    int arr [4];
    generate
        if (1) begin : g_blk
            always_comb begin
                sum = 0;
                foreach (arr[i]) begin
                    sum += arr[i];
                end
            end
        end
    endgenerate
endmodule

// breadth: reports | Banned foreach loop inside function
module b_rep_function (input int in_arr [4], output int res);
    function automatic int calc_sum(int a [4]);
        calc_sum = 0;
        foreach (a[i]) begin
            calc_sum += a[i];
        end
    endfunction
    assign res = calc_sum(in_arr);
endmodule

// breadth: reports | Multiple foreach loops in module
// expect: 2
module b_rep_count (output int s1, s2);
    int arr1 [4];
    int arr2 [4];
    always_comb begin
        s1 = 0;
        foreach (arr1[i]) begin
            s1 += arr1[i];
        end
        s2 = 0;
        foreach (arr2[j]) begin
            s2 += arr2[j];
        end
    end
endmodule
