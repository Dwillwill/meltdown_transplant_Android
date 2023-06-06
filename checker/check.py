# -*- coding: utf-8 -*
#!/usr/bin/env python3
import sys, random, math, time, subprocess, os, re

from pathlib import Path
import shutil
import json

import faulthandler

from datetime import datetime

all_logs_path = "../logs/"

# 内存类型，及其相关属性
class MemoryType(object):
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
        return MemoryType.memType.get(name).get('byte')

    # 获取所有预设数据
    @staticmethod
    def get_all_byte_in_cache_line(mem_type_list):
        list_all_bytes = []

        for key in mem_type_list:
            try:
                bytes = MemoryType.memType.get(key).get('byte')

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
            instruction += "add %s, %s, :lo12:%s\n" % (reg[0], reg[0], target)

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
all_victim_target = list(MemoryType.memType.keys())

all_Op_type_attacker = ["LOAD"]
all_size_attacker = [8, 16, 32, 64]
all_regs_attacker = list(int_regs.keys())

all_fault_type = list(Fault.faultType.keys())

all_target_align_data_access = ["address_normal"]

all_Op_type_level_ttbe_non_accessable = ["LOAD", "STORE"]
all_target_level_ttbe_non_accessable = ["address_normal"]
all_size_level_ttbe_non_accessable = [8, 16, 32, 64]

all_size_read_only = [8, 16, 32, 64]

# index_Op_type_victim: 0
# index_size_victim: 0,
# index_Op_type_attacker: 0,
# index_target_address_index: 0,
# index_size_attacker: 0,
# index_reg_attacker: 0,
# index_fault_name: 6,
# index_target_align_data_access: 0,
# index_Op_type_level_ttbe_non_accessable: 1,
# index_target_level_ttbe_non_accessable: 2,
# index_size_level_ttbr_non_accessable: 2
# index_size_read_only: 0

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

def gen_binary_file(i, instruction, role):
    if role == "attacker":
        path = "attacker/"

        code = ".global s_faulty_load \n" \
               "s_faulty_load: \n"
    else:
        path = "victim/"

        code = ".global s_fill \n" \
               "s_fill: \n"

    code += instruction

    code += "ret"

    asm_file = open(path + 'autogen.S', 'w+')
    asm_file.write(code)
    asm_file.seek(0)

    run_cmd("cd " + role + " && make clean")
    run_cmd("cd " + role + " && make -s")
    

    binary_file = Path(path + role)
    des_file = Path(str(i) + "/" + role)
    shutil.copyfile(binary_file, des_file)
    shutil.copyfile(Path("checker"), Path(str(i) + "/" + "checker"))

    if binary_file.is_file():
        return 1
    else:
        time.sleep(1)

        # 如果生成失败，等待再次生成。若二次生成失败，跳过
        binary_file = Path(path + role)
        if binary_file.is_file():
            return 1
        else:
            run_cmd("cd " + role + " && make clean")
            run_cmd("cd " + role + " && make -s")

            binary_file = Path(path + role)
            if binary_file.is_file():
                return 1
            else:
                print("error: " + instruction)

                return -1


def gen_victim_and_run(ins_victim):
    gen_binary_file(ins_victim, "victim")
    ins_victim = ""

    shell_start_victim = "taskset -c 0 ./victim/victim"

    return run_cmd_output(shell_start_victim)


def stop_victim():

    info = run_cmd("ps -ef | grep victim")
    info = info.split("\n")

    pid_victim = []

    for i in range(len(info)):
        if "victim" in info[i]:
            info_str = info[i]

            info_str = re.sub(' +', ' ', info_str)
            pid_victim.append(info_str.split(" ")[1])

    # for i in pid_victim:
    run_cmd("kill -KILL " + pid_victim[1] + " 2> /dev/null")


def gen_attacker_and_run(ins_attacker, address, op_size):
    shell_start_attacker = "taskset -c 0 timeout 3 ./attacker/attacker %s %s" % (address, op_size)

    print(shell_start_attacker)

    info = run_cmd(shell_start_attacker)

    return info

'''
index_Op_type_victim: 0, 
index_size_victim: 0,

index_Op_type_attacker: 0, 
index_size_attacker: 0, 
index_reg_attacker: 21, 

index_fault_name: 3, 
index_target_align_data_access: 0, 
index_Op_type_level_ttbe_non_accessable: 0, 
index_target_level_ttbe_non_accessable: 0, 
index_size_level_ttbr_non_accessable: 3, 
index_size_read_only: 0
'''

