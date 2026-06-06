#!/bin/bash
#SBATCH -J con-ethylene
#SBATCH -A CHM238
#SBATCH --nodes 1
#SBATCH -p batch
#SBATCH -t 2:00:00
#SBATCH -o conical_ethylene-%J.out
#SBATCH -e conical_ethylene-%J.err
module load PrgEnv-gnu cray-python rocm 2>/dev/null
export PYTHONPATH=/ccs/proj/chm238/fzahari/python_libs:$PYTHONPATH
cd ~/Programs/RANGE/examples/GAMESS_calc
python3 agent_ci_pipeline.py --molecule ethylene --no-llm
