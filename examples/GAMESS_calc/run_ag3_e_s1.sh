#!/bin/bash
#SBATCH -J ag3-e_s1
#SBATCH -A CHM238
#SBATCH --nodes 1
#SBATCH -p batch
#SBATCH -t 2:00:00
#SBATCH -o ag3_e_s1-%J.out
#SBATCH -e ag3_e_s1-%J.err
module swap PrgEnv-cray PrgEnv-gnu
module load cray-python rocm
export PYTHONPATH=/ccs/proj/chm238/fzahari/python_libs:$PYTHONPATH
cd ~/Programs/RANGE/examples/GAMESS_calc
python3 agent_ci_pipeline.py --molecule ag3 --objectives e_s1 --no-llm --no-conical
