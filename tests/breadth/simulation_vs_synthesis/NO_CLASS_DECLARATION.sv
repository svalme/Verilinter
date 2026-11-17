// Breadth tests for NO_CLASS_DECLARATION.
// Tests the prohibition of class declarations in synthesizable code.

// breadth: reports | Banned class declaration inside module
// pair: class_vs_struct
module b_rep_class (input logic clk);
    class Packet;
        int id;
        int len;
    endclass
endmodule

// breadth: clean | Struct declaration instead of OOP class
// pair: class_vs_struct
module b_clean_struct (input logic clk);
    typedef struct packed {
        int id;
        int len;
    } packet_t;
    packet_t pkt;
endmodule

// breadth: clean | Word class in comment or string literal
module b_clean_comment (input logic a, output logic b);
    // class declarations are for testbenches only
    assign b = a;
    localparam string MSG = "class construct is banned in RTL";
endmodule

// breadth: reports | Banned class declaration inside package
package b_pkg_class;
    class Transaction;
        logic [7:0] data;
    endclass
endpackage

// breadth: reports | Banned parameterized class declaration
module b_rep_param_class (input logic clk);
    class Buffer #(parameter int SIZE = 8);
        logic [SIZE-1:0] storage;
    endclass
endmodule

// breadth: reports | Multiple class declarations in module
// expect: 2
module b_rep_count (input logic clk);
    class Header;
        int src;
    endclass

    class Payload;
        int data;
    endclass
endmodule

// breadth: clean | Package with packed struct typedef instead of OOP class
package b_clean_neighbor_pkg;
    typedef struct packed {
        logic [7:0] addr;
        logic [31:0] data;
    } bus_pkt_t;
endpackage
