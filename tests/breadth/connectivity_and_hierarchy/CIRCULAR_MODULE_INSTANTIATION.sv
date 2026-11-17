// Breadth test suite for CIRCULAR_MODULE_INSTANTIATION
// Category: connectivity_and_hierarchy
//
// Tests detection of circular module instantiation topologies (cycles in the
// instantiation graph), covering direct self-instantiation, 2-module mutual cycles,
// and 3-module rings, contrasting with linear hierarchies, DAGs (diamonds), and leaf modules.

// breadth: reports | Direct self-instantiating module creating a 1-node cycle is reported.
// pair: p1
module self_instantiating_cycle;
  self_instantiating_cycle u_recurse ();
endmodule

// breadth: clean | Leaf module without child instantiations is not reported.
// pair: p1
module linear_leaf_module;
endmodule

// breadth: clean | Module instantiating a child module in a linear hierarchy without cycles is not reported.
module linear_top_module;
  linear_leaf_module u_leaf ();
endmodule

// breadth: reports | Mutual 2-module instantiation cycle between modules A and B is reported.
// pair: p2
module mutual_module_a;
  mutual_module_b u_b ();
endmodule

module mutual_module_b;
  mutual_module_a u_a ();
endmodule

// breadth: clean | One-way hierarchical parent-to-child instantiation without back-edges is not reported.
// pair: p2
module hierarchical_parent;
  hierarchical_child u_child ();
endmodule

module hierarchical_child;
endmodule

// breadth: reports | 3-module circular instantiation ring (node 1 -> node 2 -> node 3 -> node 1) is reported.
// pair: p3
module ring_node_1;
  ring_node_2 u_next ();
endmodule

module ring_node_2;
  ring_node_3 u_next ();
endmodule

module ring_node_3;
  ring_node_1 u_cycle ();
endmodule

// breadth: clean | 3-stage linear pipeline hierarchy without feedback edges is not reported.
// pair: p3
module pipeline_stage_1;
  pipeline_stage_2 u_next ();
endmodule

module pipeline_stage_2;
  pipeline_stage_3 u_next ();
endmodule

module pipeline_stage_3;
endmodule

// breadth: reports | 4-module instantiation ring creating a cycle is reported.
// pair: p4
module ring_four_1;
  ring_four_2 u_2 ();
endmodule

module ring_four_2;
  ring_four_3 u_3 ();
endmodule

module ring_four_3;
  ring_four_4 u_4 ();
endmodule

module ring_four_4;
  ring_four_1 u_back ();
endmodule

// breadth: clean | Diamond-shaped DAG hierarchy with multiple branches sharing a leaf module is not reported.
// pair: p4
module diamond_top;
  diamond_branch_a u_a ();
  diamond_branch_b u_b ();
endmodule

module diamond_branch_a;
  diamond_leaf u_leaf ();
endmodule

module diamond_branch_b;
  diamond_leaf u_leaf ();
endmodule

module diamond_leaf;
endmodule

// breadth: clean | Module instantiating multiple distinct instances of the same child module is not reported.
module multi_instance_same_child;
  diamond_leaf u_inst1 ();
  diamond_leaf u_inst2 ();
endmodule
