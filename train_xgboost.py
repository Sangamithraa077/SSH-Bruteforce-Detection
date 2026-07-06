import os
import time
import joblib
import numpy as np
import pandas as pd
from xgboost import XGBClassifier

# ─────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────
PROCESSED_DIR = r"c:\SSH_BRUTEFORCE_DETECTION\data\processed"
MODELS_DIR    = r"c:\SSH_BRUTEFORCE_DETECTION\models"
os.makedirs(MODELS_DIR, exist_ok=True)

BEHAVIORAL_FEATURES = [
    'attempt_count', 'unique_usernames', 'unique_ports',
    'duration_seconds', 'attempt_rate', 'port_diversity'
]

def get_feature_indices():
    feature_names = pd.read_csv(
        os.path.join(PROCESSED_DIR, "feature_names.csv")
    )['feature_name'].tolist()
    return [feature_names.index(f) for f in BEHAVIORAL_FEATURES]


def load_split(path, indices):
    data  = np.load(path)
    X     = data['X_train'][:, indices]
    y     = data['y_train']
    return X, y


def train_xgboost():
    print("=" * 50)
    print("Training Model 1: XGBoost Classifier")
    print("=" * 50)

    indices    = get_feature_indices()
    X_train, y_train = load_split(
        os.path.join(PROCESSED_DIR, "split_smote.npz"), indices
    )

    print(f"Training shape : {X_train.shape}")
    print(f"Class balance  : Benign={np.sum(y_train==0)}, Attack={np.sum(y_train==1)}")
    print()

    clf = XGBClassifier(
        n_estimators      = 300,
        max_depth         = 6,
        learning_rate     = 0.1,
        subsample         = 0.8,
        colsample_bytree  = 0.8,
        use_label_encoder = False,
        eval_metric       = 'logloss',
        random_state      = 42,
        n_jobs            = -1
    )

    t0 = time.time()
    clf.fit(X_train, y_train)
    elapsed = time.time() - t0

    path = os.path.join(MODELS_DIR, "xgboost_model.joblib")
    joblib.dump(clf, path)
    size_kb = os.path.getsize(path) / 1024

    print(f"  Training time : {elapsed:.4f} s")
    print(f"  Saved to      : {path}  ({size_kb:.2f} KB)")
    return elapsed, size_kb


if __name__ == "__main__":
    train_xgboost()
