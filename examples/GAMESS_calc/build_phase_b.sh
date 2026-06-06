#!/bin/bash
# Generate all GAMESS inputs + SLURM scripts to fill v16 pending cells

cd ~/Programs/RANGE/examples/GAMESS_calc

mkdir -p phase_b_inputs

# Geometry extractor
cat > phase_b_inputs/extract_geom.py << 'PYEOF'
import os, glob, sys, re

ATOMIC_Z = {'H':1.0,'C':6.0,'O':8.0,'Cu':29.0,'Ag':47.0,'Au':79.0,'Pd':46.0,'Ce':58.0}

def parse_xyz(path):
    with open(path) as f:
        lines = f.readlines()
    n = int(lines[0])
    atoms = []
    for line in lines[2:2+n]:
        p = line.split()
        atoms.append((p[0], float(p[1]), float(p[2]), float(p[3])))
    return atoms

def find_best_ci(rdir):
    best_gap = 999.0
    best_xyz = None
    for sf in glob.glob(f"{rdir}/compute_*/sf_ci_info.txt"):
        try:
            with open(sf) as f:
                txt = f.read()
            m_gap = re.search(r'^GAP\s*=\s*([\d.E+-]+)', txt, re.M)
            if not m_gap:
                continue
            gap = float(m_gap.group(1))
            if gap < best_gap:
                best_gap = gap
                best_xyz = os.path.join(os.path.dirname(sf), 'final.xyz')
        except (OSError, ValueError):
            continue
    return best_xyz, best_gap

def find_s0_min(rdir):
    best_e = None
    best_xyz = None
    for sf in glob.glob(f"{rdir}/compute_*/sf_ci_info.txt"):
        try:
            with open(sf) as f:
                for line in f:
                    if line.startswith('E_S0'):
                        e = float(line.split('=')[1].split()[0])
                        if best_e is None or e < best_e:
                            best_e = e
                            best_xyz = os.path.join(os.path.dirname(sf), 'final.xyz')
                        break
        except (OSError, ValueError):
            continue
    return best_xyz, best_e

def write_xyz_block(atoms):
    lines = []
    for el, x, y, z in atoms:
        z_atomic = ATOMIC_Z.get(el, 0.0)
        lines.append(f" {el:<3s} {z_atomic:6.1f}  {x:14.8f}  {y:14.8f}  {z:14.8f}")
    return '\n'.join(lines)

if __name__ == '__main__':
    cmd, rdir, outpath = sys.argv[1], sys.argv[2], sys.argv[3]
    if cmd == 'best_ci':
        xyz, gap = find_best_ci(rdir)
        if xyz:
            atoms = parse_xyz(xyz)
            with open(outpath, 'w') as f:
                f.write(write_xyz_block(atoms))
            print(f"  best_ci: gap={gap:.4f} eV from {xyz}")
        else:
            print(f"  ERROR: no best CI found in {rdir}", file=sys.stderr)
            sys.exit(1)
    elif cmd == 's0_min':
        xyz, e = find_s0_min(rdir)
        if xyz:
            atoms = parse_xyz(xyz)
            with open(outpath, 'w') as f:
                f.write(write_xyz_block(atoms))
            print(f"  s0_min: E={e:.6f} from {xyz}")
        else:
            print(f"  ERROR: no S0 min found in {rdir}", file=sys.stderr)
            sys.exit(1)
PYEOF

echo "=== Extracting geometries ==="

declare -A CI_OBJ=(
    [cu3]=somaki
    [ag3]=e_s0
    [au3]=e_s0
    [cu3pd]=e_s0
    [cu3_benzene]=e_s0
    [ceo]=e_s1
    [ce2_h2o]=somaki
)

for sys in cu3 ag3 au3 cu3pd cu3_benzene ceo ce2_h2o; do
    obj=${CI_OBJ[$sys]}
    rdir=results_${sys}_${obj}
    if [ -d "$rdir" ]; then
        python3 phase_b_inputs/extract_geom.py best_ci $rdir phase_b_inputs/${sys}_ci.xyz
    else
        echo "  WARNING: $rdir not found"
    fi
done

for sys in cu3 ag3 au3 ceo; do
    rdir=results_${sys}_e_s0
    if [ -d "$rdir" ]; then
        python3 phase_b_inputs/extract_geom.py s0_min $rdir phase_b_inputs/${sys}_s0min.xyz
    else
        echo "  WARNING: $rdir not found"
    fi
done

echo ""
echo "=== Writing CONICAL inputs ==="

for sys in cu3 ag3 au3; do
    cat > conical_${sys}_v16.inp << EOF
 \$CONTRL SCFTYP=ROHF RUNTYP=CONICAL TDDFT=SPNFLP
         DFTTYP=BHHLYP ISPHER=1 PP=SBKJC MULT=4 MAXIT=200 ICHARG=0 \$END
 \$SYSTEM MWORDS=200 MEMDDI=100 \$END
 \$BASIS  GBASIS=SBKJC \$END
 \$SCF    DAMP=.TRUE. SHIFT=.TRUE. DIIS=.TRUE. SOSCF=.TRUE. EXTRAP=.TRUE. \$END
 \$STATPT NSTEP=50 OPTTOL=1.0E-5 OPTTYP=BPUPD ISTATE=1 JSTATE=2 \$END
 \$TDDFT  NSTATE=5 TAMMD=.TRUE. MULT=2 \$END
 \$DATA
