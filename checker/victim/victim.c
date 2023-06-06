#include <stdio.h>
#include "medusa.h"

int main(){
    volatile uint8_t junk;
    uint8_t* ptr;

    init();

    while(1){
        if(!setjmp(trycatch_buf)){
            s_fill();
        }

        sleep(1);
    }

    return 0;
}