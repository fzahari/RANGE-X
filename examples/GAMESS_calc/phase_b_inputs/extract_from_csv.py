"""Read best CI from gap_*.csv files and copy the corresponding final.xyz."""
import csv, os, sys, math

ATOMIC_Z = {'H':1.0,'C':6.0,'O':8.0,'Cu':29.0,'Ag':47.0,'Au':79.0,'Pd':46.0,'Ce':58.0}

CSV_BASE = '/ccs/home/fzahari/Vanda/ceo_qc/article_figures/data'

# (system, objective, results_dir_prefix)
SYSTEMS = [
    ('cu3',         'somaki', 'results_cu3_somaki'),
    ('ag3',         'e_s0',   'results_ag3_e_s0'),
    ('au3',         'e_s0',   'results_au3_e_s0'),
    ('cu3pd',       'e_s0',   'results_cu3pd_e_s0'),
    ('cu3_benzene', 'e_s0',   'results_cu3_benzene_e_s0'),
    ('ceo',         'e_s1',   'results_ceo_e_s1'),
    ('ce2_h2o',     'somaki', 'results_ce2_h2o_somaki'),
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

for sys_name, obj, rdir in SYSTEMS:
    csv_path = f"{CSV_BASE}/gaps_{sys_name}_{obj}.csv"
    if not os.path.isfile(csv_path):
        print(f"  {sys_name}: CSV not found at {csv_path}")
        continue
    with open(csv_path) as f:
        reader = csv.DictReader(f)
        first = next(reader)
    gap = float(first['gap_ev'])
    compute_dir = first['compute_dir']
    xyz_path = f"{rdir}/{compute_dir}/final.xyz"
    if not os.path.isfile(xyz_path):
        print(f"  {sys_name}: XYZ missing at {xyz_path}")
        continue
    atoms = parse_xyz(xyz_path)
    out_path = f"phase_b_inputs/{sys_name}_ci.xyz"
    with open(out_path, 'w') as f:
        f.write(write_xyz_block(atoms))
    print(f"  {sys_name} ({obj}): gap={gap*1000:.2f} meV from {compute_dir}, {len(atoms)} atoms")
