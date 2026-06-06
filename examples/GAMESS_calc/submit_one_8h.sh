#!/bin/bash
#SBATCH -A CHM238
#SBATCH --nodes 1
#SBATCH -p extended
#SBATCH -t 8:00:00
module load PrgEnv-gnu cray-python rocm 2>/dev/null
cd ~/Programs/RANGE/examples/GAMESS_calc
GAMESS=~/gamess_gnu_Apr01_2026
JOB=$1
$GAMESS/rungms-dev $JOB 00 1 > ${JOB}.log 2>&1