def decode_leak_info(fault):
    Op_type_victim = ''
    size_victim = ''
    Op_type_attacker = ''
    target_address_index = ''
    size_attacker = ''
    reg_attacker = ''
    fault_name = ''
    target_align_data_access = ''
    Op_type_level_ttbe_non_accessable = ''
    target_level_ttbe_non_accessable = ''
    size_level_ttbr_non_accessable = ''
    size_read_only = ''

    infos = fault.get_self().instruction_info.split(',')

    Op_type_victim = all_Op_type_victim[int(infos[0].split(':')[1])]
    size_victim = all_size_victim[int(infos[1].split(':')[1])]

    target_address_index = fault.get_self().address_index_of_victim

    Op_type_attacker = all_Op_type_attacker[int(infos[2].split(':')[1])]
    size_attacker = all_size_attacker[int(infos[3].split(':')[1])]
    reg_attacker = int_regs.get(all_regs_attacker[int(infos[4].split(':')[1])])

    fault_name = all_fault_type[int(infos[5].split(':')[1])]
    target_align_data_access = all_target_align_data_access[int(infos[6].split(':')[1])]
    Op_type_level_ttbe_non_accessable = all_Op_type_level_ttbe_non_accessable[int(infos[7].split(':')[1])]
    target_level_ttbe_non_accessable = all_target_level_ttbe_non_accessable[int(infos[8].split(':')[1])]
    size_level_ttbr_non_accessable = all_size_level_ttbe_non_accessable[int(infos[9].split(':')[1])]

    # 调度器运行时会将其他信息输出到attacker中
    try:
        size_read_only = all_size_read_only[int(infos[10].split(':')[1])]
    except BaseException:
        print("=========-----========")
        print(infos[10])
        print(infos[10].split(':')[1])
        print(int(infos[10].split(':')[1][0]))
        print("=========-----========")

        size_read_only = int(infos[10].split(':')[1][0])

    ret = {
        'Op_type_victim': Op_type_victim,
        'size_victim': size_victim,

        'Op_type_attacker': Op_type_attacker,
        'target_address_index': target_address_index,
        'size_attacker': size_attacker,
        'reg_attacker': reg_attacker,

        'fault_name': fault_name,
        'target_align_data_access': target_align_data_access,
        'Op_type_level_ttbe_non_accessable': Op_type_level_ttbe_non_accessable,
        'target_level_ttbe_non_accessable': target_level_ttbe_non_accessable,
        'size_level_ttbr_non_accessable': size_level_ttbr_non_accessable,
        'size_read_only': size_read_only
    }

    return ret


def reappeare(num, fault, attrs, generator, contextAllocator_attacker, contextAllocator_victim):
    ins_attacker = ""
    ins_victim = ""

    kernel_address = 0xffff000009310840
    linear_address = 0xffff000000000000
    virtual_address = 0

    # 生成attacker代码
    fault_name = attrs.get('fault_name')
    size_level_ttbr_non_accessable = attrs.get('size_level_ttbr_non_accessable')
    Op_type_level_ttbe_non_accessable = attrs.get('Op_type_level_ttbe_non_accessable')
    target_level_ttbe_non_accessable = attrs.get('target_level_ttbe_non_accessable')

    size_attacker = attrs.get('size_attacker')
    reg_attacker = attrs.get('reg_attacker')

    ins_attacker += Fault.gen_fault(fault_name, contextAllocator_attacker, size_level_ttbr_non_accessable,
                                    Op_type_level_ttbe_non_accessable, target_level_ttbe_non_accessable)
    temp_ins_attacker, reg = generator.gen_load(size_attacker, None, contextAllocator_attacker)

    ins_attacker += temp_ins_attacker

    ins_attacker += generator.encode_to_cache(contextAllocator_attacker, reg)

    gen_binary_file(num, ins_attacker, "attacker")

    # 生成victim代码
    Op_type_victim = attrs.get('Op_type_victim')
    size_victim = attrs.get('size_victim')

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



    gen_binary_file(num, ins_victim, "victim")

    help_file = open(str(num) + '/' +  'help_file', 'w+')
    help_file.write("target_address_index:" + str(attrs.get('target_address_index')))
    help_file.write("\n")
    help_file.write("size_attacker:" + str(attrs.get('size_attacker')))
    help_file.write("\n")
    help_file.write(fault.toString())
    # # # 运行victim
    # victim_info = gen_victim_and_run(ins_victim)

    # victim_address_physical = victim_info[0:16]
    # victim_address_virtual = victim_info[16:32]

    # target_address_index = attrs.get('target_address_index')
    # # 运行attacker
    # type_ = fault.get_self().type
    # addr = 0

    # # virtual
    # if type_ == 'virtual':
    #     addr = int(victim_address_virtual[int(target_address_index)], 16)

    # # linear 
    # elif type_ == 'linear':
    #     addr = int(linear_address + int(victim_address_physical[int(target_address_index)],16))
    # # kernel
    # else:
    #     addr = kernel_address

    # info = gen_attacker_and_run(ins_attacker, hex(addr), attrs.get('size_attacker'))
    # info = info.split("\n")

    # if(len(info) != 2 ):
    #     print(info)
    #     print("attack error")
    # else:
    #     # 发生泄露后，且地址非法，再输出
    #     if len(info[0]) != 0 and int(info[1].split(":")[1]) == 0:
    #         # print(info)
    #         fault.get_self().new_leak = info[0]

    #         print(fault.toString())

    # stop_victim()

