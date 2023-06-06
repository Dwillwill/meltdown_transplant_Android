.global s_fill 
s_fill: 
adrp X21, address_UC 
add X21, X21, :lo12:address_UC 
ldrb W10, [X21] 
adrp X3, address_WT 
add X3, X3, :lo12:address_WT 
ldrb W8, [X3] 
adrp X4, address_WB 
add X4, X4, :lo12:address_WB 
ldrb W20, [X4] 
adrp X4, address_normal 
add X4, X4, :lo12:address_normal 
ldrb W24, [X4] 
adrp X2, address_shareable 
add X2, X2, :lo12:address_shareable 
ldrb W18, [X2] 
adrp X24, address_unpredictable 
add X24, X24, :lo12:address_unpredictable 
ldrb W25, [X24] 
adrp X2, addresses_inner_shareable 
add X2, X2, :lo12:addresses_inner_shareable 
ldrb W25, [X2] 
adrp X18, addresses_outer_shareable 
add X18, X18, :lo12:addresses_outer_shareable 
ldrb W4, [X18] 
adrp X4, addresses_not_accessed 
add X4, X4, :lo12:addresses_not_accessed 
ldrb W20, [X4] 
adrp X8, addresses_accessed 
add X8, X8, :lo12:addresses_accessed 
ldrb W24, [X8] 
adrp X10, addresses_global 
add X10, X10, :lo12:addresses_global 
ldrb W4, [X10] 
adrp X24, addresses_non_global 
add X24, X24, :lo12:addresses_non_global 
ldrb W25, [X24] 
adrp X21, address_contiguous 
add X21, X21, :lo12:address_contiguous 
ldrb W25, [X21] 
adrp X18, address_non_contiguous 
add X18, X18, :lo12:address_non_contiguous 
ldrb W8, [X18] 
adrp X24, address_non_secure 
add X24, X24, :lo12:address_non_secure 
ldrb W4, [X24] 
adrp X4, address_secure 
add X4, X4, :lo12:address_secure 
ldrb W25, [X4] 
ret