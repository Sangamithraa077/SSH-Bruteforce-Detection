"""
evaluate_all.py  —  Evaluate XGBoost, LSTM and GRU models
Metrics : Accuracy, Precision, Recall, F1, ROC-AUC, PR-AUC,
          FPR, FNR, Confusion Matrix, Inference Latency
Tests   : Dataset A (in-domain test) + Dataset B (external generalisation)
"""
import os, time, joblib
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset
from sklearn.metrics import (accuracy_score, precision_score, recall_score,
                             f1_score, roc_auc_score, average_precision_score,
                             confusion_matrix)

PROCESSED_DIR = r"c:\SSH_BRUTEFORCE_DETECTION\data\processed"
MODELS_DIR    = r"c:\SSH_BRUTEFORCE_DETECTION\models"

BEHAVIORAL_FEATURES = [
    'attempt_count', 'unique_usernames', 'unique_ports',
    'duration_seconds', 'attempt_rate', 'port_diversity'
]
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# ── Pytorch Model Definitions (must match train scripts) ──────
class LSTMClassifier(nn.Module):
    def __init__(self, input_size, hidden_size, hidden_size2):
        super().__init__()
        self.lstm1   = nn.LSTM(input_size, hidden_size, batch_first=True)
        self.drop1   = nn.Dropout(0.3)
        self.lstm2   = nn.LSTM(hidden_size, hidden_size2, batch_first=True)
        self.drop2   = nn.Dropout(0.3)
        self.fc      = nn.Linear(hidden_size2, 1)
        self.sigmoid = nn.Sigmoid()

    def forward(self, x):
        out, _ = self.lstm1(x)
        out    = self.drop1(out)
        out, _ = self.lstm2(out)
        out    = self.drop2(out)
        out    = out[:, -1, :]
        return self.sigmoid(self.fc(out)).squeeze(1)


class GRUClassifier(nn.Module):
    def __init__(self, input_size, hidden_size, hidden_size2):
        super().__init__()
        self.gru1    = nn.GRU(input_size, hidden_size, batch_first=True)
        self.drop1   = nn.Dropout(0.3)
        self.gru2    = nn.GRU(hidden_size, hidden_size2, batch_first=True)
        self.drop2   = nn.Dropout(0.3)
        self.fc      = nn.Linear(hidden_size2, 1)
        self.sigmoid = nn.Sigmoid()

    def forward(self, x):
        out, _ = self.gru1(x)
        out    = self.drop1(out)
        out, _ = self.gru2(out)
        out    = self.drop2(out)
        out    = out[:, -1, :]
        return self.sigmoid(self.fc(out)).squeeze(1)


# ── Helpers ───────────────────────────────────────────────────
def get_indices():
    fn = pd.read_csv(os.path.join(PROCESSED_DIR, "feature_names.csv"))['feature_name'].tolist()
    return [fn.index(f) for f in BEHAVIORAL_FEATURES]


def compute_metrics(y_true, y_pred, y_prob, latency_s, n_samples):
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()
    return {
        'Accuracy'   : accuracy_score(y_true, y_pred),
        'Precision'  : precision_score(y_true, y_pred, zero_division=0),
        'Recall_DR'  : recall_score(y_true, y_pred),
        'F1'         : f1_score(y_true, y_pred, zero_division=0),
        'ROC_AUC'    : roc_auc_score(y_true, y_prob),
        'PR_AUC'     : average_precision_score(y_true, y_prob),
        'FPR'        : fp / (fp + tn) if (fp + tn) > 0 else 0,
        'FNR'        : fn / (fn + tp) if (fn + tp) > 0 else 0,
        'TN'         : tn, 'FP': fp, 'FN': fn, 'TP': tp,
        'Latency_us' : (latency_s / n_samples) * 1e6
    }


def predict_sklearn(clf, X):
    t0   = time.time()
    pred = clf.predict(X)
    prob = clf.predict_proba(X)[:, 1]
    return pred, prob, time.time() - t0


def predict_torch(model, X):
    model.eval()
    Xt = torch.tensor(X[:, np.newaxis, :], dtype=torch.float32).to(DEVICE)
    with torch.no_grad():
        t0   = time.time()
        prob = model(Xt).cpu().numpy()
        lat  = time.time() - t0
    pred = (prob >= 0.5).astype(int)
    return pred, prob, lat


def load_torch(model_class, pt_path, meta_path):
    meta  = joblib.load(meta_path)
    model = model_class(**meta).to(DEVICE)
    model.load_state_dict(torch.load(pt_path, map_location=DEVICE, weights_only=True))
    model.eval()
    return model


