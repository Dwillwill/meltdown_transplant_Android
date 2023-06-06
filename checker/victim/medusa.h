#include <signal.h>
#include <unistd.h>
#include <string.h>
#include <stdio.h>
#include <stdint.h>
#include <stdbool.h>
#include <stdlib.h>
#include <time.h>
#include <pthread.h>
#include <sched.h>
#include <sys/mman.h>
#include <setjmp.h>

#include "ptedit_header.h"

// #include "cpu_prepare_header.h"

#include "cacheUtils.h"

#define PAGE_SIZE 4096

extern uint8_t * ProbeTable;

extern uint8_t * address_UC;
extern uint8_t * address_WT;
extern uint8_t * address_WB;
extern uint8_t * address_normal;

extern uint8_t * address_shareable;
extern uint8_t * address_unpredictable;
extern uint8_t * addresses_inner_shareable;
extern uint8_t * addresses_outer_shareable;

extern uint8_t * addresses_not_accessed;
extern uint8_t * addresses_accessed;

extern uint8_t * addresses_global;
extern uint8_t * addresses_non_global;

extern uint8_t * address_contiguous;
extern uint8_t * address_non_contiguous;

extern uint8_t * address_non_secure;
extern uint8_t * address_secure;

uint8_t * address_unaligned ;
uint8_t * address_uncanonical;
uint8_t * address_crosspage;

jmp_buf trycatch_buf;

void unblock_signal(int signum __attribute__((__unused__))) {
    sigset_t sigs;
    sigemptyset(&sigs);
    sigaddset(&sigs, signum);
    sigprocmask(SIG_UNBLOCK, &sigs, NULL);
}

void trycatch_segfault_handler(int signum) {
    //online cpu
    (void)signum;
    unblock_signal(SIGSEGV);
    unblock_signal(SIGBUS);
    unblock_signal(SIGILL);
    longjmp(trycatch_buf, 1);
}

extern uint64_t s_fill();

void setup_fh(){
    signal(SIGSEGV, trycatch_segfault_handler);
    signal(SIGILL, trycatch_segfault_handler);
    signal(SIGBUS, trycatch_segfault_handler);
}


void flush_pages(){
    uint8_t * ptr = NULL;
    
    for(int i = 0; i < 5; i++){
        ptr = (uint8_t *)&address_UC + i * PAGE_SIZE;
        flush(ptr);

        ptr = (uint8_t *)&address_WT + i * PAGE_SIZE;
        flush(ptr);

        ptr = (uint8_t *)&address_WB + i * PAGE_SIZE;
        flush(ptr);

        ptr = (uint8_t *)&address_normal + i * PAGE_SIZE;
        flush(ptr);

        //setup shareable attribute
        ptr = (uint8_t *)&address_shareable + i * PAGE_SIZE;
        flush(ptr);

        ptr = (uint8_t *)&address_unpredictable + i * PAGE_SIZE;
        flush(ptr);
        
        ptr = (uint8_t *)&addresses_inner_shareable + i * PAGE_SIZE;
        flush(ptr);
        
        ptr = (uint8_t *)&addresses_outer_shareable + i * PAGE_SIZE;
        flush(ptr);

        //setup access flag
        ptr = (uint8_t *)&addresses_not_accessed + i * PAGE_SIZE;
        flush(ptr);

        ptr = (uint8_t *)&addresses_accessed + i * PAGE_SIZE;
        flush(ptr);

        //setup global
        ptr = (uint8_t *)&addresses_global + i * PAGE_SIZE;
        flush(ptr);

        ptr = (uint8_t *)&addresses_non_global + i * PAGE_SIZE;
        flush(ptr);

        //setup contiguouss
        ptr = (uint8_t *)&address_contiguous + i * PAGE_SIZE;
        flush(ptr);

        ptr = (uint8_t *)&address_non_contiguous + i * PAGE_SIZE;
        flush(ptr);

        //setup permission;

        //setup secure
        ptr = (uint8_t *)&address_non_secure + i * PAGE_SIZE;
        flush(ptr);

        ptr = (uint8_t *)&address_secure + i * PAGE_SIZE;
        flush(ptr);
    }
}

