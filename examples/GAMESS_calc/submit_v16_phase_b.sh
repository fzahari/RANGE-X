#!/bin/bash
#SBATCH -J v16-phaseB
#SBATCH -A CHM238
#SBATCH --nodes 1
#SBATCH -p batch
#SBATCH -t 1:55:00
#SBATCH -o v16_phase_b-%J.out
#SBATCH -e v16_phase_b-%J.err

module load PrgEnv-gnu cray-python rocm 2>/dev/null
cd ~/Programs/RANGE/examples/GAMESS_calc
GAMESS=~/gamess_gnu_Apr01_2026

run_one() {
    local job=$1
    echo "=========================================="
    echo "=== $job at $(date) ==="
    echo "=========================================="
    $GAMESS/rungms-dev $job 00 1 > ${job}.log 2>&1
    if grep -q "TERMINATED NORMALLY" ${job}.log; then
        echo "  $job: SUCCESS"
        grep -E "FINAL.*ENERGY|EQUILIBRIUM GEOMETRY|MAXIMUM GRADIENT|EXCITATION ENERGY" ${job}.log | tail -10
    else
        echo "  $job: FAILED or INCOMPLETE"
        grep -m1 "ERROR\|TERMINATED" ${job}.log | head -3
    fi
    echo ""
}

for sys in cu3 ag3 au3 cu3pd cu3_benzene ceo ce2_h2o; do
    run_one conical_${sys}_v16
done

for sys in cu3 ag3 au3 ceo; do
    run_one vertical_${sys}_v16
done

echo "=== All v16 phase-B jobs complete at $(date) ==="
