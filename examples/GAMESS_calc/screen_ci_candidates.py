#!/usr/bin/env python3
"""
Step 2 -- Screen: Analyze RANGE ensemble for CI candidates

After RANGE exploration (inbox_ethylene_sf_ci.py), this script:
  1. Reads all sf_ci_info.txt files from the RANGE output
  2. Builds a dataset of (geometry, E_S0, E_S1, gap, cost)
  3. Trains Gaussian Process Regression on the cost surface
  4. Runs DBSCAN clustering on low-cost structures
  5. Identifies CI candidate geometries for Step 3 (Characterize)

Usage:
    python screen_ci_candidates.py --results_dir results_ethylene_sf_ci
"""

import os
import sys
import argparse
import numpy as np
from pathlib import Path

def parse_sf_ci_info(info_file):
    """Parse sf_ci_info.txt from a RANGE job directory."""
    data = {}
    with open(info_file) as f:
        for line in f:
            if '=' in line:
                key, val = line.split('=', 1)
                key = key.strip()
                val = val.strip()
                # Remove units
                if 'Ha' in val:
                    val = val.split('Ha')[0].strip()
                elif 'eV' in val:
                    val = val.split('eV')[0].strip()
                    # For gap line: "X.XX Ha = Y.YY eV"
                    if '=' in val:
                        val = val.split('=')[0].strip()
                try:
                    data[key] = float(val)
                except ValueError:
                    data[key] = val
    return data


def read_xyz(xyz_file):
    """Read XYZ file, return positions as flat array."""
    with open(xyz_file) as f:
        n = int(f.readline())
        f.readline()
        coords = []
        for _ in range(n):
            parts = f.readline().split()
            coords.extend([float(parts[1]), float(parts[2]), float(parts[3])])
    return np.array(coords)


