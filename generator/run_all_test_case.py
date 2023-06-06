#!/usr/bin/env python3

import sys, random, math, time, subprocess, os, re
from pathlib import Path
import shutil 
import json
import faulthandler
import time

def run_cmd(cmdstr):
    # cmd = cmdstr.split()
    proc = subprocess.Popen(cmdstr, stdout=subprocess.PIPE, shell=True)
    proc.wait()

    return proc.stdout.read().decode('utf8')

def run_cmd_output(cmdstr):
    proc = subprocess.Popen(cmdstr, stdout=subprocess.PIPE, stdin=subprocess.PIPE, shell=True)
    # proc.wait()

    # p.stdin.write("shunya\n".encode('utf-8'))
    ret = []
    while (proc.poll() is None and len(ret) != 32):
        line = str(proc.stdout.readline())
        line = line.replace('b\'', '')
        line = line.replace('\\n', '')
        line = line.replace('\'', '')

        ret.append(line)

    return ret

def stop_victim():

    info = run_cmd("ps -ef | grep victim")
    info = info.split("\n")

    pid_victim = []

    for i in range(len(info)):
        if "victim" in info[i]:
            info_str = info[i]

            info_str = re.sub(' +', ' ', info_str)
            pid_victim.append(info_str.split(" ")[1])

    for i in pid_victim:
        run_cmd("kill -KILL " + i + " 2> /dev/null")

def make(role, path):
    shell = "cd " + path + "/" +role+ " && make clean && make -s"
    os.system(shell)

def del_source_code(role, path):
    shell_cp = "cp " + path + "/" + role + "/"+ role + "_bin " + path + "/"
    shell_del_source_code = "rm -rf " + path + "/" + role + "/"
    
    os.system(shell_cp)
    os.system(shell_del_source_code)

def del_binary(role, path):
    shell = "rm " + path + "/" + role + "_bin"

    os.system(shell)

# type 
def run_attacker(addr, index_victim_address, dir, type):
    shell_start_attacker = "taskset -c 0 timeout 3 ./"+ dir +"/attacker_bin %s" % (addr)

    print(shell_start_attacker)

    info = run_cmd(shell_start_attacker)

    if len(info) != 0:
        path = dir+"/config"

        print(path)

        file = open(path,"r+")
        str_ = file.read()
        print("======================") 
        print(info)
        print("++++++++++++++++++++++")
        print("######################")
        print("index:"+str(index_victim_address))
        print("type:"+type)
        print("info:"+str_)
        print("++++++++++++++++++++++")
       
        file.close()


# 1. 进入每一个test case的目录内，
# 2. 编译victim，attacker，
# 3. 运行victim
# 4. 运行attacker

def start():
    test_case_counter = 0

    current_path = os.getcwd()

    kernel_address = 0xffff000009310840
    linear_address = 0xffff000000000000
    virtual_address = 0

    for root, dirs, files in os.walk(current_path):
        for dir in dirs:
            print("run:"+dir)

            shell_start_victim = "taskset -c 0 ./"+ dir +"/victim_bin"

            victim_addr_info = run_cmd_output(shell_start_victim)

            victim_addr_physical = victim_addr_info[0:16]
            victim_addr_virtual = victim_addr_info[16:32]

            if len(victim_addr_virtual) != 16:
                print("error!!! the length of victim_addr_virtual is not 16")
                # exit(-1)
                continue

            for i in range(16):
                addr_virtual = victim_addr_virtual[i]
                addr_physical = victim_addr_physical[i]

                run_attacker(addr_virtual, i, dir, "virtual")
                run_attacker(hex(linear_address + int(addr_physical, 16)), i, dir, "linear")
                run_attacker(hex(kernel_address), i, dir, "kernel")
                

            stop_victim()

            del_binary("attacker", dir)
            del_binary("victim", dir)

            test_case_counter += 1

            print("test_case_counter: " + str(test_case_counter))

        break

def compile_all():
    current_path = os.getcwd()

    for root, dirs, files in os.walk(current_path):
        for dir in dirs:
            print("compile:"+dir)

            make("attacker", dir)
            make("victim", dir)
            del_source_code("attacker", dir)
            del_source_code("victim", dir)
  
        break
        
def main():
    compile_all()

    # start()

    print("end")

if __name__ == "__main__":
    main()
