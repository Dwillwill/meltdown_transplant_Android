.global s_faulty_load 
s_faulty_load: 
adrp X5, address_normal 
add X5, X5, :lo12:address_normal 
movk X0, #0xff8, lsl #16 
lsl X0, X0, #32 
orr X5, X0, X0 
strb W5, [X5] 
ldrb W0, [X0] 

adrp X7, probe_array 
add X7, X7, :lo12:probe_array 
lsl X0, X0, #12 
ldr X0, [X7, X0] 
ret