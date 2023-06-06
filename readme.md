# meltdown-like test
## preparation
1. install pteditor
    + cd PTEditor/module
    + make
    + sudo insmod pteditor1.ko

## run
1. generate test case package
    + the generator program is located at <font color="green">generator/fuzz.py</font>
    + when generation phase complete, the test case package is located at <font color="green">/test_cases</font>
2. run test case package 
    + choose a test case package, each test case package contains a running script(run_all_test_case.py) to run all test cases in a package
    + run runnning script: <font color="green">taskset -c 4 python3 -u run_all_test_case.py > log.out</font>. the log.out is the log file, please make sure every log file have a unique name.
    + copy the log file you want to analyze to directory: <font color="green">logs</font>
3. run analyzer
    + the analyzer program is located at <font color="green">checker/check.py</font>
    + the analyzer will analyze all log file in the directory logs
    + while the log directory(logs) is not empty, run the analyzer program: <font color="green">taskset -c 4 python3 -u check.py 1> ../result/result.out</font>. the result.out is the final report

## how to check the log file
1. if final log file shows the line "######################"，it means that the test program have detected something wrong, the leak infomation is below the "######################"
2. the leak infomation is shown as the serial number, the specific type, such as operation type, operation size...., will founed in the <font color="green">type_list.md</font> file. for example, in the log file, we found the Op_type_victim is 1, according to the type_list file, the Op_type_victim is store.

## attention
1. if a log file is analyzed, please remove it from the directory <font color="green">logs</font>, or it will be analyzed repeatedly