// scenario: reports | A local variable of a function read before its write.
// pair: local-versus-module-variable
module top(output logic [3:0] o);
  function automatic logic [3:0] f(input logic [3:0] a);
    logic [3:0] t;
    f = t;
    t = a;
  endfunction
  assign o = f(4'd1);
endmodule

// scenario: clean | A module variable read in a function that a task writes: the order in the file says nothing, the call order decides.
// pair: local-versus-module-variable
module top(input logic clk);
  string decoded_str;
  logic [9:0] data_accessed;
  function automatic void dump(int fh);
    if ((data_accessed & 10'd1) != 0) $display("%s", decoded_str);
  endfunction
  task automatic decode_one(input string mnemonic);
    data_accessed = 10'd1;
    decoded_str = mnemonic;
  endtask
  always @(posedge clk) begin
    decode_one("add");
    dump(1);
  end
endmodule

// scenario: reports | A variable read before its blocking write in one combinational block.
module top(input logic a, output logic y);
  logic t;
  always_comb begin
    y = t;
    t = a;
  end
endmodule

// scenario: clean | A variable written before it is read in the same block.
module top(input logic a, output logic y);
  logic t;
  always_comb begin
    t = a;
    y = t;
  end
endmodule

// scenario: clean | The members of an interface that no module in the file uses are driven by whoever connects to it.
interface stream_intf (input logic clk_i);
  logic data;
  logic valid;
  logic ready;
  assert property (@(posedge clk_i) valid && !ready |=> $stable(data));
endinterface

// scenario: clean | A string written by $sformat is written, not read.
module top;
  string file_name;
  initial begin
    $sformat(file_name, "%s_%h.log", "a", 4);
    $display("%s", file_name);
  end
endmodule
