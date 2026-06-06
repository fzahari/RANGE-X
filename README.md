# RANGE-X

**RANGE-X** extends **RANGE** (Robust Adaptive Nature-inspired Global Explorer) with a
**GAMESS spin-flip TDDFT** evaluator for fully *gradient-free* mapping of excited-state
landscapes — ground- and excited-state minima, transition states, and conical
intersections — with no initial guess.

It is the implementation used in:

> F. Zahariev and V.-A. Glezakou, *Gradient-free framework for the discovery of conical
> intersections and photochemical reaction pathways*, Phys. Chem. Chem. Phys. (2026).

## What RANGE-X adds on top of RANGE

- `RANGE_go/energy_calculation.py` — a `GAMESS_SF_CI` evaluator that, for each trial
  geometry, writes a spin-flip TDDFT input, runs GAMESS, parses E(S₀)/E(S₁), and returns
  one of three objectives:
  - `e_s0  = E₀`                              → ground-state minima
  - `e_s1  = E₁`                              → excited-state minima
  - `somaki = ½(E₀+E₁) + (E₁−E₀)³/α`          → conical-intersection funnels
- `examples/GAMESS_calc/` — per-system templates (`input_gamess_<sys>_sf_tddft_template`),
  drivers (`inbox_<sys>_sf_ci.py`), and the orchestration script `agent_ci_pipeline.py`
  (RANGE search → GPR + DBSCAN → optional CONICAL refinement → NEB validation).

## Installation

```bash
git clone https://github.com/fzahari/RANGE-X.git
cd RANGE-X
pip install . --user
```

Requires a working GAMESS (`rungms` / `rungms-dev`) for the SF-TDDFT evaluator.

## Quick start

Run one objective per job (see `examples/GAMESS_calc/`):

```bash
python3 inbox_cu3_sf_ci.py somaki      # e_s0 | e_s1 | somaki
```

Results are written to `results_<sys>_<obj>/*/sf_ci_info.txt`
(geometry, E_S0, E_S1, gap, cost).

## Attribution & license

RANGE-X is a derivative of RANGE (https://github.com/RANGE-kit/RANGE) and is distributed
under the **same license as upstream RANGE** — see `LICENSE`. Please cite the paper above
and the original RANGE project.
