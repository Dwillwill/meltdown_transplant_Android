#!/usr/bin/env python3
import sys, random, math, time, subprocess, os

from pathlib import Path

import shutil 

import json

import faulthandler

import time

dir_test_case = 0
counter_test_case = 0

limit = None

# 单个测试用例包的数量
single_test_case_num = 100

# 测试用例包的存放目录
test_cases_lib_path = "../test_cases/"

class Fault(object):
    faultType = {
        'ALIGNMENT_FAULT_PC': 'ALIGNMENT_FAULT',
        'ALIGNMENT_FAULT_SP': 'ALIGNMENT_FAULT',
        'ALIGNMENT_FAULT_DATA_ACCESS': 'ALIGNMENT_FAULT',

        'LEVEL_1_PAGE_TABLE': 'MMU_FAULT_LOAD_STORE',
        'LEVEL_2_PAGE_TABLE': 'MMU_FAULT_LOAD_STORE',
        'LEVEL_3_PAGE_TABLE': 'MMU_FAULT_LOAD_STORE',
        'LEVEL_4_PAGE_TABLE': 'MMU_FAULT_LOAD_STORE',
        'TTBR': 'MMU_FAULT_LOAD_STORE',
        'PERMISSION_ACCESS_NON_ACCESSABLE': 'MMU_FAULT_LOAD_STORE',
        'ACCESS_FLAG': 'MMU_FAULT_LOAD_STORE',
        'ACCESS_0': 'MMU_FAULT_LOAD_STORE',
        'ACCESS_UNCANONICAL': 'MMU_FAULT_LOAD_STORE',

        'PERMISSION_ACCESS_READ_ONLY': 'MMU_FAULT_STORE',

        'UNDEFINED_UNALLOCATED': 'UNDEFINED_INSTRUCTION_FAULT',
        'UNDEFINED_DATA_PROCESS_IMMEDIATE': 'UNDEFINED_INSTRUCTION_FAULT',
        'UNDEFINED_BRANCH': 'UNDEFINED_INSTRUCTION_FAULT',
        'UNDEFINED_LOAD_STORE': 'UNDEFINED_INSTRUCTION_FAULT',
        'UNDEFINED_DATA_PROCESS_REG': 'UNDEFINED_INSTRUCTION_FAULT',
        'UNDEFINED_DATA_PROCESS_SIMD': 'UNDEFINED_INSTRUCTION_FAULT',
        'UNDEFINED_DATA_PROCESS_SIMD_1': 'UNDEFINED_INSTRUCTION_FAULT',

        'SVC': 'EXCEPTION_GENERATION_FAULT',
        'HVC': 'EXCEPTION_GENERATION_FAULT',
        'SMC': 'EXCEPTION_GENERATION_FAULT',

        'FLOAT_UNDER_FLOW': 'FLOAT_POINT_FAULT',
        'FLOAT_OVER_FLOW': 'FLOAT_POINT_FAULT',
        'FLOAT_DIVIED_ZERO': 'FLOAT_POINT_FAULT'
    }

    # ------------------------------- alignment fault -------------------------------
    # ------------------ args: 后续参数，在data access中为load的内存类型 --------------
    @staticmethod
    def ALIGNMENT_FAULT_PC(reg, *args):
        temp_instruction = ""

        temp_instruction += "adrp %s, run_nop \n" % reg[0]
        temp_instruction += "add %s, %s, :lo12:run_nop \n" % (reg[0], reg[0])
        temp_instruction += "add %s, %s, #1 \n" % (reg[0], reg[0])
        temp_instruction += "blr %s \n" % reg[0]

        return temp_instruction

    @staticmethod
    def ALIGNMENT_FAULT_SP(reg, *args):
        temp_instruction = ""

        temp_instruction += "add sp, sp, #1 \n"
        temp_instruction += "ldr %s, [sp] \n" % reg[0]

        return temp_instruction

    # 只考虑对不同target进行load，且源寄存器与目标寄存器为同一个 load x*, [x*]
    @staticmethod
    def ALIGNMENT_FAULT_DATA_ACCESS(reg, *args):
        temp_instruction = ""

        temp_instruction += "adrp %s, %s \n " % (reg[0], args[0])
        temp_instruction += "add %s, %s, :lo12:%s \n " % (reg[0], reg[0], args[0])
        temp_instruction += "add %s, %s, #1 \n" % (reg[0], reg[0])

        # if op == "LOAD":
        temp_instruction += "ldxr %s, [%s] \n " % (reg[0], reg[0])
        # else:
        #    temp_instruction += ""

        return temp_instruction

    # ------------------------------- translation fault -------------------------------
    # ------------------------ source_reg: 保存用于操作地址的寄存器 ---------------------
    # ------------------------ target_reg: 保存地址的寄存器 ----------------------------
    @staticmethod
    # args[0] : target
    # args[1] : OpType
    # args[2] : size
    # args[3] : target_reg
    # args[4] : source_reg
    def LEVEL_1_PAGE_TABLE(*args):
        source_reg = args[4]
        target_reg = args[3]
        size = args[2]
        target = args[0]

        temp_instruction = ""

        temp_instruction += "adrp %s, %s \n" % (target_reg[0], target)
        temp_instruction += "add %s, %s, :lo12:%s \n" % (target_reg[0], target_reg[0], target)

        temp_instruction += "movk %s, #0xff8, lsl #16 \n" % source_reg[0]
        temp_instruction += "lsl %s, %s, #32 \n" % (source_reg[0], source_reg[0])
        temp_instruction += "orr %s, %s, %s \n" % (target_reg[0], source_reg[0], source_reg[0])

        if args[1] == "LOAD":
            if size == 8:
                temp_instruction += "ldrb %s, [%s] \n" % (target_reg[1], target_reg[0])
            elif size == 16:
                temp_instruction += "ldrh %s, [%s] \n" % (target_reg[1], target_reg[0])
            elif size == 32:
                temp_instruction += "ldrsw %s, [%s] \n" % (target_reg[0], target_reg[0])
            elif size == 64:
                temp_instruction += "ldr %s, [%s] \n" % (target_reg[0], target_reg[0])

            return temp_instruction

        if args[1] == "STORE":
            if size == 8:
                temp_instruction += "strb %s, [%s] \n" % (target_reg[1], target_reg[0])
            elif size == 16:
                temp_instruction += "strh %s, [%s] \n" % (target_reg[1], target_reg[0])
            elif size == 32:
                temp_instruction += "str %s, [%s] \n" % (target_reg[0], target_reg[0])
            elif size == 64:
                temp_instruction += "str %s, [%s] \n" % (target_reg[0], target_reg[0])

            return temp_instruction

    @staticmethod
    # args[0] : target
    # args[1] : OpType
    # args[2] : size
    # args[3] : target_reg
    # args[4] : source_reg
    def LEVEL_2_PAGE_TABLE(*args):
        source_reg = args[4]
        target_reg = args[3]
        size = args[2]

        temp_instruction = ""

        temp_instruction += "adrp %s, %s \n" % (args[3][0], args[0])
        temp_instruction += "add %s, %s, :lo12:%s \n" % (args[3][0], args[3][0], args[0])

        temp_instruction += "movk %s, #0x7fc, lsl #16 \n" % args[4][0]
        temp_instruction += "lsl %s, %s, #12 \n" % (args[4][0], args[4][0])
        temp_instruction += "orr %s, %s, %s \n" % (args[3][0], args[3][0], args[4][0])

        if args[1] == "LOAD":
            if size == 8:
                temp_instruction += "ldrb %s, [%s] \n" % (args[3][1], args[3][0])
            elif size == 16:
                temp_instruction += "ldrh %s, [%s] \n" % (args[3][1], args[3][0])
            elif size == 32:
                temp_instruction += "ldrsw %s, [%s] \n" % (args[3][0], args[3][0])
            elif size == 64:
                temp_instruction += "ldr %s, [%s] \n" % (args[3][0], args[3][0])

            return temp_instruction

        if args[1] == "STORE":
            if size == 8:
                temp_instruction += "strb %s, [%s] \n" % (args[3][1], args[3][0])
            elif size == 16:
                temp_instruction += "strh %s, [%s] \n" % (args[3][1], args[3][0])
            elif size == 32:
                temp_instruction += "str %s, [%s] \n" % (args[3][0], args[3][0])
            elif size == 64:
                temp_instruction += "str %s, [%s] \n" % (args[3][0], args[3][0])

            return temp_instruction

    @staticmethod
    # args[0] : target
    # args[1] : OpType
    # args[2] : size
    # args[3] : target_reg
    # args[4] : source_reg
    def LEVEL_3_PAGE_TABLE(*args):
        source_reg = args[4]
        target_reg = args[3]
        size = args[2]

        temp_instruction = ""

        temp_instruction += "adrp %s, %s \n" % (args[3][0], args[0])
        temp_instruction += "add %s, %s, :lo12:%s \n" % (args[3][0], args[3][0], args[0])

        temp_instruction += "movk %s, #0x3fe, lsl #16 \n" % args[4][0]
        temp_instruction += "lsl %s, %s, #4 \n" % (args[4][0], args[4][0])
        temp_instruction += "orr %s, %s, %s \n" % (args[3][0], args[3][0], args[4][0])

        if args[1] == "LOAD":
            if size == 8:
                temp_instruction += "ldrb %s, [%s] \n" % (args[3][1], args[3][0])
            elif size == 16:
                temp_instruction += "ldrh %s, [%s] \n" % (args[3][1], args[3][0])
            elif size == 32:
                temp_instruction += "ldrsw %s, [%s] \n" % (args[3][0], args[3][0])
            elif size == 64:
                temp_instruction += "ldr %s, [%s] \n" % (args[3][0], args[3][0])

            return temp_instruction

        if args[1] == "STORE":
            if size == 8:
                temp_instruction += "strb %s, [%s] \n" % (args[3][1], args[3][0])
            elif size == 16:
                temp_instruction += "strh %s, [%s] \n" % (args[3][1], args[3][0])
            elif size == 32:
                temp_instruction += "str %s, [%s] \n" % (args[3][0], args[3][0])
            elif size == 64:
                temp_instruction += "str %s, [%s] \n" % (args[3][0], args[3][0])

            return temp_instruction

    @staticmethod
    # args[0] : target
    # args[1] : OpType
    # args[2] : size
    # args[3] : target_reg
    # args[4] : source_reg
    def LEVEL_4_PAGE_TABLE(*args):
        source_reg = args[4]
        target_reg = args[3]
        size = args[2]

        temp_instruction = ""

        temp_instruction += "adrp %s, %s \n" % (args[3][0], args[0])
        temp_instruction += "add %s, %s, :lo12:%s \n" % (args[3][0], args[3][0], args[0])

        temp_instruction += "movk %s, #0xf000, lsl #16 \n" % args[4][0]
        temp_instruction += "movk %s, #0x1ff, lsl #16 \n" % (args[4][0])
        temp_instruction += "orr %s, %s, %s \n" % (args[3][0], args[3][0], args[4][0])

        if args[1] == "LOAD":
            if size == 8:
                temp_instruction += "ldrb %s, [%s] \n" % (args[3][1], args[3][0])
            elif size == 16:
                temp_instruction += "ldrh %s, [%s] \n" % (args[3][1], args[3][0])
            elif size == 32:
                temp_instruction += "ldrsw %s, [%s] \n" % (args[3][0], args[3][0])
            elif size == 64:
                temp_instruction += "ldr %s, [%s] \n" % (args[3][0], args[3][0])

            return temp_instruction

        if args[1] == "STORE":
            if size == 8:
                temp_instruction += "strb %s, [%s] \n" % (args[3][1], args[3][0])
            elif size == 16:
                temp_instruction += "strh %s, [%s] \n" % (args[3][1], args[3][0])
            elif size == 32:
                temp_instruction += "str %s, [%s] \n" % (args[3][0], args[3][0])
            elif size == 64:
                temp_instruction += "str %s, [%s] \n" % (args[3][0], args[3][0])

            return temp_instruction

    @staticmethod
    # args[0] : target
    # args[1] : OpType
    # args[2] : size
    # args[3] : target_reg
    # args[4] : source_reg
    def TTBR(*args):
        target = args[0]
        source_reg = args[4]
        target_reg = args[3]
        size = args[2]

        temp_instruction = ""

        temp_instruction += "adrp %s, %s \n" % (target_reg[0], target)
        temp_instruction += "add %s, %s, :lo12:%s \n" % (target_reg[0], args[3][0], target)

        temp_instruction += "movk %s, #0xffff, lsl #16 \n" % source_reg[0]
        temp_instruction += "lsl %s, %s, #32 \n" % (source_reg[0], source_reg[0])
        temp_instruction += "orr %s, %s, %s \n" % (target_reg[0], source_reg[0], source_reg[0])

        if args[1] == "LOAD":
            if size == 8:
                temp_instruction += "ldrb %s, [%s] \n" % (target_reg[1], target_reg[0])
            elif size == 16:
                temp_instruction += "ldrh %s, [%s] \n" % (target_reg[1], target_reg[0])
            elif size == 32:
                temp_instruction += "ldrsw %s, [%s] \n" % (target_reg[0], target_reg[0])
            elif size == 64:
                temp_instruction += "ldr %s, [%s] \n" % (target_reg[0], target_reg[0])

            return temp_instruction

        if args[1] == "STORE":
            if size == 8:
                temp_instruction += "strb %s, [%s] \n" % (target_reg[1], target_reg[0])
            elif size == 16:
                temp_instruction += "strh %s, [%s] \n" % (target_reg[1], target_reg[0])
            elif size == 32:
                temp_instruction += "str %s, [%s] \n" % (target_reg[0], target_reg[0])
            elif size == 64:
                temp_instruction += "str %s, [%s] \n" % (target_reg[0], target_reg[0])

            return temp_instruction

    # 直接访问页表项位access_flag为0的页即可
    @staticmethod
    def ACCESS_FLAG(*args):
        temp_instruction = ""
        temp_instruction += ""
        return ""

    @staticmethod
    # 拓展: load size
    # args[0] : target
    # args[1] : OpType
    # args[2] : size
    # args[3] : target_reg
    # args[4] : source_reg
    def PERMISSION_ACCESS_READ_ONLY(*args):
        source_reg = args[4]
        target_reg = args[3]
        size = args[2]

        temp_instruction = ""

        temp_instruction += "adrp %s, read_only \n" % (source_reg[0])
        temp_instruction += "add %s, %s, :lo12:read_only \n" % (source_reg[0], source_reg[0])

        if size == 8:
            temp_instruction += "strb %s, [%s] \n" % (target_reg[1], source_reg[0])
        elif size == 16:
            temp_instruction += "strh %s, [%s] \n" % (target_reg[1], source_reg[0])
        elif size == 32:
            temp_instruction += "str %s, [%s] \n" % (target_reg[0], source_reg[0])
        elif size == 64:
            temp_instruction += "str %s, [%s] \n" % (target_reg[0], source_reg[0])

        return temp_instruction

    @staticmethod
    # 拓展: store size

    # args[0] : target, not use
    # args[1] : OpType
    # args[2] : size
    # args[3] : target_reg
    # args[4] : source_reg
    def PERMISSION_ACCESS_NON_ACCESSABLE(*args):
        source_reg = args[4]
        target_reg = args[3]
        size = args[2]

        temp_instruction = ""

        temp_instruction += "adrp %s, no_access \n" % (source_reg[0])
        temp_instruction += "add %s, %s, :lo12:no_access \n" % (source_reg[0], source_reg[0])

        if args[1] == "LOAD":
            if size == 8:
                temp_instruction += "ldrb %s, [%s] \n" % (target_reg[1], source_reg[0])
            elif size == 16:
                temp_instruction += "ldrh %s, [%s] \n" % (target_reg[1], source_reg[0])
            elif size == 32:
                temp_instruction += "ldrsw %s, [%s] \n" % (target_reg[0], source_reg[0])
            elif size == 64:
                temp_instruction += "ldr %s, [%s] \n" % (target_reg[0], source_reg[0])
                temp_instruction += "ldr %s, [%s] \n" % (target_reg[0], source_reg[0])

            return temp_instruction

        if args[1] == "STORE":
            if size == 8:
                temp_instruction += "strb %s, [%s] \n" % (target_reg[1], source_reg[0])
            elif size == 16:
                temp_instruction += "strh %s, [%s] \n" % (target_reg[1], source_reg[0])
            elif size == 32:
                temp_instruction += "str %s, [%s] \n" % (target_reg[0], source_reg[0])
            elif size == 64:
                temp_instruction += "str %s, [%s] \n" % (target_reg[0], source_reg[0])

            return temp_instruction

    @staticmethod
    # args[0] : target, not use
    # args[1] : OpType
    # args[2] : size
    # args[3] : target_reg
    # args[4] : source_reg
    def ACCESS_0(*args):
        target_reg = args[3]

        temp_instruction = ""
        temp_instruction += "mov %s, #0x0 \n" % (target_reg[0])
        temp_instruction += "ldr %s, [%s] \n" % (target_reg[0], target_reg[0])

        return temp_instruction

    @staticmethod
    # args[0] : target, not use
    # args[1] : OpType
    # args[2] : size
    # args[3] : target_reg
    # args[4] : source_reg, not use
    def ACCESS_UNCANONICAL(*args):
        source_reg = args[4]
        target_reg = args[3]
        size = args[2]

        temp_instruction = ""
        temp_instruction += "mov %s, #0x1234 \n" % (target_reg[0])
        temp_instruction += "ldr %s, [%s] \n" % (target_reg[0], target_reg[0])
        return temp_instruction

    # ------------------------------- undefined instruction -------------------------------
    @staticmethod
    def UNDEFINED_UNALLOCATED():
        temp_instruction = ""
        temp_instruction += ".word 0x00000000 \n"

        return temp_instruction

    @staticmethod
    def UNDEFINED_DATA_PROCESS_IMMEDIATE():
        temp_instruction = ""
        temp_instruction += ".word 0x46000000 \n"

        return temp_instruction

    @staticmethod
    def UNDEFINED_BRANCH():
        temp_instruction = ""
        temp_instruction += ".word 0x2be00000 \n"

        return temp_instruction

    @staticmethod
    def UNDEFINED_LOAD_STORE():
        temp_instruction = ""
        temp_instruction += ".word 0xc2000000 \n"

        return temp_instruction

    @staticmethod
    def UNDEFINED_DATA_PROCESS_REG():
        temp_instruction = ""
        temp_instruction += ".word 0x1a200000 \n"

        return temp_instruction

    @staticmethod
    def UNDEFINED_DATA_PROCESS_SIMD():
        temp_instruction = ""
        temp_instruction += ".word 0x38a02000 \n"

        return temp_instruction

    @staticmethod
    def UNDEFINED_DATA_PROCESS_SIMD_1():
        temp_instruction = ""
        temp_instruction += ".word 0x3f800000 \n"

        return temp_instruction

    # ------------------------------- exception generation instruction -------------------------------
    @staticmethod
    def SVC(imme):
        temp_instruction = ""

        temp_instruction += "SVC #%s \n" % imme

        return temp_instruction

    @staticmethod
    def HVC(imme):
        temp_instruction = ""

        temp_instruction += "HVC #%s \n" % imme

        return temp_instruction

    @staticmethod
    def SMC(imme):
        temp_instruction = ""

        temp_instruction += "SMC #%s \n" % imme

        return temp_instruction

    # ------------------------------- float-point -------------------------------
    @staticmethod
    def FLOAT_UNDER_FLOW(reg):
        temp_instruction = ""
        temp_instruction += "mov %s, #0x10000000000000 \n" % (reg[0])
        temp_instruction += "fmov d0, x0 \n"
        temp_instruction += "fmul d0, d0, d0 \n"

        return temp_instruction

    @staticmethod
    def FLOAT_OVER_FLOW(reg):
        temp_instruction = ""
        temp_instruction += "mov %s, #0x7fefffffffffffff \n" % (reg[0])
        temp_instruction += "fmov d0, x0 \n"
        temp_instruction += "fmul d0, d0, d0 \n"

        return temp_instruction

    @staticmethod
    def FLOAT_DIVIED_ZERO(reg):
        temp_instruction = ""
        temp_instruction += "mov %s, #0x0 \n" % (reg[0])
        temp_instruction += "fmov d0, %s \n" % (reg[0])
        temp_instruction += "fdiv d0, d0, d0 \n"

        return temp_instruction

    @staticmethod
    def gen_fault(fault_name, contextAllocator, size=None, OpType=None, target=None):
        temp_instruction = ""

        fault_type = Fault.faultType[fault_name]

        if (fault_type == None):
            print("fault_name error !")
            return -1

        if fault_type == 'ALIGNMENT_FAULT':
            source_reg = contextAllocator.random_int()

            fault = {
                'ALIGNMENT_FAULT_PC': Fault.ALIGNMENT_FAULT_PC,
                'ALIGNMENT_FAULT_SP': Fault.ALIGNMENT_FAULT_SP,
                'ALIGNMENT_FAULT_DATA_ACCESS': Fault.ALIGNMENT_FAULT_DATA_ACCESS
            }

            temp_instruction += fault[fault_name](source_reg, target)

            contextAllocator.free_int(source_reg)

            return temp_instruction

        if fault_type == 'MMU_FAULT_LOAD_STORE':
            source_reg = contextAllocator.random_int()
            target_reg = contextAllocator.random_int()

            fault = {
                'LEVEL_1_PAGE_TABLE': Fault.LEVEL_1_PAGE_TABLE,
                'LEVEL_2_PAGE_TABLE': Fault.LEVEL_2_PAGE_TABLE,
                'LEVEL_3_PAGE_TABLE': Fault.LEVEL_3_PAGE_TABLE,
                'LEVEL_4_PAGE_TABLE': Fault.LEVEL_4_PAGE_TABLE,
                'TTBR': Fault.TTBR,
                'ACCESS_FLAG': Fault.ACCESS_FLAG,
                'PERMISSION_ACCESS_NON_ACCESSABLE': Fault.PERMISSION_ACCESS_NON_ACCESSABLE,
                'ACCESS_0': Fault.ACCESS_0,
                'ACCESS_UNCANONICAL': Fault.ACCESS_UNCANONICAL
            }

            temp_instruction += fault[fault_name](target, OpType, size, target_reg, source_reg)

            contextAllocator.free_int(source_reg)
            contextAllocator.free_int(target_reg)

            return temp_instruction

        if fault_type == 'MMU_FAULT_STORE':
            fault = {
                'PERMISSION_ACCESS_READ_ONLY': Fault.PERMISSION_ACCESS_READ_ONLY,
            }

            target_reg = contextAllocator.random_int()
            source_reg = contextAllocator.random_int()

            temp_instruction += fault[fault_name](None, None, size, source_reg, target_reg)

            contextAllocator.free_int(source_reg)
            contextAllocator.free_int(target_reg)

            return temp_instruction

        if fault_type == 'UNDEFINED_INSTRUCTION_FAULT':
            fault = {
                'UNDEFINED_UNALLOCATED': Fault.UNDEFINED_UNALLOCATED,
                'UNDEFINED_DATA_PROCESS_IMMEDIATE': Fault.UNDEFINED_DATA_PROCESS_IMMEDIATE,
                'UNDEFINED_BRANCH': Fault.UNDEFINED_BRANCH,
                'UNDEFINED_LOAD_STORE': Fault.UNDEFINED_LOAD_STORE,
                'UNDEFINED_DATA_PROCESS_REG': Fault.UNDEFINED_DATA_PROCESS_REG,
                'UNDEFINED_DATA_PROCESS_SIMD': Fault.UNDEFINED_DATA_PROCESS_SIMD,
                'UNDEFINED_DATA_PROCESS_SIMD_1': Fault.UNDEFINED_DATA_PROCESS_SIMD_1
            }

            temp_instruction += fault[fault_name]()

            return temp_instruction

        if fault_type == 'EXCEPTION_GENERATION_FAULT':
            imme = random.randint(0, 255)

            fault = {
                'SVC': Fault.SVC,
                'HVC': Fault.HVC,
                'SMC': Fault.SMC
            }

            temp_instruction += fault[fault_name](imme)

            return temp_instruction

        if fault_type == 'FLOAT_POINT_FAULT':
            reg = contextAllocator.random_int()

            fault = {
                'FLOAT_UNDER_FLOW': Fault.FLOAT_UNDER_FLOW,
                'FLOAT_OVER_FLOW': Fault.FLOAT_OVER_FLOW,
                'FLOAT_DIVIED_ZERO': Fault.FLOAT_DIVIED_ZERO
            }

            temp_instruction += fault[fault_name](reg)

            contextAllocator.free_int(reg)

            return temp_instruction

