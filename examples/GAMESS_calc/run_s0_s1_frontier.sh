#!/bin/bash
#SBATCH -J RANGE-PES
#SBATCH -A CHM238
#SBATCH --nodes 1
#SBATCH -p batch
#SBATCH -t 2:00:00
#SBATCH -o range_pes-%J.out
#SBATCH -e range_pes-%J.err

module swap PrgEnv-cray PrgEnv-gnu
module load cray-python
module load rocm

cd ~/Programs/RANGE/examples/GAMESS_calc

echo "=== S0 minima search ==="
python3 inbox_ethylene_s0_min.py

echo "=== S1 minima search ==="
python3 inbox_ethylene_s1_min.py
