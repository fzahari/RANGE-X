#!/bin/bash
# Runs jobs through debug QOS sequentially, one at a time.
# Submits next when current finishes.

cd ~/Programs/RANGE/examples/GAMESS_calc
JOBS=(
    "vertical_ag3_v16"
    "vertical_au3_v16"
    "vertical_ceo_v16"
    "conical_cu3_v16"
    "conical_ag3_v16"
    "conical_au3_v16"
    "conical_cu3pd_v16"
    "conical_ce2_h2o_v16"
    "conical_ceo_v16"
)

for job in "${JOBS[@]}"; do
    echo ""
    echo "=== Submitting $job to debug at $(date) ==="
    JOB_ID=$(sbatch --parsable -J ${job} -o ${job}-%J.out -e ${job}-%J.err submit_one_debug.sh ${job})
    echo "Job ID: $JOB_ID"
    
    # Wait for it to finish
    while squeue -j $JOB_ID -h 2>/dev/null | grep -q .; do
        sleep 30
    done
    
    echo "  $job finished at $(date)"
    grep -E "TERMINATED NORMALLY|FAILED" ${job}.log | head -1
done

echo ""
echo "=== All debug-chain jobs complete at $(date) ==="