class ContextAllocator(object):
    int_regs = {
        "X0": ["X0", "W0"],
        "X1": ["X1", "W1"],
        "X2": ["X2", "W2"],
        "X3": ["X3", "W3"],
        "X4": ["X4", "W4"],
        "X5": ["X5", "W5"],
        "X6": ["X6", "W6"],
        "X7": ["X7", "W7"],
        "X8": ["X8", "W8"],
        "X9": ["X9", "W9"],
        "X10": ["X10", "W10"],
        "X11": ["X11", "W11"],
        "X12": ["X12", "W12"],
        "X13": ["X13", "W13"],
        "X14": ["X14", "W14"],
        "X15": ["X15", "W15"],
        "X16": ["X16", "W16"],
        "X17": ["X17", "W17"],
        "X18": ["X18", "W18"],
        "X19": ["X19", "W19"],
        "X20": ["X20", "W20"],
        "X21": ["X21", "W21"],
        "X22": ["X22", "W22"],
        "X23": ["X23", "W23"],
        "X24": ["X24", "W24"],
        "X25": ["X25", "W25"],
        "X26": ["X26", "W26"],
        "X27": ["X27", "W27"],
        "X28": ["X28", "W28"],
        # "X29": ["X29", "W29"],
        # "X30": ["X30", "W30"]
    }

    def __init__(self, rChooser):
        self.rChooser = rChooser
        self.int = {
            'freelist': ContextAllocator.int_regs,
            'allocated': {},
            'touched': {}
            # 'temp_save' : {}
        }

        self.fp = {
            'freelist': {},
            'allocated': {},
            'touched': {}
        }

        for i in range(8):
            self.fp['freelist'].update({'st%s' % i: ["st%s" % i]})

        self.vector = {
            'freelist': {},
            'allocated': {},
            'touched': {}
        }

        for i in range(8):
            self.vector['freelist'].update({'zmm%s' % i: ["zmm%s" % i, "ymm%s" % i, "xmm%s" % i, "mm%s" % i]})

    def alloc_repmov(self):
        for reg in ["rcx", "rsi", "rdi"]:
            self.alloc_int(reg)

    def get_int_save_stub(self, istream):
        x = istream

        size_push = len(self.int['touched']) * 16
        offset = size_push - 16

        x += "sub sp, sp, #%s\n" % (size_push)

        for reg in sorted(self.int['touched']):
            x += "str %s, [sp%s]\n" % (reg, "" if offset == 0 else ", #%s" % (offset))
            # x += "str %%%s\n"%(reg)
            offset -= 16
        return x

    def get_int_restore_stub(self, istream):
        x = istream

        size_push = len(self.int['touched']) * 16
        offset = 0

        for reg in sorted(self.int['touched'], reverse=True):
            x += "ldr %s, [sp%s]\n" % (reg, "" if offset == 0 else ", #%s" % (offset))
            offset += 16
        x += "add sp, sp, #%s\n" % (size_push)
        return x

        # freelist的key与touched的key的交集，从交集中选择一个寄存器，如果交集中的数据大于8，

    # 使用交集数据，不然使用freelist。
    def random(self, v):
        inters = set(v['freelist'].keys()).intersection(set(v['touched'].keys()))
        if len(inters) > 8:
            # To reduce regeister usage
            klist = list(inters)
        else:
            klist = list(v['freelist'].keys())
        ln = len(klist)
        i = self.rChooser.pick_n(ln)
        k = klist[i]
        v['allocated'].update({k: v['freelist'][k]})
        v['touched'].update({k: v['freelist'][k]})
        del v['freelist'][k]
        return v['allocated'][k]

    def alloc(self, reg, v):
        if reg in v['freelist']:
            v['allocated'].update({reg: v['freelist'][reg]})
            v['touched'].update({reg: v['freelist'][reg]})
            del v['freelist'][reg]
            return v['allocated'][reg]
        else:
            raise Exception("%s is not free" % reg)

    def free(self, reg, v):
        if reg in v['allocated']:
            v['freelist'].update({reg: v['allocated'][reg]})
            del v['allocated'][reg]
        else:
            raise Exception("%s is not allocated" % reg)

    def random_int(self):
        # print("random_int")
        return self.random(self.int)

    def random_vector(self):
        return self.random(self.vector)

    def random_fp(self):
        return self.random(self.fp)

    def alloc_int(self, reg):
        return self.alloc(reg, self.int)

    def alloc_vector(self, reg):
        return self.alloc(reg, self.vector)

    def alloc_fp(self, reg):
        return self.alloc(reg, self.fp)

    def free_int(self, reg):
        return self.free(reg[0], self.int)

    def free_vector(self, reg):
        return self.free(reg[0], self.vector)

    def free_fp(self, reg):
        return self.free(reg[0], self.fp)


