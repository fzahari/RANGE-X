#!/bin/bash
#SBATCH -J cu3bnz-stage5
#SBATCH -A CHM238
#SBATCH --nodes 1
#SBATCH -p batch
#SBATCH -t 1:55:00
#SBATCH -o cu3bnz_stage5-%J.out
#SBATCH -e cu3bnz_stage5-%J.err

module load PrgEnv-gnu cray-python rocm 2>/dev/null
export PYTHONPATH=/ccs/proj/chm238/fzahari/python_libs:$PYTHONPATH
cd ~/Programs/RANGE/examples/GAMESS_calc

python3 agent_ci_pipeline.py --molecule cu3_benzene \
    --objectives e_s0,e_s1,somaki \
    --no-llm --no-conical

echo "=== Stage 5 generation complete at $(date) ==="
ls -la agent_report_cu3_benzene.txt
