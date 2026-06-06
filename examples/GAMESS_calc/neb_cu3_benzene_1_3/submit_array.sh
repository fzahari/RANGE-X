#!/bin/bash
#SBATCH -A CHM238
#SBATCH --nodes 1
#SBATCH -p batch
#SBATCH -t 0:30:00
#SBATCH -a 1-7

module load PrgEnv-gnu cray-python rocm 2>/dev/null
cd $SLURM_SUBMIT_DIR
GAMESS=~/gamess_gnu_Apr01_2026

K=$(printf "%02d" $SLURM_ARRAY_TASK_ID)
JOB=image_${K}.inp
echo "=== $JOB at $(date) ==="
$GAMESS/rungms-dev $JOB 00 1 > ${JOB}.log 2>&1
if grep -q "TERMINATED NORMALLY" ${JOB}.log; then
    echo "  $JOB: SUCCESS"
    grep "FINAL.*ENERGY" ${JOB}.log | tail -1
else
    echo "  $JOB: FAILED"
    grep -m1 "ERROR\|TERMINATED" ${JOB}.log | head -3
fi
