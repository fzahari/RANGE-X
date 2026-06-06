#!/bin/bash
#SBATCH -J anal-cu3
#SBATCH -A CHM238
#SBATCH --nodes 1
#SBATCH -p batch
#SBATCH -t 0:30:00
#SBATCH -o analysis_cu3-%J.out
#SBATCH -e analysis_cu3-%J.err
module load PrgEnv-gnu cray-python rocm 2>/dev/null
export PYTHONPATH=/ccs/proj/chm238/fzahari/python_libs:$PYTHONPATH
cd ~/Programs/RANGE/examples/GAMESS_calc
python3 agent_ci_pipeline.py --molecule cu3 --no-conical
