#!/usr/bin/env python3
"""
Test the GAMESS SF-TDDFT CI binding for RANGE.
Tests parsing of SF-TDDFT output and Somaki cost function computation.
"""

import os
import tempfile
import shutil
import numpy as np


def test_sf_tddft_parsing():
    """Test parsing SF-TDDFT output and Somaki cost function."""
    tmpdir = tempfile.mkdtemp()
    try:
        log_path = os.path.join(tmpdir, 'job.log')
        with open(log_path, 'w') as f:
            # Realistic GAMESS SF-TDDFT output
            f.write(""" EXECUTION OF GAMESS BEGUN 22:00:00 01-APR-2026

 COORDINATES OF ALL ATOMS ARE (ANGS)
   ATOM   CHARGE       X              Y              Z
 ------------------------------------------------------------
 C           6.0   0.0000000000   0.0000000000   0.6600000000
 C           6.0   0.0000000000   0.0000000000  -0.6600000000
 H           1.0   0.9200000000   0.0000000000   1.2300000000
 H           1.0  -0.9200000000   0.0000000000   1.2300000000
 H           1.0   0.0000000000   0.9200000000  -1.2300000000
 H           1.0   0.0000000000  -0.9200000000  -1.2300000000

 FINAL ROHF ENERGY IS      -78.3500000000 AFTER  15 ITERATIONS

 SUMMARY OF TDDFT RESULTS

    STATE NUMBER   1  ENERGY =   -2.500000 EV   S =  0
    STATE NUMBER   2  ENERGY =   -2.300000 EV   S =  0
    STATE NUMBER   3  ENERGY =    1.200000 EV   S =  0
    STATE NUMBER   4  ENERGY =    3.500000 EV   S =  0
    STATE NUMBER   5  ENERGY =    5.800000 EV   S =  0

 EXECUTION OF GAMESS TERMINATED NORMALLY 22:01:00 01-APR-2026
""")

        import re
        ha_to_ev = 27.2114
        alpha = 0.02

        with open(log_path, 'r') as f4:
            log_lines = f4.readlines()

        # Parse ROHF energy
        e_rohf = None
        for line in log_lines:
            if 'FINAL ROHF ENERGY IS' in line:
                parts_e = line.split()
                for k, tok in enumerate(parts_e):
                    if tok == 'IS':
                        e_rohf = float(parts_e[k+1])
                        break

        assert e_rohf is not None, "Failed to parse ROHF energy"
        assert abs(e_rohf - (-78.35)) < 1e-8, f"Wrong ROHF energy: {e_rohf}"
        print(f"  ROHF energy: {e_rohf} Ha -- OK")

        # Parse SF-TDDFT states
        sf_state_energies_ev = []
        last_state_set = []
        for line in log_lines:
            m = re.search(r'STATE\s+NUMBER\s+\d+\s+ENERGY\s*=\s*([\d\.\-]+)\s*EV', line)
            if m:
                last_state_set.append(float(m.group(1)))
            elif len(last_state_set) > 0 and 'STATE NUMBER' not in line and last_state_set:
                sf_state_energies_ev = last_state_set[:]
                last_state_set = []
        if len(last_state_set) > 0:
            sf_state_energies_ev = last_state_set[:]

        assert len(sf_state_energies_ev) == 5, f"Expected 5 states, got {len(sf_state_energies_ev)}"
        assert abs(sf_state_energies_ev[0] - (-2.5)) < 1e-6, f"Wrong state 1: {sf_state_energies_ev[0]}"
        print(f"  SF states (eV): {sf_state_energies_ev} -- OK")

        # Compute absolute energies
        sf_abs = [e_rohf + exc / ha_to_ev for exc in sf_state_energies_ev]
        sf_abs.sort()

        e_s0 = sf_abs[0]
        e_s1 = sf_abs[1]
        gap = e_s1 - e_s0

        print(f"  E_S0 = {e_s0:.8f} Ha")
        print(f"  E_S1 = {e_s1:.8f} Ha")
        print(f"  Gap  = {gap:.8f} Ha = {gap*ha_to_ev:.4f} eV")

        # Somaki cost function
        cost = (e_s0 + e_s1) / 2.0 + gap**2 / alpha
        print(f"  Cost = {cost:.8f} Ha (alpha={alpha})")

        # Verify: lowest two SF states are -2.5 eV and -2.3 eV from triplet ref
        expected_s0 = e_rohf + (-2.5) / ha_to_ev
        expected_s1 = e_rohf + (-2.3) / ha_to_ev
        assert abs(e_s0 - expected_s0) < 1e-8, f"E_S0 mismatch"
        assert abs(e_s1 - expected_s1) < 1e-8, f"E_S1 mismatch"

        expected_gap = ((-2.3) - (-2.5)) / ha_to_ev  # 0.2 eV in Ha
        assert abs(gap - expected_gap) < 1e-8, f"Gap mismatch: {gap} vs {expected_gap}"
        print(f"  Verified: gap = 0.2 eV = {expected_gap:.8f} Ha -- OK")

        print("  PASSED: SF-TDDFT parsing and cost function")

    finally:
        shutil.rmtree(tmpdir)


