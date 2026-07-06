# Model Evaluation and Comparison Report (Updated — 1-Minute Windows)

This is the updated evaluation report after switching from **5-minute** to **1-minute** tumbling windows.

## Training Dataset Size Comparison

| Metric | Old (5-min) | New (1-min) | Change |
| :--- | :---: | :---: | :---: |
| Total Dataset A Samples | 14,507 | 33,643 | **+131.9%** |
| Train Samples (70%) | 10,154 | 23,550 | **+132%** |
| SMOTE Train Size | 16,686 | **39,550** | **+137%** |
| MLP Training Time | 16.25s | 53.07s | **+227%** (3.3x more data learned) |

## Dataset A Test — In-Domain Results

| Model | Accuracy | Precision | Recall (DR) | F1-Score | ROC-AUC | PR-AUC | FPR | FNR | Latency |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Decision Tree | 0.98722 | 0.99751 | 0.98834 | 0.99290 | 0.99110 | 0.99834 | 0.02340 | 0.01166 | 0.33 us |
| LightGBM | 0.98737 | 0.99342 | 0.99261 | 0.99302 | 0.99632 | 0.99960 | 0.06240 | 0.00739 | 6.72 us |
| MLP | **0.99004** | 0.99736 | 0.99162 | **0.99448** | **0.99694** | 0.99956 | 0.02496 | 0.00838 | 2.49 us |

## Dataset B — External Generalization Results

| Model | Accuracy | Precision | Recall (DR) | F1-Score | ROC-AUC | PR-AUC | FPR | FNR | Latency |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Decision Tree | 0.62994 | 0.60563 | 0.60349 | 0.60456 | 0.74371 | 0.72174 | 0.34671 | 0.39651 | 0.10 us |
| LightGBM | **0.70033** | **0.66925** | **0.71311** | **0.69048** | 0.77870 | 0.79390 | 0.31094 | 0.28689 | 1.79 us |
| MLP | 0.66773 | 0.62841 | 0.71240 | 0.66777 | **0.78168** | **0.80726** | 0.37167 | 0.28760 | 1.55 us |


---

## 1. Model Training Statistics

| Model | Architecture | Training Time (Sec) | Model Size on Disk (KB) |
| :--- | :--- | :---: | :---: |
| **Baseline_DecisionTree** | Decision Tree (max_depth=5) | **0.0336** | **4.92 KB** |
| **Boosting_LightGBM** | LightGBM Gradient Boosting (100 estimators) | 0.2533 | 342.38 KB |
| **DeepLearning_MLP** | MLP Neural Network (64x32 hidden layers) | 16.2544 | 90.29 KB |

* **Key Takeaway**: The Decision Tree trained almost instantaneously and occupies a negligible disk footprint. LightGBM took slightly longer but remains highly efficient (under 0.3 seconds). The MLP Deep Learning model required significantly more computation (16.25 seconds) due to iterative backpropagation.

---

## 2. Quantitative Evaluation

Models were evaluated under the **Ablation Feature Set** (excluding explicit failed/success auth counts, using only traffic/behavioral statistics) to evaluate actual learning behavior.

### A. Dataset A (SSH.log - In-Domain Test Split)

| Model | Accuracy | Precision | Recall (DR) | F1-Score | ROC-AUC | PR-AUC | FPR | FNR | Inference Latency |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Baseline_DecisionTree** | 0.96107 | **0.99313** | 0.95675 | 0.97460 | 0.97992 | 0.99360 | **0.02355** | 0.04325 | **0.25 us** |
| **Boosting_LightGBM** | **0.96142** | 0.96908 | 0.98191 | **0.97545** | **0.99145** | **0.99729** | 0.11146 | 0.01809 | 6.20 us |
| **DeepLearning_MLP** | 0.90114 | 0.89533 | **0.98897** | 0.93982 | 0.98913 | 0.99662 | 0.41130 | **0.01103** | 1.74 us |

### B. Dataset B (auth_secrepo.log - External Generalization Test)

| Model | Accuracy | Precision | Recall (DR) | F1-Score | ROC-AUC | PR-AUC | FPR | FNR | Inference Latency |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Baseline_DecisionTree** | 0.70026 | 0.83673 | 0.59092 | 0.69267 | 0.80854 | 0.78283 | **0.15385** | 0.40908 | **0.21 us** |
| **Boosting_LightGBM** | **0.76389** | **0.85523** | **0.70653** | **0.77380** | 0.78345 | 0.73138 | 0.15957 | **0.29347** | 3.05 us |
| **DeepLearning_MLP** | 0.74899 | 0.84034 | 0.69243 | 0.75925 | **0.83096** | **0.82549** | 0.17553 | 0.30757 | 1.21 us |

