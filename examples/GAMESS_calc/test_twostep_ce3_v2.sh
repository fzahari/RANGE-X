#!/bin/bash
GAMESS=~/gamess_gnu_Apr01_2026
JOB1=twostep2_ce3_s1
JOB2=twostep2_ce3_s2

# Step 1: Pure ROHF DOUBLET (this converges in 16 iterations!)
cat > ${JOB1}.inp << 'EOF'
 $CONTRL SCFTYP=ROHF RUNTYP=ENERGY
         ISPHER=1 PP=SBKJC MULT=2 MAXIT=200 ICHARG=3 $END
 $SYSTEM MWORDS=400 MEMDDI=200 $END
 $BASIS  GBASIS=SBKJC $END
 $SCF    DAMP=.TRUE. SHIFT=.TRUE. DIIS=.TRUE. $END
 $DATA
Ce3+(H2O) step1 pure ROHF doublet
C1
 Ce   58.0   0.000000   0.000000   0.000000
 O     8.0   2.500000   0.000000   0.000000
 H     1.0   3.256950   0.585882   0.000000
 H     1.0   3.256950  -0.585882   0.000000
 $END
EOF

echo "=== Step 1: Pure ROHF doublet ==="
$GAMESS/rungms-dev $JOB1 00 1 > ${JOB1}.log 2>&1
grep "FINAL" ${JOB1}.log

if ! grep -q "TERMINATED NORMALLY" ${JOB1}.log; then
    echo "Step 1 FAILED"
    exit 1
fi

# Find the orbitals
echo "Looking for orbitals..."
find /tmp/fzahari/ -name "${JOB1}*" 2>/dev/null
ls ~/restart/${JOB1}* 2>/dev/null

# Try F07 (PUNCH file) in scratch
f07=$(find /tmp/fzahari/ -name "${JOB1}.F07" 2>/dev/null | head -1)
dat=$(find /tmp/fzahari/ -path "*/restart/${JOB1}.dat" 2>/dev/null | head -1)

if [ -n "$dat" ]; then
    echo "Found dat: $dat"
    sed -n '/ \$VEC/,/ \$END/p' "$dat" > vec_ce3.txt
elif [ -n "$f07" ]; then
    echo "Found F07: $f07"
    sed -n '/ \$VEC/,/ \$END/p' "$f07" > vec_ce3.txt
else
    # Try copying from scratch before rungms deletes it
    echo "No VEC found. Trying alternate approach..."
    # Check if rungms already cleaned up
    find /tmp/fzahari/ -name "${JOB1}.*" 2>/dev/null
    exit 1
fi

nvec=$(wc -l < vec_ce3.txt)
echo "VEC lines: $nvec"
head -2 vec_ce3.txt
