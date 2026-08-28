module dpi_import_export_demo;
    import "DPI-C" function int c_func(int a);
    export "DPI-C" function dpi_import_export_demo_export;

    function void dpi_import_export_demo_export();
    endfunction
endmodule
