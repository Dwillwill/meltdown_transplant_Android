#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <unistd.h>
#include <arpa/inet.h>

struct address{
    char victim_addr_physical[16][64];
    char victim_addr_virtual[16][64];
};


void run_victim_output(struct address * add){
    char buf[1024] = {0}; 
    FILE * fp;
    if((fp = popen("taskset 80 ./victim", "r")) == NULL){
        perror("Fail to popen\n");
        exit(1);
    }
    char * lines[32];
    int i = 0;
    while(fgets(buf, 64, fp) != NULL){
        lines[i] = buf;
        printf("%d\n", i);
        printf("%s",lines[i]);
        if(i < 16){
            strcpy(add->victim_addr_physical[i], buf);
            i++;
        }
        else if(i >= 16){
            strcpy(add->victim_addr_virtual[i-16], buf);
            i++;
        }
        if(i == 32){
            break;
        }
    }
}

void run_attacker(char * addr, char * size){
    FILE * fp;
    char buf[1024] = {0};
    char command[128] = "taskset 80 timeout 3 ./attacker ";

    int client_fd;
    struct sockaddr_in ser_addr;

    strcat(command, addr);
    strcat(command, " ");
    strcat(command, size);
    printf("%s", command);
    if((fp = popen(command, "r")) == NULL){
        perror("Fail to popen\n");
        exit(1);
    }
    while(fgets(buf, 1024, fp) != NULL){
  
    }
}

void stop_victim(){
    FILE * fp;
    char * p;
    char buf[1024] = {0};
    char command[128] = "ps -ef | grep victim";
    char command_kill[128] = "kill ";
    if((fp = popen(command, "r")) == NULL){
        perror("Fail to popen\n");
        exit(1);
    }
    fgets(buf, 1024, fp);
    // printf("%s", buf);
    p = strtok(buf, " ");
    p = strtok(NULL, " ");
    // printf("%s\n", p);
    strncat(command_kill, p, 128);
    if((fp = popen(command_kill, "r")) == NULL){
        perror("Fail to popen\n");
        exit(1);
    }
}
void start(){
    u_int64_t kernel_address = 0xffff000009310840;
    u_int64_t linear_address = 0xffff000000000000;
    u_int64_t virtual_address = 0;

    printf("Run test example...\n");
    
    struct address add;
    int count = 0;
    run_victim_output(&add);
    char * addr;
        
    FILE * fp;
    fp = fopen("help_file", "r+");
    char buf[1024] = {0};
    char point[5] = {0};
    char * att_type, * target_index, *size_att;
    char tp[64], arg2[64];
    int target_idx;
    while(fgets(buf, 1024, fp) != NULL){
            // printf("%s", buf);
        strncpy(point, buf, 4);
            // printf("%s\n", type);
            
        if(strcmp(point, "type") == 0){
            att_type = strtok(buf, ":");
            att_type = strtok(NULL, ":");
            strcpy(tp, att_type);
            // printf("%s\n", p);
        }
        else if(strcmp(point, "targ") == 0){
            target_index = strtok(buf, ":");
            target_index = strtok(NULL, ":");
            sscanf(target_index, "%d", &target_idx);
                // printf("%s\n", p);
        }
        else if(strcmp(point, "size") == 0){
            size_att = strtok(buf, ":");
            size_att = strtok(NULL, ":");
                // printf("%s\n", p);
            strcpy(arg2, size_att);
        }
    }
    printf("%s\n", tp);
    tp[strlen(tp) - 1] = '\0';
    printf("%s\n", tp);

    if(strcmp(tp, "virtual") == 0){
        addr = add.victim_addr_virtual[target_idx];
    }
    else if(strcmp(tp, "linear") == 0){

        u_int64_t addr_phy;
        sscanf(add.victim_addr_physical[target_idx], "%lx", &addr_phy);
        // printf("%lx\n", addr_phy);
        char addr_phy_offset[128];
        sprintf(addr_phy_offset, "%#lx", linear_address + addr_phy);
        // printf("%s\n", addr_phy_offset);
        addr = addr_phy_offset;
    }
    else if(strcmp(tp, "kernel") == 0){
        char kernel_addr[128];
        sprintf(kernel_addr, "%#lx", kernel_address);
        addr = kernel_addr;
    }
    printf("%s\n", addr);
    addr[strlen(addr) - 1] = '\0';
    printf("%s\n", addr);
    run_attacker(addr, arg2);
    stop_victim();
}
int main(){
    start();
    return 0;
}