${sys^^} CONICAL refinement v16
C1
$(cat phase_b_inputs/${sys}_ci.xyz)
 \$END
EOF
    echo "  conical_${sys}_v16.inp"
done

cat > conical_cu3pd_v16.inp << EOF
 \$CONTRL SCFTYP=ROHF RUNTYP=CONICAL TDDFT=SPNFLP
         DFTTYP=BHHLYP ISPHER=1 PP=SBKJC MULT=3 MAXIT=200 ICHARG=0 \$END
 \$SYSTEM MWORDS=400 MEMDDI=200 \$END
 \$BASIS  GBASIS=SBKJC \$END
 \$SCF    DAMP=.TRUE. SHIFT=.TRUE. DIIS=.TRUE. SOSCF=.TRUE. EXTRAP=.TRUE. \$END
 \$STATPT NSTEP=50 OPTTOL=1.0E-5 OPTTYP=BPUPD ISTATE=1 JSTATE=2 \$END
 \$TDDFT  NSTATE=5 TAMMD=.TRUE. MULT=1 \$END
 \$DATA
Cu3Pd CONICAL refinement v16
C1
$(cat phase_b_inputs/cu3pd_ci.xyz)
 \$END
EOF
echo "  conical_cu3pd_v16.inp"

cat > conical_cu3_benzene_v16.inp << EOF
 \$CONTRL SCFTYP=ROHF RUNTYP=CONICAL TDDFT=SPNFLP
         DFTTYP=BHHLYP ISPHER=1 PP=READ MULT=4 MAXIT=200 ICHARG=0 \$END
 \$SYSTEM MWORDS=400 MEMDDI=200 \$END
 \$SCF    DAMP=.TRUE. SHIFT=.TRUE. DIIS=.TRUE. SOSCF=.TRUE. EXTRAP=.TRUE. \$END
 \$STATPT NSTEP=50 OPTTOL=1.0E-5 OPTTYP=BPUPD ISTATE=1 JSTATE=2 \$END
 \$TDDFT  NSTATE=5 TAMMD=.TRUE. MULT=2 \$END
 \$DATA
Cu3-benzene CONICAL refinement v16
C1
$(cat phase_b_inputs/cu3_benzene_ci.xyz)
 \$END
 \$ECP
Cu-ECP SBKJC
Cu-ECP SBKJC
Cu-ECP SBKJC
C-ECP NONE
C-ECP NONE
C-ECP NONE
C-ECP NONE
C-ECP NONE
C-ECP NONE
H-ECP NONE
H-ECP NONE
H-ECP NONE
H-ECP NONE
H-ECP NONE
H-ECP NONE
 \$END
EOF
echo "  conical_cu3_benzene_v16.inp"

cat > conical_ceo_v16.inp << EOF
 \$CONTRL SCFTYP=UHF RUNTYP=CONICAL TDDFT=SPNFLP
         DFTTYP=BHHLYP ISPHER=1 PP=SBKJC MULT=3 MAXIT=300 ICHARG=0 \$END
 \$SYSTEM MWORDS=400 MEMDDI=200 \$END
 \$BASIS  GBASIS=SBKJC \$END
 \$SCF    DAMP=.TRUE. SHIFT=.TRUE. DIIS=.TRUE. SOSCF=.TRUE. EXTRAP=.TRUE. \$END
 \$STATPT NSTEP=50 OPTTOL=1.0E-5 OPTTYP=BPUPD ISTATE=1 JSTATE=2 \$END
 \$TDDFT  NSTATE=5 TAMMD=.TRUE. MULT=1 \$END
 \$DATA
CeO CONICAL refinement v16 (UHF SOSCF)
C1
$(cat phase_b_inputs/ceo_ci.xyz)
 \$END
EOF
echo "  conical_ceo_v16.inp"

cat > conical_ce2_h2o_v16.inp << EOF
 \$CONTRL SCFTYP=UHF RUNTYP=CONICAL TDDFT=SPNFLP
         DFTTYP=BHHLYP ISPHER=1 PP=SBKJC MULT=3 MAXIT=300 ICHARG=2 \$END
 \$SYSTEM MWORDS=400 MEMDDI=200 \$END
 \$BASIS  GBASIS=SBKJC \$END
 \$SCF    DAMP=.TRUE. SHIFT=.TRUE. DIIS=.TRUE. SOSCF=.TRUE. EXTRAP=.TRUE. \$END
 \$STATPT NSTEP=50 OPTTOL=1.0E-5 OPTTYP=BPUPD ISTATE=1 JSTATE=2 \$END
 \$TDDFT  NSTATE=5 TAMMD=.TRUE. MULT=1 \$END
 \$DATA
Ce2+(H2O) CONICAL refinement v16 (UHF SOSCF)
C1
$(cat phase_b_inputs/ce2_h2o_ci.xyz)
 \$END
