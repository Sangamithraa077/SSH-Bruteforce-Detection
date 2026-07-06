"""
train_lstm.py  —  LSTM model for SSH Brute Force Detection
Architecture : Sequence input (each 1-min window treated as 1 time-step,
               feature vector of length 6) → LSTM(64) → Dropout(0.3)
               → LSTM(32) → Dropout(0.3) → Dense(1, sigmoid)
"""
import os, time, joblib
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset

PROCESSED_DIR = r"c:\SSH_BRUTEFORCE_DETECTION\data\processed"
MODELS_DIR    = r"c:\SSH_BRUTEFORCE_DETECTION\models"
os.makedirs(MODELS_DIR, exist_ok=True)

BEHAVIORAL_FEATURES = [
    'attempt_count', 'unique_usernames', 'unique_ports',
    'duration_seconds', 'attempt_rate', 'port_diversity'
]
INPUT_SIZE   = len(BEHAVIORAL_FEATURES)
HIDDEN_SIZE  = 64
HIDDEN_SIZE2 = 32
NUM_EPOCHS   = 30
BATCH_SIZE   = 256
LR           = 1e-3
DEVICE       = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# ── Model Definition ──────────────────────────────────────────
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
        # x: (batch, seq_len, features) — seq_len = 1 here
        out, _ = self.lstm1(x)
        out    = self.drop1(out)
        out, _ = self.lstm2(out)
        out    = self.drop2(out)
        out    = out[:, -1, :]          # last time-step
        return self.sigmoid(self.fc(out)).squeeze(1)


# ── Helpers ───────────────────────────────────────────────────
def get_indices():
    fn = pd.read_csv(os.path.join(PROCESSED_DIR, "feature_names.csv"))['feature_name'].tolist()
    return [fn.index(f) for f in BEHAVIORAL_FEATURES]


def make_loader(X, y, shuffle=True):
    # Add seq_len dimension → (N, 1, F)
    Xt = torch.tensor(X[:, np.newaxis, :], dtype=torch.float32)
    yt = torch.tensor(y, dtype=torch.float32)
    return DataLoader(TensorDataset(Xt, yt),
                      batch_size=BATCH_SIZE, shuffle=shuffle)


# ── Training Loop ─────────────────────────────────────────────
def train_lstm():
    print("=" * 50)
    print("Training Model 2: LSTM Classifier")
    print(f"Device: {DEVICE}")
    print("=" * 50)

    idx = get_indices()
    raw = np.load(os.path.join(PROCESSED_DIR, "split_smote.npz"))
    X_train = raw['X_train'][:, idx]
    y_train = raw['y_train']

    print(f"Training shape : {X_train.shape}")
    print(f"Class balance  : Benign={np.sum(y_train==0)}, Attack={np.sum(y_train==1)}\n")

    loader = make_loader(X_train, y_train)

    model     = LSTMClassifier(INPUT_SIZE, HIDDEN_SIZE, HIDDEN_SIZE2).to(DEVICE)
    criterion = nn.BCELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=LR)

    t0 = time.time()
    model.train()
    for epoch in range(1, NUM_EPOCHS + 1):
        total_loss = 0.0
        for Xb, yb in loader:
            Xb, yb = Xb.to(DEVICE), yb.to(DEVICE)
            optimizer.zero_grad()
            pred = model(Xb)
            loss = criterion(pred, yb)
            loss.backward()
            optimizer.step()
            total_loss += loss.item() * len(yb)
        avg_loss = total_loss / len(X_train)
        if epoch % 5 == 0 or epoch == 1:
            print(f"  Epoch {epoch:3d}/{NUM_EPOCHS}  loss={avg_loss:.4f}")

    elapsed = time.time() - t0

    # Save model weights + metadata for inference
    path_pt  = os.path.join(MODELS_DIR, "lstm_model.pt")
    path_meta = os.path.join(MODELS_DIR, "lstm_meta.joblib")
    torch.save(model.state_dict(), path_pt)
    joblib.dump({"input_size": INPUT_SIZE, "hidden_size": HIDDEN_SIZE,
                 "hidden_size2": HIDDEN_SIZE2}, path_meta)

    size_kb = os.path.getsize(path_pt) / 1024
    print(f"\n  Training time : {elapsed:.2f} s")
    print(f"  Saved to      : {path_pt}  ({size_kb:.2f} KB)")
    return elapsed, size_kb


if __name__ == "__main__":
    train_lstm()
