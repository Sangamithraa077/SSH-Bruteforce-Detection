import os
import time
import joblib
import numpy as np
import pandas as pd
from sklearn.tree import DecisionTreeClassifier
from lightgbm import LGBMClassifier
from sklearn.neural_network import MLPClassifier

# Configurations
PROCESSED_DIR = r"c:\SSH_BRUTEFORCE_DETECTION\data\processed"
MODELS_DIR = r"c:\SSH_BRUTEFORCE_DETECTION\models"
os.makedirs(MODELS_DIR, exist_ok=True)

def train_models():
    print("==================================================")
    print("Step 3: Model Training")
    print("==================================================")
    
    # 1. Load data
    print("Loading SMOTE-balanced training split...")
    train_data = np.load(os.path.join(PROCESSED_DIR, "split_smote.npz"))
    X_train_full = train_data['X_train']
    y_train = train_data['y_train']
    
    # 2. Get behavioral feature indices
    feature_names = pd.read_csv(os.path.join(PROCESSED_DIR, "feature_names.csv"))['feature_name'].tolist()
    behavioral_features = [
        'attempt_count', 'unique_usernames', 'unique_ports', 'duration_seconds', 'attempt_rate', 'port_diversity'
    ]
    behavioral_indices = [feature_names.index(f) for f in behavioral_features]
    
    X_train = X_train_full[:, behavioral_indices]
    print(f"Training set shape: {X_train.shape}")
    print(f"Features: {behavioral_features}")
    print(f"Class distribution: Benign={np.sum(y_train==0)}, Attack={np.sum(y_train==1)}")
    print()
    
    # Define models
    models = {
        'Baseline_DecisionTree': DecisionTreeClassifier(max_depth=5, random_state=42),
        'Boosting_LightGBM': LGBMClassifier(n_estimators=100, random_state=42, verbose=-1, n_jobs=-1),
        'DeepLearning_MLP': MLPClassifier(hidden_layer_sizes=(64, 32), max_iter=500, random_state=42)
    }
    
    training_stats = []
    
    # Train and save each model
    for name, clf in models.items():
        print(f"Training {name}...")
        start_time = time.time()
        clf.fit(X_train, y_train)
        elapsed_time = time.time() - start_time
        print(f"  Training completed in {elapsed_time:.4f} seconds.")
        
        # Save model to disk
        model_path = os.path.join(MODELS_DIR, f"{name.lower()}.joblib")
        joblib.dump(clf, model_path)
        
        # Get file size
        file_size_kb = os.path.getsize(model_path) / 1024.0
        print(f"  Model saved to {model_path} ({file_size_kb:.2f} KB).")
        print()
        
        training_stats.append({
            'Model_Name': name,
            'Training_Time_Sec': elapsed_time,
            'Model_Size_KB': file_size_kb
        })
        
    df_stats = pd.DataFrame(training_stats)
    df_stats.to_csv(os.path.join(PROCESSED_DIR, "training_stats.csv"), index=False)
    print("Training stats saved successfully!")

if __name__ == "__main__":
    train_models()
