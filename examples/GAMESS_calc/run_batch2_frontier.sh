#!/bin/bash
#SBATCH -J RANGE-B2
#SBATCH -A CHM238
#SBATCH --nodes 1
#SBATCH -p batch
#SBATCH -t 2:00:00
#SBATCH -o range_b2-%J.out
#SBATCH -e range_b2-%J.err

module swap PrgEnv-cray PrgEnv-gnu
module load cray-python
module load rocm

cd ~/Programs/RANGE/examples/GAMESS_calc

echo "=== Gap only ==="
python3 inbox_ethylene_gap.py

echo "=== S1 near CI ==="
python3 inbox_ethylene_s1_near_ci.py
