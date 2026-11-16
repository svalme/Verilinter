// case: reports | A signal that is read and never driven.
module top(output logic o);
  logic floating;
  assign o = floating;
endmodule

// case: reports | Part of a vector that nothing drives.
module top(output logic [1:0] o);
  logic [1:0] v;
  assign v[0] = 1'b1;
  assign o = v;
endmodule

// case: clean | A signal an instance output drives.
module child(output logic y);
  assign y = 1'b1;
endmodule
module top(output logic o);
  logic w;
  child u1(.y(w));
  assign o = w;
endmodule

// case: clean | A string a system task writes.
module top;
  string file_name;
  initial begin
    $sformat(file_name, "%s", "a");
    $display("%s", file_name);
  end
endmodule

// case: clean | Members of an interface with no user in the file: the connecting modules drive them.
interface stream_intf (input logic clk_i);
  logic data;
  logic valid;
  logic ready;
  assert property (@(posedge clk_i) valid && !ready |=> $stable(data));
endinterface

// case: reports | A member of an interface that a module reads and nothing drives.
interface bus_if;
  logic req;
  logic gnt;
endinterface
module sub(bus_if b);
  logic x;
  assign x = b.req;
endmodule