# tested
# pick page offset,address and a random chooser
class RandomChooser(object):
    PAGE_SIZE = 4096

    def _init__(self):

        None

    def pick_offset(self):
        return 8 * random.randint(0, 512)
        # return random.randint(0, RandomChooser.PAGE_SIZE)

    def pick_page(self, t, safe=False):
        if t == "addressesP":
            return 0

        if t == "addressesNC":
            return random.randint(0, 0x7fffff) << 28

        if safe:
            return random.randint(0, 30)
        else:
            return random.randint(0, 31)

    def pick_one(self, candidates):
        ln = len(candidates)
        rnd = random.randint(0, ln - 1)
        return candidates[rnd]

    # tested
    def pick_address(self, ref=None, safe=False, same=False, ht=False):
        if safe:
            types = []
            for k in MemAddress.Types:
                if MemAddress.Types[k]["safe"]:
                    types.append(k)
        else:
            types = list(MemAddress.Types.keys())

        t = self.pick_one(types)
        if ht:
            t += "Ht"

        p = self.pick_page(t, safe=safe)
        o = self.pick_offset()

        if ref is None:
            return MemAddress(t, p, o)
        else:
            if not safe and same:
                # safe false
                return MemAddress(ref.type, ref.page, ref.offset)
            else:
                # safe true
                return MemAddress(t, p, o, ref, self.pick_n(12))

    # tested
    def pick_memsize(self):
        # as number of bits from 64 bit
        return 2 ** (random.randint(0, 6))

    def pick_memsize_int(self):
        return random.randint(3, 6)

    def pick_bool(self):
        return random.randint(0, 1) == 1

    def pick_n(self, n):
        return random.randint(0, n - 1)

    def chance(self, n):
        return random.randint(0, int(100 / n) - 1) == 0

    def pick_safe_address(self):
        key = self.pick_one(
            list(MemAddress.Types)
        )

        return MemAddress.Types.get(key).get("value")

