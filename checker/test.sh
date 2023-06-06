#!/bin/bash
mkdir log
for dir in `ls`; do
    cd $dir;
    ./checker > log$dir.txt;
    mv log$dir.txt ../log/
    cd ..;
    done