# r2SCAN+NN vs r2SCAN on GSCDB137

- run created: 2026-10-27 22:00:01
- basis: `def2-tzvpp`, mode: `scf`, dispersion: `d3bj`, grid level: 4
- selection: preset `applied`, 891 reactions, 1645 molecules

- scored: **891 reactions** across **43 datasets**

Reference values are GSCDB137's gold-standard data. All energies use the same geometry, basis, grid and dispersion correction for both methods, so every difference below comes from the functional.

## Overall

Mean per-set MAE averages the 43 sets measured in kcal/mol; the relative metric covers all 43.

| Method | mean per-set MAE (kcal/mol) | mean relative metric | sets improved |
|---|---|---|---|
| r2SCAN | 2.065 | 3.11 | - |
| r2SCAN+NN(pointwise[d3r2scan_phase5] w=0.17861 ep47) | 2.037 | 3.03 | 23/43 |

"Relative metric" is each set's error divided by the reference uncertainty of that set (GSCDB's own normalisation), which is what makes a 0.3 kcal/mol noncovalent error comparable to a 3 kcal/mol barrier-height error. Lower is better; below ~1 means the functional is as accurate as the reference data.

## By property type

Mean over the sets of each type (kcal/mol sets only). The 95% CI on dMAE resamples reactions within each set; an interval that contains 0 means no measurable effect.

| Datatype | Sets | Points | MAE[r2SCAN] | MAE[r2SCAN+NN(pointwise[d3r2scan_phase5] w=0.17861 ep47)] | dMAE[r2SCAN+NN(pointwise[d3r2scan_phase5] w=0.17861 ep47)] (95% CI) |
|---|---|---|---|---|---|
| Barrier Height | 8 | 141 | 5.485 | 5.480 | -0.005 [-0.045, +0.032] |
| Intramolecular Noncovalent | 7 | 152 | 0.382 | 0.378 | -0.005 [-0.009, -0.001] |
| Isomerization | 8 | 167 | 1.648 | 1.653 | +0.005 [-0.021, +0.031] |
| Noncovalent | 10 | 212 | 0.566 | 0.526 | -0.040 [-0.050, -0.031] |
| Thermochemistry | 10 | 219 | 2.341 | 2.262 | -0.079 [-0.318, +0.160] |
| **all** | 43 | 891 | 2.065 | 2.037 | -0.029 [-0.088, +0.032] |

## Without reactions made of training molecules

30 scored reactions consist only of molecules that are also training components (same elements, charge and geometry within 0.1 A; gscdb_overlap.py). Their energies were fitted directly, so they are left out here.

| Datatype | Sets | Points | MAE[r2SCAN] | MAE[r2SCAN+NN(pointwise[d3r2scan_phase5] w=0.17861 ep47)] | dMAE[r2SCAN+NN(pointwise[d3r2scan_phase5] w=0.17861 ep47)] (95% CI) |
|---|---|---|---|---|---|
| Barrier Height | 8 | 140 | 5.479 | 5.472 | -0.007 [-0.045, +0.030] |
| Intramolecular Noncovalent | 7 | 152 | 0.382 | 0.378 | -0.005 [-0.009, -0.001] |
| Isomerization | 8 | 162 | 1.646 | 1.649 | +0.004 [-0.023, +0.030] |
| Noncovalent | 10 | 204 | 0.556 | 0.514 | -0.042 [-0.052, -0.031] |
| Thermochemistry | 10 | 203 | 2.327 | 2.426 | +0.099 [-0.188, +0.376] |
| **all** | 43 | 861 | 2.058 | 2.070 | +0.012 [-0.057, +0.078] |

