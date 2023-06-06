.data
.global ProbeTable
ProbeTable:
    .space 4096*256, 0x20

dummy:
    .space 0x1000

junk:
    .space 4096*4, 0x21
//normal address

.global address_UC
address_UC:
    .space 4096*5, 0x22

.global address_WT
address_WT: 
    .space 4096*5, 0x23

.global address_WB
address_WB:
    .space 4096*5, 0x24

.global address_normal
address_normal:
    .space 4096*5, 0x25

.global address_shareable
address_shareable:
    .space 4096*5, 0x26

.global address_unpredictable
address_unpredictable:
    .space 4096*5, 0x27

.global addresses_inner_shareable
addresses_inner_shareable:
    .space 4096*5, 0x28

.global addresses_outer_shareable
addresses_outer_shareable:
    .space 4096*5, 0x29

.global addresses_global
addresses_global: 
    .space 4096*5, 0x2a

.global addresses_non_global
addresses_non_global:
    .space 4096*5, 0x2b

.global address_contiguous
address_contiguous:
    .space 4096*5, 0x2c

.global address_non_contiguous
address_non_contiguous:
    .space 4096*5, 0x2d

.global addresses_not_accessed
addresses_not_accessed:
    .space 4096*5, 0x2e

.global addresses_accessed
addresses_accessed:
    .space 4096*5, 0x2f

.global address_secure
address_secure:
    .space 4096*5, 0x30

.global address_non_secure
address_non_secure:
    .space 4096*5, 0x31

.global address_alignment
address_alignment:
    //16 bit
    .space 4096*5, 0x32