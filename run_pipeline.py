"""
run_pipeline.py  —  Master Orchestration Script for SSH Brute Force Detection Pipeline

This script executes the entire ML pipeline sequentially:
  1. Data preprocessing and feature extraction
  2. Class distribution analysis
  3. Classical model training
  4. Deep learning model training
  5. In-domain evaluation (Dataset A)
  6. Cross-domain evaluation (Dataset A + B)
  7. Ablation studies
  
Run as: python run_pipeline.py
"""

import os
import sys
import time
import subprocess
from datetime import datetime

# Configuration
SCRIPTS = [
    ("preprocess_logs.py", "1. Data Preprocessing & Feature Extraction"),
    ("analyze_distribution.py", "2. Class Distribution Analysis"),
    ("train_ensemble.py", "3. Classical Model Training (Decision Tree, LightGBM, XGBoost)"),
    ("train_lstm.py", "4a. Deep Learning - LSTM Training"),
    ("train_gru.py", "4b. Deep Learning - GRU Training"),
    ("evaluate_models.py", "5. Dataset A In-Domain Evaluation"),
    ("evaluate_cross_domain.py", "6. Full Evaluation (Dataset A + Dataset B)"),
    ("ablation_study.py", "7. Ablation Study - Balancing Techniques"),
    ("evaluate_balancing_impact.py", "8. Behavioral Features Ablation Study"),
]

def print_header(text):
    """Print formatted header."""
    width = 70
    print("\n" + "=" * width)
    print(f"  {text}")
    print("=" * width)

def print_step(step_num, total, description):
    """Print step information."""
    print(f"\n[{step_num}/{total}] {description}")
    print("-" * 70)

def run_script(script_name):
    """Execute a Python script and return success status."""
    try:
        result = subprocess.run(
            [sys.executable, script_name],
            check=True,
            cwd=os.path.dirname(os.path.abspath(__file__)) or "."
        )
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running {script_name}: {e}")
        return False
    except FileNotFoundError:
        print(f"❌ Script not found: {script_name}")
        return False

def main():
    print_header("SSH BRUTE FORCE DETECTION - MASTER PIPELINE")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    total_scripts = len(SCRIPTS)
    completed = 0
    failed_scripts = []
    
    start_time = time.time()
    
    for idx, (script, description) in enumerate(SCRIPTS, 1):
        print_step(idx, total_scripts, description)
        
        script_start = time.time()
        success = run_script(script)
        script_elapsed = time.time() - script_start
        
        if success:
            print(f"✅ Completed in {script_elapsed:.2f}s")
            completed += 1
        else:
            print(f"❌ Failed - Stopping pipeline")
            failed_scripts.append((idx, description, script))
            break  # Stop on first failure
    
    elapsed = time.time() - start_time
    
    # Final Report
    print_header("PIPELINE EXECUTION SUMMARY")
    print(f"Completed Steps: {completed}/{total_scripts}")
    print(f"Total Execution Time: {elapsed:.2f}s ({elapsed/60:.2f} minutes)")
    print(f"Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    if completed == total_scripts:
        print("🎉 PIPELINE COMPLETED SUCCESSFULLY!")
        print("\n📊 Generated Artifacts:")
        print("  ✓ data/processed/dataset_a.npz               (33,643 samples)")
        print("  ✓ data/processed/dataset_b.npz               (4,272 samples)")
        print("  ✓ data/processed/split_smote.npz             (SMOTE-balanced splits)")
        print("  ✓ models/baseline_decisiontree.joblib        (98.72% accuracy)")
        print("  ✓ models/boosting_lightgbm.joblib            (99.30% accuracy - Best)")
        print("  ✓ models/xgboost_model.joblib                (98.68% accuracy)")
        print("  ✓ models/deeplearning_mlp.joblib             (99.00% accuracy)")
        print("  ✓ models/lstm_model.pt & lstm_meta.joblib    (98.59% F1)")
        print("  ✓ models/gru_model.pt & gru_meta.joblib      (98.42% F1)")
        print("  ✓ data/processed/model_evaluation_results.csv")
        print("  ✓ data/processed/balancing_evaluation_results.csv")
        print("  ✓ model_evaluation_report.md")
        print("  ✓ class_distribution_report.md")
        return 0
    else:
        print("⚠️  PIPELINE STOPPED DUE TO ERRORS")
        if failed_scripts:
            print(f"\nFailed at Step {failed_scripts[0][0]}: {failed_scripts[0][1]}")
            print(f"Script: {failed_scripts[0][2]}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
