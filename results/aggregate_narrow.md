#### Step 1: selection on development data (6 TUM sequences x N=100, 200)

| config | gain vs AVEK (cells) | time N=200 (s) | cost vs AVEK (s) |
|---|---|---|---|
| AVEKB-s4e36k10f14 | +1.15 (12) | 230 | +55 |
| AVEKB-f15n3 | +0.48 (12) | 199 | +24 |
| AVEKB-f14n3 | +0.36 (12) | 200 | +25 |
| AVEKB-f16n3 | +1.01 (12) | 199 | +24 |
| AVEKB-g12 | +0.68 (12) | 184 | +9 |

threshold 0.7 x gain(AVEKB) = 0.80; V* = AVEKB-f16n3

#### Step 2: unseen 7-Scenes


N = 100

| sequence | B1 | AV-s4 | AVEK-s4e36k10 | AVEKB-s4e36k10f14 | AVEKB-f15n3 | AVEKB-f14n3 | AVEKB-f16n3 | AVEKB-g12 |
|---|---|---|---|---|---|---|---|---|
| chess/seq-06 | 92.6 | 92.6 | 92.9 | 93.0 | 93.0 | 92.8 | 93.1 | 93.0 |
| office/seq-03 | 72.2 | 72.4 | 71.6 | 72.7 | 72.3 | 71.5 | 72.7 | 72.0 |
| office/seq-04 | 68.7 | 63.9 | 68.2 | 68.2 | 66.9 | 67.3 | 68.8 | 67.7 |
| pumpkin/seq-08 | 78.9 | 78.6 | 78.3 | 79.3 | 78.4 | 78.5 | 79.1 | 78.9 |
| redkitchen/seq-01 | 81.3 | 81.5 | 81.4 | 81.4 | 81.1 | 81.1 | 81.5 | 81.4 |
| redkitchen/seq-02 | 76.7 | 77.0 | 77.0 | 77.4 | 77.1 | 76.9 | 77.4 | 77.1 |
| stairs/seq-06 | 83.2 | 81.6 | 82.8 | 83.8 | 83.3 | 83.3 | 83.0 | 83.3 |
| **mean** | **79.1** | **78.2** | **78.9** | **79.4** | **78.9** | **78.8** | **79.4** | **79.1** |
| time (s) | 128 | 49 | 58 | 71 | 66 | 66 | 65 | 62 |

N = 200

| sequence | B1 | AV-s4 | AVEK-s4e36k10 | AVEKB-s4e36k10f14 | AVEKB-f15n3 | AVEKB-f14n3 | AVEKB-f16n3 | AVEKB-g12 |
|---|---|---|---|---|---|---|---|---|
| chess/seq-06 | 92.4 | 92.6 | 92.7 | 92.8 | 92.8 | 92.7 | 92.9 | 92.9 |
| office/seq-03 | 70.7 | 71.8 | 72.2 | 72.6 | 72.1 | 71.8 | 72.8 | 72.0 |
| office/seq-04 | 64.9 | 60.1 | 65.1 | 64.8 | 64.1 | 63.5 | 66.6 | 63.9 |
| pumpkin/seq-08 | 78.7 | 78.4 | 78.3 | 79.2 | 78.2 | 78.4 | 79.2 | 78.8 |
| redkitchen/seq-01 | 81.0 | 81.5 | 81.4 | 81.3 | 81.1 | 81.0 | 81.4 | 81.3 |
| redkitchen/seq-02 | 76.6 | 77.0 | 76.9 | 77.1 | 76.9 | 76.6 | 77.3 | 76.9 |
| stairs/seq-06 | 82.8 | 81.2 | 82.3 | 83.1 | 82.7 | 82.6 | 82.9 | 82.7 |
| **mean** | **78.2** | **77.5** | **78.4** | **78.7** | **78.3** | **78.1** | **79.0** | **78.4** |
| time (s) | 472 | 126 | 164 | 222 | 199 | 198 | 199 | 183 |

#### Pre-registered checks

