.global s_fill 
s_fill: 
adrp X17, address_UC 
add X17, X17, :lo12:address_UC 
ldrb W6, [X17] 
adrp X11, address_WT 
add X11, X11, :lo12:address_WT 
ldrb W4, [X11] 
adrp X1, address_WB 
add X1, X1, :lo12:address_WB 
ldrb W8, [X1] 
adrp X8, address_normal 
add X8, X8, :lo12:address_normal 
ldrb W11, [X8] 
adrp X19, address_shareable 
add X19, X19, :lo12:address_shareable 
ldrb W4, [X19] 
adrp X7, address_unpredictable 
add X7, X7, :lo12:address_unpredictable 
ldrb W14, [X7] 
adrp X4, addresses_inner_shareable 
add X4, X4, :lo12:addresses_inner_shareable 
ldrb W14, [X4] 
adrp X11, addresses_outer_shareable 
add X11, X11, :lo12:addresses_outer_shareable 
ldrb W27, [X11] 
adrp X19, addresses_not_accessed 
add X19, X19, :lo12:addresses_not_accessed 
ldrb W14, [X19] 
adrp X11, addresses_accessed 
add X11, X11, :lo12:addresses_accessed 
ldrb W7, [X11] 
adrp X27, addresses_global 
add X27, X27, :lo12:addresses_global 
ldrb W4, [X27] 
adrp X7, addresses_non_global 
add X7, X7, :lo12:addresses_non_global 
ldrb W14, [X7] 
adrp X6, address_contiguous 
add X6, X6, :lo12:address_contiguous 
ldrb W11, [X6] 
adrp X7, address_non_contiguous 
add X7, X7, :lo12:address_non_contiguous 
ldrb W8, [X7] 
adrp X19, address_non_secure 
add X19, X19, :lo12:address_non_secure 
ldrb W11, [X19] 
adrp X8, address_secure 
add X8, X8, :lo12:address_secure 
ldrb W4, [X8] 
ret