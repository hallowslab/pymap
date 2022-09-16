#!/bin/bash
FILES="/var/log/pymap/*/**"

for f in $FILES
do
    grep -E 'Transfer started at *' $f
done