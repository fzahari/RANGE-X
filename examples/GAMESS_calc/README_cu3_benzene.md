# Cu3/benzene Bundle for RANGE-GAMESS SF-TDDFT CI Search

## April 19, 2026

Supporting the Yarkony article (section 3.3.2). Follow-up to:
Krupka & de Lara-Castells, Phys. Chem. Chem. Phys. 2024, 26, 28349-28360
(DOI: 10.1039/D4CP03271C). They used multi-reference RS2C on a
constrained 2D scan; we use RANGE for unconstrained global search in
~9 DOF (Cu3 internal + Cu3-benzene relative geometry).

### New Files to Copy to Frontier

Copy all files to `~/Programs/RANGE/examples/GAMESS_calc/`:

```bash
scp inbox_cu3_benzene_sf_ci.py frontier:~/Programs/RANGE/examples/GAMESS_calc/
scp input_gamess_cu3_benzene_sf_tddft_template frontier:~/Programs/RANGE/examples/GAMESS_calc/
scp run_cu3_benzene_*.sh frontier:~/Programs/RANGE/examples/GAMESS_calc/
```

### No RANGE patch needed

Cu (Z=29), C (Z=6), and H (Z=1) are already in the element mapping in
`energy_calculation.py` -- Cu was added when the isolated Cu3 system was
set up, and C/H have been there since ethylene. Unlike Cu3Pd (which
required a Pd=46 patch), no modifications to RANGE are needed.

### Agent pipeline support

The SLURM scripts invoke `agent_ci_pipeline.py --molecule cu3_benzene`.
If the agent pipeline does not recognize the `cu3_benzene` molecule name
yet, add it to the molecule lookup in `agent_ci_pipeline.py` (same
pattern as `cu3pd`, `ag3`, `cu3`, `au3`, etc.) -- it should just need a
one-line entry pointing to `inbox_cu3_benzene_sf_ci.py`.

### Cu3/benzene Setup

| Property | Value |
|----------|-------|
| Fragments | 3 Cu atoms + 1 rigid benzene (4 fragments) |
| Cu basis  | SBKJC ECP (small-core, relativistic) |
| C basis   | 6-31G(d) (N31, NGAUSS=6, NDFUNC=1) |
| H basis   | 6-31G (N31, NGAUSS=6) |
| Method    | SF-TDDFT / BHHLYP |
| Reference | ROHF quartet (MULT=4), ICHARG=0 |
| SF target | Doublet (MULT=2), NSTATE=5, Tamm-Dancoff |
| Template  | `input_gamess_cu3_benzene_sf_tddft_template` |
| Inbox     | `inbox_cu3_benzene_sf_ci.py` |

### Mixed-Basis Input

Unlike Cu3Pd (all SBKJC), this system needs two basis sets in one
GAMESS input. The template uses the canonical GAMESS pattern:

```
 $CONTRL ... PP=READ ... $END
 $BASIS  BASNAM(1)=metal,metal,metal,ligC x6,ligH x6 $END
 $metal  GBASIS=SBKJC $END
 $ligC   GBASIS=N31 NGAUSS=6 NDFUNC=1 $END
 $ligH   GBASIS=N31 NGAUSS=6 $END
 $ECP
Cu-ecp SBKJC
...  (3 x Cu)
C-ecp none
...  (6 x C)
H-ecp none
...  (6 x H)
 $END
```

The atom order in the generated `$DATA` block MUST be
`Cu, Cu, Cu, C x 6, H x 6`. This is preserved by RANGE as long as
fragments are declared as `[cu_xyz, benzene_xyz]` with counts
`[3, 1]` in the inbox, and benzene's xyz file lists the 6 C's first,
then the 6 H's (as written).

**Verify on the first run:** `cat results_cu3_benzene_*/*/job.inp | head -30`
-- confirm the atom order matches the BASNAM list.

### Electron Count Check

SBKJC on Cu valence-only; all-electron on C/H:
- Cu: 19 valence e- x 3 = 57
- C:  6 x 6 = 36
- H:  1 x 6 = 6
- **Total = 99 valence e- (odd)** => MULT must be even.
- Quartet reference (MULT=4) -> SF to doublet (MULT=2): correct.

If SCF fails to converge:
- Try MULT=6 -> MULT=2 (sextet -> doublet SF) as alternate ref
- The template already includes `$SCF DAMP=.TRUE. SHIFT=.TRUE. DIIS=.TRUE.`
  to aid convergence (same as Cu3Pd template).

### To Submit

```bash
cd ~/Programs/RANGE/examples/GAMESS_calc
for obj in e_s0 e_s1 somaki; do
    sbatch run_cu3_benzene_${obj}.sh
done
```

### Search Space

9 effective DOF:
- Cu3 internal geometry (3 Cu atom positions)
- Cu3 vertical separation from benzene (1 DOF, collectively via z)
- Cu3 lateral position over the ring (2 DOF, collectively via xy)
- Cu3 orientation relative to ring (3 DOF, implicit in the 3 Cu xyz)

Box constraints (see inbox):
- Cu atoms: x,y in [-2, 2] A, z in [2, 5] A -- covers physisorption
  (~3 A, parallel, C3v-like) and chemisorption (~2 A, perpendicular,
  C2v-like) from Krupka 2024
- Benzene: effectively fixed at origin in xy-plane

### 2-hour walltime on CHM238

This system is larger than Cu3Pd (15 atoms vs 4, 99 valence e- vs 75).
Per-evaluation runtime will be significantly longer. RANGE will likely
not finish a full 50-iteration optimization within one 2-hour window.

The agent pipeline skips geometries that already have `sf_ci_info.txt`
files, so resubmitting the same job picks up where the previous one
stopped. If needed: `sbatch run_cu3_benzene_e_s0.sh` 2-3 times.

### Science Question

Does the benzene pi system lift or modify the Jahn-Teller CI of
isolated Cu3? Does RANGE find additional low-lying configurations
that Krupka's constrained 2D scan missed? Direct connection to
catalysis (supported metal clusters on pi-systems).