# ── Main Evaluation ───────────────────────────────────────────
def evaluate_all():
    print("=" * 56)
    print("Step 4 (Updated): Evaluating XGBoost | LSTM | GRU")
    print("=" * 56)

    idx = get_indices()

    # Load datasets
    raw  = np.load(os.path.join(PROCESSED_DIR, "split_raw.npz"))
    X_te = raw['X_test'][:, idx];  y_te = raw['y_test']

    db   = np.load(os.path.join(PROCESSED_DIR, "dataset_b.npz"))
    X_b  = db['X'][:, idx];        y_b  = db['y']

    records = []

    # ── 1. XGBoost ────────────────────────────────────────────
    print("\n[1/3] XGBoost ...")
    xgb_path = os.path.join(MODELS_DIR, "xgboost_model.joblib")
    if os.path.exists(xgb_path):
        xgb = joblib.load(xgb_path)
        p, pr, lat = predict_sklearn(xgb, X_te)
        m_te = compute_metrics(y_te, p, pr, lat, len(X_te))
        p, pr, lat = predict_sklearn(xgb, X_b)
        m_b  = compute_metrics(y_b,  p, pr, lat, len(X_b))
        records.append(("XGBoost", m_te, m_b))
        print("  Done.")
    else:
        print("  xgboost_model.joblib not found — run train_xgboost.py first.")

    # ── 2. LSTM ───────────────────────────────────────────────
    print("\n[2/3] LSTM ...")
    lstm_pt   = os.path.join(MODELS_DIR, "lstm_model.pt")
    lstm_meta = os.path.join(MODELS_DIR, "lstm_meta.joblib")
    if os.path.exists(lstm_pt):
        lstm = load_torch(LSTMClassifier, lstm_pt, lstm_meta)
        p, pr, lat = predict_torch(lstm, X_te)
        m_te = compute_metrics(y_te, p, pr, lat, len(X_te))
        p, pr, lat = predict_torch(lstm, X_b)
        m_b  = compute_metrics(y_b,  p, pr, lat, len(X_b))
        records.append(("LSTM", m_te, m_b))
        print("  Done.")
    else:
        print("  lstm_model.pt not found — run train_lstm.py first.")

    # ── 3. GRU ────────────────────────────────────────────────
    print("\n[3/3] GRU ...")
    gru_pt   = os.path.join(MODELS_DIR, "gru_model.pt")
    gru_meta = os.path.join(MODELS_DIR, "gru_meta.joblib")
    if os.path.exists(gru_pt):
        gru = load_torch(GRUClassifier, gru_pt, gru_meta)
        p, pr, lat = predict_torch(gru, X_te)
        m_te = compute_metrics(y_te, p, pr, lat, len(X_te))
        p, pr, lat = predict_torch(gru, X_b)
        m_b  = compute_metrics(y_b,  p, pr, lat, len(X_b))
        records.append(("GRU", m_te, m_b))
        print("  Done.")
    else:
        print("  gru_model.pt not found — run train_gru.py first.")

    # ── Print tables ──────────────────────────────────────────
    header = "| Model | Acc | Prec | Recall(DR) | F1 | ROC-AUC | PR-AUC | FPR | FNR | Latency |"
    sep    = "|---|---|---|---|---|---|---|---|---|---|"

    print("\n\n=== Dataset A (SSH.log) — In-Domain Test ===")
    print(header); print(sep)
    for name, m, _ in records:
        print(f"| {name} | {m['Accuracy']:.5f} | {m['Precision']:.5f} | "
              f"{m['Recall_DR']:.5f} | {m['F1']:.5f} | {m['ROC_AUC']:.5f} | "
              f"{m['PR_AUC']:.5f} | {m['FPR']:.5f} | {m['FNR']:.5f} | "
              f"{m['Latency_us']:.2f} us |")

    print("\n=== Confusion Matrices — Dataset A Test ===")
    for name, m, _ in records:
        print(f"  [{name}]  TN={m['TN']}  FP={m['FP']}  FN={m['FN']}  TP={m['TP']}")

    print("\n\n=== Dataset B (auth_secrepo.log) — External Generalisation ===")
    print(header); print(sep)
    for name, _, m in records:
        print(f"| {name} | {m['Accuracy']:.5f} | {m['Precision']:.5f} | "
              f"{m['Recall_DR']:.5f} | {m['F1']:.5f} | {m['ROC_AUC']:.5f} | "
              f"{m['PR_AUC']:.5f} | {m['FPR']:.5f} | {m['FNR']:.5f} | "
              f"{m['Latency_us']:.2f} us |")

    print("\n=== Confusion Matrices — Dataset B ===")
    for name, _, m in records:
        print(f"  [{name}]  TN={m['TN']}  FP={m['FP']}  FN={m['FN']}  TP={m['TP']}")

    # Save CSV
    rows = []
    for name, m_te, m_b in records:
        rows.append({**{'Model': name},
                     **{f'Test_{k}': v for k, v in m_te.items()},
                     **{f'B_{k}':    v for k, v in m_b.items()}})
    pd.DataFrame(rows).to_csv(
        os.path.join(PROCESSED_DIR, "model_evaluation_results.csv"), index=False)
    print("\nResults saved to data/processed/model_evaluation_results.csv")


if __name__ == "__main__":
    evaluate_all()
