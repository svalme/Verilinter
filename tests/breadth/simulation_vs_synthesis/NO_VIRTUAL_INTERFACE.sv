// Breadth tests for NO_VIRTUAL_INTERFACE.
// Tests the prohibition of virtual interface declarations.

// breadth: reports | Banned virtual interface variable declaration
// pair: virtual_interface_vs_port
interface bus_if;
    logic req;
endinterface

module b_rep_vif;
    virtual bus_if vif;
endmodule

// breadth: clean | Direct interface port connection without virtual keyword
// pair: virtual_interface_vs_port
interface bus_port_if;
    logic req;
endinterface

module b_clean_itf_port (bus_port_if port_if);
    assign port_if.req = 1'b0;
endmodule

// breadth: clean | Word virtual interface in comment or string literal
module b_clean_comment (input logic a, output logic b);
    // virtual interface handles are used for OOP testbenches
    assign b = a;
    localparam string MSG = "virtual interface banned";
endmodule

// breadth: reports | Banned virtual interface inside class
interface mem_if;
    logic clk;
endinterface

module b_rep_class_vif;
    class Driver;
        virtual mem_if vif;
    endclass
endmodule

// breadth: reports | Banned virtual interface inside package
interface ctrl_if;
    logic en;
endinterface

package b_pkg_vif;
    typedef virtual ctrl_if ctrl_vif_t;
endpackage

// breadth: reports | Multiple virtual interface declarations
// expect: 2
interface d_if;
    logic d;
endinterface

module b_rep_count;
    virtual d_if vif1;
    virtual d_if vif2;
endmodule

// breadth: clean | Interface instance and direct interface port connection
interface b_raw_bus_if;
    logic clk;
endinterface

module b_sub_dev (b_raw_bus_if port_if);
endmodule

module b_clean_neighbor_itf_inst;
    b_raw_bus_if bus ();
    b_sub_dev u_sub (bus);
endmodule
