#!/bin/bash
#SBATCH -J Cu3-AGENT
#SBATCH -A CHM238
#SBATCH --nodes 1
#SBATCH -p batch
#SBATCH -t 2:00:00
#SBATCH -o agent_cu3-%J.out
#SBATCH -e agent_cu3-%J.err

echo "Job ID: $SLURM_JOBID"
echo "Node: $SLURM_NODELIST"
echo "Start: $(date)"

module swap PrgEnv-cray PrgEnv-gnu
module load cray-python
module load rocm

export PYTHONPATH=/ccs/proj/chm238/fzahari/python_libs:$PYTHONPATH

cd ~/Programs/RANGE/examples/GAMESS_calc

python3 agent_ci_pipeline.py --molecule cu3

echo "End: $(date)"
