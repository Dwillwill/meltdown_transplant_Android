#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <unistd.h>
#include <arpa/inet.h>

#define SERVER_PORT 8888
#define BUFF_LEN 512
#define SERVER_IP "172.22.14.235"

struct address{
    char victim_addr_physical[16][64];
    char victim_addr_virtual[16][64];
};


void udp_msg_sender(int fd, struct sockaddr * dst, char * buf){
    socklen_t len;
    struct sockaddr_in src;
    len = sizeof(*dst);
    printf("client:%s\n", buf);
    sendto(fd, buf, BUFF_LEN, 0, dst, len);
    memset(buf, 0, BUFF_LEN);
    recvfrom(fd, buf, BUFF_LEN, 0, (struct sockaddr*)&src, &len);
    printf("server:%s\n", buf);
}



void run_victim_output(struct address * add){
    char buf[1024] = {0};
    FILE * fp;
    if((fp = popen("taskset 80 ./victim_bin", "r")) == NULL){
        perror("Fail to popen\n");
        exit(1);
    }
    char * lines[32];
    int i = 0;
    while(fgets(buf, 64, fp) != NULL){
        lines[i] = buf;
        // printf("%d\n", i);
        // printf("%s",lines[i]);
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

void run_attacker_sendUDP_to_shunya(char * addr, int index, char * type){
    FILE * fp;
    char buf[1024] = {0};
    char command[128] = "taskset 80 timeout 3 ./attacker_bin ";

    int client_fd;
    struct sockaddr_in ser_addr;

    strncat(command, addr, 128);
    printf("%s", command);
    if((fp = popen(command, "r")) == NULL){
        perror("Fail to popen\n");
        exit(1);
    }
    while(fgets(buf, 1024, fp) != NULL){
        // client_fd = socket(AF_INET, SOCK_DGRAM, 0);
        // if(client_fd < 0){
        //     printf("create socket fail!\n");
        //     return -1;
        // }
        // memset(&ser_addr, 0, sizeof(ser_addr));
        // ser_addr.sin_family = AF_INET;
        // ser_addr.sin_addr.s_addr = inet_addr(SERVER_IP);
        // // ser_addr.sin_addr.s_addr = htonl(INADDR_ANY);  //注意网络序转换
        // ser_addr.sin_port = htons(SERVER_PORT);  //注意网络序转换
        // udp_msg_sender(client_fd, (struct sockaddr*)&ser_addr, buf);
        FILE * fp2 = fopen("config", "r+");
        char str_[1024] = {0};
        fgets(str_, 1024, fp2);
        printf("======================\n");
        printf("%s\n", buf);
        printf("++++++++++++++++++++++\n");
        printf("######################\n");
        printf("index:%d\n", index);
        printf("type:%s\n", type);
        printf("info:%s\n", str_);
        printf("++++++++++++++++++++++\n");
        fclose(fp2);
    }
    // close(client_fd);
}

void stop_victim(){
    FILE * fp;
    char * p;
    char buf[1024] = {0};
    char command[128] = "ps -ef | grep victim_bin";
    char command_kill[128] = "kill ";
    if((fp = popen(command, "r")) == NULL){
        perror("Fail to popen\n");
        exit(1);
    }
    fgets(buf, 1024, fp);
    printf("%s", buf);
    p = strtok(buf, " ");
    p = strtok(NULL, " ");
    printf("%s\n", p);
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

    // printf("Run test example...\n");
    
    struct address add;
    int count = 0;
    run_victim_output(&add);
    // for(int j = 0; j < 16; j++){
    //     printf("%s\n", add.victim_addr_physical[j]);
    // }
    // for(int j = 0; j < 16; j++){
    //     count++;
    //     printf("%s\n", add.victim_addr_virtual[j]);
    // }
    // if(count != 16){
    //     printf("error!!! the length of victim_addr_virtual is not 16");
    // }
    // printf("ok\n");
    for(int i = 0; i < 16; i++){
        char * addr_virtual = add.victim_addr_virtual[i];
        char * addr_physical = add.victim_addr_physical[i];

        u_int64_t addr_phy;
        sscanf(addr_physical, "%lx", &addr_phy);
        // printf("%lx\n", addr_phy);

        char addr_phy_offset[128];
        sprintf(addr_phy_offset, "%#lx", linear_address + addr_phy);
        // printf("%s\n", addr_phy_offset);
        
        char kernel_addr[128];
        sprintf(kernel_addr, "%#lx", kernel_address);
        // printf("%s\n", kernel_addr);

        run_attacker_sendUDP_to_shunya(addr_virtual, i, "virtual");
        run_attacker_sendUDP_to_shunya(addr_phy_offset, i, "linear");
        run_attacker_sendUDP_to_shunya(kernel_addr, i, "kernel");
        stop_victim();
    }
}
int main(){
    start();
    return 0;
}
