# -*- coding: utf-8 -*-
"""
RANGE-GAMESS SF-TDDFT Conical Intersection Search for Cu3

Cu3 (gold trimer) has rich photochemistry:
- Ground state: 2B2 (C2v obtuse triangle)
- CI at D3h equilateral triangle (Jahn-Teller intersection)
- Low-lying excited states from 5s/4d orbital mixing

Three individual Cu atoms as fragments.
RANGE explores all relative positions,
covering triangular, linear, and asymmetric geometries.

SF-TDDFT: ROHF quartet reference -> doublet target states
ECP: SBKJC (built into GAMESS, handles relativistic effects)
"""

from RANGE_go.ga_abc import GA_ABC
from RANGE_go.cluster_model import cluster_model
from RANGE_go.energy_calculation import energy_computation

import numpy as np
import os
import glob

print("=" * 60)
print("RANGE-GAMESS SF-TDDFT CI Search: Cu3")
print("  Three Cu atoms -- exploring all geometries")
print("=" * 60)

# ============================================================
# Step 0: Create Cu atom XYZ files
# ============================================================
print("\nStep 0: Creating Cu atom files")
os.environ['KMP_DUPLICATE_LIB_OK'] = 'True'

for label in ['a', 'b', 'c']:
    fname = f'cu_{label}.xyz'
    with open(fname, 'w') as f:
        f.write("1\n")
        f.write(f"Cu atom {label}\n")
        f.write("Cu   0.000000   0.000000   0.000000\n")
    print(f"  Created {fname}")

# Three Cu atoms with box constraints:
# Cu1: near origin (anchor)
# Cu2: to the right (~2.5 A along +x)
# Cu3: above (allows triangular, linear, all geometries)
# Boxes are wide enough for equilateral D3h, obtuse C2v, and linear D_inf_h
input_molecules = ['cu_a.xyz', 'cu_b.xyz', 'cu_c.xyz']
input_num_of_molecules = [1, 1, 1]
input_constraint_type = ['in_box', 'in_box', 'in_box']
input_constraint_value = [
    (-0.3, -0.3, -0.2,  0.3,  0.3, 0.2),    # Cu1: near origin
    ( 1.5, -0.8, -0.2,  2.8,  0.8, 0.2),    # Cu2: ~2.5 A along +x
    (-0.5,  0.8, -0.2,  1.8,  2.6, 0.2),    # Cu3: above, allows triangle
]

# ============================================================
# Step 1: Setting cluster model
# ============================================================
print("\nStep 1: Setting cluster model (three Cu atoms)")
cluster = cluster_model(input_molecules, input_num_of_molecules,
                        input_constraint_type, input_constraint_value)
cluster_template, cluster_boundary, cluster_conversion_rule = cluster.generate_bounds()
print(f"  Search space dimension: {len(cluster_boundary[0])} parameters")

# ============================================================
# Step 2: Setting SF-TDDFT calculator
# ============================================================
print("\nStep 2: Setting SF-TDDFT calculator")

# Coarse LJ pre-optimization
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

# SF-TDDFT CI search for Cu3
# Quartet reference (MULT=4) -> Doublet targets (MULT=2)
# cost_type can be overridden: 'somaki', 'e_s0', 'e_s1', 'gap', etc.
geo_opt_control_line = dict(
    method='GAMESS_SF_CI',
    input='input_gamess_cu3_sf_tddft_template',
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
output_folder_name = 'results_cu3_e_s1'
print(f"\nStep 3: Running RANGE GA_ABC optimization")
print(f"  Output: {output_folder_name}/")
print(f"  Method: SF-TDDFT / BHHLYP / SBKJC ECP")
print(f"  Reference: ROHF quartet (MULT=4)")
print(f"  Target: Doublet states (MULT=2)")
print(f"  Cost: Somaki C = (E_S0+E_S1)/2 + (E_S1-E_S0)^2/alpha")
print(f"  Alpha = {geo_opt_control_line['alpha']} Ha")
print(f"  Fragments: 3 x Cu atom")

optimization = GA_ABC(
    computation.obj_func_compute_energy,
    cluster_boundary,
    colony_size=10,
    limit=20,
    max_iteration=15,
    ga_interval=2,
    ga_parents=3,
    mutate_rate=0.5,
    mutat_sigma=0.05,
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
    print("\nNo results found. Check for GAMESS errors in job directories.")
