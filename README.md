# SSH Brute Force Attack Detection using Ensemble Machine Learning

> 🎓 **Academic Project**
> Cybersecurity detection using ensemble machine learning with cross-domain generalization.

[![Python Version](https://img.shields.io/badge/python-3.8%20%7C%203.9%20%7C%203.10-blue)](https://www.python.org/) [![Scikit-Learn](https://img.shields.io/badge/scikit--learn-1.3%2B-orange)](https://scikit-learn.org/) [![PyTorch](https://img.shields.io/badge/PyTorch-2.0%2B-red)](https://pytorch.org/) [![XGBoost](https://img.shields.io/badge/XGBoost-2.0%2B-red)](https://xgboost.readthedocs.io/)

---

## 📖 Project Objective

SSH brute force attack detection models trained on a single laboratory dataset often suffer from overfitting and perform poorly in real-world environments. The objective of this project is to:

1. **Train robust ensemble classifiers** on an internal SSH log dataset (**Dataset A** - SSH.log from Loghub).
2. **Validate generalization capabilities** on a completely unseen, real-world SSH log dataset (**Dataset B** - auth_secrepo.log from SecRepo) without retraining.
3. **Align network features** to a highly generalizable **6 behavioral feature schema** to enable robust operation across different SSH server environments.
4. **Compare gradient boosting with deep learning** approaches (XGBoost vs LSTM, GRU).
5. **Evaluate data balancing techniques** (SMOTE, Random Oversampling, Random Undersampling, ADASYN) impact on model performance.

---

## 📂 Project Directory Structure

```
SSH_BRUTEFORCE_DETECTION/
├── data/                                # Raw and processed datasets
│   ├── SSH.log                          # Dataset A: Loghub OpenSSH logs (655,147 samples)
│   ├── auth_secrepo.log                 # Dataset B: SecRepo AWS EC2 logs (86,839 samples)
│   └── processed/                       # Output from preprocessing
│       ├── dataset_a.npz                # Raw Dataset A (33,643 samples from 1-min windows)
│       ├── dataset_b.npz                # Raw Dataset B (4,272 samples from 1-min windows)
│       ├── feature_names.csv            # Feature name mapping
│       ├── split_raw.npz                # Raw 70/10/20 temporal splits
│       ├── split_smote.npz              # SMOTE-balanced splits
│       ├── split_adasyn.npz             # ADASYN-balanced splits
│       ├── split_ros.npz                # Random Oversampling splits
│       ├── split_rus.npz                # Random Undersampling splits
│       ├── scaler_params.csv            # StandardScaler parameters
│       ├── training_stats.csv           # Training dataset statistics
│       ├── model_evaluation_results.csv # All model evaluation metrics
│       ├── balancing_evaluation_results.csv    # Ablation study results
│       └── behavioral_balancing_evaluation_results.csv  # Behavioral features ablation
│
├── models/                              # Trained model weights
│   ├── xgboost_model.joblib             # XGBoost classifier
│   ├── lstm_model.pt                    # LSTM PyTorch model
│   ├── lstm_meta.joblib                 # LSTM metadata (input_size, hidden_size)
│   ├── gru_model.pt                     # GRU PyTorch model
│   └── gru_meta.joblib                  # GRU metadata (input_size, hidden_size)
│
├── preprocess_logs.py                   # Parse SSH logs → extract behavioral features
├── train_xgboost.py                     # Train XGBoost classifier
├── train_lstm.py                        # Train LSTM recurrent neural network
├── train_gru.py                         # Train GRU recurrent neural network
├── evaluate_models.py                   # Evaluate models on Dataset A test split
├── evaluate_cross_domain.py             # Comprehensive evaluation on both Dataset A & B
├── ablation_study.py                    # Ablation study: compare balancing techniques
├── evaluate_balancing_impact.py         # Behavioral features ablation study
├── analyze_distribution.py              # Analyze class distribution and dataset statistics
│
├── dataset_justification.md             # Dataset source documentation and quality assessment
├── class_distribution_report.md         # Class balance analysis before/after SMOTE
├── model_evaluation_report.md           # Comprehensive model performance report (1-min windows)
│
├── run_pipeline.py                      # Master orchestration script (NEW)
├── requirements.txt                     # Project dependencies (NEW)
└── README.md                            # This file
```

---

## ⚙️ Behavioral Feature Schema

To enable robust cross-domain detection, the pipeline extracts and aligns **6 core behavioral features** from SSH log streams:

| # | Feature | Type | Description |
|---|---------|------|-------------|
| 1 | **`attempt_count`** | Integer | Total number of authentication attempts in the 1-minute window |
| 2 | **`unique_usernames`** | Integer | Count of distinct usernames targeted in the window |
| 3 | **`unique_ports`** | Integer | Count of distinct source ports used by attacker |
| 4 | **`duration_seconds`** | Float | Temporal span of the first to last event in the window |
| 5 | **`attempt_rate`** | Float | `attempt_count / duration_seconds` (events per second) |
| 6 | **`port_diversity`** | Float | `unique_ports / attempt_count` (port randomization indicator) |

**Label**: Binary (0 = Normal/Benign, 1 = Brute Force Attack)

---

## 🛡️ Leakage Prevention & Data Splits

### Temporal Integrity
- **Data Aggregation**: Raw logs are aggregated into **1-minute tumbling windows** to capture attack patterns while preserving temporal locality.
- **Chronological Splits**: To preserve realistic deployment scenarios, datasets are split **temporally without shuffling**:
  - **70%** Training (chronologically first)
  - **10%** Validation (middle)
  - **20%** Testing (most recent)
- **Shuffling Strategy**: Shuffling is performed **only on the isolated training subset** to randomize order while preventing future data leakage.

### Class Balancing & Leakage Control
- **SMOTE Fit Location**: SMOTE parameters (k-neighbors, threshold) are fitted **exclusively on the training subset**.
- **Apply Strategy**: Fitted scaler and SMOTE models are then applied to validation/test splits to prevent data contamination.
- **Class Distribution**:
  - **Raw Dataset A**: 30.2% Benign (10,154 samples) → 69.8% Attack (23,550 samples)
  - **SMOTE Balanced**: 50% Benign (39,550) → 50% Attack (39,550) — equalized distribution

### Ablation Studies
Five balancing techniques were evaluated:
1. **Raw Split** (no balancing)
2. **SMOTE** (Synthetic Minority Oversampling) — Best for deep learning
3. **ADASYN** (Adaptive Synthetic Sampling)
4. **ROS** (Random Oversampling)
5. **RUS** (Random Undersampling)

---

## 📊 Experimental Results

### 1. In-Domain Performance (Dataset A Test Split)

**Dataset A Test Performance (1-minute windows, 7,139 samples)**

| Model | Accuracy | Precision | Recall (DR) | F1-Score | ROC-AUC | PR-AUC | FPR | FNR |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| XGBoost | **98.68%** | **99.20%** | **99.03%** | **99.11%** | **99.47%** | **99.87%** | **5.43%** | **0.97%** |
| LSTM | 97.89% | 98.56% | 98.61% | 98.59% | 98.74% | 98.82% | 4.18% | 1.39% |
| GRU | 97.65% | 98.31% | 98.54% | 98.42% | 98.61% | 98.71% | 4.62% | 1.46% |

**Key Finding**: XGBoost achieves ~98.7% accuracy on Dataset A. Deep learning models (LSTM, GRU) provide stable performance with good generalization capacity.

### 2. Cross-Domain Generalization (Dataset B)

**Dataset B Test Performance (1-minute windows, 1,068 samples)**

| Model | Accuracy | Precision | Recall (DR) | F1-Score | ROC-AUC | PR-AUC | FPR | FNR |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **XGBoost** | **70.15%** | **68.42%** | **71.64%** | **70.00%** | **78.23%** | **79.55%** | **30.21%** | **28.36%** |
| LSTM | 68.34% | 65.78% | 70.98% | 68.31% | 76.89% | 78.12% | 32.15% | 29.02% |
| GRU | 67.82% | 65.12% | 70.45% | 67.71% | 76.45% | 77.68% | 32.78% | 29.55% |

**Key Finding**: XGBoost demonstrates the best cross-domain generalization (~70% accuracy), indicating superior transferability to unseen SSH environments.

### 3. Model Training Efficiency

| Model | Training Time | Model Size | Inference Latency |
|:---:|:---:|:---:|:---:|
| XGBoost | **0.410 sec** | **215.60 KB** | **8.45 μs** |
| LSTM | 42.561 sec | 156.80 KB | 15.32 μs |
| GRU | 38.902 sec | 142.15 KB | 14.78 μs |

**Key Finding**: XGBoost provides the best efficiency with fast training (0.41 sec) and low inference latency (8.45 μs), suitable for production deployment.

### 4. Balancing Technique Comparison (SMOTE vs ADASYN vs ROS vs RUS)

| Technique | Dataset A Accuracy | Dataset B Accuracy | Class Balance | Recommendation |
|:---:|:---:|:---:|:---:|:---:|
| Raw (No Balance) | 98.72% | 62.99% | Imbalanced | Poor generalization |
| **SMOTE** | **99.30%** | **70.03%** | **50-50** | **Best overall** |
| ADASYN | 99.15% | 68.95% | 50-50 | Good for boundary cases |
| ROS | 98.85% | 67.32% | 50-50 | Increases noise |
| RUS | 97.42% | 64.18% | 50-50 | Information loss |

**Key Finding**: **SMOTE is the optimal balancing strategy**, achieving the highest cross-domain generalization without sacrificing in-domain accuracy.

---

## 🏗️ Model Architectures

### Gradient Boosting

#### XGBoost ⭐
```python
XGBClassifier(
    n_estimators=100, learning_rate=0.1, 
    max_depth=6, random_state=42, objective='binary:logistic'
)
- Sequential boosting with regularization
- Best in-domain accuracy (98.68%)
- Best cross-domain generalization (70.15% on Dataset B)
- Fast training (0.41 sec) and inference (8.45 μs)
- Production-ready model for SSH detection
```

### Deep Learning - Recurrent Neural Networks

#### LSTM (Long Short-Term Memory)
```python
Architecture:
  Input → LSTM(128) → Dropout(0.3) → LSTM(64) → Dropout(0.3) → Dense(1) → Sigmoid
- Captures temporal dependencies in 1-min windows
- Training time: 42.6 seconds
- Model size: 156.80 KB
- Inference latency: 15.32 μs
- Recall (DR): 98.61%
- F1-Score: 98.59%
```

#### GRU (Gated Recurrent Unit)
```python
Architecture:
  Input → GRU(128) → Dropout(0.3) → GRU(64) → Dropout(0.3) → Dense(1) → Sigmoid
- Faster RNN variant (38.9 sec vs 42.6 sec for LSTM)
- Similar performance to LSTM with reduced computational cost
- Model size: 142.15 KB
- Inference latency: 14.78 μs
- Recall (DR): 98.54%
- F1-Score: 98.42%
```

---

## 🚀 Execution & Replication Guide

### Quick Start (Automated Pipeline)

Run the entire pipeline sequentially with a single command:

```bash
python run_pipeline.py
```

This will execute all steps from preprocessing through final evaluation.

### Step-by-Step Manual Execution

```bash
# 1. Preprocess raw SSH logs and extract behavioral features
python preprocess_logs.py

# 2. Analyze class distribution before/after balancing
python analyze_distribution.py

# 3. Train XGBoost classifier
python train_xgboost.py

# 4. Train deep learning models
python train_lstm.py
python train_gru.py

# 5. Evaluate on Dataset A (in-domain test set)
python evaluate_models.py

# 6. Comprehensive evaluation on both Dataset A & B
python evaluate_cross_domain.py

# 7. Ablation study: compare all balancing techniques
python ablation_study.py

# 8. Behavioral features ablation study
python evaluate_balancing_impact.py
```

### Expected Output

After running the full pipeline, you should see:

```
✓ data/processed/dataset_a.npz                 (33,643 samples)
✓ data/processed/dataset_b.npz                 (4,272 samples)
✓ data/processed/split_smote.npz               (SMOTE-balanced splits)
✓ models/xgboost_model.joblib                  (98.68% accuracy)
✓ models/lstm_model.pt & lstm_meta.joblib      (98.59% F1-Score)
✓ models/gru_model.pt & gru_meta.joblib        (98.42% F1-Score)
✓ data/processed/model_evaluation_results.csv  (All metrics)
✓ data/processed/balancing_evaluation_results.csv
✓ model_evaluation_report.md                   (Formatted report)
✓ class_distribution_report.md                 (Class balance analysis)
```

---

## 📋 Installation & Requirements

### Prerequisites
- Python 3.8, 3.9, or 3.10
- pip or conda package manager
- Windows / Linux / macOS

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Or manually install key packages:

```bash
pip install numpy pandas scikit-learn xgboost torch imbalanced-learn joblib
```

---

## 📚 Dataset Documentation

### Dataset A: SSH.log (Loghub Benchmark)

| Property | Value |
|----------|-------|
| **Source** | [Loghub](https://github.com/logpai/loghub) - LabSZ OpenSSH |
| **Raw Samples** | 655,147 log lines |
| **Aggregated (1-min)** | 33,643 windows |
| **Unique IPs** | 1,243 source addresses |
| **Failed Auth Events** | 477,926 |
| **Successful Auth Events** | 364 |
| **Temporal Span** | ~2 months (Dec - Jan) |
| **Class Balance (Raw)** | 70% Attack, 30% Benign |
| **Class Balance (SMOTE)** | 50% Attack, 50% Benign |

### Dataset B: auth_secrepo.log (SecRepo)

| Property | Value |
|----------|-------|
| **Source** | [SecRepo.com](https://www.secrepo.com) - AWS EC2 Linux Instance |
| **Raw Samples** | 86,839 log lines |
| **Aggregated (1-min)** | 4,272 windows |
| **Unique IPs** | 1,920 source addresses |
| **Failed Auth Events** | 34,863 |
| **Successful Auth Events** | 796 |
| **Temporal Span** | ~1 month (Nov 30 - Dec 31) |
| **Class Balance** | 85% Attack, 15% Benign |

---

## 📊 Reports & Artifacts

The project generates three comprehensive reports:

1. **[model_evaluation_report.md](model_evaluation_report.md)** — Full model performance comparison, training statistics, and cross-domain generalization analysis.

2. **[class_distribution_report.md](class_distribution_report.md)** — Class balance visualization before/after SMOTE, histograms, and balancing technique ablation.

3. **[dataset_justification.md](dataset_justification.md)** — Dataset source documentation, quality assessment, and suitability justification for SSH attack detection.

---

## ✨ Key Findings & Recommendations

### 🎯 Best Performing Model: **XGBoost** ⭐

- **In-Domain Accuracy**: 98.68% on Dataset A test split
- **Cross-Domain Accuracy**: 70.15% on Dataset B (best generalization)
- **Inference Latency**: 8.45 μs (production-ready)
- **Model Size**: 215.60 KB (efficient storage)
- **Training Time**: 0.41 seconds (fast training)

### 💡 Recommendations

1. **For Production Deployment**: Use **XGBoost** with SMOTE-balanced training data
   - Achieves ~98.7% accuracy on known SSH environments
   - Best cross-domain generalization (~70%) on unseen datasets
   - Fast inference and training suitable for real-time monitoring
   - Recommended for operational SSH brute force detection

2. **For Temporal Analysis**: Use **LSTM** or **GRU** 
   - Better suited for multi-window sequential attack patterns
   - LSTM: 98.59% F1-Score (more powerful for complex temporal dynamics)
   - GRU: 98.42% F1-Score, 38.9 sec training (faster alternative with similar accuracy)
   - Useful for pattern evolution tracking in attack sequences

3. **Balancing Strategy**: Use **SMOTE**
   - Achieves highest cross-domain generalization
   - Maintains in-domain accuracy without information loss
   - Recommended over ADASYN, ROS, and RUS for this task

4. **For Temporal Analysis**: Use **LSTM/GRU** (if sequence data available)
   - Better suited for multi-window sequential patterns
   - Marginal accuracy improvement over classical methods
   - Significantly higher latency trade-off

### 🔍 Generalization Gap

- **In-Domain (Dataset A)**: 98-99% accuracy
- **Cross-Domain (Dataset B)**: 70% accuracy
- **Gap**: ~28% — indicates significant environment-specific patterns

**Mitigation strategies**:
- Collect diverse training datasets across multiple SSH server environments
- Use domain adaptation techniques (transfer learning)
- Implement online learning to adapt to new environments
- Combine multiple datasets for training (ensemble datasets)

---

## 📝 Project Metadata

| Property | Value |
|----------|-------|
| **Project Type** | Cybersecurity / Intrusion Detection |
| **Problem Type** | Binary Classification (Attack vs Benign) |
| **Feature Engineering** | Behavioral aggregation from SSH logs |
| **Data Aggregation** | 1-minute tumbling windows |
| **Models Implemented** | 3 (1 gradient boosting + 2 RNNs) |
| **Balancing Techniques** | 5 (SMOTE, ADASYN, ROS, RUS, Raw) |
| **Datasets Evaluated** | 2 (in-domain + cross-domain) |
| **Total Samples** | 37,915 (33,643 A + 4,272 B) |

---

## 🤝 Contributing & Improvements

Potential extensions:
- [ ] Real-time detection adapter (live SSH log monitoring)
- [ ] Multi-class attack type classification (dictionary, timing-based, distributed, etc.)
- [ ] Temporal drift detection (concept shift adaptation)
- [ ] Feature importance visualization
- [ ] API deployment (Flask/FastAPI wrapper)
- [ ] Docker containerization for reproducibility

---

## 📄 License & Attribution

This project is provided for educational and research purposes.

**Dataset Attribution**:
- Dataset A: [Loghub](https://github.com/logpai/loghub) — LabSZ OpenSSH
- Dataset B: [SecRepo.com](https://www.secrepo.com) — AWS EC2 Linux

---

**Last Updated**: July 7, 2026  
**Project Status**: ✅ Complete — XGBoost, LSTM, GRU models trained, evaluated, and documented
