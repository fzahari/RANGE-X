# -*- coding: utf-8 -*-
"""
RANGE-GAMESS TDDFT Excited State Search for [Ce(H2O)]3+

Ce3+ has [Xe]4f1 configuration (doublet ground state).
Regular TDDFT (not SF) from UHF doublet reference.
UHF required for f-electron SCF convergence.

Fragments: Ce3+ ion + H2O molecule (2 fragments)
RANGE explores Ce-O distance and H2O orientation.
"""

from RANGE_go.ga_abc import GA_ABC
from RANGE_go.cluster_model import cluster_model
from RANGE_go.energy_calculation import energy_computation

import numpy as np
import os
import glob

print("=" * 60)
print("RANGE-GAMESS TDDFT Excited State Search: [Ce(H2O)]3+")
print("  Ce3+ + H2O -- exploring Ce-O distance and orientation")
print("=" * 60)

print("\nStep 0: Creating fragment files")
os.environ['KMP_DUPLICATE_LIB_OK'] = 'True'

ce_xyz = 'ce_ion.xyz'
with open(ce_xyz, 'w') as f:
    f.write("1\n")
    f.write("Ce3+ ion\n")
    f.write("Ce   0.000000   0.000000   0.000000\n")
print(f"  Created {ce_xyz}")

h2o_xyz = 'h2o.xyz'
with open(h2o_xyz, 'w') as f:
    f.write("3\n")
    f.write("H2O molecule\n")
    f.write("O    0.000000   0.000000   0.000000\n")
    f.write("H    0.756950   0.585882   0.000000\n")
    f.write("H   -0.756950   0.585882   0.000000\n")
print(f"  Created {h2o_xyz}")

input_molecules = [ce_xyz, h2o_xyz]
input_num_of_molecules = [1, 1]
input_constraint_type = ['in_box', 'in_box']
input_constraint_value = [
    (-0.3, -0.3, -0.3,  0.3,  0.3, 0.3),
    ( 1.8, -1.0, -1.0,  3.5,  1.0, 1.0),
]

print("\nStep 1: Setting cluster model (Ce3+ + H2O)")
cluster = cluster_model(input_molecules, input_num_of_molecules,
                        input_constraint_type, input_constraint_value)
cluster_template, cluster_boundary, cluster_conversion_rule = cluster.generate_bounds()
print(f"  Search space dimension: {len(cluster_boundary[0])} parameters")

print("\nStep 2: Setting TDDFT calculator (UHF)")

coarse_opt_parameter = dict(
    coarse_calc_eps='UFF',
    coarse_calc_sig='UFF',
    coarse_calc_chg=0,
    coarse_calc_step=10,
    coarse_calc_fmax=10,
    coarse_calc_constraint=None
)

gamess_path = os.path.expanduser('~/gamess_gnu_Apr01_2026')
calculator_command_line = f" {gamess_path}/rungms-dev {{input_script}} 00 1 > job.log "

geo_opt_control_line = dict(
    method='GAMESS_SF_CI',
    input='input_gamess_ce3_h2o_tddft_template',
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

output_folder_name = 'results_ce3_h2o_sf_ci'
print(f"\nStep 3: Running RANGE GA_ABC optimization")
print(f"  Output: {output_folder_name}/")
print(f"  Method: UHF TDDFT / BHHLYP / SBKJC ECP")
print(f"  Reference: UHF doublet (MULT=2), ICHARG=3")
print(f"  Target: Doublet excited states (MULT=2)")

optimization = GA_ABC(
    computation.obj_func_compute_energy,
    cluster_boundary,
    colony_size=10,
    limit=20,
    max_iteration=50,
    ga_interval=2,
    ga_parents=3,
    mutate_rate=0.5,
    mutat_sigma=0.05,
    output_directory=output_folder_name,
)
optimization.run(print_interval=1)

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
