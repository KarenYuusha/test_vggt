#### Low-memory forward on a T4 (per sequence)

| scene | seq | N (frames used) | config | AUC@30 | Chamfer | time | peak GB |
|---|---|---|---|---|---|---|---|
| chess | seq-02 | 200 (200) | AVE-s4e36 | 89.6 | 0.032 | 146 s | 4.30 |
| fire | seq-02 | 200 (200) | AVE-s4e36 | 92.5 | 0.036 | 144 s | 4.30 |
| office | seq-09 | 200 (200) | AVE-s4e36 | 70.1 | 0.038 | 148 s | 4.30 |
| pumpkin | seq-03 | 200 (200) | AVE-s4e36 | 75.2 | 0.036 | 147 s | 4.30 |
| redkitchen | seq-12 | 200 (200) | AVE-s4e36 | 81.0 | 0.027 | 151 s | 4.30 |
| stairs | seq-03 | 200 (200) | AVE-s4e36 | 76.1 | 0.033 | 153 s | 4.30 |
| chess | seq-02 | 400 (400) | B1 | 89.7 | 0.035 | 1820 s | 6.46 |
| chess | seq-02 | 400 (400) | AV-s4 | 89.6 | 0.031 | 400 s | 5.29 |
| chess | seq-02 | 400 (400) | AVE-s4e36 | 89.5 | 0.032 | 428 s | 5.29 |
| fire | seq-02 | 400 (400) | B1 | 92.4 | 0.038 | 1817 s | 6.46 |
| fire | seq-02 | 400 (400) | AV-s4 | 92.1 | 0.036 | 400 s | 5.29 |
| fire | seq-02 | 400 (400) | AVE-s4e36 | 92.3 | 0.035 | 427 s | 5.29 |
| office | seq-09 | 400 (400) | B1 | 68.9 | 0.039 | 1925 s | 6.46 |
| office | seq-09 | 400 (400) | AV-s4 | 66.4 | 0.038 | 410 s | 5.29 |
| office | seq-09 | 400 (400) | AVE-s4e36 | 69.9 | 0.038 | 437 s | 5.29 |
| pumpkin | seq-03 | 400 (400) | B1 | 75.3 | 0.038 | 1933 s | 6.46 |
| pumpkin | seq-03 | 400 (400) | AV-s4 | 74.4 | 0.036 | 413 s | 5.29 |
| pumpkin | seq-03 | 400 (400) | AVE-s4e36 | 75.0 | 0.036 | 440 s | 5.29 |
| redkitchen | seq-12 | 400 (400) | B1 | 81.5 | 0.026 | 2007 s | 6.46 |
| redkitchen | seq-12 | 400 (400) | AV-s4 | 80.6 | 0.027 | 415 s | 5.29 |
| redkitchen | seq-12 | 400 (400) | AVE-s4e36 | 80.9 | 0.027 | 445 s | 5.29 |
| stairs | seq-03 | 400 (400) | B1 | 73.3 | 0.036 | 2012 s | 6.46 |
| stairs | seq-03 | 400 (400) | AV-s4 | 72.3 | 0.031 | 415 s | 5.29 |
| stairs | seq-03 | 400 (400) | AVE-s4e36 | 75.1 | 0.034 | 445 s | 5.29 |
| chess | seq-02 | 800 (800) | B1 | 89.4 | 0.034 | 7183 s | 9.66 |
| chess | seq-02 | 800 (800) | AV-s4 | 89.3 | 0.031 | 1373 s | 7.41 |
| chess | seq-02 | 800 (800) | AVE-s4e36 | 89.3 | 0.031 | 1469 s | 7.41 |
| fire | seq-02 | 800 (800) | AV-s4 | 91.8 | 0.036 | 1378 s | 7.41 |
| fire | seq-02 | 800 (800) | AVE-s4e36 | 92.0 | 0.035 | 1474 s | 7.41 |
| office | seq-09 | 800 (800) | AV-s4 | 66.5 | 0.039 | 1441 s | 7.41 |
| office | seq-09 | 800 (800) | AVE-s4e36 | 69.1 | 0.037 | 1537 s | 7.41 |
| pumpkin | seq-03 | 800 (800) | AV-s4 | 74.3 | 0.036 | 1450 s | 7.41 |
| pumpkin | seq-03 | 800 (800) | AVE-s4e36 | 74.8 | 0.037 | 1549 s | 7.41 |
| redkitchen | seq-12 | 800 (800) | AV-s4 | 80.7 | 0.027 | 1479 s | 7.41 |
| redkitchen | seq-12 | 800 (800) | AVE-s4e36 | 80.8 | 0.027 | 1580 s | 7.41 |
| stairs | seq-03 | 800 (500) | AV-s4 | 72.2 | 0.031 | 610 s | 5.81 |
| stairs | seq-03 | 800 (500) | AVE-s4e36 | 74.9 | 0.034 | 653 s | 5.81 |

#### Pre-registered checks

H21: standard forward OOM at N=400 {'B1': True, 'AV-s4': True, 'AVE-s4e36': True}; low-memory runs done for every planned config/N: True; max peak 9.66 GB -> True
H22: N=200 low-memory − standard AUC over 6 sequences: mean +0.00, max |diff| 0.02 -> True
H23: N=400 speed-up AVE vs B1 over 6 sequences 4.39x (≥5); N=800 [4.89] (≥8) -> False
H24: N=400 AVE − B1 mean +0.27 (≥ −1.0), AVE − AV-s4 mean +1.19 (≥ 0) -> True
H25: N=800 AVE − AV-s4 over 6 sequences: mean +1.03, per sequence {'chess': -0.1, 'fire': 0.2, 'office': 2.6, 'pumpkin': 0.5, 'redkitchen': 0.2, 'stairs': 2.7} -> True
