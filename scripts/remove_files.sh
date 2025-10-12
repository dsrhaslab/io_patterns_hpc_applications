#!/bin/bash

BASE_DIR="../../results"

# Remove srun_dstat files
find "$BASE_DIR" -type f -path "*/dstat/srun_dstat_*.log" -print -delete

# Remove PID_TID files in tracer directories
find "$BASE_DIR" -type f -path "*/tracer/*" -name "[0-9]*_[0-9]*" -print -delete