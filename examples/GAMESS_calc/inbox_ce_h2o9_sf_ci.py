# -*- coding: utf-8 -*-
"""
RANGE-GAMESS SF-TDDFT Conical Intersection Search for [Ce(H2O)9]3+

Ce(III) nonahydrate in tricapped trigonal prism coordination.
This is the production f-element system for the Yarkony article
and the bridge to DARE actinide photochemistry.

Ce3+ [Xe]4f1: doublet ground state, 4f->5d excitation
9 H2O in first coordination shell (~2.5 A Ce-O distance)

Fragments: Ce3+ + 9 x H2O (10 fragments)
RANGE explores Ce-O distances and H2O orientations.

SF-TDDFT: ROHF quartet reference (MULT=4) -> doublet target (MULT=2)
ECP: SBKJC for all atoms
"""

from RANGE_go.ga_abc import GA_ABC
from RANGE_go.cluster_model import cluster_model
from RANGE_go.energy_calculation import energy_computation

import numpy as np
import os
import glob

print("=" * 60)
print("RANGE-GAMESS SF-TDDFT CI Search: [Ce(H2O)9]3+")
print("  Ce3+ + 9 H2O -- tricapped trigonal prism")
print("=" * 60)

# ============================================================
# Step 0: Create fragment XYZ files
# ============================================================
print("\nStep 0: Creating fragment files")
os.environ['KMP_DUPLICATE_LIB_OK'] = 'True'

# Fragment 1: Ce3+ ion
ce_xyz = 'ce_ion.xyz'
with open(ce_xyz, 'w') as f:
    f.write("1\n")
    f.write("Ce3+ ion\n")
    f.write("Ce   0.000000   0.000000   0.000000\n")
print(f"  Created {ce_xyz}")

# Fragment 2-10: H2O molecules (all identical)
h2o_xyz = 'h2o.xyz'
with open(h2o_xyz, 'w') as f:
    f.write("3\n")
    f.write("H2O molecule\n")
    f.write("O    0.000000   0.000000   0.000000\n")
    f.write("H    0.756950   0.585882   0.000000\n")
    f.write("H   -0.756950   0.585882   0.000000\n")
print(f"  Created {h2o_xyz}")

# Tricapped trigonal prism arrangement around Ce3+
# Ce-O equilibrium ~2.5 A
# 6 prismatic waters + 3 capping waters
# Each box allows +-1.0 A exploration around equilibrium

# Prismatic top triangle (z ~ +1.2 A)
w1 = ( 2.2,  0.0,  1.2)   # +x, top
w2 = (-1.1,  1.9,  1.2)   # -x+y, top
w3 = (-1.1, -1.9,  1.2)   # -x-y, top

# Prismatic bottom triangle (z ~ -1.2 A)
w4 = ( 2.2,  0.0, -1.2)   # +x, bottom
w5 = (-1.1,  1.9, -1.2)   # -x+y, bottom
w6 = (-1.1, -1.9, -1.2)   # -x-y, bottom

# Capping waters (equatorial, z ~ 0)
w7 = ( 0.0,  2.5,  0.0)   # +y, equatorial
w8 = ( 2.2, -1.25, 0.0)   # +x-y, equatorial
w9 = (-2.2, -1.25, 0.0)   # -x-y, equatorial

water_positions = [w1, w2, w3, w4, w5, w6, w7, w8, w9]
box_half = 1.0  # allow +-1.0 A in each direction

input_molecules = [ce_xyz] + [h2o_xyz] * 9
input_num_of_molecules = [1] * 10
input_constraint_type = ['in_box'] * 10

# Ce near origin (tight box)
constraint_values = [(-0.3, -0.3, -0.3, 0.3, 0.3, 0.3)]

# 9 H2O boxes centered on equilibrium positions
for (wx, wy, wz) in water_positions:
    box = (wx - box_half, wy - box_half, wz - box_half,
           wx + box_half, wy + box_half, wz + box_half)
    constraint_values.append(box)

input_constraint_value = constraint_values

print(f"  Ce3+ at origin")
print(f"  9 H2O in tricapped trigonal prism (Ce-O ~ 2.5 A)")
print(f"  Box freedom: +- {box_half} A per water")

# ============================================================
# Step 1: Setting cluster model
# ============================================================
print("\nStep 1: Setting cluster model (Ce3+ + 9 H2O)")
cluster = cluster_model(input_molecules, input_num_of_molecules,
                        input_constraint_type, input_constraint_value)
cluster_template, cluster_boundary, cluster_conversion_rule = cluster.generate_bounds()
print(f"  Search space dimension: {len(cluster_boundary[0])} parameters")
print(f"  = 10 fragments x 6 DOF (3 position + 3 orientation)")

# ============================================================
# Step 2: Setting SF-TDDFT calculator
# ============================================================
print("\nStep 2: Setting SF-TDDFT calculator")

coarse_opt_parameter = dict(
    coarse_calc_eps='UFF',
    coarse_calc_sig='UFF',
    coarse_calc_chg=0,
    coarse_calc_step=20,      # More steps for larger system
    coarse_calc_fmax=10,
    coarse_calc_constraint=None
)

gamess_path = os.path.expanduser('~/gamess_gnu_Apr01_2026')
calculator_command_line = f" {gamess_path}/rungms-dev {{input_script}} 00 1 > job.log "

geo_opt_control_line = dict(
    method='GAMESS_SF_CI',
    input='input_gamess_ce_h2o9_sf_tddft_template',
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
output_folder_name = 'results_ce_h2o9_sf_ci'
print(f"\nStep 3: Running RANGE GA_ABC optimization")
print(f"  Output: {output_folder_name}/")
print(f"  Method: SF-TDDFT / BHHLYP / SBKJC ECP")
print(f"  Reference: ROHF quartet (MULT=4), ICHARG=3")
print(f"  Target: Doublet states (MULT=2)")
print(f"  Atoms: 28 (1 Ce + 9 O + 18 H)")
print(f"  Cost: Somaki, alpha = {geo_opt_control_line['alpha']} Ha")

optimization = GA_ABC(
    computation.obj_func_compute_energy,
    cluster_boundary,
    colony_size=15,       # Larger colony for higher-dimensional search
    limit=30,             # More patience
    max_iteration=40,     # Fewer iterations (each is expensive)
    ga_interval=2,
    ga_parents=3,
    mutate_rate=0.5,
    mutat_sigma=0.03,     # Smaller steps for complex system
    output_directory=output_folder_name,
)
optimization.run(print_interval=1)

# ============================================================
# Step 4: Quick analysis
# ============================================================
print("\n" + "=" * 60)
print("Step 4: Quick analysis of results")
print("=" * 60)

ha_to_ev = 27.2114
results = []
for info_file in glob.glob(os.path.join(output_folder_name, '**', 'sf_ci_info.txt'), recursive=True):
    data = {}
    with open(info_file) as f:
        for line in f:
            if '=' in line:
                key, val = line.split('=', 1)
                key = key.strip()
                val = val.strip().split()[0]
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
else:
    print("\nNo results found. Check for GAMESS errors.")
