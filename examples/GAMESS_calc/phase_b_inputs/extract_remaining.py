"""Extract best CI for the 5 systems whose CSVs aren't present.
Reads sf_ci_info.txt files directly with correct format: 'Gap = X Ha = Y eV'."""
import os, glob, re

ATOMIC_Z = {'H':1.0,'C':6.0,'O':8.0,'Cu':29.0,'Ag':47.0,'Au':79.0,'Pd':46.0,'Ce':58.0}

# (system, objective)
SYSTEMS = [
    ('cu3',     'somaki'),
    ('ag3',     'e_s0'),
    ('au3',     'e_s0'),
    ('ceo',     'e_s1'),
    ('ce2_h2o', 'somaki'),
]

def parse_xyz(path):
    with open(path) as f:
        lines = f.readlines()
    n = int(lines[0])
    atoms = []
    for line in lines[2:2+n]:
        p = line.split()
        atoms.append((p[0], float(p[1]), float(p[2]), float(p[3])))
    return atoms

def write_xyz_block(atoms):
    out = []
    for el, x, y, z in atoms:
        z_at = ATOMIC_Z.get(el, 0.0)
        out.append(f" {el:<3s} {z_at:6.1f}  {x:14.8f}  {y:14.8f}  {z:14.8f}")
    return '\n'.join(out)

# Pattern: "Gap = 0.0184295080 Ha = 0.501493 eV"
GAP_RE = re.compile(r'^Gap\s*=\s*([\d.E+-]+)\s*Ha\s*=\s*([\d.E+-]+)\s*eV', re.M)

for sys_name, obj in SYSTEMS:
    rdir = f"results_{sys_name}_{obj}"
    if not os.path.isdir(rdir):
        print(f"  {sys_name}: dir {rdir} not found")
        continue
    
    best_gap_ev = 999.0
    best_compute = None
    n_scanned = 0
    
    for sf in glob.glob(f"{rdir}/compute_*/sf_ci_info.txt"):
        try:
            with open(sf) as f:
                txt = f.read()
        except OSError:
            continue
        m = GAP_RE.search(txt)
        if not m:
            continue
        n_scanned += 1
        gap_ev = float(m.group(2))
        if gap_ev < best_gap_ev:
            best_gap_ev = gap_ev
            best_compute = os.path.dirname(sf)
    
    if best_compute is None:
        print(f"  {sys_name}: no parseable sf_ci_info.txt found ({n_scanned} scanned)")
        continue
    
    xyz_path = os.path.join(best_compute, 'final.xyz')
    if not os.path.isfile(xyz_path):
        print(f"  {sys_name}: final.xyz missing at {xyz_path}")
        continue
    
    atoms = parse_xyz(xyz_path)
    out_path = f"phase_b_inputs/{sys_name}_ci.xyz"
    with open(out_path, 'w') as f:
        f.write(write_xyz_block(atoms))
    
    print(f"  {sys_name} ({obj}): gap={best_gap_ev*1000:.2f} meV from {os.path.basename(best_compute)}, {len(atoms)} atoms (scanned {n_scanned} files)")
