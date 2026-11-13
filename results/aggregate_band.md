
#### N = 100

| sequence | B1 | AV-s4 | AVE | AVEK | AVEB | AVEKB |
|---|---|---|---|---|---|---|
| fr1_plant | 94.3 | 91.8 | 91.8 | 92.5 | 93.7 | 94.0 |
| fr1_rpy | 45.9 | 43.6 | 42.7 | 43.4 | 41.5 | 42.6 |
| fr1_teddy | 94.4 | 92.6 | 92.2 | 92.7 | 93.4 | 93.8 |
| fr2_360_hemisphere | 58.7 | 48.8 | 44.5 | 50.7 | 53.3 | 56.3 |
| fr2_desk | 97.5 | 97.1 | 97.2 | 97.3 | 97.5 | 97.6 |
| fr3_sitting_halfsphere | 90.6 | 86.8 | 86.3 | 87.9 | 88.6 | 89.4 |
| **mean** | **80.3** | **76.8** | **75.8** | **77.4** | **78.0** | **79.0** |
| time (s) | 133 | 53 | 56 | 64 | 70 | 76 |
| Chamfer | 0.065 | 0.069 | 0.070 | 0.070 | 0.068 | 0.068 |

#### N = 200

| sequence | B1 | AV-s4 | AVE | AVEK | AVEB | AVEKB |
|---|---|---|---|---|---|---|
| fr1_plant | 94.0 | 91.2 | 90.9 | 91.8 | 93.4 | 93.6 |
| fr1_rpy | 44.3 | 41.7 | 42.7 | 42.6 | 38.9 | 40.3 |
| fr1_teddy | 94.4 | 92.9 | 92.7 | 93.3 | 93.6 | 93.9 |
| fr2_360_hemisphere | 58.1 | 50.8 | 45.7 | 51.9 | 51.5 | 54.5 |
| fr2_desk | 97.5 | 97.0 | 97.1 | 97.3 | 97.5 | 97.6 |
| fr3_sitting_halfsphere | 90.6 | 85.7 | 85.6 | 87.4 | 87.7 | 88.9 |
| **mean** | **79.8** | **76.6** | **75.8** | **77.4** | **77.1** | **78.1** |
| time (s) | 467 | 136 | 145 | 175 | 206 | 230 |
| Chamfer | 0.063 | 0.060 | 0.064 | 0.063 | 0.063 | 0.063 |

#### Pre-registered checks

H30 N=100: AVEB-s4e36f14 - AVE-s4e36 mean +2.23 (wins 5/6, Wilcoxon p=0.156), needs >= +1.0
H30 N=200: AVEB-s4e36f14 - AVE-s4e36 mean +1.32 (wins 5/6, Wilcoxon p=0.312), needs >= +1.0
H30: True

H31 N=100: AVEB-s4e36f14 - AVEK-s4e36k10 mean +0.60 (wins 5/6, Wilcoxon p=0.312), needs >= +0.0
H31 N=200: AVEB-s4e36f14 - AVEK-s4e36k10 mean -0.29 (wins 4/6, Wilcoxon p=1.000), needs >= +0.0
H31: False

H32 N=100: AVEKB-s4e36k10f14 - AVEK-s4e36k10 mean +1.54 (wins 5/6, Wilcoxon p=0.094), needs >= +0.5
H32 N=200: AVEKB-s4e36k10f14 - AVEK-s4e36k10 mean +0.75 (wins 5/6, Wilcoxon p=0.312), needs >= +0.5
H32: True

H33 N=100: rotation sequences, AVEK gap to B1 3.54, AVEKB gain +1.87 -> 53% closed
H33 N=200: rotation sequences, AVEK gap to B1 2.82, AVEKB gain +0.68 -> 24% closed
H33: False

N=100 speed-up vs B1: AV-s4 2.49x, AVE 2.36x, AVEK 2.08x, AVEB 1.89x, AVEKB 1.74x
N=200 speed-up vs B1: AV-s4 3.44x, AVE 3.23x, AVEK 2.67x, AVEB 2.27x, AVEKB 2.03x

summary: {'H30': True, 'H31': False, 'H32': True, 'H33': False}
