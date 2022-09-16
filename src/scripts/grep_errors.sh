#!/bin/bash
FILES="/var/log/pymap/*/*.txt"

for f in $FILES
do
    cat $f | grep -E 'errors encountered during the sync|Err .*'
    grep -lE 'errors encountered during the sync|Err .*' $f
done