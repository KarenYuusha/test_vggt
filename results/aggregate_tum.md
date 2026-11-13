
#### N = 50

| sequence | B1 | K-r2k10 | AV-s4 | AVE-s4e36 | AVEK-s4e36k10 |
|---|---|---|---|---|---|
| fr1_360 | 59.8 | 50.1 | 49.0 | 46.8 | 51.5 |
| fr1_desk | 93.1 | 93.0 | 92.4 | 92.6 | 92.7 |
| fr1_room | 83.5 | 76.1 | 73.1 | 79.6 | 80.4 |
| fr3_long_office | 96.8 | 95.4 | 95.0 | 94.9 | 95.1 |
| fr3_str_tex_far | 97.7 | 96.6 | 96.6 | 96.3 | 96.9 |
| fr3_walking_xyz | 89.0 | 86.4 | 87.7 | 87.5 | 88.1 |

mean AUC (time): B1 86.7 (41 s); K-r2k10 82.9 (24 s); AV-s4 82.3 (22 s); AVE-s4e36 83.0 (24 s); AVEK-s4e36k10 84.1 (25 s)

#### N = 100

| sequence | B1 | K-r2k10 | AV-s4 | AVE-s4e36 | AVEK-s4e36k10 |
|---|---|---|---|---|---|
| fr1_360 | 62.5 | 55.1 | 55.4 | 53.2 | 56.7 |
| fr1_desk | 93.4 | 93.2 | 92.6 | 92.7 | 93.1 |
| fr1_room | 83.5 | 79.3 | 74.2 | 77.4 | 81.0 |
| fr3_long_office | 96.9 | 96.0 | 95.7 | 95.3 | 95.9 |
| fr3_str_tex_far | 97.2 | 96.2 | 96.0 | 95.7 | 96.2 |
| fr3_walking_xyz | 91.0 | 89.7 | 90.0 | 89.3 | 90.4 |

mean AUC (time): B1 87.4 (128 s); K-r2k10 84.9 (63 s); AV-s4 84.0 (52 s); AVE-s4e36 83.9 (55 s); AVEK-s4e36k10 85.6 (62 s)

#### N = 200

| sequence | B1 | K-r2k10 | AV-s4 | AVE-s4e36 | AVEK-s4e36k10 |
|---|---|---|---|---|---|
| fr1_360 | 59.7 | 54.2 | 53.4 | 52.6 | 55.7 |
| fr1_desk | 93.0 | 92.7 | 92.4 | 92.5 | 92.6 |
| fr1_room | 82.1 | 80.6 | 75.7 | 81.7 | 81.9 |
| fr3_long_office | 96.7 | 96.0 | 95.6 | 95.3 | 95.8 |
| fr3_str_tex_far | 96.6 | 95.7 | 95.5 | 95.1 | 95.4 |
| fr3_walking_xyz | 90.1 | 88.4 | 88.7 | 88.3 | 89.1 |

mean AUC (time): B1 86.4 (454 s); K-r2k10 84.6 (192 s); AV-s4 83.6 (133 s); AVE-s4e36 84.2 (141 s); AVEK-s4e36k10 85.1 (170 s)

#### N = 400

| sequence | B1 | K-r2k10 | AV-s4 | AVE-s4e36 | AVEK-s4e36k10 |
|---|---|---|---|---|---|
| fr1_360 | – | – | 51.1 | 49.8 | 52.3 |
| fr1_desk | – | – | 92.1 | 92.2 | 92.3 |
| fr1_room | – | – | 79.1 | 81.2 | 82.1 |
| fr3_long_office | – | – | 95.5 | 95.3 | 95.7 |
| fr3_str_tex_far | – | – | 94.7 | 94.3 | 94.8 |
| fr3_walking_xyz | – | – | 88.3 | 88.0 | 89.1 |

mean AUC (time): AV-s4 83.5 (387 s); AVE-s4e36 83.5 (414 s); AVEK-s4e36k10 84.4 (537 s)

#### Pre-registered checks

N=50: AVE − AV-s4 mean +0.67 (wins 2/6, p=0.844); AVEK − AV-s4 mean +1.79 (wins 6/6)
N=100: AVE − AV-s4 mean -0.03 (wins 2/6, p=0.562); AVEK − AV-s4 mean +1.60 (wins 6/6)
N=200: AVE − AV-s4 mean +0.69 (wins 2/6, p=0.562); AVEK − AV-s4 mean +1.54 (wins 5/6)
N=400: AVE − AV-s4 mean -0.01 (wins 2/6, p=0.562); AVEK − AV-s4 mean +0.90 (wins 6/6)
H26 (AVE ≥ AV-s4 on average at every N): False [True, False, True, False]
N=100: AVE − B1 per sequence {'fr1_360': -9.3, 'fr1_desk': -0.6, 'fr1_room': -6.0, 'fr3_walking_xyz': -1.7, 'fr3_long_office': -1.6, 'fr3_str_tex_far': -1.5}, mean -3.46
N=200: AVE − B1 per sequence {'fr1_360': -7.1, 'fr1_desk': -0.5, 'fr1_room': -0.4, 'fr3_walking_xyz': -1.8, 'fr3_long_office': -1.4, 'fr3_str_tex_far': -1.5}, mean -2.11
H27 (AVE − B1 mean ≥ −1.0 at N=100, 200): False [False, False]
H28 (AVE within 2 of B1 on every sequence except fr1_360): False [False, True]
fr1_360 N=100: drop vs B1 {'AVE-s4e36': -9.3, 'AVEK-s4e36k10': -5.7, 'K-r2k10': -7.3, 'AV-s4': -7.1}
fr1_360 N=200: drop vs B1 {'AVE-s4e36': -7.1, 'AVEK-s4e36k10': -3.9, 'K-r2k10': -5.4, 'AV-s4': -6.2}
H29 (keyframe configs drop less than AVE on fr1_360, exploratory): True [True, True]
