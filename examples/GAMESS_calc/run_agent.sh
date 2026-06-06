#!/bin/bash
#SBATCH -J CI-AGENT
#SBATCH -A CHM238
#SBATCH --nodes 1
#SBATCH -p batch
#SBATCH -t 4:00:00
#SBATCH -o agent-%J.out
#SBATCH -e agent-%J.err

# ============================================================
# Agentic CI Search Pipeline - Frontier
# ============================================================
# Runs RANGE + GAMESS (CPU) and Qwen 2.5 7B (GPU) on same node
# No internet required
# ============================================================

echo "Job ID: $SLURM_JOBID"
echo "Node: $SLURM_NODELIST"
echo "Start: $(date)"

# Environment setup
module swap PrgEnv-cray PrgEnv-gnu
module load cray-python
module load rocm

# ROCm PyTorch from project space
export PYTHONPATH=/ccs/proj/chm238/fzahari/python_libs:$PYTHONPATH

cd ~/Programs/RANGE/examples/GAMESS_calc

# Run the agent
# Options:
#   --molecule ethylene     (molecule name)
#   --no-llm                (skip LLM, rule-based only)
#   --no-conical            (skip CONICAL refinement)
#   --objectives e_s0 e_s1 somaki  (which objectives to run)

python3 agent_ci_pipeline.py --molecule ethylene

echo "End: $(date)"
