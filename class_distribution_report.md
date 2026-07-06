# Class Distribution Analysis and Data Balancing Report

This report presents a comprehensive class distribution analysis and evaluates multiple data balancing techniques for the **SSH Brute Force Detection** project. It documents the distribution metrics at both the log-line (event) level and the aggregated time-window (sample) level, analyzes the impact of balancing on model performance, and provides a clear technical justification for the selected balancing technique.

---

## 1. Class Distribution Analysis

### A. Raw Log-Line (Event-Level) Distribution
At the raw event level, each log line represents a system message. Benign events include CRON session logs, administrative logins, and connection closures. Attack events include failed passwords, invalid user guesses, and authentication failures.

* **Dataset A (`SSH.log`)**:
  * **Benign Events**: 177,221 (27.05%) *(calculated as Total - Failures)*
  * **Attack Events**: 477,926 (72.95%) *(explicit failed passwords and invalid user attempts)*
  * **Class Ratio (Benign:Attack)**: 0.3708 : 1 (or 1 : 2.70)
  * **Imbalance Severity**: **Mild Imbalance**

* **Dataset B (`auth_secrepo.log`)**:
  * **Benign Events**: 51,976 (59.85%)
  * **Attack Events**: 34,863 (40.15%) *(explicit failed passwords and invalid user attempts)*
  * **Class Ratio (Benign:Attack)**: 1.4908 : 1 (or 1 : 0.67)
  * **Imbalance Severity**: **Mild Imbalance**

---

### B. Time-Window (Sample-Level) Distribution
To capture the behavioral nature of brute force attacks, logs are aggregated into **5-minute tumbling windows** grouped by source IP address. 
* **Attack Window (1)**: $\ge 5$ failed attempts OR $\ge 1$ invalid user attempts.
* **Benign Window (0)**: All other windows (normal admin logins, cron sessions, low failure rates).

Applying this grouping yields the following distributions across our splits:

| Dataset Split | Total Samples | Benign Samples | Attack Samples | Class Ratio (Benign:Attack) | Imbalance Severity |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Dataset A - Train (70%)** | 10,154 | 1,811 (17.84%) | 8,343 (82.16%) | 0.2171 (or 1 : 4.61) | **Moderate Imbalance** (Benign is minority) |
| **Dataset A - Val (10%)** | 1,450 | 341 (23.52%) | 1,109 (76.48%) | 0.3075 (or 1 : 3.25) | **Mild Imbalance** |
| **Dataset A - Test (20%)** | 2,903 | 637 (21.94%) | 2,266 (78.06%) | 0.2811 (or 1 : 3.56) | **Mild Imbalance** |
| **Dataset B (External)** | 5,705 | 2,444 (42.84%) | 3,261 (57.16%) | 0.7495 (or 1 : 1.33) | **Mild Imbalance** |

> [!NOTE]
> **Key Insight**: Unlike many cybersecurity contexts where the attack class is the minority, in these targeted brute force logs, the **Benign** class is the minority in the windowed dataset (comprising only 17.84% of Dataset A Train). This occurs because the log sources are under continuous, high-volume brute-force attacks, creating a high density of attack windows.

---

## 2. Evaluation of Data Balancing Techniques

To prevent the model from trivially memorizing the labels, we performed an **ablation study** by removing explicit authentication status counts (e.g., `failed_count`, `invalid_user_count`). We trained Random Forest classifiers on purely **behavioral/traffic features** (attempt counts, unique target usernames, unique source ports, duration, connection rates, and port diversity). 

Balancing was applied **only to the training set** of Dataset A. Validation, Test, and external Dataset B were kept raw to ensure realistic, unbiased performance reporting.

### A. Performance on Dataset A (In-Domain Temporal Test)

