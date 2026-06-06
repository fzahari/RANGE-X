# -*- coding: utf-8 -*-
"""
RANGE-GAMESS SF-TDDFT Conical Intersection Search for Ethylene

Key insight: Ethylene is treated as TWO CH2 fragments.
RANGE explores their relative position and orientation,
which naturally parametrizes the C=C stretch and HCCH twist --
exactly the coordinates relevant for the S0/S1 CI.

The Somaki cost function C = (E_S0+E_S1)/2 + (E_S1-E_S0)^2/alpha
is minimized by RANGE's GA_ABC optimizer to locate CI regions.

Usage on Frontier:
    module swap PrgEnv-cray PrgEnv-gnu
    module load cray-python
    pip install --user ase scipy
    pip install --user -e /path/to/RANGE
    python inbox_ethylene_sf_ci.py
"""

from RANGE_go.ga_abc import GA_ABC
from RANGE_go.cluster_model import cluster_model
from RANGE_go.energy_calculation import energy_computation

import numpy as np
import os

print("="*60)
print("RANGE-GAMESS SF-TDDFT CI Search: Ethylene")
print("  Two CH2 fragments -- exploring twist + stretch")
print("="*60)

# ============================================================
# Step 0: Create CH2 fragment XYZ files
# ============================================================
print("\nStep 0: Creating CH2 fragment files")
os.environ['KMP_DUPLICATE_LIB_OK'] = 'True'

# Fragment 1: C + two H's (one side of ethylene)
# Centered at origin, H's in the xz-plane
ch2_a_xyz = 'ch2_a.xyz'
with open(ch2_a_xyz, 'w') as f:
    f.write("3\n")
    f.write("CH2 fragment A (centered at origin)\n")
    f.write("C    0.000000    0.000000    0.000000\n")
    f.write("H    0.000000    0.923708    0.573795\n")
    f.write("H    0.000000   -0.923708    0.573795\n")
print(f"  Created {ch2_a_xyz}")

# Fragment 2: identical CH2
ch2_b_xyz = 'ch2_b.xyz'
with open(ch2_b_xyz, 'w') as f:
    f.write("3\n")
    f.write("CH2 fragment B (centered at origin)\n")
    f.write("C    0.000000    0.000000    0.000000\n")
    f.write("H    0.000000    0.923708    0.573795\n")
    f.write("H    0.000000   -0.923708    0.573795\n")
print(f"  Created {ch2_b_xyz}")

# Two CH2 fragments:
# Fragment A is placed at ~(0, 0, +0.665) with some rotation freedom
# Fragment B is placed at ~(0, 0, -0.665) with rotation freedom
# The relative rotation around z explores the dihedral
# The relative z-distance explores C=C stretch
input_molecules = [ch2_a_xyz, ch2_b_xyz]
input_num_of_molecules = [1, 1]
input_constraint_type = ['in_box', 'in_box']
# Allow each CH2 to move within a box near its equilibrium position
# This permits C=C stretch (z displacement) and twist (rotation)
input_constraint_value = [
    (-0.5, -0.5, 0.3,  0.5, 0.5, 1.0),   # Fragment A near z=+0.665
    (-0.5, -0.5, -1.0, 0.5, 0.5, -0.3),   # Fragment B near z=-0.665
]

# ============================================================
# Step 1: Setting cluster model
# ============================================================
print("\nStep 1: Setting cluster model (two CH2 fragments)")
cluster = cluster_model(input_molecules, input_num_of_molecules,
                        input_constraint_type, input_constraint_value,
                        )
cluster_template, cluster_boundary, cluster_conversion_rule = cluster.generate_bounds()
print(f"  Search space dimension: {len(cluster_boundary[0])} parameters")
print(f"  = 2 fragments x 6 DOF (x,y,z + 3 Euler angles)")

# ============================================================
# Step 2: Setting SF-TDDFT calculator with Somaki cost function
# ============================================================
print("\nStep 2: Setting SF-TDDFT calculator")

