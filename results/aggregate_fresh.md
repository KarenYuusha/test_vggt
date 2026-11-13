
#### N = 50 (11 sequences)

| config | AUC@30 | Δ vs B1 | worst Δ | within 2 | Chamfer | fid_pose | T4 time | speed-up |
|---|---|---|---|---|---|---|---|---|
| B1 | 78.4 | +0.00 | +0.0 | 11/11 | 0.043 | nan | 42 s | 1.0× |
| AV-s4 | 77.9 | -0.44 | -2.7 | 10/11 | 0.040 | 93.9 | 21 s | 2.0× |
| AVE-s4e36 | 78.5 | +0.16 | -1.2 | 11/11 | 0.040 | 94.0 | 22 s | 1.9× |
| AVEK-s4e36k10 | 78.4 | -0.01 | -2.6 | 10/11 | 0.041 | 95.1 | 24 s | 1.7× |
| AVEK-s4e36k20 | 78.4 | +0.06 | -1.9 | 11/11 | 0.041 | 94.5 | 23 s | 1.8× |
| K-r2k10 | 78.3 | -0.06 | -1.7 | 11/11 | 0.040 | 95.3 | 26 s | 1.6× |

AVEK-s4e36k10 − AV-s4: mean +0.43, wins 9/11, Wilcoxon p = 0.042

AVE-s4e36 − AV-s4: mean +0.61, wins 9/11, Wilcoxon p = 0.083

AVEK-s4e36k10 − K-r2k10: mean +0.05, wins 4/11, Wilcoxon p = 0.700

AVEK-s4e36k20 − AV-s4: mean +0.50, wins 9/11, Wilcoxon p = 0.083

#### N = 100 (11 sequences)

| config | AUC@30 | Δ vs B1 | worst Δ | within 2 | Chamfer | fid_pose | T4 time | speed-up |
|---|---|---|---|---|---|---|---|---|
| B1 | 78.3 | +0.00 | +0.0 | 11/11 | 0.042 | nan | 133 s | 1.0× |
| AV-s4 | 77.9 | -0.42 | -3.3 | 10/11 | 0.040 | 94.5 | 51 s | 2.6× |
| AVE-s4e36 | 78.4 | +0.12 | -3.1 | 10/11 | 0.040 | 94.6 | 53 s | 2.5× |
| AVEK-s4e36k10 | 78.2 | -0.09 | -4.3 | 10/11 | 0.040 | 95.7 | 60 s | 2.2× |
| AVEK-s4e36k20 | 78.4 | +0.09 | -2.9 | 10/11 | 0.040 | 95.3 | 56 s | 2.4× |
| K-r2k10 | 78.1 | -0.14 | -4.0 | 10/11 | 0.040 | 95.6 | 67 s | 2.0× |

AVEK-s4e36k10 − AV-s4: mean +0.33, wins 9/11, Wilcoxon p = 0.175

AVE-s4e36 − AV-s4: mean +0.53, wins 9/11, Wilcoxon p = 0.054

AVEK-s4e36k10 − K-r2k10: mean +0.05, wins 6/11, Wilcoxon p = 0.898

AVEK-s4e36k20 − AV-s4: mean +0.50, wins 10/11, Wilcoxon p = 0.032

#### N = 200 (11 sequences)

| config | AUC@30 | Δ vs B1 | worst Δ | within 2 | Chamfer | fid_pose | T4 time | speed-up |
|---|---|---|---|---|---|---|---|---|
| B1 | 77.5 | +0.00 | +0.0 | 11/11 | 0.041 | nan | 497 s | 1.0× |
| AV-s4 | 77.6 | +0.10 | -2.6 | 10/11 | 0.040 | 94.4 | 132 s | 3.8× |
| AVE-s4e36 | 78.4 | +0.93 | -0.5 | 11/11 | 0.040 | 94.3 | 139 s | 3.6× |
| AVEK-s4e36k10 | 78.3 | +0.79 | -0.5 | 11/11 | 0.040 | 95.7 | 171 s | 2.9× |
| AVEK-s4e36k20 | 78.3 | +0.82 | -0.7 | 11/11 | 0.040 | 95.3 | 155 s | 3.2× |
| K-r2k10 | 78.2 | +0.74 | -0.4 | 11/11 | 0.040 | 95.6 | 203 s | 2.5× |

AVEK-s4e36k10 − AV-s4: mean +0.69, wins 10/11, Wilcoxon p = 0.010

AVE-s4e36 − AV-s4: mean +0.84, wins 9/11, Wilcoxon p = 0.005

AVEK-s4e36k10 − K-r2k10: mean +0.05, wins 7/11, Wilcoxon p = 0.520

AVEK-s4e36k20 − AV-s4: mean +0.72, wins 9/11, Wilcoxon p = 0.005

#### Pre-registered checks

H16 (mean ≥ AV-s4 and smaller worst drop, every N): False [(True, True), (True, False), (True, True)]
H17 (all sequences within 2 of B1 at N=100, 200): False [False, True]
H18 (mean Δ ≥ −0.5 at N=100, 200): True [-0.09, 0.79]
H19 (AVE-s4e36 mean ≥ AV-s4, every N): True [True, True, True]
H20 (≥10% faster than K-r2k10 and AUC ≥ K-r2k10 − 0.2 at N=200): True (K-r2k10 time / ours = 1.19, AUC diff = +0.05)