# 内存类型，及其相关属性
class MemroyType(object):
    # name
    # attr : {
    #   cacheable : cache中会保留对应的信息; 0: false, 1: true
    # }
    memType = {
        'address_UC': {
            'attr': {
                'valid': 0,
                'dirty': 0,
                'cacheable': 0
            },
            'byte': '3a'

        },
        'address_WT': {
            'attr': {
                'valid': 0,
                'dirty': 0,
                'cacheable': 1
            },
            'byte': '3b'
        },
        'address_WB': {
            'attr': {
                'valid': 0,
                'dirty': 0,
                'cacheable': 1
            },
            'byte': '3c'
        },
        'address_normal': {
            'attr': {
                'valid': 0,
                'dirty': 0,
                'cacheable': 1
            },
            'byte': '3d'
        },

        'address_shareable': {
            'attr': {
                'cacheable': 1
            },
            'byte': '3c'
        },
        'address_unpredictable': {
            'attr': {
                'cacheable': 1
            },
            'byte': '3d'
        },
        'addresses_inner_shareable': {
            'attr': {
                'cacheable': 1
            },
            'byte': '3e'
        },
        'addresses_outer_shareable': {
            'attr': {
                'cacheable': 1
            },
            'byte': '3f'
        },

        'addresses_not_accessed': {
            'attr': {
                'cacheable': 1
            },
            'byte': '44'
        },
        'addresses_accessed': {
            'attr': {
                'cacheable': 1
            },
            'byte': '44'
        },

        'addresses_global': {
            'attr': {
                'cacheable': 1
            },
            'byte': '40'
        },
        'addresses_non_global': {
            'attr': {
                'cacheable': 1
            },
            'byte': '41'
        },

        'address_contiguous': {
            'attr': {
                'cacheable': 1
            },
            'byte': '42'
        },
        'address_non_contiguous': {
            'attr': {
                'cacheable': 1
            },
            'byte': '43'
        },

        'address_non_secure': {
            'attr': {
                'cacheable': 1
            },
            'byte': '44'
        },
        'address_secure': {
            'attr': {
                'cacheable': 1
            },
            'byte': '44'
        },
    }

    @staticmethod
    def get_byte_by_name(name):
        return MemroyType.memType.get(name).get('byte')

    # 获取所有预设数据
    @staticmethod
    def get_all_byte_in_cache_line(mem_type_list):
        list_all_bytes = []

        for key in mem_type_list:
            try:
                bytes = MemroyType.memType.get(key).get('byte')

                # 一个cache line
                for i in range(3):
                    bytes += bytes

                list_all_bytes.append(bytes)

            except AttributeError:
                continue

        return list_all_bytes

    def get_mem_type_and_attr_by_name(name):
        return memType.get(name)

    def __init__(self, name):
        self.type = get_mem_type_and_attr_by_name(name)

    def get_attr(self, name):
        return self.type.get('attr').get(name)