# Coarse LJ pre-optimization prevents atomic clashes
coarse_opt_parameter = dict(
    coarse_calc_eps='UFF',
    coarse_calc_sig='UFF',
    coarse_calc_chg=0,
    coarse_calc_step=10,
    coarse_calc_fmax=10,
    coarse_calc_constraint=None
)

# GAMESS GNU build path on Frontier
gamess_path = os.path.expanduser('~/gamess_gnu_Apr01_2026')
calculator_command_line = f" {gamess_path}/rungms-dev {{input_script}} 00 1 > job.log "

# SF-TDDFT CI search
# alpha = 0.02 Ha (Somaki et al. value for formaldehyde)
geo_opt_control_line = dict(
    method='GAMESS_SF_CI',
    input='input_gamess_sf_tddft_template',
    alpha=0.02,
)

computation = energy_computation(
    templates=cluster_template,
    go_conversion_rule=cluster_conversion_rule,
    calculator=calculator_command_line,
    calculator_type='external',
    geo_opt_para=geo_opt_control_line,
    if_coarse_calc=True,
    coarse_calc_para=coarse_opt_parameter,
    save_output_level='Full',
)

# ============================================================
# Step 3: Run RANGE
# ============================================================
output_folder_name = 'results_ethylene_mean'
print(f"\nStep 3: Running RANGE GA_ABC optimization")
print(f"  Output: {output_folder_name}/")
print(f"  Method: SF-TDDFT / BHHLYP / 6-31G(d,p)")
print(f"  Cost: Somaki C = (E_S0+E_S1)/2 + (E_S1-E_S0)^2/alpha")
print(f"  Alpha = {geo_opt_control_line['alpha']} Ha")
print(f"  Fragments: 2 x CH2, exploring relative twist + stretch")

optimization = GA_ABC(
    computation.obj_func_compute_energy,
    cluster_boundary,
    colony_size=10,       # 10 structures per generation
    limit=20,             # Abandon after 20 failures
    max_iteration=50,     # 50 generations (increase for production)
    ga_interval=2,        # GA crossover every 2 iterations
    ga_parents=3,
    mutate_rate=0.5,
    mutat_sigma=0.05,     # Step size for mutations
    output_directory=output_folder_name,
)
optimization.run(print_interval=1)

# ============================================================
# Step 4: Quick analysis
# ============================================================
print("\n" + "="*60)
print("Step 4: Quick analysis of results")
print("="*60)

# Scan results for lowest-cost and lowest-gap structures
import glob
ha_to_ev = 27.2114
results = []
for info_file in glob.glob(os.path.join(output_folder_name, '**', 'sf_ci_info.txt'), recursive=True):
    data = {}
    with open(info_file) as f:
        for line in f:
            if '=' in line:
                key, val = line.split('=', 1)
                key = key.strip()
                val = val.strip().split()[0]  # Take first token
                try:
                    data[key] = float(val)
                except ValueError:
                    pass
    if 'Gap' in data and 'Cost_C' in data:
        results.append({
            'file': info_file,
            'gap_ev': data['Gap'] * ha_to_ev,
            'cost': data['Cost_C'],
            'e_s0': data.get('E_S0', 0),
            'e_s1': data.get('E_S1', 0),
        })

if results:
    results.sort(key=lambda r: abs(r['gap_ev']))
    print(f"\nFound {len(results)} completed calculations")
    print(f"\nTop 5 smallest gaps:")
    print(f"  {'Gap (eV)':>10s}  {'Cost (Ha)':>14s}  {'E_S0 (Ha)':>14s}")
    for r in results[:5]:
        print(f"  {r['gap_ev']:10.4f}  {r['cost']:14.8f}  {r['e_s0']:14.8f}")

    print(f"\n  Best gap: {results[0]['gap_ev']:.4f} eV")
    print(f"  Compare to manual SF-TDDFT MECI: gap = 0.000 eV")
    print(f"\nNext: python screen_ci_candidates.py --results_dir {output_folder_name}")
else:
    print("\nNo results found. Check for GAMESS errors in job directories.")
