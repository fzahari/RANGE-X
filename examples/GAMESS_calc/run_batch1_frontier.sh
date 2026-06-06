#!/bin/bash
#SBATCH -J RANGE-B1
#SBATCH -A CHM238
#SBATCH --nodes 1
#SBATCH -p batch
#SBATCH -t 2:00:00
#SBATCH -o range_b1-%J.out
#SBATCH -e range_b1-%J.err

module swap PrgEnv-cray PrgEnv-gnu
module load cray-python
module load rocm

cd ~/Programs/RANGE/examples/GAMESS_calc

echo "=== S0 minima ==="
python3 inbox_ethylene_s0_min.py

echo "=== S1 minima ==="
python3 inbox_ethylene_s1_min.py

echo "=== Mean energy ==="
python3 inbox_ethylene_mean.py
