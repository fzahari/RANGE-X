#!/bin/bash
#SBATCH -J con-ceo
#SBATCH -A CHM238
#SBATCH --nodes 1
#SBATCH -p batch
#SBATCH -t 2:00:00
#SBATCH -o conical_ceo_direct-%J.out
#SBATCH -e conical_ceo_direct-%J.err

module load PrgEnv-gnu cray-python rocm 2>/dev/null
cd ~/Programs/RANGE/examples/GAMESS_calc
GAMESS=~/gamess_gnu_Apr01_2026

echo "=== Starting CeO CONICAL refinement at $(date) ==="
$GAMESS/rungms-dev conical_ceo 00 1 > conical_ceo.log 2>&1
status=$?
echo "=== rungms-dev exit code: $status ==="
echo "=== End at $(date) ==="

# Quick result extraction
echo ""
echo "=== Result summary ==="
if grep -q "TERMINATED NORMALLY" conical_ceo.log; then
    echo "SUCCESS"
    echo "Final ENERGY GAP entries:"
    grep "ENERGY GAP=" conical_ceo.log | tail -3
    echo "Final coords:"
    grep -A 6 "EQUILIBRIUM GEOMETRY LOCATED" conical_ceo.log | tail -8
else
    echo "FAILED"
    echo "Error context:"
    grep -B 2 -A 5 "ERROR\|TERMINATED -ABNORMALLY-" conical_ceo.log | tail -20
fi
