import os
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, average_precision_score

PROCESSED_DIR = r"c:\SSH_BRUTEFORCE_DETECTION\data\processed"

def evaluate_balancing():
    print("==================================================")
    print("Evaluating Data Balancing Techniques")
    print("==================================================")
    
    # Load test sets
    raw_data = np.load(os.path.join(PROCESSED_DIR, "split_raw.npz"))
    X_val = raw_data['X_val']
    y_val = raw_data['y_val']
    X_test = raw_data['X_test']
    y_test = raw_data['y_test']
    
    dataset_b = np.load(os.path.join(PROCESSED_DIR, "dataset_b.npz"))
    X_b = dataset_b['X']
    y_b = dataset_b['y']
    
    # Balancing configurations
    configs = {
        'Raw (No Balancing)': os.path.join(PROCESSED_DIR, "split_raw.npz"),
        'Random Undersampling (RUS)': os.path.join(PROCESSED_DIR, "split_rus.npz"),
        'Random Oversampling (ROS)': os.path.join(PROCESSED_DIR, "split_ros.npz"),
        'SMOTE': os.path.join(PROCESSED_DIR, "split_smote.npz"),
    }
    
    # Check if ADASYN was generated
    if os.path.exists(os.path.join(PROCESSED_DIR, "split_adasyn.npz")):
        configs['ADASYN'] = os.path.join(PROCESSED_DIR, "split_adasyn.npz")
        
    results = []
    
    for config_name, path in configs.items():
        print(f"Training classifier on configuration: {config_name}...")
        data = np.load(path)
        X_train = data['X_train']
        y_train = data['y_train']
        
        # Train Random Forest classifier
        clf = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
        clf.fit(X_train, y_train)
        
        # Evaluate on Dataset A Test
        y_pred_test = clf.predict(X_test)
        y_prob_test = clf.predict_proba(X_test)[:, 1]
        
        acc_test = accuracy_score(y_test, y_pred_test)
        prec_test = precision_score(y_test, y_pred_test)
        rec_test = recall_score(y_test, y_pred_test)
        f1_test = f1_score(y_test, y_pred_test)
        auc_test = roc_auc_score(y_test, y_prob_test)
        pr_auc_test = average_precision_score(y_test, y_prob_test)
        
        # Evaluate on Dataset B (External)
        y_pred_b = clf.predict(X_b)
        y_prob_b = clf.predict_proba(X_b)[:, 1]
        
        acc_b = accuracy_score(y_b, y_pred_b)
        prec_b = precision_score(y_b, y_pred_b)
        rec_b = recall_score(y_b, y_pred_b)
        f1_b = f1_score(y_b, y_pred_b)
        auc_b = roc_auc_score(y_b, y_prob_b)
        pr_auc_b = average_precision_score(y_b, y_prob_b)
        
        results.append({
            'Config': config_name,
            # Dataset A Test metrics
            'Test_Acc': acc_test,
            'Test_Prec': prec_test,
            'Test_Rec': rec_test,
            'Test_F1': f1_test,
            'Test_AUC': auc_test,
            'Test_PR_AUC': pr_auc_test,
            # Dataset B metrics
            'B_Acc': acc_b,
            'B_Prec': prec_b,
            'B_Rec': rec_b,
            'B_F1': f1_b,
            'B_AUC': auc_b,
            'B_PR_AUC': pr_auc_b,
        })
        
    df_results = pd.DataFrame(results)
    
    # Save results to processed directory
    df_results.to_csv(os.path.join(PROCESSED_DIR, "balancing_evaluation_results.csv"), index=False)
    
    print("\n=== Dataset A (SSH.log) Test Split Evaluation ===")
    for _, row in df_results.iterrows():
        print(f"[{row['Config']}]")
        print(f"  Accuracy:  {row['Test_Acc']:.5f}")
        print(f"  Precision: {row['Test_Prec']:.5f}")
        print(f"  Recall:    {row['Test_Rec']:.5f} (Detection Rate)")
        print(f"  F1-Score:  {row['Test_F1']:.5f}")
        print(f"  ROC-AUC:   {row['Test_AUC']:.5f}")
        print(f"  PR-AUC:    {row['Test_PR_AUC']:.5f}")
        print()
        
    print("=== Dataset B (auth_secrepo.log) Generalization Evaluation ===")
    for _, row in df_results.iterrows():
        print(f"[{row['Config']}]")
        print(f"  Accuracy:  {row['B_Acc']:.5f}")
        print(f"  Precision: {row['B_Prec']:.5f}")
        print(f"  Recall:    {row['B_Rec']:.5f} (Detection Rate)")
        print(f"  F1-Score:  {row['B_F1']:.5f}")
        print(f"  ROC-AUC:   {row['B_AUC']:.5f}")
        print(f"  PR-AUC:    {row['B_PR_AUC']:.5f}")
        print()

if __name__ == "__main__":
    evaluate_balancing()
