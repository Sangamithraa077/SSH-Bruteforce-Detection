import os
import numpy as np

PROCESSED_DIR = r"c:\SSH_BRUTEFORCE_DETECTION\data\processed"

def analyze_distributions():
    print("==================================================")
    print("Class Distribution Analysis for SSH Brute Force Detection")
    print("==================================================")
    
    # 1. Dataset A
    if os.path.exists(os.path.join(PROCESSED_DIR, "split_raw.npz")):
        data_a = np.load(os.path.join(PROCESSED_DIR, "split_raw.npz"))
        y_train = data_a['y_train']
        y_val = data_a['y_val']
        y_test = data_a['y_test']
        
        for name, y in [("Dataset A - Train", y_train), ("Dataset A - Val", y_val), ("Dataset A - Test", y_test)]:
            total = len(y)
            benign = np.sum(y == 0)
            attack = np.sum(y == 1)
            benign_pct = (benign / total) * 100
            attack_pct = (attack / total) * 100
            ratio = benign / attack if attack > 0 else float('inf')
            
            # Imbalance Severity Evaluation
            # Standard guidelines (e.g. Google Developers / ML guides):
            # - Mild: Minority class is 20-40% of the dataset
            # - Moderate: Minority class is 1-20% of the dataset
            # - Extreme: Minority class is <1% of the dataset
            minority_pct = min(benign_pct, attack_pct)
            if minority_pct < 1:
                severity = "Extreme Imbalance (<1% minority)"
            elif minority_pct < 20:
                severity = "Moderate Imbalance (1-20% minority)"
            else:
                severity = "Mild Imbalance (20-40% minority)"
                
            print(f"{name}:")
            print(f"  Total Samples: {total}")
            print(f"  Benign Samples: {benign} ({benign_pct:.2f}%)")
            print(f"  Attack Samples: {attack} ({attack_pct:.2f}%)")
            print(f"  Class Ratio (Benign:Attack): {ratio:.4f} (or 1:{1/ratio:.2f})")
            print(f"  Imbalance Severity: {severity}")
            print()
            
    # 2. Dataset B (External Evaluation)
    if os.path.exists(os.path.join(PROCESSED_DIR, "dataset_b.npz")):
        data_b = np.load(os.path.join(PROCESSED_DIR, "dataset_b.npz"))
        y_b = data_b['y']
        
        total = len(y_b)
        benign = np.sum(y_b == 0)
        attack = np.sum(y_b == 1)
        benign_pct = (benign / total) * 100
        attack_pct = (attack / total) * 100
        ratio = benign / attack if attack > 0 else float('inf')
        
        minority_pct = min(benign_pct, attack_pct)
        if minority_pct < 1:
            severity = "Extreme Imbalance (<1% minority)"
        elif minority_pct < 20:
            severity = "Moderate Imbalance (1-20% minority)"
        else:
            severity = "Mild Imbalance (20-40% minority)"
            
        print("Dataset B (External Evaluation - auth_secrepo):")
        print(f"  Total Samples: {total}")
        print(f"  Benign Samples: {benign} ({benign_pct:.2f}%)")
        print(f"  Attack Samples: {attack} ({attack_pct:.2f}%)")
        print(f"  Class Ratio (Benign:Attack): {ratio:.4f} (or 1:{1/ratio:.2f})")
        print(f"  Imbalance Severity: {severity}")
        print()

if __name__ == "__main__":
    analyze_distributions()