# 代码块
class Code_Block(object):
    def __init__(self, code, attr, memType, offset, memOp, dataSize, faultType, data):
        self.code = code

        # fault or safe
        self.attr = attr

        # the memory type
        self.memType = memType

        # offset of the operation target to a page
        self.offset = offset

        # load, store,
        self.memOp = memOp

        # data size : 8bit-64bit
        self.dataSize = dataSize

        # fault type : ttbr, page table bit and so on
        self.faultType = faultType

        self.data = data

class Generator(object):
    def gen_load(self, size, target, contextAllocator, reg=None):
        load_reg = contextAllocator.random_int()
        flag = 1

        if reg == None:
            reg = contextAllocator.random_int()
            flag = 0

        instruction = ""

        if target == None:
            if size == 8:
                instruction += "ldrb %s, [%s] \n" % (reg[1], "X0")
            elif size == 16:
                instruction += "ldrh %s, [%s] \n" % (reg[1], "X0")
            elif size == 32:
                instruction += "ldrsw %s, [%s] \n" % (reg[0], "X0")
            elif size == 64:
                instruction += "ldr %s, [%s] \n" % (reg[0], "X0")
        else:
            instruction += "adrp %s, %s \n" % (load_reg[0], target)
            instruction += "add %s, %s, :lo12:%s \n" % (load_reg[0], load_reg[0], target)

            if size == 8:
                instruction += "ldrb %s, [%s] \n" % (reg[1], load_reg[0])
            elif size == 16:
                instruction += "ldrh %s, [%s] \n" % (reg[1], load_reg[0])
            elif size == 32:
                instruction += "ldrsw %s, [%s] \n" % (reg[0], load_reg[0])
            elif size == 64:
                instruction += "ldr %s, [%s] \n" % (reg[0], load_reg[0])

        contextAllocator.free_int(load_reg)
        
        if flag == 0:
            contextAllocator.free_int(reg)

        return instruction, reg

    def gen_store(self, size, target, contextAllocator):
        store_reg = contextAllocator.random_int()
        reg = contextAllocator.random_int()

        instruction = ""

        instruction += "mov %s, #0xff \n" % (store_reg[0])

        if target == None:
            if size == 8:
                instruction += "strb %s, [%s] \n" % (store_reg[1], "X0")
            elif size == 16:
                instruction += "strh %s, [%s] \n" % (store_reg[1], "X0")
            elif size == 32:
                instruction += "str %s, [%s] \n" % (store_reg[1], "X0")
            elif size == 64:
                instruction += "str %s, [%s] \n" % (store_reg[1], "X0")
        else:
            instruction += "adrp %s, %s \n" % (reg[0], target)
            instruction += "add %s, %s, :lo12:%s" % (reg[0], reg[0], target)

            if size == 8:
                instruction += "strb %s, [%s] \n" % (store_reg[1], reg[0])
            elif size == 16:
                instruction += "strh %s, [%s] \n" % (store_reg[1], reg[0])
            elif size == 32:
                instruction += "str %s, [%s] \n" % (store_reg[0], reg[0])
            elif size == 64:
                instruction += "str %s, [%s] \n" % (store_reg[0], reg[0])

        contextAllocator.free_int(store_reg)
        contextAllocator.free_int(reg)

        return instruction

    def encode_to_cache(self, contextAllocator, reg):
        reg_encoder = contextAllocator.random_int()

        while reg_encoder == reg:
            contextAllocator.free_int(reg_encoder)

            reg_encoder = contextAllocator.random_int()

        instruction = "\n"

        instruction += "adrp %s, probe_array \n" % reg_encoder[0]
        instruction += "add %s, %s, :lo12:probe_array \n" % (reg_encoder[0], reg_encoder[0])
        instruction += "lsl %s, %s, #12 \n" % (reg[0], reg[0])
        instruction += "ldr %s, [%s, %s] \n" % (reg[0], reg_encoder[0], reg[0])

        contextAllocator.free_int(reg_encoder)

        return instruction

