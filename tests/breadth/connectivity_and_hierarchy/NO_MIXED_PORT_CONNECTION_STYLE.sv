// Breadth test suite for NO_MIXED_PORT_CONNECTION_STYLE
// Category: connectivity_and_hierarchy
//
// Tests detection of module instances mixing named and ordered (positional)
// port connection styles within the same instance, contrasting with homogeneous
// named/ordered instances, wildcard connections, shorthand connections, and multi-instance separation.

// breadth: reports | Instance mixing named port connection followed by positional connection is reported.
// pair: p1
module child_two_ports (
    input wire a,
    input wire b
);
endmodule

module mixed_named_then_ordered (
    input wire x,
    input wire y
);
  child_two_ports u_child (
      .a(x),
      y // Ordered connection mixed with named connection
  );
endmodule

// breadth: clean | Instance using exclusively named port connections is not reported.
// pair: p1
module homogeneous_named_ports (
    input wire x,
    input wire y
);
  child_two_ports u_child (
      .a(x),
      .b(y)
  );
endmodule

// breadth: reports | Instance mixing positional port connection followed by named connection is reported.
// pair: p2
module mixed_ordered_then_named (
    input wire x,
    input wire y
);
  child_two_ports u_child (
      x,
      .b(y)
  );
endmodule

// breadth: clean | Instance using exclusively positional port connections is not reported.
// pair: p2
module homogeneous_ordered_ports (
    input wire x,
    input wire y
);
  child_two_ports u_child (
      x,
      y
  );
endmodule

// breadth: reports | Instance sandwiching a positional connection between two named connections is reported.
// pair: p3
module child_three_ports (
    input wire a,
    input wire b,
    input wire c
);
endmodule

module mixed_named_ordered_named (
    input wire x,
    input wire y,
    input wire z
);
  child_three_ports u_child (
      .a(x),
      y,
      .c(z)
  );
endmodule

// breadth: clean | Wildcard .* port connection combined with named override is not reported.
// pair: p3
module wildcard_with_named_ports (
    input wire a,
    input wire b
);
  // Wildcard .* with named override is not mixed style
  child_two_ports u_child (
      .*,
      .a(a)
  );
endmodule

// breadth: clean | Dot-name shorthand port connection combined with standard named connection is not reported.
// pair: p4
module shorthand_with_named_ports (
    input wire a,
    input wire b
);
  // .name shorthand alongside standard named connection is clean
  child_two_ports u_child (
      .a,
      .b(b)
  );
endmodule

// breadth: reports | Instance mixing dot-name shorthand connection with positional connection is reported.
// pair: p4
module mixed_shorthand_and_ordered (
    input wire a,
    input wire y
);
  child_two_ports u_child (
      .a,
      y
  );
endmodule

// breadth: clean | Two distinct instances using different connection styles independently are not reported.
module two_instances_different_styles (
    input wire x1,
    input wire y1,
    input wire x2,
    input wire y2
);
  // Distinct instances may use different styles without error
  child_two_ports u_named (
      .a(x1),
      .b(y1)
  );

  child_two_ports u_ordered (
      x2,
      y2
  );
endmodule

// breadth: clean | Instance with empty port connection list is not reported.
module empty_instance_port_list;
  child_two_ports u_empty ();
endmodule