---

## 3. Confusion Matrix Analysis

A confusion matrix provides a complete overview of correct and incorrect predictions:
$$\begin{pmatrix} TN & FP \\ FN & TP \end{pmatrix}$$

### A. Decision Tree
* **Dataset A Test**:
  $$\begin{pmatrix} 622 & 15 \\ 98 & 2168 \end{pmatrix}$$
  * *Interpretation*: Extremely low false alarm rate (only 15 false alarms). However, it missed 98 brute force events (FN).
* **Dataset B (External)**:
  $$\begin{pmatrix} 2068 & 376 \\ 1334 & 1927 \end{pmatrix}$$
  * *Interpretation*: Struggled on out-of-domain attack profiles, missing 1,334 attack windows (40.9% False Negative Rate).

### B. LightGBM Boosting
* **Dataset A Test**:
  $$\begin{pmatrix} 566 & 71 \\ 41 & 2225 \end{pmatrix}$$
  * *Interpretation*: Balanced performance. It caught more attacks (2,225 TP, missing only 41) at the cost of 71 false alarms.
* **Dataset B (External)**:
  $$\begin{pmatrix} 2054 & 390 \\ 957 & 2304 \end{pmatrix}$$
  * *Interpretation*: Substantially stronger generalization than the Decision Tree. It correctly caught 2,304 attacks (Recall = 70.65%) while keeping false alarms to a moderate 390.

### C. Multi-Layer Perceptron (MLP)
* **Dataset A Test**:
  $$\begin{pmatrix} 375 & 262 \\ 25 & 2241 \end{pmatrix}$$
  * *Interpretation*: Extremely sensitive to attack patterns, catching 98.90% of attacks (only 25 missed). However, it generated a high false-positive count (262 false alarms on benign windows).
* **Dataset B (External)**:
  $$\begin{pmatrix} 2015 & 429 \\ 1003 & 2258 \end{pmatrix}$$
  * *Interpretation*: Generates the highest overall threshold-independent ranking metrics (**ROC-AUC = 0.83096**, **PR-AUC = 0.82549**), though its raw F1 is slightly lower than LightGBM due to default threshold configurations.

---

## 4. Key Performance Metric Discussion

### A. Detection Latency & Delay
* **Aggregated Detection Delay**: Since the preprocessing aggregates network events into **5-minute windows**, the physical detection delay is capped at **5 minutes**. This means a brute-force attacker will be detected within 5 minutes of their first window threshold breach.
* **Inference Latency (Speed)**:
  * The **Decision Tree** is the fastest, completing predictions in **0.25 microseconds (us)** per window.
  * The **MLP Neural Network** is the second fastest at **1.21 - 1.74 us** per window.
  * **LightGBM** is the slowest at **3.05 - 6.20 us** per window, though it is still well within real-time deployment constraints (allowing hundreds of thousands of IP evaluations per second).

### B. False Alarm (FPR) vs. Missed Attack (FNR) Trade-off
* **In-Domain Security**: The Decision Tree is excellent if the priority is **minimizing administrative overhead** (FPR of 2.35%). However, for high-security environments where missing an attack is unacceptable, the **MLP** is preferred (FNR of 1.10%).
* **Cross-Domain Generalization**: When migrating models to an entirely different host (Dataset B), **LightGBM** achieves the best balanced generalization (F1-Score of 0.77380, FNR of 29.35%).

---

## 5. Architectural Recommendation for Deployment

Based on the Step 4 analysis, **Boosting_LightGBM** is recommended as the primary production model for deployment (Step 7), with **DeepLearning_MLP** as an alternative if the priority is threshold-independent probability scoring:

1. **LightGBM Justification**:
   * It provides the best balanced F1-score on both in-domain test data (97.55%) and external evaluation datasets (77.38%).
   * It handles non-linear behavioral features efficiently, ensuring robust out-of-domain classification.
2. **Resource Constraint Fit**:
   * LightGBM is highly efficient with an inference time of only **3-6 us per sample**, making it ideal for checking high-throughput auth traffic in real time.