EOF
echo "  conical_ce2_h2o_v16.inp"

echo ""
echo "=== Writing vertical-excitation inputs ==="

for sys in cu3 ag3 au3; do
    cat > vertical_${sys}_v16.inp << EOF
 \$CONTRL SCFTYP=ROHF RUNTYP=ENERGY TDDFT=SPNFLP
         DFTTYP=BHHLYP ISPHER=1 PP=SBKJC MULT=4 MAXIT=200 ICHARG=0 \$END
 \$SYSTEM MWORDS=200 MEMDDI=100 \$END
 \$BASIS  GBASIS=SBKJC \$END
 \$SCF    DAMP=.TRUE. SHIFT=.TRUE. DIIS=.TRUE. SOSCF=.TRUE. EXTRAP=.TRUE. \$END
 \$TDDFT  NSTATE=5 TAMMD=.TRUE. MULT=2 \$END
 \$DATA
${sys^^} vertical excitation at S0 minimum (v16)
C1
$(cat phase_b_inputs/${sys}_s0min.xyz)
 \$END
EOF
    echo "  vertical_${sys}_v16.inp"
done

cat > vertical_ceo_v16.inp << EOF
 \$CONTRL SCFTYP=UHF RUNTYP=ENERGY TDDFT=SPNFLP
         DFTTYP=BHHLYP ISPHER=1 PP=SBKJC MULT=3 MAXIT=300 ICHARG=0 \$END
 \$SYSTEM MWORDS=400 MEMDDI=200 \$END
 \$BASIS  GBASIS=SBKJC \$END
 \$SCF    DAMP=.TRUE. SHIFT=.TRUE. DIIS=.TRUE. SOSCF=.TRUE. EXTRAP=.TRUE. \$END
 \$TDDFT  NSTATE=5 TAMMD=.TRUE. MULT=1 \$END
 \$DATA
CeO vertical excitation at S0 minimum (v16, UHF)
C1
$(cat phase_b_inputs/ceo_s0min.xyz)
 \$END
EOF
echo "  vertical_ceo_v16.inp"

echo ""
echo "=== Writing SLURM submit scripts ==="

cat > submit_v16_phase_b.sh << 'SLURMEOF'
#!/bin/bash
#SBATCH -J v16-phaseB
#SBATCH -A CHM238
#SBATCH --nodes 1
#SBATCH -p batch
#SBATCH -t 6:00:00
#SBATCH -o v16_phase_b-%J.out
#SBATCH -e v16_phase_b-%J.err

module load PrgEnv-gnu cray-python rocm 2>/dev/null
cd ~/Programs/RANGE/examples/GAMESS_calc
GAMESS=~/gamess_gnu_Apr01_2026

run_one() {
    local job=$1
    echo "=========================================="
    echo "=== $job at $(date) ==="
    echo "=========================================="
    $GAMESS/rungms-dev $job 00 1 > ${job}.log 2>&1
    if grep -q "TERMINATED NORMALLY" ${job}.log; then
        echo "  $job: SUCCESS"
        grep -E "FINAL.*ENERGY|EQUILIBRIUM GEOMETRY|MAXIMUM GRADIENT|EXCITATION ENERGY" ${job}.log | tail -10
    else
        echo "  $job: FAILED or INCOMPLETE"
        grep -m1 "ERROR\|TERMINATED" ${job}.log | head -3
    fi
    echo ""
}

for sys in cu3 ag3 au3 cu3pd cu3_benzene ceo ce2_h2o; do
    run_one conical_${sys}_v16
done

for sys in cu3 ag3 au3 ceo; do
    run_one vertical_${sys}_v16
done

echo "=== All v16 phase-B jobs complete at $(date) ==="
SLURMEOF
chmod +x submit_v16_phase_b.sh
echo "  submit_v16_phase_b.sh"

cat > submit_cu3_benzene_stage5.sh << 'STAGEEOF'
#!/bin/bash
#SBATCH -J cu3bnz-stage5
#SBATCH -A CHM238
#SBATCH --nodes 1
#SBATCH -p batch
#SBATCH -t 12:00:00
#SBATCH -o cu3bnz_stage5-%J.out
#SBATCH -e cu3bnz_stage5-%J.err

module load PrgEnv-gnu cray-python rocm 2>/dev/null
export PYTHONPATH=/ccs/proj/chm238/fzahari/python_libs:$PYTHONPATH
cd ~/Programs/RANGE/examples/GAMESS_calc

python3 agent_ci_pipeline.py --molecule cu3_benzene \
    --objectives e_s0,e_s1,somaki \
    --no-llm --no-conical --skip-stage1

echo "=== Stage 5 generation complete at $(date) ==="
ls -la agent_report_cu3_benzene.txt
STAGEEOF
chmod +x submit_cu3_benzene_stage5.sh
echo "  submit_cu3_benzene_stage5.sh"

echo ""
echo "ALL READY. Inspect first, then submit:"
echo "  cat phase_b_inputs/cu3_ci.xyz"
echo "  cat conical_cu3_v16.inp"
echo "  sbatch submit_v16_phase_b.sh"
echo "  sbatch submit_cu3_benzene_stage5.sh"
