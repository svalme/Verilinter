module uwire_demo(input a, input b, output c, output d);
    uwire w1;
    wand w2;
    assign w1 = a;
    assign c = w1;
    assign w2 = b;
    assign d = w2;
endmodule