| Balancing Technique | Accuracy | Precision | Recall (Detection Rate) | F1-Score | ROC-AUC | PR-AUC |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Raw (No Balancing)** | 0.88598 | 0.87602 | **0.99470** | 0.93160 | 0.98182 | 0.99140 |
| **Random Undersampling (RUS)** | 0.96383 | 0.97578 | 0.97793 | 0.97686 | **0.98843** | **0.99615** |
| **Random Oversampling (ROS)** | **0.97072** | **0.98061** | 0.98191 | **0.98126** | 0.98663 | 0.99422 |
| **SMOTE** | 0.96039 | 0.96781 | 0.98191 | 0.97481 | 0.98489 | 0.99359 |
| **ADASYN** | 0.89115 | 0.88146 | 0.99426 | 0.93447 | 0.98730 | 0.99466 |

### B. Performance on Dataset B (External Generalization Test)

| Balancing Technique | Accuracy | Precision | Recall (Detection Rate) | F1-Score | ROC-AUC | PR-AUC |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Raw (No Balancing)** | **0.78545** | 0.85084 | **0.75744** | **0.80143** | 0.81327 | 0.86709 |
| **Random Undersampling (RUS)** | 0.73550 | 0.84873 | 0.65379 | 0.73861 | 0.81259 | 0.86682 |
| **Random Oversampling (ROS)** | 0.76021 | 0.85330 | 0.70101 | 0.76970 | 0.80727 | 0.85864 |
| **SMOTE** | 0.76670 | **0.85609** | 0.71144 | 0.77709 | **0.82809** | **0.87579** |
| **ADASYN** | 0.77336 | 0.84575 | 0.73812 | 0.78828 | 0.80642 | 0.84728 |

---

## 3. Analysis of Balancing Effects

1. **Bias Mitigation on Dataset A**:
   * The **Raw** model is biased towards predicting the majority class (Attack), yielding a high Recall (0.99470) but a low Precision (0.87602) due to high false positives on benign samples.
   * Applying **RUS, ROS, or SMOTE** balances the training representation of benign behavior. This dramatically reduces false positives, driving Precision up by over **10%** (from 0.876 to 0.980 for ROS) and increasing the overall F1-score from **0.931 to 0.981**.

2. **Loss of Generalization under Undersampling (RUS)**:
   * While RUS performs well in-domain (F1 of 0.976), it suffers a severe degradation on the unseen Dataset B (Recall drops to 0.65379, F1 drops to 0.73861). 
   * This occurs because RUS discards over 78% of the majority class (Attack) samples to balance the set, removing crucial behavioral variations of brute force attacks. This leaves the model unable to generalize to different attack speeds or patterns present on host B.

3. **Synthetic Sampling (SMOTE) for Robust Boundaries**:
   * On the external Dataset B, **SMOTE** achieves the highest **ROC-AUC (0.82809)** and **PR-AUC (0.87579)**. 
   * While the Raw model's F1-score is slightly higher (due to the majority-class bias aligning with Dataset B's distribution), SMOTE provides a more stable, threshold-independent ranking capability. By creating synthetic interpolation points between benign samples, SMOTE generalizes better to unseen benign behaviors than ROS (which merely duplicates existing points and risks overfitting).

---

## 4. Final Justification of Balancing Selection

Based on the quantitative results and domain context, **SMOTE (Synthetic Minority Over-sampling Technique)** is selected as the optimal data balancing technique for this project.

### Justification Highlights:
* **Information Preservation**: Unlike Random Undersampling (RUS), which discards critical attack profiles and degrades external recall to 65.38%, SMOTE preserves all raw training observations.
* **Overfitting Prevention**: Unlike Random Oversampling (ROS), which duplicates minority (benign) data points and can cause the decision trees to overfit to specific hostnames or timing configurations, SMOTE synthesizes new examples along the line segments joining minority class neighbors. This widens the decision boundary for benign traffic.
* **Superior Generalization Metric**: SMOTE achieves the highest area under the ROC and Precision-Recall curves on the unseen external dataset (ROC-AUC of 0.828, PR-AUC of 0.875), proving it constructs the most generalizable decision boundary for identifying SSH brute force attacks in heterogeneous systems.