Left out: AlkIsod14_1, AlkIsod14_2, AlkIsod14_7, AlkIsomer11_1, BDE99_10, BDE99_11, BDE99_15, BDE99_26, BDE99_31, BDE99_37, BDE99_51, BDE99_60, BDE99_71, BDE99_75, BDE99_78, BDE99_85, BDE99_86, BH28_BHPERI_6, DS14_10, HB49_39, ISO34_1, ISO34_25, ISO34_26, ISO34_3, S22_2, S22_20, S22_3, S22_4, S22_9, S66_1

## r2SCAN+NN(pointwise[d3r2scan_phase5] w=0.17861 ep47): per-set verdict

| Dataset | Type | N | Unit | MAE r2SCAN | MAE NN | dMAE | % | win rate | p | 95% CI on dMAE | bias r2SCAN | bias NN |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| RC21 | TC | 21 | kcal/mol | 5.193 | 3.325 | -1.867 | +36% | 0.81 | 0.001 | [-2.744, -0.932] | +4.727 | +1.932 |
| RSE43 | TC | 30 | kcal/mol | 1.567 | 0.640 | -0.927 | +59% | 0.90 | 0.000 | [-1.284, -0.628] | -1.567 | -0.283 |
| BHPERI11 | BH | 11 | kcal/mol | 5.107 | 4.723 | -0.384 | +8% | 0.91 | 0.002 | [-0.455, -0.284] | -5.107 | -4.723 |
| YBDE18 | TC | 18 | kcal/mol | 3.325 | 2.949 | -0.376 | +11% | 0.44 | 0.799 | [-1.307, +0.565] | -2.830 | -1.211 |
| BSR36 | TC | 30 | kcal/mol | 0.384 | 0.202 | -0.182 | +47% | 0.67 | 0.016 | [-0.334, -0.045] | -0.374 | +0.095 |
| Styrene42 | ISO | 30 | kcal/mol | 2.964 | 2.803 | -0.161 | +5% | 0.77 | 0.000 | [-0.236, -0.090] | +2.635 | +2.438 |
| BH28 | BH | 28 | kcal/mol | 5.492 | 5.339 | -0.152 | +3% | 0.61 | 0.036 | [-0.271, -0.031] | -5.151 | -5.013 |
| FH51 | TC | 30 | kcal/mol | 2.142 | 2.024 | -0.118 | +5% | 0.73 | 0.100 | [-0.256, +0.029] | -0.213 | -0.295 |
| PNICO23 | NC | 23 | kcal/mol | 1.074 | 0.982 | -0.092 | +9% | 0.91 | 0.000 | [-0.114, -0.068] | +1.065 | +0.957 |
| S22 | NC | 22 | kcal/mol | 0.445 | 0.354 | -0.091 | +20% | 0.82 | 0.000 | [-0.128, -0.054] | +0.440 | +0.315 |
| AlkIsod14 | TC | 14 | kcal/mol | 0.629 | 0.542 | -0.088 | +14% | 1.00 | 0.000 | [-0.107, -0.068] | -0.629 | -0.542 |
| HB49 | NC | 30 | kcal/mol | 1.229 | 1.156 | -0.073 | +6% | 0.90 | 0.000 | [-0.096, -0.048] | -1.192 | -1.098 |
| S66 | NC | 30 | kcal/mol | 0.357 | 0.286 | -0.071 | +20% | 0.77 | 0.002 | [-0.105, -0.038] | -0.319 | -0.201 |
| DS14 | NC | 14 | kcal/mol | 0.430 | 0.374 | -0.056 | +13% | 0.86 | 0.013 | [-0.082, -0.022] | -0.427 | -0.349 |
| HSG | NC | 21 | kcal/mol | 0.439 | 0.404 | -0.035 | +8% | 0.67 | 0.076 | [-0.068, -0.001] | -0.364 | -0.273 |
| BUT14DIOL | INC | 30 | kcal/mol | 0.406 | 0.373 | -0.033 | +8% | 0.93 | 0.000 | [-0.038, -0.026] | +0.377 | +0.341 |
| X40 | NC | 30 | kcal/mol | 0.443 | 0.410 | -0.033 | +7% | 0.73 | 0.124 | [-0.067, +0.004] | -0.387 | -0.291 |
| CARBHB8 | NC | 8 | kcal/mol | 0.954 | 0.923 | -0.032 | +3% | 0.88 | 0.148 | [-0.054, -0.003] | +0.954 | +0.923 |
| AlkIsomer11 | ISO | 11 | kcal/mol | 0.358 | 0.327 | -0.031 | +9% | 1.00 | 0.001 | [-0.049, -0.018] | +0.358 | +0.327 |
| NBC10 | NC | 30 | kcal/mol | 0.144 | 0.119 | -0.024 | +17% | 0.73 | 0.038 | [-0.065, +0.019] | -0.078 | +0.011 |
| Pentane13 | INC | 13 | kcal/mol | 0.245 | 0.239 | -0.006 | +2% | 0.77 | 0.191 | [-0.013, +0.001] | +0.245 | +0.239 |
| SCONF | INC | 17 | kcal/mol | 0.765 | 0.760 | -0.005 | +1% | 0.53 | 0.579 | [-0.019, +0.007] | +0.391 | +0.403 |
| MCONF | INC | 30 | kcal/mol | 0.618 | 0.614 | -0.004 | +1% | 0.53 | 0.887 | [-0.021, +0.014] | +0.560 | +0.540 |
| ACONF | INC | 15 | kcal/mol | 0.139 | 0.142 | +0.003 | -2% | 0.53 | 0.330 | [-0.000, +0.006] | +0.139 | +0.142 |
| Amino20x4 | INC | 30 | kcal/mol | 0.202 | 0.206 | +0.004 | -2% | 0.40 | 0.221 | [-0.009, +0.017] | +0.182 | +0.178 |
| ICONF | INC | 17 | kcal/mol | 0.301 | 0.310 | +0.009 | -3% | 0.35 | 0.035 | [+0.002, +0.015] | +0.186 | +0.193 |
| ISO34 | ISO | 30 | kcal/mol | 1.349 | 1.357 | +0.009 | -1% | 0.53 | 0.670 | [-0.087, +0.095] | -0.080 | +0.046 |
| BHDIV7 | BH | 7 | kcal/mol | 5.924 | 5.944 | +0.020 | -0% | 0.29 | 0.688 | [-0.220, +0.246] | -5.924 | -5.944 |
| EIE22 | ISO | 22 | kcal/mol | 2.017 | 2.038 | +0.021 | -1% | 0.32 | 0.092 | [-0.002, +0.043] | +1.990 | +2.008 |
| BHROT27 | BH | 27 | kcal/mol | 0.793 | 0.820 | +0.027 | -3% | 0.48 | 0.036 | [+0.012, +0.044] | +0.776 | +0.802 |
| NBPRC | TC | 12 | kcal/mol | 1.781 | 1.815 | +0.035 | -2% | 0.50 | 1.000 | [-0.084, +0.170] | -0.906 | -0.843 |
| PX9 | BH | 9 | kcal/mol | 9.644 | 9.680 | +0.035 | -0% | 0.33 | 0.652 | [-0.048, +0.124] | -9.644 | -9.680 |
| TAUT15 | ISO | 15 | kcal/mol | 1.613 | 1.653 | +0.039 | -2% | 0.67 | 1.000 | [-0.018, +0.107] | +0.433 | +0.466 |
| WCPT26 | BH | 26 | kcal/mol | 8.816 | 8.858 | +0.042 | -0% | 0.42 | 0.303 | [-0.024, +0.106] | -8.816 | -8.858 |
| DIE60 | ISO | 30 | kcal/mol | 1.892 | 1.935 | +0.043 | -2% | 0.30 | 0.002 | [+0.021, +0.066] | +1.892 | +1.935 |
| PArel | ISO | 20 | kcal/mol | 1.544 | 1.597 | +0.053 | -3% | 0.30 | 0.001 | [+0.022, +0.090] | +0.681 | +0.710 |
| ISOL23 | ISO | 9 | kcal/mol | 1.447 | 1.511 | +0.065 | -4% | 0.44 | 0.359 | [-0.086, +0.215] | -1.027 | -1.064 |
| INV23 | BH | 19 | kcal/mol | 1.250 | 1.350 | +0.100 | -8% | 0.26 | 0.005 | [+0.039, +0.169] | -0.705 | -0.793 |
| ADIM6 | NC | 4 | kcal/mol | 0.147 | 0.250 | +0.103 | -70% | 0.00 | n/a | [+0.075, +0.130] | -0.147 | -0.250 |
| DARC | TC | 14 | kcal/mol | 2.547 | 2.751 | +0.204 | -8% | 0.29 | 0.358 | [-0.087, +0.429] | +1.358 | +1.875 |
| CRBH14 | BH | 14 | kcal/mol | 6.852 | 7.123 | +0.271 | -4% | 0.00 | 0.000 | [+0.240, +0.302] | -6.852 | -7.123 |
| CR20 | TC | 20 | kcal/mol | 0.857 | 1.536 | +0.678 | -79% | 0.15 | 0.001 | [+0.395, +0.900] | -0.493 | -1.492 |
| BDE99nonMR | TC | 30 | kcal/mol | 4.986 | 6.834 | +1.848 | -37% | 0.40 | 0.124 | [-0.305, +3.836] | +1.392 | -6.025 |

