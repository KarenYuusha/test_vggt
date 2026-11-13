#### Step 1: development data (6 rotation-heavy TUM sequences x N=100, 200)

N = 100

| sequence | B1 | AVEK-s4e36k10 | AVEKB-f16n3 | AVEK-rand | AVEKU-u10 | AVU-u5 | AVEKBU-f16u10 |
|---|---|---|---|---|---|---|---|
| fr1_360/seq-01 | 62.5 | 56.7 | 58.2 | 58.8 | 58.5 | 58.8 | 59.8 |
| fr1_plant/seq-01 | 94.3 | 92.5 | 93.7 | 92.9 | 93.0 | 93.0 | 94.1 |
| fr1_room/seq-01 | 83.5 | 81.0 | 81.1 | 82.5 | 82.4 | 79.5 | 81.6 |
| fr1_rpy/seq-01 | 45.9 | 43.4 | 44.2 | 44.4 | 43.7 | 45.0 | 44.2 |
| fr1_teddy/seq-01 | 94.4 | 92.7 | 93.3 | 93.3 | 93.4 | 93.1 | 93.7 |
| fr2_360_hemisphere/seq-01 | 58.7 | 50.8 | 54.6 | 52.8 | 50.9 | 52.9 | 53.6 |
| **mean** | **73.2** | **69.5** | **70.9** | **70.8** | **70.3** | **70.4** | **71.2** |
| time (s) | 126 | 56 | 64 | 63 | 69 | 67 | 74 |

N = 200

| sequence | B1 | AVEK-s4e36k10 | AVEKB-f16n3 | AVEK-rand | AVEKU-u10 | AVU-u5 | AVEKBU-f16u10 |
|---|---|---|---|---|---|---|---|
| fr1_360/seq-01 | 59.7 | 55.7 | 58.0 | 56.2 | 56.6 | 56.4 | 59.1 |
| fr1_plant/seq-01 | 94.0 | 91.8 | 93.1 | 92.4 | 92.4 | 92.6 | 93.4 |
| fr1_room/seq-01 | 82.1 | 81.9 | 82.8 | 82.0 | 81.4 | 82.1 | 82.4 |
| fr1_rpy/seq-01 | 44.3 | 42.6 | 42.1 | 43.1 | 43.4 | 43.6 | 42.6 |
| fr1_teddy/seq-01 | 94.4 | 93.3 | 93.7 | 93.4 | 93.5 | 93.5 | 93.9 |
| fr2_360_hemisphere/seq-01 | 58.1 | 51.9 | 52.9 | 54.7 | 54.0 | 53.2 | 54.7 |
| **mean** | **72.1** | **69.5** | **70.4** | **70.3** | **70.2** | **70.2** | **71.0** |
| time (s) | 451 | 161 | 193 | 189 | 200 | 201 | 236 |

| config | gain vs AVEK (cells) | time N=200 (s) |
|---|---|---|
| AVEKB-f16n3 | +1.12 (12) | 193 |
| AVEK-rand | +1.03 (12) | 189 |
| AVEKU-u10 | +0.75 (12) | 200 |
| AVU-u5 | +0.78 (12) | 201 |
| AVEKBU-f16u10 | +1.55 (12) | 236 |

C* = AVU-u5; combined kept = False (gain(f16u10) - gain(f16n3) = +0.43)

#### Step 2: 6 unseen TUM sequences

N = 100

| sequence | B1 | AVEK-s4e36k10 | AVEKB-f16n3 | AVEKU-u10 | AVU-u5 | AVEKBU-f16u10 |
|---|---|---|---|---|---|---|
| fr2_360_kidnap/seq-01 | 66.3 | 64.7 | 65.2 | 64.7 | 64.4 | 65.3 |
| fr2_pioneer_360/seq-01 | 84.6 | 73.2 | 75.1 | 76.8 | 80.1 | 78.3 |
| fr2_rpy/seq-01 | 73.1 | 63.0 | 66.1 | 68.9 | 64.1 | 69.6 |
| fr2_xyz/seq-01 | 96.5 | 97.2 | 97.1 | 97.2 | 97.0 | 97.0 |
| fr3_sitting_rpy/seq-01 | 53.3 | 50.6 | 50.8 | 52.3 | 50.6 | 51.7 |
| fr3_walking_halfsphere/seq-01 | 89.6 | 86.7 | 88.3 | 87.3 | 87.2 | 88.8 |
| **mean** | **77.2** | **72.5** | **73.8** | **74.5** | **73.9** | **75.1** |
| time (s) | 132 | 60 | 68 | 67 | 67 | 74 |

N = 200

| sequence | B1 | AVEK-s4e36k10 | AVEKB-f16n3 | AVEKU-u10 | AVU-u5 | AVEKBU-f16u10 |
|---|---|---|---|---|---|---|
| fr2_360_kidnap/seq-01 | 66.1 | 63.4 | 64.3 | 64.6 | 64.3 | 65.1 |
| fr2_pioneer_360/seq-01 | 84.2 | 77.4 | 79.0 | 79.4 | 81.0 | 80.9 |
| fr2_rpy/seq-01 | 66.6 | 57.6 | 59.4 | 59.1 | 59.0 | 60.6 |
| fr2_xyz/seq-01 | 96.8 | 97.3 | 97.3 | 97.3 | 97.2 | 97.2 |
| fr3_sitting_rpy/seq-01 | 51.4 | 47.7 | 48.5 | 48.6 | 49.0 | 49.1 |
| fr3_walking_halfsphere/seq-01 | 88.7 | 86.6 | 88.0 | 86.9 | 87.0 | 88.1 |
| **mean** | **75.6** | **71.7** | **72.7** | **72.7** | **72.9** | **73.5** |
| time (s) | 489 | 169 | 205 | 201 | 201 | 234 |
AVEKU-u10: vs AVEK +1.49 (12 cells, wins 12), vs f16n3 +0.34, time N=200 201 s
AVU-u5: vs AVEK +1.31 (12 cells, wins 8), vs f16n3 +0.16, time N=200 201 s
AVEKBU-f16u10: vs AVEK +2.21 (12 cells, wins 10), vs f16n3 +1.06, time N=200 234 s

H40: AVU-u5 - AVEK +1.31 over 12 cells (needs >= +0.50)
H40w: N=200, 6 sequences, mean +1.27, wins 5/6, one-sided Wilcoxon p=0.0312
H41: AVU-u5 - f16n3 +0.16; time ratio vs f16n3 at N=200 0.98
speed-up vs B1 at N=200: AVEK-s4e36k10 2.90x
speed-up vs B1 at N=200: AVEKB-f16n3 2.39x
speed-up vs B1 at N=200: AVEKU-u10 2.44x
speed-up vs B1 at N=200: AVU-u5 2.43x
speed-up vs B1 at N=200: AVEKBU-f16u10 2.09x

summary: {'H40': True, 'H40w': True, 'H41': True, 'H42': 'n/a (combined variant dropped in step 1)'}
