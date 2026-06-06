#!/bin/bash
# === run_cu3_benzene_e_s1.sh ===
#SBATCH -J cu3bnz-e_s1
#SBATCH -A CHM238
#SBATCH --nodes 1
#SBATCH -p batch
#SBATCH -t 2:00:00
#SBATCH -o cu3_benzene_e_s1-%J.out
#SBATCH -e cu3_benzene_e_s1-%J.err
module load PrgEnv-gnu cray-python rocm 2>/dev/null
export PYTHONPATH=/ccs/proj/chm238/fzahari/python_libs:$PYTHONPATH
cd ~/Programs/RANGE/examples/GAMESS_calc
python3 agent_ci_pipeline.py --molecule cu3_benzene --objectives e_s1 --no-llm --no-conical --force