int set_pages(){
    uint8_t * ptr = NULL;
    ptedit_entry_t entry;

    int uc_mt = ptedit_find_first_mt(PTEDIT_MT_UC);
    int wt_mt = ptedit_find_first_mt(PTEDIT_MT_WT);
    int wb_mt = ptedit_find_first_mt(PTEDIT_MT_WB);

    if (ptedit_init()) {
        printf("Error: Could not initalize PTEditor, did you load the kernel module?\n");
        return -1;
    }

    for(int i = 0; i < 5; i++){
        //setup different memory type
        ptr = (uint8_t *)&address_UC + i * PAGE_SIZE;
        ptr[0] = ptr[0] + 1 - 1;
        entry = ptedit_resolve(ptr, 0);
        entry.pte = ptedit_apply_mt(entry.pte, uc_mt);
        entry.valid = PTEDIT_VALID_MASK_PTE;
        ptedit_update(ptr, 0, &entry);

        ptr = (uint8_t *)&address_WT + i * PAGE_SIZE;
        ptr[0] = ptr[0] + 1 - 1;
        entry = ptedit_resolve(ptr, 0);
        entry.pte = ptedit_apply_mt(entry.pte, wt_mt);
        ptedit_update(ptr, 0, &entry);

        ptr = (uint8_t *)&address_WB + i * PAGE_SIZE;
        ptr[0] = ptr[0] + 1 - 1;
        entry = ptedit_resolve(ptr, 0);
        entry.pte = ptedit_apply_mt(entry.pte, wb_mt);
        entry.valid = PTEDIT_VALID_MASK_PTE;
        ptedit_update(ptr, 0, &entry);

        ptr = (uint8_t *)&address_normal + i * PAGE_SIZE;
        ptr[0] = ptr[0] + 1 - 1;

        //setup shareable attribute
        ptr = (uint8_t *)&address_shareable + i * PAGE_SIZE;
        ptr[0] = ptr[0] + 1 - 1;
        ptedit_pte_clear_bit(ptr, 0, PTEDIT_PAGE_BIT_SHARE_BIT0);
        ptedit_pte_clear_bit(ptr, 0, PTEDIT_PAGE_BIT_SHARE_BIT1);

        ptr = (uint8_t *)&address_unpredictable + i * PAGE_SIZE;
        ptr[0] = ptr[0] + 1 - 1;
        ptedit_pte_clear_bit(ptr, 0, PTEDIT_PAGE_BIT_SHARE_BIT0);
        ptedit_pte_set_bit(ptr, 0, PTEDIT_PAGE_BIT_SHARE_BIT1);
        
        ptr = (uint8_t *)&addresses_inner_shareable + i * PAGE_SIZE;
        ptr[0] = ptr[0] + 1 - 1;
        ptedit_pte_set_bit(ptr, 0, PTEDIT_PAGE_BIT_SHARE_BIT0);
        ptedit_pte_clear_bit(ptr, 0, PTEDIT_PAGE_BIT_SHARE_BIT1);
        
        ptr = (uint8_t *)&addresses_outer_shareable + i * PAGE_SIZE;
        ptr[0] = ptr[0] + 1 - 1;
        ptedit_pte_set_bit(ptr, 0, PTEDIT_PAGE_BIT_SHARE_BIT0);
        ptedit_pte_set_bit(ptr, 0, PTEDIT_PAGE_BIT_SHARE_BIT1);

        //setup access flag
        ptr = (uint8_t *)&addresses_not_accessed + i * PAGE_SIZE;
        ptr[0] = ptr[0] + 1 - 1;
        ptedit_pte_clear_bit(ptr, 0, PTEDIT_PAGE_BIT_ACCESSED);

        ptr = (uint8_t *)&addresses_accessed + i * PAGE_SIZE;
        ptr[0] = ptr[0] + 1 - 1;
        ptedit_pte_set_bit(ptr, 0, PTEDIT_PAGE_BIT_ACCESSED);

        //setup global
        ptr = (uint8_t *)&addresses_global + i * PAGE_SIZE;
        ptr[0] = ptr[0] + 1 - 1;
        ptedit_pte_clear_bit(ptr, 0, PTEDIT_PAGE_BIT_NOT_GLOBAL);

        ptr = (uint8_t *)&addresses_non_global + i * PAGE_SIZE;
        ptr[0] = ptr[0] + 1 - 1;
        ptedit_pte_set_bit(ptr, 0, PTEDIT_PAGE_BIT_NOT_GLOBAL);

        //setup contiguous
        ptr = (uint8_t *)&address_contiguous + i * PAGE_SIZE;
        ptr[0] = ptr[0] + 1 - 1;
        ptedit_pte_set_bit(ptr, 0, PTEDIT_PAGE_BIT_CONTIGUOUS);

        ptr = (uint8_t *)&address_non_contiguous + i * PAGE_SIZE;
        ptr[0] = ptr[0] + 1 - 1;
        ptedit_pte_clear_bit(ptr, 0, PTEDIT_PAGE_BIT_CONTIGUOUS);

        //setup permission;

        //setup secure
        ptr = (uint8_t *)&address_non_secure + i * PAGE_SIZE;
        ptr[0] = ptr[0] + 1 - 1;
        ptedit_pte_set_bit(ptr, 0, PTEDIT_PAGE_BIT_NON_SECURE);

        ptr = (uint8_t *)&address_secure + i * PAGE_SIZE;
        ptr[0] = ptr[0] + 1 - 1;
        ptedit_pte_clear_bit(ptr, 0, PTEDIT_PAGE_BIT_NON_SECURE);
    }

    ptedit_cleanup();
}

