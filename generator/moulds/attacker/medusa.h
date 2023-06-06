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

#include "cacheUtils.h"

#define PAGE_SIZE 4096

extern uint8_t * ProbeTable;


extern uint8_t * address_normal;


extern uint8_t * address_non_secure;
extern uint8_t * address_secure;

char *read_only;
char *no_access;

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

extern void s_faulty_load(size_t addr);

void setup_fh(){
    signal(SIGSEGV, trycatch_segfault_handler);
    signal(SIGBUS, trycatch_segfault_handler);    
    signal(SIGILL, trycatch_segfault_handler);
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

    //初始化只读和不可访问页面 
    read_only = (char*) mmap(NULL, 5*PAGE_SIZE, PROT_READ, MAP_ANON | MAP_PRIVATE, -1, 0);
    no_access = (char*) mmap(NULL, 5*PAGE_SIZE, PROT_NONE, MAP_ANON | MAP_PRIVATE, -1, 0);

    for(int i = 0; i < 5; i++){
        ptr = (uint8_t *)&address_normal + i * PAGE_SIZE;
        ptr[0] = ptr[0] + 1 - 1;
    }

    ptedit_cleanup();
}
