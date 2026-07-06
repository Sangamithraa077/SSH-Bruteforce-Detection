# SSH Brute Force Attack Detection using Ensemble Machine Learning

> 🎓 **Academic Project**  
> Cybersecurity detection using ensemble machine learning with cross-domain generalization.

[![Python Version](https://img.shields.io/badge/python-3.8%20%7C%203.9%20%7C%203.10-blue)](https://www.python.org/) [![Scikit-Learn](https://img.shields.io/badge/scikit--learn-1.3%2B-orange)](https://scikit-learn.org/) [![PyTorch](https://img.shields.io/badge/PyTorch-2.0%2B-red)](https://pytorch.org/) [![XGBoost](https://img.shields.io/badge/XGBoost-2.0%2B-red)](https://xgboost.readthedocs.io/)

---

## 📖 Project Objective

SSH brute force attack detection models trained on single datasets suffer from overfitting and poor real-world performance. This project aims to:

1. Train robust classifiers on SSH logs (**Dataset A** - Loghub SSH.log: 655,147 samples)
2. Validate generalization on unseen real-world logs (**Dataset B** - SecRepo auth_secrepo.log: 86,839 samples)
3. Use **6 behavioral features** extracted from SSH logs for cross-domain detection
4. Compare gradient boosting (XGBoost) with deep learning (LSTM, GRU)
5. Evaluate multiple balancing techniques (SMOTE, ADASYN, ROS, RUS)

---

## 📂 Project Directory Structure

```
SSH_BRUTEFORCE_DETECTION/
├── data/                                    # Datasets and processed outputs
│   ├── SSH.log, auth_secrepo.log           # Raw datasets (655K & 86K samples)
│   └── processed/                          # Aggregated, split, and balanced data
│
├── models/                                  # Trained model weights
│   ├── xgboost_model.joblib                # XGBoost classifier
│   ├── lstm_model.pt, lstm_meta.joblib    # LSTM model + metadata
│   └── gru_model.pt, gru_meta.joblib      # GRU model + metadata
│
├── preprocess_logs.py                      # Parse logs & extract 6 behavioral features
├── train_xgboost.py                        # XGBoost training
├── train_lstm.py, train_gru.py            # Deep learning training
├── evaluate_models.py                      # Dataset A evaluation
├── evaluate_cross_domain.py                # Dataset A + B evaluation
├── ablation_study.py                       # Balancing technique comparison
├── analyze_distribution.py                 # Class distribution analysis
├── run_pipeline.py                         # Master orchestration script
├── requirements.txt                        # Dependencies
│
├── README.md                               # This file
├── model_evaluation_report.md              # Performance metrics
├── class_distribution_report.md            # Class balance analysis
└── dataset_justification.md                # Dataset documentation
```

---

## ⚙️ Behavioral Feature Schema

6 behavioral features extracted from 1-minute SSH log windows:

| # | Feature | Description |
|---|---------|-------------|
| 1 | `attempt_count` | Authentication attempts in window |
| 2 | `unique_usernames` | Distinct usernames targeted |
| 3 | `unique_ports` | Source ports used |
| 4 | `duration_seconds` | First to last event span |
| 5 | `attempt_rate` | Events per second |
| 6 | `port_diversity` | Source port randomization indicator |

**Label**: Binary (0=Benign, 1=Attack)

---

## 🛡️ Data Integrity & Balancing

- **Temporal Splits**: 70% training, 10% validation, 20% testing (chronological order, no shuffling)
- **Leakage Prevention**: SMOTE fit only on training set, applied to validation/test
- **Class Balance**: SMOTE brings raw split from 70:30 to 50:50 attack:benign ratio
- **Techniques Evaluated**: SMOTE (best), ADASYN, ROS, RUS, Raw

---

## 📊 Experimental Results

### Dataset A (In-Domain) — 7,139 test samples

| Model | Accuracy | Precision | Recall | F1-Score | ROC-AUC |
|:---:|:---:|:---:|:---:|:---:|:---:|
| **XGBoost** | **98.68%** | 99.20% | 99.03% | 99.11% | 99.47% |
| LSTM | 97.89% | 98.56% | 98.61% | 98.59% | 98.74% |
| GRU | 97.65% | 98.31% | 98.54% | 98.42% | 98.61% |

### Dataset B (Cross-Domain) — 1,068 test samples

| Model | Accuracy | Precision | Recall | F1-Score | ROC-AUC |
|:---:|:---:|:---:|:---:|:---:|:---:|
| **XGBoost** | **70.15%** | 68.42% | 71.64% | 70.00% | 78.23% |
| LSTM | 68.34% | 65.78% | 70.98% | 68.31% | 76.89% |
| GRU | 67.82% | 65.12% | 70.45% | 67.71% | 76.45% |

**Key Finding**: XGBoost achieves best in-domain accuracy (98.68%) and best cross-domain generalization (70.15% on unseen SSH environment).

### Model Efficiency

| Model | Training Time | Model Size | Inference Latency |
|:---:|:---:|:---:|:---:|
| XGBoost | 0.41 sec | 215.60 KB | 8.45 μs |
| LSTM | 42.6 sec | 156.80 KB | 15.32 μs |
| GRU | 38.9 sec | 142.15 KB | 14.78 μs |

---

## 🏗️ Model Architectures

### XGBoost ⭐ (Best Model)
```python
XGBClassifier(n_estimators=100, learning_rate=0.1, max_depth=6)
- Fastest training (0.41 sec)
- Best in-domain accuracy (98.68%)
- Best cross-domain generalization (70.15%)
- Production-ready for real-time detection
```

### LSTM (Temporal Learning)
```python
Input → LSTM(128) → Dropout(0.3) → LSTM(64) → Dropout(0.3) → Dense(1) → Sigmoid
- Captures temporal attack patterns
- F1-Score: 98.59%
- Inference: 15.32 μs
```

### GRU (Fast Temporal)
```python
Input → GRU(128) → Dropout(0.3) → GRU(64) → Dropout(0.3) → Dense(1) → Sigmoid
- Faster RNN variant (38.9 sec training)
- F1-Score: 98.42%
- Inference: 14.78 μs
```

---

## 🚀 Quick Start

### Automated Pipeline
```bash
python run_pipeline.py  # Runs all 8 steps automatically
```

### Manual Execution
```bash
python preprocess_logs.py               # 1. Preprocessing
python analyze_distribution.py          # 2. Distribution analysis
python train_xgboost.py                 # 3. Train XGBoost
python train_lstm.py && python train_gru.py  # 4. Train deep learning
python evaluate_models.py               # 5. Evaluate Dataset A
python evaluate_cross_domain.py         # 6. Evaluate Dataset A+B
python ablation_study.py                # 7. Ablation study
python evaluate_balancing_impact.py     # 8. Feature ablation
```

---

## 📋 Installation

### Prerequisites
Python 3.8+ (Windows/Linux/macOS)

### Setup
```bash
pip install -r requirements.txt
```

---

## 📚 Datasets

| Property | Dataset A (Loghub) | Dataset B (SecRepo) |
|----------|:---:|:---:|
| **Samples** | 655,147 | 86,839 |
| **Windows (1-min)** | 33,643 | 4,272 |
| **Attack %** | 69.8% | 85% |
| **Source** | LabSZ OpenSSH | AWS EC2 Linux |

---

## 📊 Reports

- **[model_evaluation_report.md](model_evaluation_report.md)** — Detailed metrics & performance
- **[class_distribution_report.md](class_distribution_report.md)** — Class balance analysis
- **[dataset_justification.md](dataset_justification.md)** — Dataset documentation

---

## 💡 Key Recommendations

1. **Production Use**: Deploy **XGBoost** with SMOTE balancing
   - ~98.7% accuracy on known environments
   - ~70% generalization on unseen environments
   - Fast inference (8.45 μs)

2. **Temporal Analysis**: Use **LSTM** for sequential pattern detection
   - Better for multi-window attack evolution
   - Slightly higher inference cost (15.32 μs)

3. **Fast Alternative**: Use **GRU** for resource-constrained systems
   - Similar LSTM performance (98.42% F1)
   - 3.7 sec faster training

---

## 📝 Project Metadata

| Aspect | Value |
|--------|-------|
| **Type** | Binary Classification (Intrusion Detection) |
| **Models** | XGBoost, LSTM, GRU (3 total) |
| **Features** | 6 behavioral features from SSH logs |
| **Datasets** | 2 (in-domain + cross-domain) |
| **Samples** | 37,915 aggregated windows |
| **Balancing** | SMOTE (best), ADASYN, ROS, RUS |

---

## 🤝 Potential Extensions

- Real-time detection adapter (live SSH monitoring)
- Multi-class attack classification
- Concept drift detection
- API wrapper (Flask/FastAPI)
- Docker containerization

---

## 📄 Attribution

**Datasets**: [Loghub](https://github.com/logpai/loghub), [SecRepo.com](https://www.secrepo.com)

---

**Status**: ✅ Complete — XGBoost, LSTM, GRU models trained & evaluated  
**Updated**: July 7, 2026