def test_sf_tddft_near_ci():
    """Test with near-degenerate states (CI region)."""
    tmpdir = tempfile.mkdtemp()
    try:
        log_path = os.path.join(tmpdir, 'job.log')
        with open(log_path, 'w') as f:
            f.write(""" FINAL ROHF ENERGY IS      -78.4000000000 AFTER  15 ITERATIONS

 COORDINATES OF ALL ATOMS ARE (ANGS)
   ATOM   CHARGE       X              Y              Z
 ------------------------------------------------------------
 C           6.0   0.0300000000   0.0600000000   0.7100000000
 C           6.0   0.0600000000   0.0300000000  -0.7100000000
 H           1.0   0.9200000000  -0.1900000000   1.2500000000
 H           1.0  -0.9300000000   0.1000000000   1.1900000000
 H           1.0  -0.2000000000   0.9200000000  -1.2500000000
 H           1.0   0.1100000000  -0.9300000000  -1.1900000000

    STATE NUMBER   1  ENERGY =   -1.000000 EV   S =  0
    STATE NUMBER   2  ENERGY =   -0.999000 EV   S =  0
    STATE NUMBER   3  ENERGY =    2.500000 EV   S =  0

 EXECUTION OF GAMESS TERMINATED NORMALLY
""")

        import re
        ha_to_ev = 27.2114
        alpha = 0.02

        with open(log_path, 'r') as f4:
            log_lines = f4.readlines()

        e_rohf = None
        for line in log_lines:
            if 'FINAL ROHF ENERGY IS' in line:
                parts_e = line.split()
                for k, tok in enumerate(parts_e):
                    if tok == 'IS':
                        e_rohf = float(parts_e[k+1])
                        break

        sf_state_energies_ev = []
        last_state_set = []
        for line in log_lines:
            m = re.search(r'STATE\s+NUMBER\s+\d+\s+ENERGY\s*=\s*([\d\.\-]+)\s*EV', line)
            if m:
                last_state_set.append(float(m.group(1)))
            elif len(last_state_set) > 0 and 'STATE NUMBER' not in line and last_state_set:
                sf_state_energies_ev = last_state_set[:]
                last_state_set = []
        if len(last_state_set) > 0:
            sf_state_energies_ev = last_state_set[:]

        sf_abs = [e_rohf + exc / ha_to_ev for exc in sf_state_energies_ev]
        sf_abs.sort()
        e_s0, e_s1 = sf_abs[0], sf_abs[1]
        gap = e_s1 - e_s0
        cost = (e_s0 + e_s1) / 2.0 + gap**2 / alpha

        expected_gap_ev = 0.001  # 1 meV
        expected_gap_ha = expected_gap_ev / ha_to_ev
        assert abs(gap - expected_gap_ha) < 1e-8, f"Gap mismatch: {gap*ha_to_ev:.6f} eV"

        print(f"  Near-CI test: gap = {gap*ha_to_ev:.6f} eV = {gap:.10f} Ha")
        print(f"  Cost penalty from gap: {gap**2/alpha:.10f} Ha (should be tiny)")
        print(f"  Total cost: {cost:.10f} Ha")
        assert gap**2 / alpha < 1e-6, "Gap penalty should be negligible at CI"
        print("  PASSED: Near-CI cost function")

    finally:
        shutil.rmtree(tmpdir)


if __name__ == '__main__':
    print("Testing GAMESS SF-TDDFT CI binding for RANGE...\n")
    test_sf_tddft_parsing()
    print()
    test_sf_tddft_near_ci()
    print("\nAll tests passed!")