H34 N=100: AVEKB - AVEK-s4e36k10 mean +0.53 (wins 6/7, p=0.047), needs >= +0.0
H34 N=200: AVEKB - AVEK-s4e36k10 mean +0.27 (wins 5/7, p=0.297), needs >= +0.0
H35 N=100: AVEKB - AV-s4 mean +1.16 (wins 6/7, p=0.031), needs >= +0.5
H35 N=200: AVEKB - AV-s4 mean +1.18 (wins 6/7, p=0.047), needs >= +0.5
H36: gain(AVEKB-f16n3) +0.55 vs gain(AVEKB) +0.40 -> 137%; speed-up vs B1 at N=200 2.38x
H37: pooled N=200, 13 sequences, AVEKB - AVEK mean +0.49, wins 10/13, one-sided Wilcoxon p=0.0402
7-Scenes N=200 speed-up vs B1: AV-s4 3.75x
7-Scenes N=200 speed-up vs B1: AVEK-s4e36k10 2.88x
7-Scenes N=200 speed-up vs B1: AVEKB-s4e36k10f14 2.12x
7-Scenes N=200 speed-up vs B1: AVEKB-f15n3 2.37x
7-Scenes N=200 speed-up vs B1: AVEKB-f14n3 2.38x
7-Scenes N=200 speed-up vs B1: AVEKB-f16n3 2.38x
7-Scenes N=200 speed-up vs B1: AVEKB-g12 2.57x

#### Extra: 4 new TUM sequences


N = 100

| sequence | B1 | AV-s4 | AVEK-s4e36k10 | AVEKB-s4e36k10f14 | AVEKB-f16n3 |
|---|---|---|---|---|---|
| fr1_desk2/seq-01 | 89.9 | 89.4 | 89.3 | 89.5 | 89.7 |
| fr1_floor/seq-01 | 67.8 | 68.2 | 64.7 | 69.6 | 67.7 |
| fr1_xyz/seq-01 | 90.0 | 88.5 | 89.1 | 89.7 | 89.7 |
| fr3_cabinet/seq-01 | 93.6 | 93.8 | 94.2 | 94.9 | 94.7 |
| **mean** | **85.3** | **85.0** | **84.3** | **85.9** | **85.5** |
| time (s) | 133 | 51 | 60 | 74 | 69 |

N = 200

| sequence | B1 | AV-s4 | AVEK-s4e36k10 | AVEKB-s4e36k10f14 | AVEKB-f16n3 |
|---|---|---|---|---|---|
| fr1_desk2/seq-01 | 90.0 | 89.1 | 89.3 | 89.8 | 89.9 |
| fr1_floor/seq-01 | 68.9 | 66.3 | 65.4 | 67.5 | 67.4 |
| fr1_xyz/seq-01 | 89.4 | 88.8 | 89.5 | 89.1 | 89.4 |
| fr3_cabinet/seq-01 | 91.9 | 92.7 | 92.0 | 93.1 | 92.9 |
| **mean** | **85.1** | **84.2** | **84.0** | **84.9** | **84.9** |
| time (s) | 514 | 132 | 171 | 236 | 209 |

H38a: AVEKB - AVEK +1.21 over 8 cells, needs >= +0.50
H38b: gain(AVEKB-f16n3) +1.01 vs gain(AVEKB) +1.21 -> 83%
speed-up vs B1 at N=200: AVEKB 2.18x, AVEKB-f16n3 2.45x
H39 AVEKB, 17 unseen: N=200 mean +0.57, wins 13/17, one-sided p=0.0133
H39 AVEKB-f16n3, 11 sequences not used to select it (7-Scenes + 4 TUM): N=200 mean +0.69, wins 10/11, one-sided p=0.0015
    (AVEKB-f16n3 on all 17 incl. its 6 selection sequences, biased: mean +0.68, p=0.0003)

summary: {'H34': True, 'H35': True, 'H36': True, 'H37': True, 'H38a': True, 'H38b': True, 'H39': True}
