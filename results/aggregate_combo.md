#### 6 new TUM sequences

N = 100

| sequence | B1 | AVEK-s4e36k10 | AVEKB-f16n3 | AVU-u5 | AVEKBU-f16u10 |
|---|---|---|---|---|---|
| fr2_desk_with_person/seq-01 | 96.6 | 96.2 | 96.2 | 96.3 | 96.3 |
| fr2_large_with_loop/seq-01 | 88.7 | 84.8 | 86.8 | 86.4 | 87.5 |
| fr2_pioneer_slam/seq-01 | 88.5 | 85.3 | 86.1 | 86.3 | 87.4 |
| fr3_nostr_tex_near_loop/seq-01 | 86.8 | 83.8 | 86.0 | 86.9 | 87.3 |
| fr3_teddy/seq-01 | 95.5 | 93.5 | 93.7 | 94.0 | 94.1 |
| fr3_walking_rpy/seq-01 | 67.1 | 63.9 | 64.7 | 64.6 | 65.6 |
| **mean** | **87.2** | **84.6** | **85.6** | **85.8** | **86.4** |
| time (s) | 125 | 58 | 65 | 65 | 72 |

N = 200

| sequence | B1 | AVEK-s4e36k10 | AVEKB-f16n3 | AVU-u5 | AVEKBU-f16u10 |
|---|---|---|---|---|---|
| fr2_desk_with_person/seq-01 | 96.7 | 96.4 | 96.4 | 96.5 | 96.6 |
| fr2_large_with_loop/seq-01 | 87.9 | 83.9 | 85.2 | 85.5 | 85.4 |
| fr2_pioneer_slam/seq-01 | 87.9 | 85.9 | 86.5 | 86.9 | 87.2 |
| fr3_nostr_tex_near_loop/seq-01 | 87.2 | 87.9 | 90.0 | 87.5 | 89.7 |
| fr3_teddy/seq-01 | 95.3 | 93.2 | 93.5 | 93.9 | 93.8 |
| fr3_walking_rpy/seq-01 | 64.6 | 61.7 | 62.8 | 62.6 | 63.2 |
| **mean** | **86.6** | **84.8** | **85.7** | **85.5** | **86.0** |
| time (s) | 470 | 164 | 198 | 196 | 227 |
speed-up vs B1 at N=200: AVEK-s4e36k10 2.87x
speed-up vs B1 at N=200: AVEKB-f16n3 2.37x
speed-up vs B1 at N=200: AVU-u5 2.40x
speed-up vs B1 at N=200: AVEKBU-f16u10 2.07x

#### 4 new 7-Scenes sequences

N = 100

| sequence | B1 | AVEK-s4e36k10 | AVEKB-f16n3 | AVU-u5 | AVEKBU-f16u10 |
|---|---|---|---|---|---|
| office/seq-05 | 72.3 | 69.5 | 70.5 | 68.1 | 71.6 |
| office/seq-08 | 76.2 | 76.7 | 76.1 | 76.5 | 76.4 |
| redkitchen/seq-05 | 58.7 | 58.2 | 57.7 | 58.7 | 58.1 |
| redkitchen/seq-07 | 68.2 | 67.2 | 67.0 | 68.5 | 67.8 |
| **mean** | **68.8** | **67.9** | **67.8** | **68.0** | **68.5** |
| time (s) | 132 | 60 | 67 | 67 | 74 |

N = 200

| sequence | B1 | AVEK-s4e36k10 | AVEKB-f16n3 | AVU-u5 | AVEKBU-f16u10 |
|---|---|---|---|---|---|
| office/seq-05 | 70.3 | 67.0 | 68.2 | 68.7 | 68.5 |
| office/seq-08 | 76.2 | 76.8 | 76.2 | 76.7 | 76.2 |
| redkitchen/seq-05 | 57.1 | 56.9 | 56.4 | 57.3 | 56.8 |
| redkitchen/seq-07 | 61.5 | 66.6 | 67.4 | 67.2 | 66.7 |
| **mean** | **66.3** | **66.8** | **67.0** | **67.5** | **67.1** |
| time (s) | 496 | 168 | 205 | 202 | 235 |
speed-up vs B1 at N=200: AVEK-s4e36k10 2.96x
speed-up vs B1 at N=200: AVEKB-f16n3 2.42x
speed-up vs B1 at N=200: AVU-u5 2.46x
speed-up vs B1 at N=200: AVEKBU-f16u10 2.11x

H43: f16u10 - f16n3 on TUM +0.54 over 12 cells, wins 11 (needs >= +0.50)
H43w: N=200, 6 sequences [ 0.1  0.3  0.7 -0.3  0.3  0.5], one-sided Wilcoxon p=0.1094
(reference) AVU-u5 - f16n3 on TUM -0.01; AVU-u5 - AVEK +0.91
H44: f16u10 - f16n3 on 7-Scenes +0.34 over 8 cells (needs >= -0.30)
H45: AVU-u5 - f16n3 on 7-Scenes +0.30 over 8 cells (needs >= -0.50)
(reference) AVU-u5 - AVEK on 7-Scenes +0.35
H46: pooled N=200, 10 sequences, f16u10 - f16n3 mean +0.16, wins 8, one-sided Wilcoxon p=0.1162
Holm over the round's tests: H40w (kfx round) p=0.0312 -> 0.0938, H43w p=0.1094 -> 0.2188, H46 p=0.1162 -> 0.2188

summary: {'H43': True, 'H43w': False, 'H44': True, 'H45': True, 'H46': False}
