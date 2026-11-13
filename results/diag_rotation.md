#### D1: AUC@30 deficit vs B1 per sequence

| sequence | N | B1 | AVGGT | AVEK | f16n3 | early grid only | late compr. only |
|---|---|---|---|---|---|---|---|
| fr1_360 | 100 | 62.5 | -7.1 | -5.7 | -4.3 | -2.2 | -5.3 |
| fr1_360 | 200 | 59.7 | -6.2 | -3.9 | -1.6 | -2.6 | -3.4 |
| fr1_plant | 100 | 94.3 | -2.5 | -1.8 | -0.6 | -0.3 | -1.6 |
| fr1_plant | 200 | 94.0 | -2.8 | -2.3 | -0.9 | -0.3 | -2.0 |
| fr1_room | 100 | 83.5 | -9.3 | -2.4 | -2.4 | -1.0 | -1.9 |
| fr1_room | 200 | 82.1 | -6.4 | -0.2 | +0.7 | -0.8 | +0.6 |
| fr1_rpy | 100 | 45.9 | -2.4 | -2.6 | -1.8 | -0.8 | -2.4 |
| fr1_rpy | 200 | 44.3 | -2.6 | -1.8 | -2.3 | -0.3 | -2.0 |
| fr1_teddy | 100 | 94.4 | -1.8 | -1.7 | -1.1 | -0.3 | -1.6 |
| fr1_teddy | 200 | 94.4 | -1.6 | -1.1 | -0.7 | -0.3 | -1.0 |
| fr2_360_hemisphere | 100 | 58.7 | -9.9 | -8.0 | -4.2 | -1.3 | -7.3 |
| fr2_360_hemisphere | 200 | 58.1 | -7.4 | -6.2 | -5.3 | -2.8 | -4.8 |

#### D2: mean per-pair deficit vs B1 by GT rotation between the two frames (AUC points)

| config | 0–30° (share of pairs) | 30–90° (share of pairs) | 90–180° (share of pairs) |
|---|---|---|---|
| AVGGT | +3.1 (15%) | +4.2 (42%) | +7.0 (43%) |
| AVEK | +1.9 (15%) | +2.3 (42%) | +4.7 (43%) |
| f16n3 | +1.4 (15%) | +1.5 (42%) | +2.9 (43%) |
| early grid only | +0.8 (15%) | +1.1 (42%) | +1.0 (43%) |
| late compr. only | +1.5 (15%) | +1.9 (42%) | +4.1 (43%) |

#### D3: share of the deficit in pairs touching the worst 10% frames (those pairs are ~19% of all)

- AVGGT: 64% of the deficit (pairs touching them: 19%; same selection on shuffled deficits: 28%), over 12 cells
- AVEK: 59% of the deficit (pairs touching them: 19%; same selection on shuffled deficits: 28%), over 11 cells
- f16n3: 75% of the deficit (pairs touching them: 19%; same selection on shuffled deficits: 32%), over 8 cells
- early grid only: 60% of the deficit (pairs touching them: 19%; same selection on shuffled deficits: 29%), over 4 cells
- late compr. only: 66% of the deficit (pairs touching them: 19%; same selection on shuffled deficits: 30%), over 10 cells

#### D3b: Spearman correlation of the per-frame deficit with (a) B1's per-frame score, (b) GT rotation to the previous sampled frame

- AVGGT: (a) +0.09  (b) -0.01  (D4: rotation to nearest keyframe) +0.10  (mean over 12 cells)
- AVEK: (a) +0.11  (b) +0.02  (D4: rotation to nearest keyframe) +0.08  (mean over 12 cells)
- f16n3: (a) +0.04  (b) +0.05  (D4: rotation to nearest keyframe) +0.09  (mean over 12 cells)
- early grid only: (a) -0.14  (b) -0.01  (D4: rotation to nearest keyframe) +0.02  (mean over 12 cells)
- late compr. only: (a) +0.12  (b) +0.02  (D4: rotation to nearest keyframe) +0.07  (mean over 12 cells)

#### Oracle experiment (O1, O2): cells where AVEK loses >= 1 point vs B1

| sequence | N | B1 | AVEK | AVEK-rand | AVEK-oracle | recovered |
|---|---|---|---|---|---|---|
| fr1_360 | 100 | 62.5 | 56.7 | 58.8 | 58.0 | 23% |
| fr1_360 | 200 | 59.7 | 55.7 | 56.2 | 57.1 | 34% |
| fr1_plant | 100 | 94.3 | 92.5 | 92.9 | 93.0 | 29% |
| fr1_plant | 200 | 94.0 | 91.8 | 92.4 | 92.2 | 20% |
| fr1_room | 100 | 83.5 | 81.0 | 82.5 | 82.3 | 53% |
| fr1_room (excluded) | 200 | 82.1 | 81.9 | 82.0 | 81.7 | – |
| fr1_rpy | 100 | 45.9 | 43.4 | 44.4 | 44.4 | 39% |
| fr1_rpy | 200 | 44.3 | 42.6 | 43.1 | 43.9 | 72% |
| fr1_teddy | 100 | 94.4 | 92.7 | 93.3 | 93.2 | 32% |
| fr1_teddy | 200 | 94.4 | 93.3 | 93.4 | 93.7 | 33% |
| fr2_360_hemisphere | 100 | 58.7 | 50.8 | 52.8 | 51.7 | 11% |
| fr2_360_hemisphere | 200 | 58.1 | 51.9 | 54.7 | 54.1 | 35% |

O1: mean recovered 35% over 11 cells (needs >= 50%) -> False
O2: mean oracle - rand -0.09 (needs >= +1.0) -> False

check vs kernel AUC: 72/72 agree