def main():
    parser = argparse.ArgumentParser(description="Screen RANGE ensemble for CI candidates")
    parser.add_argument("--results_dir", default="results_ethylene_sf_ci",
                        help="RANGE output directory")
    parser.add_argument("--gap_threshold", type=float, default=0.5,
                        help="Gap threshold (eV) for CI candidates (default: 0.5)")
    parser.add_argument("--n_clusters_min", type=int, default=1,
                        help="Minimum expected CI clusters")
    args = parser.parse_args()

    results_dir = Path(args.results_dir)
    ha_to_ev = 27.2114

    # Collect data from all job directories
    print(f"Scanning {results_dir} for SF-TDDFT results...")
    records = []
    for job_dir in sorted(results_dir.rglob("*")):
        info_file = job_dir / "sf_ci_info.txt"
        start_xyz = job_dir / "start.xyz"
        if info_file.exists() and start_xyz.exists():
            data = parse_sf_ci_info(str(info_file))
            coords = read_xyz(str(start_xyz))
            if 'E_S0' in data and 'E_S1' in data and 'Gap' in data:
                records.append({
                    'dir': str(job_dir),
                    'coords': coords,
                    'e_s0': data['E_S0'],
                    'e_s1': data['E_S1'],
                    'gap': data['Gap'],
                    'gap_ev': data['Gap'] * ha_to_ev,
                    'cost': data.get('Cost_C', 1e10),
                })

    if not records:
        print("No SF-TDDFT results found. Run inbox_ethylene_sf_ci.py first.")
        return

    print(f"Found {len(records)} completed SF-TDDFT calculations")

    # Sort by gap
    records.sort(key=lambda r: abs(r['gap']))

    # Print summary table
    print(f"\n{'Rank':>5s}  {'Gap (eV)':>10s}  {'E_S0 (Ha)':>14s}  {'E_S1 (Ha)':>14s}  {'Cost (Ha)':>14s}  {'Dir'}")
    print("-" * 90)
    for i, r in enumerate(records[:20]):
        print(f"{i+1:5d}  {r['gap_ev']:10.4f}  {r['e_s0']:14.8f}  {r['e_s1']:14.8f}  {r['cost']:14.8f}  {os.path.basename(r['dir'])}")

    # Identify CI candidates (gap below threshold)
    candidates = [r for r in records if abs(r['gap_ev']) < args.gap_threshold]
    print(f"\n{len(candidates)} structures with gap < {args.gap_threshold} eV")

    if not candidates:
        print("No CI candidates found. Try:")
        print("  - Increasing gap_threshold")
        print("  - Running more RANGE iterations")
        print("  - Adjusting alpha parameter")
        return

    # DBSCAN clustering on CI candidates
    try:
        from sklearn.cluster import DBSCAN

        coords_matrix = np.array([r['coords'] for r in candidates])
        # RMSD-like distance: eps in Angstrom * sqrt(n_atoms)
        n_atoms = len(candidates[0]['coords']) // 3
        clustering = DBSCAN(eps=0.5 * np.sqrt(n_atoms), min_samples=2).fit(coords_matrix)
        labels = clustering.labels_
        n_clusters = len(set(labels) - {-1})
        print(f"\nDBSCAN found {n_clusters} CI cluster(s)")

        for cluster_id in range(n_clusters):
            members = [c for c, l in zip(candidates, labels) if l == cluster_id]
            best = min(members, key=lambda r: abs(r['gap']))
            print(f"\n  Cluster {cluster_id}: {len(members)} members")
            print(f"    Best gap: {best['gap_ev']:.4f} eV")
            print(f"    Best dir: {os.path.basename(best['dir'])}")
            print(f"    -> Use this geometry for RUNTYP=CONICAL")

        # Outliers
        outliers = [c for c, l in zip(candidates, labels) if l == -1]
        if outliers:
            print(f"\n  {len(outliers)} unclustered CI candidates (outliers)")

    except ImportError:
        print("\nscikit-learn not available. Skipping DBSCAN clustering.")
        print("Install with: pip install scikit-learn --user")
        print("\nBest CI candidate (lowest gap):")
        best = candidates[0]
        print(f"  Gap: {best['gap_ev']:.4f} eV")
        print(f"  Dir: {best['dir']}")

    # GPR interpolation
    try:
        from sklearn.gaussian_process import GaussianProcessRegressor
        from sklearn.gaussian_process.kernels import RBF, ConstantKernel

        print("\nTraining GPR on cost function surface...")
        X = np.array([r['coords'] for r in records])
        y = np.array([r['cost'] for r in records])

        # Normalize
        X_mean = X.mean(axis=0)
        X_std = X.std(axis=0) + 1e-10
        X_norm = (X - X_mean) / X_std

        kernel = ConstantKernel(1.0) * RBF(length_scale=1.0)
        gpr = GaussianProcessRegressor(kernel=kernel, n_restarts_optimizer=5, alpha=1e-6)
        gpr.fit(X_norm, y)
        print(f"  GPR R² score: {gpr.score(X_norm, y):.4f}")
        print(f"  GPR kernel: {gpr.kernel_}")

        # Predict at candidate locations to validate
        y_pred, y_std = gpr.predict(X_norm[:len(candidates)], return_std=True)
        print(f"  Prediction uncertainty at CI candidates: {np.mean(y_std):.6f} Ha")

        # ============================================================
        # GPR-based discovery: find new CI candidates without GAMESS
        # ============================================================
        print("\n--- GPR-based CI candidate discovery ---")

        # 1. Dense random sampling of the search space
        n_grid = 100000
        X_min = X.min(axis=0)
        X_max = X.max(axis=0)
        rng = np.random.default_rng(42)
        X_grid = rng.uniform(X_min, X_max, size=(n_grid, X.shape[1]))
        X_grid_norm = (X_grid - X_mean) / X_std

        y_grid, y_grid_std = gpr.predict(X_grid_norm, return_std=True)

        # 2. Find predicted low-cost points (CI candidates)
        best_idx = np.argsort(y_grid)[:20]
        print(f"\n  Top GPR-predicted CI candidates (from {n_grid} random points):")
        print(f"  {'Rank':>4}  {'Pred Cost (Ha)':>14}  {'Uncertainty':>11}  {'Nearest RANGE (A)':>17}")
        for rank, idx in enumerate(best_idx):
            # Distance to nearest RANGE-sampled point
            dists = np.linalg.norm(X - X_grid[idx], axis=1)
            nearest_dist = dists.min()
            nearest_idx = dists.argmin()
            print(f"  {rank+1:4d}  {y_grid[idx]:14.10f}  {y_grid_std[idx]:11.6f}  {nearest_dist:17.4f}")

        # Save top GPR-predicted candidates
        for i, idx in enumerate(best_idx[:5]):
            natoms = X_grid.shape[1] // 3
            coords = X_grid[idx].reshape(natoms, 3)
            out_xyz = f"gpr_candidate_{i:02d}.xyz"
            with open(out_xyz, 'w') as fg:
                fg.write(f"{natoms}\n")
                fg.write(f"GPR predicted cost={y_grid[idx]:.10f} uncertainty={y_grid_std[idx]:.6f}\n")
                # Use element list from first record
                elems = records[0].get('elements', ['X'] * natoms)
                for j in range(natoms):
                    fg.write(f"{elems[j]}  {coords[j,0]:.10f}  {coords[j,1]:.10f}  {coords[j,2]:.10f}\n")
        print(f"\n  Saved gpr_candidate_00.xyz ... gpr_candidate_04.xyz")

        # 3. High-uncertainty regions (adaptive sampling targets)
        high_unc_idx = np.argsort(y_grid_std)[-20:][::-1]
        low_cost_high_unc = [i for i in range(n_grid)
                             if y_grid[i] < np.percentile(y_grid, 10) and y_grid_std[i] > np.median(y_grid_std)]
        print(f"\n  Adaptive sampling: {len(low_cost_high_unc)} points with low predicted cost + high uncertainty")
        if len(low_cost_high_unc) > 0:
            best_explore = sorted(low_cost_high_unc, key=lambda i: y_grid[i])[:5]
            for i, idx in enumerate(best_explore):
                natoms = X_grid.shape[1] // 3
                coords = X_grid[idx].reshape(natoms, 3)
                out_xyz = f"gpr_explore_{i:02d}.xyz"
                with open(out_xyz, 'w') as fg:
                    fg.write(f"{natoms}\n")
                    fg.write(f"GPR explore: cost={y_grid[idx]:.10f} unc={y_grid_std[idx]:.6f}\n")
                    elems = records[0].get('elements', ['X'] * natoms)
                    for j in range(natoms):
                        fg.write(f"{elems[j]}  {coords[j,0]:.10f}  {coords[j,1]:.10f}  {coords[j,2]:.10f}\n")
            print(f"  Saved gpr_explore_00.xyz ... gpr_explore_{min(4, len(best_explore)-1):02d}.xyz")
            print(f"  -> Run GAMESS on these to improve GPR in uncertain regions")

        # 4. CI seam mapping
        gap_threshold = 0.01 / 27.2114  # 10 meV in Ha
        # For seam mapping, we need gap predictions, not cost
        # Approximate: points where cost is very low relative to minimum
        cost_threshold = np.percentile(y_grid, 1)  # Bottom 1%
        seam_points = X_grid[y_grid < cost_threshold]
        print(f"\n  CI seam mapping: {len(seam_points)} points in bottom 1% of predicted cost")

        # 5. Minimum energy path from S0 min to CI
        # Linear interpolation between highest-gap and lowest-gap sampled structures
        gaps = np.array([r['gap'] for r in records])
        s0_min_idx = np.argmax(gaps)  # Largest gap ~ S0 minimum
        ci_idx = np.argmin(gaps)      # Smallest gap ~ CI
        n_path = 50
        path_coords = np.array([X[s0_min_idx] + t * (X[ci_idx] - X[s0_min_idx])
                                for t in np.linspace(0, 1, n_path)])
        path_norm = (path_coords - X_mean) / X_std
        path_cost, path_std = gpr.predict(path_norm, return_std=True)
        print(f"\n  Minimum energy path (S0 min -> CI, {n_path} points):")
        print(f"  {'Point':>5}  {'Cost (Ha)':>12}  {'Unc (Ha)':>10}")
        for i in range(0, n_path, 10):
            print(f"  {i:5d}  {path_cost[i]:12.6f}  {path_std[i]:10.6f}")
        print(f"  Cost at S0 min: {path_cost[0]:.6f}")
        print(f"  Cost at CI:     {path_cost[-1]:.6f}")
        print(f"  Max cost along path: {path_cost.max():.6f} (barrier estimate)")
        if path_cost.max() > path_cost[0] + 0.001:
            print(f"  -> Possible barrier of {(path_cost.max() - path_cost[0])*27.2114:.3f} eV")
        else:
            print(f"  -> Barrierless path from S0 min to CI")

    except ImportError:
        print("\nscikit-learn not available. Skipping GPR interpolation.")

    # Save candidate XYZ files for CONICAL runs
    print("\nSaving CI candidate geometries...")
    for i, r in enumerate(candidates[:5]):  # Top 5 candidates
        out_xyz = f"ci_candidate_{i:02d}.xyz"
        src = os.path.join(r['dir'], 'start.xyz')
        if os.path.exists(src):
            import shutil
            shutil.copy(src, out_xyz)
            print(f"  {out_xyz}: gap = {r['gap_ev']:.4f} eV")

    print("\nDone. Next step: run GAMESS RUNTYP=CONICAL on ci_candidate_*.xyz")


if __name__ == "__main__":
    main()