def stop_victim():
    info = run_cmd("ps -ef | grep victim")
    info = info.split("\n")

    pid_victim = []

    for i in range(len(info)):
        if "victim" in info[i]:
            pid_victim.append(info[i].split(" ")[5])

    for i in pid_victim:
        run_cmd("echo 'shunya' | sudo -S kill -KILL " + i)

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

def gen_binary_file(instruction, role):
    if role == "attacker":
        path = "moulds/attacker/"

        code = ".global s_faulty_load \n" \
               "s_faulty_load: \n"
    else:
        path = "moulds/victim/"

        code = ".global s_fill \n" \
               "s_fill: \n"

    code += instruction

    code += "ret"

    asm_file = open(path + 'autogen.S', 'w+')
    asm_file.write(code)
    asm_file.seek(0)

    # run_cmd("cd " + path + " && make clean && make")
    # run_cmd("cd " + path + " && make -s")

    # binary_file = Path(path + role)

    # if binary_file.is_file():
    #     return 1
    # else:
    #     time.sleep(1)

    #     # 如果生成失败，等待再次生成。若二次生成失败，跳过
    #     binary_file = Path(path + role)
    #     if binary_file.is_file():
    #         return 1
    #     else:
    #         run_cmd("cd " + role + " && make clean")
    #         run_cmd("cd " + role + " && make -s")

    #         binary_file = Path(path + role)
    #         if binary_file.is_file():
    #             return 1
    #         else:
    #             print("error: " + instruction)

    #             return -1

def gen_victim_and_run(ins_victim):
    gen_binary_file(ins_victim, "victim")
    ins_victim = ""

    shell_start_victim = "echo 'shunya' | sudo -S ./victim/victim"

    return run_cmd_output(shell_start_victim)

def gen_attacker_and_run(ins_attacker, address_virtual, address_physical):
    gen_binary_file(ins_attacker, "attacker")

    shell_start_attacker = "./attacker/attacker %s, %s" % (address_virtual, address_physical)

    info = run_cmd(shell_start_attacker)

    if len(info) != 0:
        print("======================\n" + info + "======================")

    sys.stdout.flush()

# 0: Optype victimindex_reg_attacker
# 1: size for victim

# 2: Optype for attacker
# 3: target address
# 3: size for attacker
# 4. reg for attacker

# 5. fault name
# 6. Optype for fualt level ttbr nonaccsable
# 7. target for fualt level ttbr nonaccsable
# 8. size for fualt level ttbr nonaccsable

# 9. size for read only
def log(*args):
    Op_type_victim = args[0]
    size_victim = args[1]

    Op_type_attacker = args[2]
    target_address_index = args[3]
    size_attacker = args[4]
    reg_attacker = args[5]

    fault_name = args[6]

    target_align_data_access = args[7]

    Op_type_level_ttbe_non_accessable = args[8]
    target_level_ttbe_non_accessable = args[9]
    size_level_ttbe_non_accessable = args[10]

    size_read_only = args[11]

    print("Op_type_victim: %s, size_victim: %s, "
          "Op_type_attacker: %s, target_address_index: %s, size_attacker: %s, reg_attacker: %s, "
          "fault_name: %s, "
          "target_align_data_access: %s, "
          "Op_type_level_ttbe_non_accessable: %s, target_level_ttbe_non_accessable: %s, size_level_ttbr_non_accessable: %s "
          "size_read_only: %s "
          % (
             Op_type_victim, size_victim,
             Op_type_attacker, target_address_index, size_attacker, reg_attacker,
             fault_name,
             target_align_data_access,
             Op_type_level_ttbe_non_accessable, target_level_ttbe_non_accessable, size_level_ttbe_non_accessable,
             size_read_only
             ))

def log_index(*args): 
    index_Op_type_victim = args[0]
    index_size_victim = args[1]

    index_Op_type_attacker = args[2]
    index_size_attacker = args[3]
    index_reg_attacker = args[4]

    index_fault_name = args[5]

    index_target_align_data_access = args[6]

    index_Op_type_level_ttbe_non_accessable = args[7]
    index_target_level_ttbe_non_accessable = args[8]
    index_size_level_ttbe_non_accessable = args[9]

    index_size_read_only = args[10]

    str_info = "counter: %s, dir_test_case: %s, index_Op_type_victim: %s, index_size_victim: %s, index_Op_type_attacker: %s, index_size_attacker: %s, index_reg_attacker: %s, index_fault_name: %s, index_target_align_data_access: %s, index_Op_type_level_ttbe_non_accessable: %s, index_target_level_ttbe_non_accessable: %s, index_size_level_ttbr_non_accessable: %s, index_size_read_only: %s " % (
            str(counter_test_case),
            str(dir_test_case),
             index_Op_type_victim, 
             index_size_victim,

             index_Op_type_attacker, 
             index_size_attacker, 
             index_reg_attacker,

             index_fault_name,

             index_target_align_data_access,

             index_Op_type_level_ttbe_non_accessable, 
             index_target_level_ttbe_non_accessable, 
             index_size_level_ttbe_non_accessable,

             index_size_read_only
             )

    print(str_info)

    return str_info

def log_to_config(config_info):
    config_file = open("moulds/config", "w+")
    config_file.write(config_info)
    config_file.seek(0)

