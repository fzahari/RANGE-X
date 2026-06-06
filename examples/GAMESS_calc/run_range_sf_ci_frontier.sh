#!/bin/bash
#SBATCH -J RANGE-SF-CI
#SBATCH -A CHM238
#SBATCH --nodes 1
#SBATCH -p batch
#SBATCH -t 2:00:00
#SBATCH -o range_sf_ci-%J.out
#SBATCH -e range_sf_ci-%J.err

echo "Job ID: $SLURM_JOBID"
echo "Node: $SLURM_NODELIST"
echo "Start: $(date)"

# GNU environment (required -- CCE has gradient bugs)
module swap PrgEnv-cray PrgEnv-gnu 2>/dev/null
module load cray-python
module load rocm

# GAMESS environment
export GAMESS_DIR="${HOME}/gamess_gnu_Apr01_2026"
export PATH="${GAMESS_DIR}:${PATH}"

# Override GMSPATH in rungms-dev
# (already done if you applied the sed fix)

# OpenMP settings for GAMESS
export OMP_STACKSIZE=4G
export OMP_NUM_THREADS=8
export OMP_MAX_ACTIVE_LEVELS=1
export OMP_PROC_BIND=close
export OMP_PLACES=cores
ulimit -s unlimited

# Run RANGE
cd ${SLURM_SUBMIT_DIR}
python inbox_ethylene_sf_ci.py

echo "End: $(date)"
