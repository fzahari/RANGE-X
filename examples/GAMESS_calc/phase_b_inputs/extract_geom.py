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
