static inline uint64_t probe(void *addr){
    uint64_t time1,time2,read_data;

    asm volatile(
    "dsb sy \n\t"
    "isb \n\t"
    "mrs %0, PMCCNTR_EL0 \n\t"
    "isb \n\t"
    "ldr %2, [%3] \n\t"
    "dsb ish \n\t"
    "isb \n\t"
    "mrs %1, PMCCNTR_EL0 \n\t"
    "isb \n\t"
    "dsb sy\n\t"
    "dc civac, %3\n\t"
    "dsb sy\n\t"
    : "=&r"(time1), "=&r"(time2), "=&r"(read_data)
    : "r"(addr)
    );

    return time2 - time1;
}

static inline void flush(void *addr) {
        asm volatile ("DC CIVAC, %[ad]" : : [ad] "r" (addr));
        asm volatile("DSB SY");
}
