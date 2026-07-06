import os
import time
import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import confusion_matrix, accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, average_precision_score

PROCESSED_DIR = r"c:\SSH_BRUTEFORCE_DETECTION\data\processed"
MODELS_DIR = r"c:\SSH_BRUTEFORCE_DETECTION\models"

def evaluate_models():
    print("==================================================")
    print("Step 4: Model Evaluation & Comparison")
    print("==================================================")
    
    # 1. Load test splits
    print("Loading test splits...")
    raw_data = np.load(os.path.join(PROCESSED_DIR, "split_raw.npz"))
    X_test_full = raw_data['X_test']
    y_test = raw_data['y_test']
    
    dataset_b = np.load(os.path.join(PROCESSED_DIR, "dataset_b.npz"))
    X_b_full = dataset_b['X']
    y_b = dataset_b['y']
    
    # 2. Filter behavioral features
    feature_names = pd.read_csv(os.path.join(PROCESSED_DIR, "feature_names.csv"))['feature_name'].tolist()
    behavioral_features = [
        'attempt_count', 'unique_usernames', 'unique_ports', 'duration_seconds', 'attempt_rate', 'port_diversity'
    ]
    behavioral_indices = [feature_names.index(f) for f in behavioral_features]
    
    X_test = X_test_full[:, behavioral_indices]
    X_b = X_b_full[:, behavioral_indices]
    
    # Load training stats
    training_stats = pd.read_csv(os.path.join(PROCESSED_DIR, "training_stats.csv")).set_index('Model_Name')
    
    # List of models to load
    model_files = {
        'Baseline_DecisionTree': 'baseline_decisiontree.joblib',
        'Boosting_LightGBM': 'boosting_lightgbm.joblib',
        'DeepLearning_MLP': 'deeplearning_mlp.joblib'
    }
    
    evaluation_results = []
    
    for name, file_name in model_files.items():
        model_path = os.path.join(MODELS_DIR, file_name)
        print(f"Evaluating {name}...")
        
        if not os.path.exists(model_path):
            print(f"  Warning: Model file {model_path} not found. Skipping.")
            continue
            
        clf = joblib.load(model_path)
        
        # A. Evaluate on Dataset A Test (In-Domain)
        # Measure inference speed
        start_time = time.time()
        y_pred_test = clf.predict(X_test)
        elapsed_inference_test = time.time() - start_time
        y_prob_test = clf.predict_proba(X_test)[:, 1]
        
        # Metrics
        acc_test = accuracy_score(y_test, y_pred_test)
        prec_test = precision_score(y_test, y_pred_test)
        rec_test = recall_score(y_test, y_pred_test)
        f1_test = f1_score(y_test, y_pred_test)
        auc_test = roc_auc_score(y_test, y_prob_test)
        pr_auc_test = average_precision_score(y_test, y_prob_test)
        
        # Confusion matrix and rates
        tn_t, fp_t, fn_t, tp_t = confusion_matrix(y_test, y_pred_test).ravel()
        fpr_test = fp_t / (fp_t + tn_t) if (fp_t + tn_t) > 0 else 0
        fnr_test = fn_t / (fn_t + tp_t) if (fn_t + tp_t) > 0 else 0
        
        # B. Evaluate on Dataset B (External Validation)
        start_time = time.time()
        y_pred_b = clf.predict(X_b)
        elapsed_inference_b = time.time() - start_time
        y_prob_b = clf.predict_proba(X_b)[:, 1]
        
        acc_b = accuracy_score(y_b, y_pred_b)
        prec_b = precision_score(y_b, y_pred_b) if np.sum(y_pred_b) > 0 else 0
        rec_b = recall_score(y_b, y_pred_b)
        f1_b = f1_score(y_b, y_pred_b) if np.sum(y_pred_b) > 0 else 0
        auc_b = roc_auc_score(y_b, y_prob_b)
        pr_auc_b = average_precision_score(y_b, y_prob_b)
        
        # Confusion matrix and rates for Dataset B
        tn_b, fp_b, fn_b, tp_b = confusion_matrix(y_b, y_pred_b).ravel()
        fpr_b = fp_b / (fp_b + tn_b) if (fp_b + tn_b) > 0 else 0
        fnr_b = fn_b / (fn_b + tp_b) if (fn_b + tp_b) > 0 else 0
        
        # Calculate latency in microseconds per sample
        lat_test_us = (elapsed_inference_test / len(X_test)) * 1e6
        lat_b_us = (elapsed_inference_b / len(X_b)) * 1e6
        
        # Retrieve training time & size
        train_time = training_stats.loc[name, 'Training_Time_Sec']
        model_size = training_stats.loc[name, 'Model_Size_KB']
        
        evaluation_results.append({
            'Model': name,
            'Training_Time_Sec': train_time,
            'Model_Size_KB': model_size,
            
            # Dataset A Test metrics
            'Test_Acc': acc_test,
            'Test_Prec': prec_test,
            'Test_Rec': rec_test,
            'Test_F1': f1_test,
            'Test_AUC': auc_test,
            'Test_PR_AUC': pr_auc_test,
            'Test_FPR': fpr_test,
            'Test_FNR': fnr_test,
            'Test_Latency_us': lat_test_us,
            'Test_TN': tn_t, 'Test_FP': fp_t, 'Test_FN': fn_t, 'Test_TP': tp_t,
            
            # Dataset B (External) metrics
            'B_Acc': acc_b,
            'B_Prec': prec_b,
            'B_Rec': rec_b,
            'B_F1': f1_b,
            'B_AUC': auc_b,
            'B_PR_AUC': pr_auc_b,
            'B_FPR': fpr_b,
            'B_FNR': fnr_b,
            'B_Latency_us': lat_b_us,
            'B_TN': tn_b, 'B_FP': fp_b, 'B_FN': fn_b, 'B_TP': tp_b,
        })
        
    df_eval = pd.DataFrame(evaluation_results)
    df_eval.to_csv(os.path.join(PROCESSED_DIR, "model_evaluation_results.csv"), index=False)
    print("Evaluation completed and results saved to processed directory!")
    
    # Print clean Markdown tables to output log
    print("\n=== Dataset A (SSH.log) Test Evaluation ===")
    print("| Model | Acc | Prec | Recall (DR) | F1-Score | ROC-AUC | PR-AUC | FPR | FNR | Latency/Sample |")
    print("|---|---|---|---|---|---|---|---|---|---|")
    for _, row in df_eval.iterrows():
        print(f"| {row['Model']} | {row['Test_Acc']:.5f} | {row['Test_Prec']:.5f} | {row['Test_Rec']:.5f} | {row['Test_F1']:.5f} | {row['Test_AUC']:.5f} | {row['Test_PR_AUC']:.5f} | {row['Test_FPR']:.5f} | {row['Test_FNR']:.5f} | {row['Test_Latency_us']:.2f} us |")
        
    print("\n=== Dataset B (auth_secrepo.log) External Generalization Evaluation ===")
    print("| Model | Acc | Prec | Recall (DR) | F1-Score | ROC-AUC | PR-AUC | FPR | FNR | Latency/Sample |")
    print("|---|---|---|---|---|---|---|---|---|---|")
    for _, row in df_eval.iterrows():
        print(f"| {row['Model']} | {row['B_Acc']:.5f} | {row['B_Prec']:.5f} | {row['B_Rec']:.5f} | {row['B_F1']:.5f} | {row['B_AUC']:.5f} | {row['B_PR_AUC']:.5f} | {row['B_FPR']:.5f} | {row['B_FNR']:.5f} | {row['B_Latency_us']:.2f} us |")

if __name__ == "__main__":
    evaluate_models()
