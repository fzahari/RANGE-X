#!/bin/bash
#SBATCH -J con-ce2h
#SBATCH -A CHM238
#SBATCH --nodes 1
#SBATCH -p batch
#SBATCH -t 2:00:00
#SBATCH -o conical_ce2_h2o_direct-%J.out
#SBATCH -e conical_ce2_h2o_direct-%J.err

module load PrgEnv-gnu cray-python rocm 2>/dev/null
cd ~/Programs/RANGE/examples/GAMESS_calc
GAMESS=~/gamess_gnu_Apr01_2026

echo "=== Starting Ce2+(H2O) CONICAL refinement at $(date) ==="
$GAMESS/rungms-dev conical_ce2_h2o 00 1 > conical_ce2_h2o_direct.log 2>&1
status=$?
echo "=== rungms-dev exit code: $status ==="
echo "=== End at $(date) ==="

echo ""
echo "=== Result summary ==="
if grep -q "TERMINATED NORMALLY" conical_ce2_h2o_direct.log; then
    echo "SUCCESS"
    echo "Final ENERGY GAP entries:"
    grep "ENERGY GAP=" conical_ce2_h2o_direct.log | tail -3
    echo "Final coords:"
    grep -A 8 "EQUILIBRIUM GEOMETRY LOCATED" conical_ce2_h2o_direct.log | tail -10
else
    echo "FAILED"
    echo "Error context:"
    grep -B 2 -A 5 "ERROR\|TERMINATED -ABNORMALLY-" conical_ce2_h2o_direct.log | tail -20
fi
