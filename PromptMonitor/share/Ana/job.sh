#!/bin/bash

MODEL=$1
MO=$2

METHOD="time-interval"
FAR="1permonth"

time python bounceTime.py --method ${METHOD} --far ${FAR} --model ${MODEL} --mo ${MO}
