#!/bin/bash
#SBATCH -J sp-d3h
#SBATCH -A CHM238
#SBATCH --nodes 1
#SBATCH -p batch
#SBATCH -t 1:00:00
#SBATCH -o sp_d3h-%J.out
#SBATCH -e sp_d3h-%J.err

module load PrgEnv-gnu cray-python rocm 2>/dev/null
cd ~/Programs/RANGE/examples/GAMESS_calc
GAMESS=~/gamess_gnu_Apr01_2026

for sys in cu3 ag3 au3; do
    echo "=== $sys at $(date) ==="
    $GAMESS/rungms-dev sp_${sys}_d3h 00 1 > sp_${sys}_d3h.log 2>&1
    if grep -q "TERMINATED NORMALLY" sp_${sys}_d3h.log; then
        echo "  $sys: SUCCESS"
        grep "FINAL RO-BHHLYP ENERGY" sp_${sys}_d3h.log | tail -1
        echo "  Excitation energies:"
        grep -A 1 "ALPHA -> BETA SPIN-FLIP" sp_${sys}_d3h.log | tail -10
        echo "  Spin-flip states (last set):"
        awk '/ALPHA -> BETA SPIN-FLIP EXCITATIONS/{found=1; next} found && /STATE #/{print}' sp_${sys}_d3h.log | tail -10
    else
        echo "  $sys: FAILED"
        grep -m1 "ERROR\|TERMINATED" sp_${sys}_d3h.log
    fi
    echo ""
done