size_t libkdump_virt_to_phys(size_t virtual_address) {
  size_t phys = 0;

	ptedit_entry_t entry;

	if (ptedit_init()) {
      printf("Error: Could not initalize PTEditor, did you load the kernel module?\n");
      return 1;
  }

  entry = ptedit_resolve(virtual_address, 0);


  phys = (ptedit_get_pfn(entry.pte) << 12) | (((size_t)virtual_address) & 0xfff);

  ptedit_cleanup();

  return phys;
}

void ouput_address(){
    uint8_t* ptr;

    ptr = (uint8_t *)&address_UC;
    printf("0x%zx\n", libkdump_virt_to_phys(ptr));
    fflush(stdout);

    ptr = (uint8_t *)&address_WT;
    printf("0x%zx\n", libkdump_virt_to_phys(ptr));
    fflush(stdout);

    ptr = (uint8_t *)&address_WB;
    printf("0x%zx\n", libkdump_virt_to_phys(ptr));
    fflush(stdout);

    ptr = (uint8_t *)&address_normal;
    printf("0x%zx\n", libkdump_virt_to_phys(ptr));
    fflush(stdout);

    //setup shareable attribute
    ptr = (uint8_t *)&address_shareable;
    printf("0x%zx\n", libkdump_virt_to_phys(ptr));
    fflush(stdout);

    ptr = (uint8_t *)&address_unpredictable;
    printf("0x%zx\n", libkdump_virt_to_phys(ptr));
    fflush(stdout);

    ptr = (uint8_t *)&addresses_inner_shareable;
    printf("0x%zx\n", libkdump_virt_to_phys(ptr));
    fflush(stdout);

    ptr = (uint8_t *)&addresses_outer_shareable;
    printf("0x%zx\n", libkdump_virt_to_phys(ptr));
    fflush(stdout);

    //setup access flag
    ptr = (uint8_t *)&addresses_not_accessed;
    printf("0x%zx\n", libkdump_virt_to_phys(ptr));
    fflush(stdout);

    ptr = (uint8_t *)&addresses_accessed;
    printf("0x%zx\n", libkdump_virt_to_phys(ptr));
    fflush(stdout);

    //setup global
    ptr = (uint8_t *)&addresses_global;
    printf("0x%zx\n", libkdump_virt_to_phys(ptr));
    fflush(stdout);

    ptr = (uint8_t *)&addresses_non_global;
    printf("0x%zx\n", libkdump_virt_to_phys(ptr));
    fflush(stdout);

    //setup contiguous
    ptr = (uint8_t *)&address_contiguous;
    printf("0x%zx\n", libkdump_virt_to_phys(ptr));
    fflush(stdout);

    ptr = (uint8_t *)&address_non_contiguous;
    printf("0x%zx\n", libkdump_virt_to_phys(ptr));
    fflush(stdout);

    //setup permission;

    //setup secure
    ptr = (uint8_t *)&address_non_secure;
    printf("0x%zx\n", libkdump_virt_to_phys(ptr));
    fflush(stdout);

    ptr = (uint8_t *)&address_secure;
    printf("0x%zx\n", libkdump_virt_to_phys(ptr));
    fflush(stdout);

    // virtual address
    printf("0x%zx\n", (uint8_t *)&address_UC);
    fflush(stdout);

    printf("0x%zx\n", (uint8_t *)&address_WT);
    fflush(stdout);
    printf("0x%zx\n", (uint8_t *)&address_WB);
    fflush(stdout);
    printf("0x%zx\n", (uint8_t *)&address_normal);
    fflush(stdout);

    printf("0x%zx\n", (uint8_t *)&address_shareable);
    fflush(stdout);
    printf("0x%zx\n", (uint8_t *)&address_unpredictable);
    fflush(stdout);
    printf("0x%zx\n", (uint8_t *)&addresses_inner_shareable);
    fflush(stdout);
    printf("0x%zx\n", (uint8_t *)&addresses_outer_shareable);
    fflush(stdout);
    
    printf("0x%zx\n", (uint8_t *)&addresses_not_accessed);
    fflush(stdout);
    printf("0x%zx\n", (uint8_t *)&addresses_accessed);
    fflush(stdout);

    printf("0x%zx\n", (uint8_t *)&addresses_global);
    fflush(stdout);
    printf("0x%zx\n", (uint8_t *)&addresses_non_global);
    fflush(stdout);

    printf("0x%zx\n", (uint8_t *)&address_contiguous);
    fflush(stdout);
    printf("0x%zx\n", (uint8_t *)&address_non_contiguous);
    fflush(stdout);

    printf("0x%zx\n", (uint8_t *)&address_non_secure);
    fflush(stdout);
    printf("0x%zx\n", (uint8_t *)&address_secure);
    fflush(stdout);
}

void init(){
    set_pages();
    ouput_address();

    printf("hello");

    // flush_pages();
    setup_fh();
}