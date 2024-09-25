#!/bin/bash

MODEL=intp3003.data
MO=0

#./job.sh ${MODEL} ${MO}

for MODEL in gar82703 gar81123 #intp1311.data intp3003.data gar82703 gar81123
do
    for MO in 0 1
    do
        hep_sub job.sh -argu ${MODEL} ${MO} # -o /dev/null -e /dev/null
    done
done
