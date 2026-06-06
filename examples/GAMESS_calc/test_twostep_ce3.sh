#!/bin/bash
# Two-step ROHF SF-TDDFT for Ce3+(H2O)
# Step 1: Pure ROHF (no DFT) → converge orbitals
# Step 2: ROHF + BHHLYP + SF-TDDFT with MOREAD from step 1

GAMESS=~/gamess_gnu_Apr01_2026
JOB1=twostep_ce3_s1
JOB2=twostep_ce3_s2

# Step 1: Pure ROHF, no DFT
cat > ${JOB1}.inp << 'EOF'
 $CONTRL SCFTYP=ROHF RUNTYP=ENERGY
         ISPHER=1 PP=SBKJC MULT=4 MAXIT=200 ICHARG=3 $END
 $SYSTEM MWORDS=400 MEMDDI=200 $END
 $BASIS  GBASIS=SBKJC $END
 $SCF    DAMP=.TRUE. SHIFT=.TRUE. DIIS=.TRUE. SOSCF=.FALSE. RSTRCT=.TRUE. $END
 $DATA
Ce3+(H2O) step1 pure ROHF quartet
C1
 Ce   58.0   0.000000   0.000000   0.000000
 O     8.0   2.500000   0.000000   0.000000
 H     1.0   3.256950   0.585882   0.000000
 H     1.0   3.256950  -0.585882   0.000000
 $END
EOF

echo "=== Step 1: Pure ROHF ==="
$GAMESS/rungms-dev $JOB1 00 1 > ${JOB1}.log 2>&1

if ! grep -q "TERMINATED NORMALLY" ${JOB1}.log; then
    echo "Step 1 FAILED"
    grep "UNCONVERGED\|ERROR" ${JOB1}.log | head -3
    exit 1
fi

grep "FINAL" ${JOB1}.log
echo "Step 1 converged!"

# Extract $VEC from PUNCH file before it's deleted
# rungms saves to $HOME/restart/$JOB.dat for non-GDDI
# or we grab from the log — GAMESS prints orbitals if we look
# Check restart dir
if [ -f ~/restart/${JOB1}.dat ]; then
    echo "Found .dat in ~/restart/"
    sed -n '/ \$VEC/,/ \$END/p' ~/restart/${JOB1}.dat > vec_ce3.txt
elif [ -f /tmp/fzahari/*/restart/${JOB1}.dat ]; then
    datf=$(find /tmp/fzahari/ -name "${JOB1}.dat" 2>/dev/null | head -1)
    echo "Found .dat at $datf"
    sed -n '/ \$VEC/,/ \$END/p' "$datf" > vec_ce3.txt
else
    echo "No .dat file found. Checking F07..."
    f07=$(find /tmp/fzahari/ -name "${JOB1}.F07" 2>/dev/null | head -1)
    if [ -n "$f07" ]; then
        echo "Found F07 at $f07"
        sed -n '/ \$VEC/,/ \$END/p' "$f07" > vec_ce3.txt
    else
        echo "No orbitals found! Listing scratch..."
        find /tmp/fzahari/ -name "*${JOB1}*" 2>/dev/null
        exit 1
    fi
fi

nvec=$(wc -l < vec_ce3.txt)
echo "Extracted $VEC: $nvec lines"

if [ "$nvec" -lt 3 ]; then
    echo "VEC too short, failed to extract"
    exit 1
fi

# Count NORB (number of orbitals)
# Each orbital block starts with a line like " 1  1" (orbital# component#)
# In the $VEC block, each orbital uses ceil(nbasis/5) lines
# Safest: let GAMESS figure it out with NORB=0 or count from the file
# NORB = number of distinct orbital indices in column 1
norb=$(awk '/\$VEC/,/\$END/' vec_ce3.txt | grep -v '^\$' | awk '{print substr($0,1,2)}' | sort -u | wc -l)
echo "NORB = $norb"

# Step 2: ROHF + BHHLYP + SF-TDDFT with MOREAD
cat > ${JOB2}.inp << STEP2EOF
 \$CONTRL SCFTYP=ROHF RUNTYP=ENERGY TDDFT=SPNFLP
         DFTTYP=BHHLYP ISPHER=1 PP=SBKJC MULT=4 MAXIT=200 ICHARG=3 \$END
 \$SYSTEM MWORDS=400 MEMDDI=200 \$END
 \$BASIS  GBASIS=SBKJC \$END
 \$SCF    DAMP=.TRUE. SHIFT=.TRUE. DIIS=.TRUE. SOSCF=.FALSE. RSTRCT=.TRUE. \$END
 \$GUESS  GUESS=MOREAD NORB=$norb \$END
 \$TDDFT  NSTATE=5 TAMMD=.TRUE. MULT=2 \$END
 \$DATA
Ce3+(H2O) step2 ROHF BHHLYP SF-TDDFT from pure ROHF orbitals
C1
 Ce   58.0   0.000000   0.000000   0.000000
 O     8.0   2.500000   0.000000   0.000000
 H     1.0   3.256950   0.585882   0.000000
 H     1.0   3.256950  -0.585882   0.000000
 \$END
$(cat vec_ce3.txt)
STEP2EOF

echo ""
echo "=== Step 2: ROHF + BHHLYP + SF-TDDFT ==="
$GAMESS/rungms-dev $JOB2 00 1 > ${JOB2}.log 2>&1

if grep -q "TERMINATED NORMALLY" ${JOB2}.log; then
    echo "Step 2: SUCCESS!"
    grep "FINAL" ${JOB2}.log | grep -v "0.0000000000"
    awk '/SUMMARY OF SPIN-FLIP/,/SELECTING/' ${JOB2}.log | head -15
else
    grep "FINAL\|UNCONVERGED\|ERROR" ${JOB2}.log | head -5
fi
