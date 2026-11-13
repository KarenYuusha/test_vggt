
N = 400 (AUC@30; '-' = not run)

| sequence | frames used | B1 | AVE-s4e36 | AVEK-s4e36k10 | AVEKB-f16n3 | AVU-u5 | AVEKBU-f16u10 | AVU-c40 |
|---|---|---|---|---|---|---|---|---|
| fr2_coke/seq-01 | 400 | 94.6 | 94.5 | 94.9 | 95.0 | 95.3 | 95.3 | 95.2 |
| fr2_dishes/seq-01 | 400 | 94.6 | 96.3 | 96.6 | 96.7 | 96.7 | 96.7 | 96.7 |
| fr2_flowerbouquet/seq-01 | 400 | 97.4 | 96.0 | 96.6 | 96.9 | 96.9 | 97.1 | 96.5 |
| fr2_pioneer_slam2/seq-01 | 400 | 66.4 | 63.6 | 64.2 | 65.4 | 64.9 | 66.2 | 64.7 |
| fr2_pioneer_slam3/seq-01 | 400 | 74.9 | 67.3 | 72.8 | 74.1 | 76.1 | 75.2 | 72.2 |
| fr3_large_cabinet/seq-01 | 400 | 94.9 | 93.0 | 94.0 | 94.5 | 94.3 | 94.4 | 94.1 |
| fr3_sitting_xyz/seq-01 | 400 | 92.5 | 90.1 | 91.1 | 92.3 | 91.3 | 92.3 | 90.9 |
| fr3_str_tex_near/seq-01 | 400 | 89.3 | 86.1 | 87.3 | 87.7 | 88.0 | 88.2 | 87.4 |
| **mean (8 complete)** | | **88.1** | **85.9** | **87.2** | **87.8** | **87.9** | **88.2** | **87.2** |
| time (s) | | 1856 | 428 | 557 | 705 | 695 | 827 | 556 |
| peak GB | | 6.46 | 5.29 | 6.18 | 6.46 | 5.53 | 6.46 | 5.41 |
| Chamfer | | 0.061 | 0.069 | 0.065 | 0.064 | 0.063 | 0.063 | 0.065 |

N = 800 (AUC@30; '-' = not run)

| sequence | frames used | B1 | AVE-s4e36 | AVEK-s4e36k10 | AVEKB-f16n3 | AVU-u5 | AVEKBU-f16u10 | AVU-c40 |
|---|---|---|---|---|---|---|---|---|
| fr2_coke/seq-01 | 800 | 92.6 | 94.1 | 94.4 | 94.5 | 94.4 | 94.5 | 94.4 |
| fr2_dishes/seq-01 | 800 | 89.3 | 95.2 | 94.9 | 95.2 | 94.2 | 94.3 | 95.1 |
| fr2_flowerbouquet/seq-01 | 800 | 96.8 | 95.7 | 96.2 | 96.7 | 96.6 | 96.8 | 96.0 |
| fr2_pioneer_slam2/seq-01 | 800 | 72.8 | 61.0 | 62.4 | 64.6 | 63.4 | 65.1 | 62.6 |
| fr2_pioneer_slam3/seq-01 | 800 | 63.0 | 67.3 | 71.1 | 71.3 | 70.0 | 72.0 | 69.4 |
| fr3_large_cabinet/seq-01 | 800 | 93.9 | 92.7 | 93.7 | 94.3 | 93.9 | 94.4 | 93.4 |
| fr3_sitting_xyz/seq-01 | 800 | 92.6 | 89.9 | 90.8 | 92.1 | 91.4 | 92.3 | 90.5 |
| fr3_str_tex_near/seq-01 | 800 | 87.7 | 84.7 | 86.1 | 86.5 | 86.6 | 87.2 | 85.5 |
| **mean (8 complete)** | | **86.1** | **85.1** | **86.2** | **86.9** | **86.3** | **87.1** | **85.9** |
| time (s) | | 7244 | 1455 | 2007 | 2596 | 2603 | 3124 | 1726 |
| peak GB | | 9.66 | 7.41 | 13.64 | 13.64 | 7.79 | 13.64 | 7.44 |
| Chamfer | | 0.061 | 0.067 | 0.064 | 0.063 | 0.063 | 0.063 | 0.065 |

speed-up vs B1 at N=400: AVE-s4e36 4.34x, AVEK-s4e36k10 3.33x, AVEKB-f16n3 2.63x, AVU-u5 2.67x, AVEKBU-f16u10 2.24x, AVU-c40 3.34x
speed-up vs B1 at N=800: AVE-s4e36 4.98x, AVEK-s4e36k10 3.61x, AVEKB-f16n3 2.79x, AVU-u5 2.78x, AVEKBU-f16u10 2.32x, AVU-c40 4.20x

H47: AVU-u5 - AVEK +0.42 over 16 cells, wins 13 (needs >= +0.50)
H47w: N=800, 8 sequences [-0.  -0.7  0.4  1.  -1.1  0.2  0.6  0.6], one-sided Wilcoxon p=0.3711
H48: f16u10 - f16n3 +0.25 over 16 cells, wins 13 (needs >= +0.50)
H49: f16u10 - B1 +0.56 over 16 cells (needs >= -1.00)
H50a: N=800 B1/AVE-s4e36 time 4.98x over 8 sequences (needs >= 4.5)
H50b: N=800 B1/AVU-u5 time 2.78x over 8 sequences (needs >= 3.0)
H50c: N=800 B1/AVEKBU-f16u10 time 2.32x over 8 sequences (needs >= 2.5)
H51: AVU-c40 - AVU-u5 -0.60 over 16 cells (needs >= -0.30); time ratio at N=800 0.66 (needs <= 0.80)
H52: AVU-c40 - AVE +1.07 over 16 cells, wins 15 (needs >= +0.50); time ratio at N=800 1.19 (needs <= 1.15)
(reference) AVE-s4e36 - B1: N=400 -2.19, N=800 -1.00
(reference) AVEK-s4e36k10 - B1: N=400 -0.86, N=800 +0.15
(reference) AVEKB-f16n3 - B1: N=400 -0.23, N=800 +0.85
(reference) AVU-u5 - B1: N=400 -0.11, N=800 +0.25
(reference) AVEKBU-f16u10 - B1: N=400 +0.12, N=800 +1.00
(reference) AVU-c40 - B1: N=400 -0.85, N=800 -0.20

long-sequence pick (fastest within 1.0 of B1 at N=800, 8 sequences): AVE-s4e36
Holm: H40w p=0.0312 -> 0.1250, H43w p=0.1094 -> 0.3281, H46 p=0.1162 -> 0.3281, H47w p=0.3711 -> 0.3711

summary: {'H47': False, 'H47w': False, 'H48': False, 'H49': True, 'H50a': True, 'H50b': False, 'H50c': False, 'H51': False, 'H52': False}