**Summary for r2SCAN+NN(pointwise[d3r2scan_phase5] w=0.17861 ep47):** improved 23 of 43 sets (15 significantly at p<0.05), degraded 20 (7 significantly).

Best (significant) gains:

- **RC21** (Thermochemistry): 5.19 -> 3.33 kcal/mol (+36%, win rate 0.81, n=21) -- Fragmentations and rearrangements in organic radical cations
- **RSE43** (Thermochemistry): 1.57 -> 0.64 kcal/mol (+59%, win rate 0.90, n=30) -- Radical stabilization energies
- **BHPERI11** (Barrier Height): 5.11 -> 4.72 kcal/mol (+8%, win rate 0.91, n=11) -- Barrier heights of pericyclic reactions
- **BSR36** (Thermochemistry): 0.38 -> 0.20 kcal/mol (+47%, win rate 0.67, n=30) -- Hydrocarbon bond separation reaction energies
- **Styrene42** (Isomerization): 2.96 -> 2.80 kcal/mol (+5%, win rate 0.77, n=30) -- Isomerization energies of C8H8

Worst (significant) regressions:

- **CR20** (Thermochemistry): 0.86 -> 1.54 kcal/mol (-79%, win rate 0.15, n=20) -- Cycloreversion reaction energies
- **CRBH14** (Barrier Height): 6.85 -> 7.12 kcal/mol (-4%, win rate 0.00, n=14) -- Barrier heights for cycloreversion of heterocyclic rings
- **INV23** (Barrier Height): 1.25 -> 1.35 kcal/mol (-8%, win rate 0.26, n=19) -- Inversion/Racemization barrier heights
- **PArel** (Isomerization): 1.54 -> 1.60 kcal/mol (-3%, win rate 0.30, n=20) -- Isomerization energies of protonated isomers
- **DIE60** (Isomerization): 1.89 -> 1.94 kcal/mol (-2%, win rate 0.30, n=30) -- Isomerization energies for double-bond migration in conjugated dienes

## Numerical health

- molecules computed: 1645
- molecules that failed setup: 0
- molecules with at least one non-converged SCF: 0

A non-converged molecule poisons every reaction it appears in, so those reactions are dropped rather than scored. If the count is large for one method only, the comparison is biased -- rerun those molecules with a tighter/looser SCF before quoting numbers.
