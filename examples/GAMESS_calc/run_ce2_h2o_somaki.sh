#!/bin/bash
#SBATCH -J ce2-somaki
#SBATCH -A CHM238
#SBATCH --nodes 1
#SBATCH -p batch
#SBATCH -t 2:00:00
#SBATCH -o ce2_h2o_somaki-%J.out
#SBATCH -e ce2_h2o_somaki-%J.err
module load PrgEnv-gnu cray-python rocm 2>/dev/null
export PYTHONPATH=/ccs/proj/chm238/fzahari/python_libs:$PYTHONPATH
cd ~/Programs/RANGE/examples/GAMESS_calc
python3 agent_ci_pipeline.py --molecule ce2_h2o --objectives somaki --no-llm --no-conical
