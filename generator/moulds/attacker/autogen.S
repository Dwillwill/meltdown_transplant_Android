.global s_faulty_load 
s_faulty_load: 
adrp X25, read_only 
add X25, X25, :lo12:read_only 
str X20, [X25] 
ldrsw X3, [X0] 

adrp X4, probe_array 
add X4, X4, :lo12:probe_array 
lsl X3, X3, #12 
ldr X3, [X4, X3] 
ret