class Error(object):
    def __init__(self):
        self.original_leak = ""
        self.type = ""
        self.instruction_info = ""
        self.address_index_of_victim = ""
        self.new_leak = ""

    def get_self(self):
        return self

    def toString(self):
        string = ""
        string += "######################\n"
        string += "original_leak:" + self.original_leak + "\n"
        string += "type:" + self.type + "\n"
        string += "instruction_info:" + self.instruction_info + "\n"
        string += "address_index_of_victim:" + str(self.address_index_of_victim) + "\n"
        string += "new_leak:" + self.new_leak + "\n"
        string += "++++++++++++++++++++++\n"

        return string

    def setValue(self, original_leak, type_, instruction_info, address_index_of_victim, new_leak):
        self.original_leak = original_leak
        self.type = type_
        self.instruction_info = instruction_info
        self.address_index_of_victim = address_index_of_victim
        self.new_leak = new_leak

def gen_one_test_case(fault):
    generator = Generator()

    randomChooser = RandomChooser()

    contextAllocator_attacker = ContextAllocator(randomChooser)
    contextAllocator_victim = ContextAllocator(randomChooser)

    attrs = decode_leak_info(fault)

    ins_attacker = ""
    ins_victim = ""

    # 生成attacker代码
    fault_name = attrs.get('fault_name')
    size_level_ttbr_non_accessable = attrs.get('size_level_ttbr_non_accessable')
    Op_type_level_ttbe_non_accessable = attrs.get('Op_type_level_ttbe_non_accessable')
    target_level_ttbe_non_accessable = attrs.get('target_level_ttbe_non_accessable')

    size_attacker = attrs.get('size_attacker')
    reg_attacker = attrs.get('reg_attacker')

    ins_attacker += Fault.gen_fault(fault_name, contextAllocator_attacker, size_level_ttbr_non_accessable,
                                    Op_type_level_ttbe_non_accessable, target_level_ttbe_non_accessable)
    temp_ins_attacker, reg = generator.gen_load(size_attacker, None, contextAllocator_attacker)

    ins_attacker += temp_ins_attacker

    ins_attacker += generator.encode_to_cache(contextAllocator_attacker, reg)

    # 生成victim代码
    Op_type_victim = attrs.get('Op_type_victim')
    size_victim = attrs.get('size_victim')

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

    print("=========================== attacker ===========================")
    print(ins_attacker)

    print("=========================== victim ===========================")
    print(ins_victim)

def check():
    all_logs = os.listdir(all_logs_path)

    for log in all_logs:
        file = open(all_logs_path + log, 'r+')

        random_attacker = RandomChooser()
        random_victim = RandomChooser()

        contextAllocator_attacker = ContextAllocator(random_attacker)
        contextAllocator_victim = ContextAllocator(random_victim)

        generator = Generator()

        line3 = file.readline()
        num = 0
        while 1:
            if not line3:
                print("read complete")

                return

            if line3 == '======================\n':
                fault = Error()
                os.mkdir(str(num))
                '''
                1. get original leak
                2. get leak info
                '''

                # 1
                line3 = file.readline()
                while (line3 != "++++++++++++++++++++++\n"):
                    fault.get_self().original_leak = line3.replace("\n", "")

                    line3 = file.readline()

                # 2
                while (file.readline() != "######################\n"):
                    continue

                line3 = file.readline()
                while (line3 != "++++++++++++++++++++++\n"):
                    if ("index:" in line3):
                        line3 = line3.replace(" ", "")
                        line3 =line3.replace("\n", "")
                        fault.get_self().address_index_of_victim = int(line3.split(":")[1])


                    if ("type:" in line3):
                        line3 = line3.replace(" ", "")
                        line3 =line3.replace("\n", "")
                        fault.get_self().type = line3.split(":")[1]


                    if ("info:" in line3):
                        line3 = line3.replace(" ", "")
                        line3 = line3.replace("\n", "")
                        fault.get_self().instruction_info = re.split("dir_test_case:[0-9]*,", line3)[1]

                    line3 = file.readline()

                attrs = decode_leak_info(fault)
                reappeare(num, fault, attrs, generator, contextAllocator_attacker, contextAllocator_victim)
                num = num + 1


            line3 = file.readline()


def main():
    start = datetime.now()
    end = 0

    check()

    end = datetime.now()

    print("end")
    print("cost: " + str( (end - start) ))


'''
ouput format：
if leak:
    1. original leak
    2. instruction info
    3. address index of victim
    3. new leak
'''
if __name__ == "__main__":
    main()  