def gen_test_case(ins_victim, ins_attacker):
    global dir_test_case
    global counter_test_case

    # removeable
    if(limit != None):
        if(counter_test_case == limit):
            print("end")
            exit(1)

    if counter_test_case % single_test_case_num == 0:
        dir_test_case += 1
        counter_test_case = 0

        run_cmd("mkdir " + test_cases_lib_path + str(dir_test_case))

        shutil.copy("run_all_test_case.py", test_cases_lib_path+str(dir_test_case)+"/")

    gen_binary_file(ins_victim, "victim")
    gen_binary_file(ins_attacker, "attacker")

    path = test_cases_lib_path+str(dir_test_case)+"/"+str(counter_test_case)+"/"

    run_cmd("mkdir " + path)

    run_cmd("cp -r moulds/* " + path )

    counter_test_case+=1


def run_test_gen_test_case():
    int_regs = {
        # "X0": ["X0", "W0"],
        "X1": ["X1", "W1"],
        "X2": ["X2", "W2"],
        "X3": ["X3", "W3"],
        "X4": ["X4", "W4"],
        "X5": ["X5", "W5"],
        "X6": ["X6", "W6"],
        "X7": ["X7", "W7"],
        "X8": ["X8", "W8"],
        "X11": ["X11", "W11"],
        "X12": ["X12", "W12"],
        "X13": ["X13", "W13"],
        "X14": ["X14", "W14"],
        "X15": ["X15", "W15"],
        "X16": ["X16", "W16"],
        "X17": ["X17", "W17"],
        "X18": ["X18", "W18"],
        "X19": ["X19", "W19"],
        "X20": ["X20", "W20"],
        "X21": ["X21", "W21"],
        "X22": ["X22", "W22"],
        "X23": ["X23", "W23"],
        "X24": ["X24", "W24"],
        "X25": ["X25", "W25"],
        "X26": ["X26", "W26"],
        "X27": ["X27", "W27"],
        "X28": ["X28", "W28"],
        # "X29": ["X29", "W29"],
        # "X30": ["X30", "W30"]
    }

    all_Op_type_victim = ["LOAD", "STORE"]
    all_size_victim = [8, 16, 32, 64]
    all_victim_target = list(MemroyType.memType.keys())

    all_Op_type_attacker = ["LOAD"]
    all_size_attacker = [8, 16, 32, 64]
    all_regs_attacker = list(int_regs.keys())

    all_fault_type = list(Fault.faultType.keys())

    all_target_align_data_access = ["address_normal"]

    all_Op_type_level_ttbe_non_accessable = ["LOAD", "STORE"]
    all_target_level_ttbe_non_accessable = ["address_normal"]
    all_size_level_ttbe_non_accessable = [64]

    all_size_read_only = [64]

    ##设成所需的组件
    random = RandomChooser()
    contextAllocator_attacker = ContextAllocator(random)
    contextAllocator_victim = ContextAllocator(random)
    generator = Generator()

    index_Op_type_victim = 0
    while index_Op_type_victim < len(all_Op_type_victim):
        Op_type_victim = all_Op_type_victim[index_Op_type_victim]

        index_size_victim = 0
        while index_size_victim < len(all_size_victim):
            size_victim = all_size_victim[index_size_victim]

            ins_victim = ""

            index_victim_target = 0
            while index_victim_target < len(all_victim_target):
                victim_target = all_victim_target[index_victim_target]
                # --------------------- run victim --------------------
                if Op_type_victim == "LOAD":
                    temp_ins_victim, _ = generator.gen_load(size_victim, victim_target, contextAllocator_victim)

                else:
                    temp_ins_victim = generator.gen_store(size_victim, victim_target, contextAllocator_victim)

                ins_victim += temp_ins_victim

                index_victim_target += 1

            # 这一部分放到测试用例中生成
            # victim_info = gen_victim_and_run(ins_victim)

            # victim_address_physical = victim_info[0:16]
            # victim_address_virtual = victim_info[16:32]

            # i = 0
            # while i < 16:
            #     victim_physical = victim_address_physical[i]
            #     victim_virtual = victim_address_virtual[i]

            index_reg_attacker = 0
            while index_reg_attacker < len(all_regs_attacker):
                reg_attacker = int_regs.get(all_regs_attacker[index_reg_attacker])

                index_Op_type_attacker = 0
                while index_Op_type_attacker < len(all_Op_type_attacker):
                    Op_type_attacker = all_Op_type_attacker[index_Op_type_attacker]

                    index_size_attacker = 0
                    while index_size_attacker < len(all_size_attacker):
                        size_attacker = all_size_attacker[index_size_attacker]

                        ins_attacker = ""

                        # ---------------------------- generate fault and attacker fault load  ----------------------------
                        index_fault_type = 0
                        while index_fault_type < len(all_fault_type):
                            fault_name = all_fault_type[index_fault_type]

                            if fault_name in ['LEVEL_1_PAGE_TABLE', 'LEVEL_2_PAGE_TABLE', 'LEVEL_3_PAGE_TABLE',
                                                  'LEVEL_4_PAGE_TABLE', 'TTBR', 'PERMISSION_ACCESS_NON_ACCESSABLE',
                                                  'ACCESS_UNCANONICAL', 'ACCESS_0']:

                                index_Op_type_level_ttbe_non_accessable = 0
                                while index_Op_type_level_ttbe_non_accessable < len(all_Op_type_level_ttbe_non_accessable):
                                    Op_type_level_ttbe_non_accessable = all_Op_type_level_ttbe_non_accessable[index_Op_type_level_ttbe_non_accessable]

                                    index_target_level_ttbe_non_accessable = 0
                                    while index_target_level_ttbe_non_accessable < len(all_target_level_ttbe_non_accessable):
                                        target_level_ttbe_non_accessable = all_target_level_ttbe_non_accessable[index_target_level_ttbe_non_accessable]

                                        index_size_level_ttbe_non_accessable = 0
                                        while index_size_level_ttbe_non_accessable < len(all_size_level_ttbe_non_accessable):
                                            size_level_ttbe_non_accessable = all_size_level_ttbe_non_accessable[index_size_level_ttbe_non_accessable]

                                            ins_attacker += Fault.gen_fault(fault_name, contextAllocator_attacker,
                                                                                size_level_ttbe_non_accessable,
                                                                                Op_type_level_ttbe_non_accessable,
                                                                                target_level_ttbe_non_accessable)

                                            if Op_type_attacker == "LOAD":
                                                temp_ins_attacker, reg = generator.gen_load(size_attacker, None,
                                                                                                contextAllocator_attacker,
                                                                                                reg_attacker)

                                            else:
                                                temp_ins_attacker, reg = generator.gen_load(size_attacker, None,
                                                                                                contextAllocator_attacker)

                                            ins_attacker += temp_ins_attacker

                                            ins_attacker += generator.encode_to_cache(contextAllocator_attacker, reg)

                                            str_info = log_index(
                                                    index_Op_type_victim,
                                                    index_size_victim,

                                                    index_Op_type_attacker,
                                                    
                                                    index_size_attacker,
                                                    index_reg_attacker,

                                                    index_fault_type,

                                                    0,

                                                    index_Op_type_level_ttbe_non_accessable,
                                                    index_target_level_ttbe_non_accessable,
                                                    index_size_level_ttbe_non_accessable,

                                                    0
                                            )

                                            log_to_config(str_info)

                                            gen_test_case(ins_victim, ins_attacker)

                                            ins_attacker = ""

                                            index_size_level_ttbe_non_accessable += 1

                                        index_target_level_ttbe_non_accessable += 1

                                    index_Op_type_level_ttbe_non_accessable += 1

                            elif fault_name in ['PERMISSION_ACCESS_READ_ONLY']:
                                index_size_read_only = 0
                                while index_size_read_only < len(all_size_read_only):
                                    size_read_only = all_size_read_only[index_size_read_only]

                                    ins_attacker += Fault.gen_fault(fault_name, contextAllocator_attacker, size_read_only,
                                                                        None, None)

                                    if Op_type_attacker == "LOAD":
                                        temp_ins_attacker, reg = generator.gen_load(size_attacker, None,
                                                                                        contextAllocator_attacker, reg_attacker)

                                    else:
                                        temp_ins_attacker, reg = generator.gen_load(size_attacker, None,
                                                                                        contextAllocator_attacker)

                                    ins_attacker += temp_ins_attacker

                                    ins_attacker += generator.encode_to_cache(contextAllocator_attacker, reg)

                                    str_info = log_index(
                                        index_Op_type_victim,
                                        index_size_victim,

                                        index_Op_type_attacker,
                                    
                                        index_size_attacker,
                                        index_reg_attacker,

                                        index_fault_type,

                                        0,

                                        0,
                                        0,
                                        0,

                                        index_size_read_only
                                    )

                                    log_to_config(str_info)


                                    gen_test_case(ins_victim, ins_attacker)

                                    ins_attacker = ""

                                    index_size_read_only += 1

                            elif fault_name in ['ALIGNMENT_FAULT_DATA_ACCESS']:

                                index_target_align_data_access = 0
                                while index_target_align_data_access < len(all_target_align_data_access):
                                    target_align_data_access = all_target_align_data_access[index_target_align_data_access]

                                    ins_attacker += Fault.gen_fault(fault_name, contextAllocator_attacker, None,
                                                                        None, target_align_data_access)

                                    if Op_type_attacker == "LOAD":
                                        temp_ins_attacker, reg = generator.gen_load(size_attacker, None,
                                                                                        contextAllocator_attacker, reg_attacker)

                                    else:
                                        temp_ins_attacker, reg = generator.gen_load(size_attacker, None,
                                                                                        contextAllocator_attacker)

                                    ins_attacker += temp_ins_attacker

                                    ins_attacker += generator.encode_to_cache(contextAllocator_attacker, reg)

                                    str_info = log_index(
                                                    index_Op_type_victim,
                                                    index_size_victim,

                                                    index_Op_type_attacker,
                                                    
                                                    index_size_attacker,
                                                    index_reg_attacker,

                                                    index_fault_type,

                                                    index_target_align_data_access,

                                                    0,
                                                    0,
                                                    0,

                                                    0
                                        )

                                    log_to_config(str_info)

                                    gen_test_case(ins_victim, ins_attacker)

                                    ins_attacker = ""

                                    index_target_align_data_access += 1

                            else:
                                ins_attacker += Fault.gen_fault(fault_name, contextAllocator_attacker, None, None, None)

                                if Op_type_attacker == "LOAD":
                                        temp_ins_attacker, reg = generator.gen_load(size_attacker, None,
                                                                                    contextAllocator_attacker, reg_attacker)

                                else:
                                        temp_ins_attacker, reg = generator.gen_load(size_attacker, None,
                                                                                    contextAllocator_attacker)

                                ins_attacker += temp_ins_attacker

                                ins_attacker += generator.encode_to_cache(contextAllocator_attacker, reg)

                                str_info = log_index(
                                                    index_Op_type_victim,
                                                    index_size_victim,

                                                    index_Op_type_attacker,
                                                
                                                    index_size_attacker,
                                                    index_reg_attacker,

                                                    index_fault_type,

                                                    0,

                                                    0,
                                                    0,
                                                    0,

                                                    0
                                )

                                log_to_config(str_info)

                                gen_test_case(ins_victim, ins_attacker)

                                ins_attacker = ""

                            index_fault_type += 1

                        index_size_attacker += 1

                    index_Op_type_attacker += 1

                index_reg_attacker += 1

            ins_victim = ""

            index_size_victim += 1

        index_Op_type_victim += 1

