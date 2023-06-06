.data
.global ProbeTable
ProbeTable:
    .space 4096*256, 0x10

dummy:
    .space 0x1000

junk:
    .space 4096*4, 0x11
//normal address

.global address_UC
address_UC:
    .space 4096*5, 0x12

.global address_WT
address_WT: 
    .space 4096*5, 0x13

.global address_WB
address_WB:
    .space 4096*5, 0x14

.global address_normal
address_normal:
    .space 4096*5, 0x15

.global address_shareable
address_shareable:
    .space 4096*5, 0x16

.global address_unpredictable
address_unpredictable:
    .space 4096*5, 0x17

.global addresses_inner_shareable
addresses_inner_shareable:
    .space 4096*5, 0x18

.global addresses_outer_shareable
addresses_outer_shareable:
    .space 4096*5, 0x19

.global addresses_global
addresses_global: 
    .space 4096*5, 0x1a

.global addresses_non_global
addresses_non_global:
    .space 4096*5, 0x1b

.global address_contiguous
address_contiguous:
    .space 4096*5, 0x1c

.global address_non_contiguous
address_non_contiguous:
    .space 4096*5, 0x1d

.global addresses_not_accessed
addresses_not_accessed:
    .space 4096*5, 0x1e

.global addresses_accessed
addresses_accessed:
    .space 4096*5, 0x1f

.global address_secure
address_secure:
    .space 4096*5, 0x20

.global address_non_secure
address_non_secure:
    .space 4096*5, 0x21

.global address_alignment
address_alignment:
    //16 bit
    .space 4096*5*2, 0x22