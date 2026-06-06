# RANGE SF-TDDFT Conical Intersection Search Update

## What's new

### Modified: `RANGE_go/energy_calculation.py`
Added `GAMESS_SF_CI` method alongside existing `GAMESS` method.
- Generates SF-TDDFT input (ROHF triplet reference, BHHLYP, spin-flip singlet targets)
- Parses both S0 and S1 absolute energies from SF-TDDFT output
- Computes Somaki cost function: C = (E_S0 + E_S1)/2 + (E_S1 - E_S0)^2/alpha
- Saves `sf_ci_info.txt` in each job directory with E_S0, E_S1, gap, cost
- Existing `GAMESS` method is unchanged

### New files in `examples/GAMESS_calc/`
- `input_gamess_sf_tddft_template` -- GAMESS template for SF-TDDFT energy runs
- `inbox_ethylene_sf_ci.py` -- RANGE driver for ethylene CI search
  - Uses TWO CH2 fragments to parametrize twist + stretch
  - RANGE explores relative orientation -> dihedral angle
- `screen_ci_candidates.py` -- Post-RANGE screening (GPR + DBSCAN)
- `test_gamess_sf_ci_binding.py` -- Unit tests for SF-TDDFT parsing
- `run_range_sf_ci_frontier.sh` -- Frontier SLURM script

## Deploy on Frontier

```bash
# Overlay onto existing RANGE installation
cd ~/RANGE   # or wherever RANGE is installed
tar xzf RANGE_sf_ci_update.tar.gz

# Install dependencies
module swap PrgEnv-cray PrgEnv-gnu
module load cray-python
pip install --user ase scipy scikit-learn

# Run
cd examples/GAMESS_calc
sbatch run_range_sf_ci_frontier.sh
```

## Key design decisions

1. **SF-TDDFT throughout**: Conventional TDA-TDDFT fails at the
   ethylene CI due to RHF reference breakdown at 90-degree twist.
   SF-TDDFT with ROHF triplet reference handles this correctly.

2. **Two-fragment model**: Ethylene = 2 x CH2. RANGE explores their
   relative position (C=C stretch) and rotation (HCCH dihedral).
   This naturally parametrizes the CI-relevant coordinates.

3. **Somaki cost function**: C = (E_S0+E_S1)/2 + (E_S1-E_S0)^2/alpha
   balances minimizing average energy with closing the gap.
   alpha = 0.02 Ha (from Somaki, Inagaki, Hatanaka).

4. **BHHLYP functional**: 50% HF exchange, standard for SF-TDDFT.

## Validation

Compare RANGE results against manual calculations:
- S0 optimized geometry: E = -78.5338 Ha, C=C = 1.331 A (B3LYP)
- SF-TDDFT MECI: gap = 0.000001 Ha at 90-degree twisted/pyramidalized geometry
- Dihedral scan: gap narrows from 8.46 eV (planar) to 1.67 eV (90 deg, conventional TDDFT)
