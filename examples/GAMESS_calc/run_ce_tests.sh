#!/bin/bash
#SBATCH -J ce-test
#SBATCH -A CHM238
#SBATCH --nodes 1
#SBATCH -p batch
#SBATCH -t 0:30:00
#SBATCH -o ce_tests-%J.out
#SBATCH -e ce_tests-%J.err
module load PrgEnv-gnu cray-python rocm 2>/dev/null
cd ~/Programs/RANGE/examples/GAMESS_calc
GAMESS=~/gamess_gnu_Apr01_2026

# Generate all test inputs
for scf in uhf rohf; do
    SCF_UPPER=$(echo $scf | tr 'a-z' 'A-Z')
    for charge in 3 2; do
        if [ "$charge" = "3" ]; then
            mult_ref=4; mult_tgt=2; label="ce3"
        else
            mult_ref=3; mult_tgt=1; label="ce2"
        fi
        for dist in 2p0 2p5 3p0; do
            r=$(echo $dist | tr 'p' '.')
            rh=$(awk "BEGIN{printf \"%.6f\", $r + 0.75695}")
            job="${label}_${scf}_${dist}"
            cat > test_${job}.inp << INP
 \$CONTRL SCFTYP=${SCF_UPPER} RUNTYP=ENERGY TDDFT=SPNFLP
         DFTTYP=BHHLYP ISPHER=1 PP=SBKJC MULT=${mult_ref} MAXIT=200 ICHARG=${charge} \$END
 \$SYSTEM MWORDS=400 MEMDDI=200 \$END
 \$BASIS  GBASIS=SBKJC \$END
 \$SCF    DAMP=.TRUE. SHIFT=.TRUE. DIIS=.TRUE. SOSCF=.FALSE. \$END
 \$TDDFT  NSTATE=5 TAMMD=.TRUE. MULT=${mult_tgt} \$END
 \$DATA
${label} ${scf} Ce-O=${r}A MULT=${mult_ref}->${mult_tgt}
C1
 Ce   58.0   0.000000   0.000000   0.000000
 O     8.0   ${r}000000   0.000000   0.000000
 H     1.0   ${rh}   0.585882   0.000000
 H     1.0   ${rh}  -0.585882   0.000000
 \$END
INP
        done
    done
done

# Run all 12 tests: 2 SCF x 2 charges x 3 distances
echo "System          | SCF  | MULT | Dist | Result"
echo "----------------|------|------|------|-------"
for scf in uhf rohf; do
    for label in ce3 ce2; do
        for dist in 2p0 2p5 3p0; do
            job="${label}_${scf}_${dist}"
            r=$(echo $dist | tr 'p' '.')
            $GAMESS/rungms-dev test_${job} 00 1 > test_${job}.log 2>&1
            if grep -q "TERMINATED NORMALLY" test_${job}.log; then
                energy=$(grep "FINAL" test_${job}.log | grep -v "0.0000000000" | awk '{print $NF}')
                iters=$(grep "AFTER" test_${job}.log | head -1 | awk '{print $(NF-1)}')
                gap=$(awk '/SUMMARY OF SPIN-FLIP/{found=1} found && /^   [0-9]/{print $3; exit}' test_${job}.log)
                printf "%-15s | %-4s | %-4s | %-4s | OK %s iters, E=%s\n" "${label}(H2O)" "$scf" "" "$r" "$iters" "$energy"
                awk '/SUMMARY OF SPIN-FLIP/,/SELECTING/' test_${job}.log | head -12
            else
                printf "%-15s | %-4s | %-4s | %-4s | FAILED\n" "${label}(H2O)" "$scf" "" "$r"
                grep "UNCONVERGED\|ERROR" test_${job}.log | head -1
            fi
            echo ""
        done
    done
done