def test():
    ins_attacker =  '''
                    s_faulty_load: 
                    mov X12, #0x0 
                    fmov d0, X12 
                    fdiv d0, d0, d0 
                    ldr X28, [X0] 

                    adrp X12, probe_array 
                    add X12, X12, :lo12:probe_array 
                    lsl X28, X28, #12 
                    ldr X28, [X12, X28] 
                    '''

    ins_victim =    '''
                    mov X26, #0xff
                    adrp X21, address_UC
                    add X21, X21, :lo12:address_UC
                    str X26, [X21]
                    mov X21, #0xff 
                    adrp X26, address_WT 
                    add X26, X26, :lo12:address_WT
                    str X21, [X26] 
                    mov X7, #0xff 
                    adrp X20, address_WB 
                    add X20, X20, :lo12:address_WB
                    str X7, [X20] 
                    mov X20, #0xff 
                    adrp X1, address_normal 
                    add X1, X1, :lo12:address_normal
                    str X20, [X1] 
                    mov X0, #0xff 
                    adrp X7, address_shareable 
                    add X7, X7, :lo12:address_shareable
                    str X0, [X7] 
                    mov X21, #0xff 
                    adrp X7, address_unpredictable 
                    add X7, X7, :lo12:address_unpredictable
                    str X21, [X7] 
                    mov X7, #0xff 
                    adrp X20, addresses_inner_shareable 
                    add X20, X20, :lo12:addresses_inner_shareable
                    str X7, [X20] 
                    mov X21, #0xff 
                    adrp X0, addresses_outer_shareable 
                    add X0, X0, :lo12:addresses_outer_shareable
                    str X21, [X0] 
                    mov X7, #0xff 
                    adrp X19, addresses_not_accessed 
                    add X19, X19, :lo12:addresses_not_accessed
                    str X7, [X19] 
                    mov X1, #0xff 
                    adrp X0, addresses_accessed 
                    add X0, X0, :lo12:addresses_accessed
                    str X1, [X0] 
                    mov X14, #0xff 
                    adrp X8, addresses_global 
                    add X8, X8, :lo12:addresses_global
                    str X14, [X8] 
                    mov X20, #0xff 
                    adrp X19, addresses_non_global 
                    add X19, X19, :lo12:addresses_non_global
                    str X20, [X19] 
                    mov X9, #0xff 
                    adrp X14, address_contiguous 
                    add X14, X14, :lo12:address_contiguous
                    str X9, [X14] 
                    mov X14, #0xff 
                    adrp X0, address_non_contiguous 
                    add X0, X0, :lo12:address_non_contiguous
                    str X14, [X0] 
                    mov X0, #0xff 
                    adrp X14, address_non_secure 
                    add X14, X14, :lo12:address_non_secure
                    str X0, [X14] 
                    mov X20, #0xff 
                    adrp X7, address_secure 
                    add X7, X7, :lo12:address_secure
                    str X20, [X7] 
                    '''

    gen_test_case(ins_victim, ins_attacker)

def main():
    # test()
    # test()
    # test()
    # test()
    # test()
    run_test_gen_test_case()

    print("done")

if __name__ == "__main__":
    main()
