import os
import re
import numpy as np
import pandas as pd
from datetime import datetime
from sklearn.preprocessing import StandardScaler
from imblearn.over_sampling import RandomOverSampler, SMOTE, ADASYN
from imblearn.under_sampling import RandomUnderSampler

# Configuration
WINDOW_SIZE_MINUTES = 1
DATA_DIR = r"c:\SSH_BRUTEFORCE_DETECTION\data"
PROCESSED_DIR = r"c:\SSH_BRUTEFORCE_DETECTION\data\processed"

os.makedirs(PROCESSED_DIR, exist_ok=True)

# Month map to convert syslog months to numbers
MONTHS_MAP = {
    'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
    'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12
}

def parse_log_file(filepath):
    print(f"Parsing raw log file: {filepath}...")
    
    # PID to IP map
    pid_to_ip = {}
    ip_pattern = re.compile(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b')
    pid_pattern = re.compile(r'sshd\[(\d+)\]')
    port_pattern = re.compile(r'\bport (\d+)\b')
    
    # Simple templates for event classification
    failed_re = re.compile(r'failed|auth.*fail|authentication failure', re.IGNORECASE)
    invalid_re = re.compile(r'invalid user', re.IGNORECASE)
    success_re = re.compile(r'accepted|session opened', re.IGNORECASE)
    
    raw_events = []
    year = 2025
    prev_month_num = None
    
    # First pass: Build PID-to-IP map
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            pid_match = pid_pattern.search(line)
            if pid_match:
                pid = pid_match.group(1)
                ip_match = ip_pattern.search(line)
                if ip_match:
                    pid_to_ip[pid] = ip_match.group(0)
                    
    # Second pass: Extract structured events
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
                
            # Parse syslog header
            ts_str = line[:15].strip()
            parts = ts_str.split()
            if len(parts) < 3:
                continue
            month_str, day_str, time_str = parts[0], parts[1], parts[2]
            month_num = MONTHS_MAP.get(month_str)
            if not month_num:
                continue
                
            # Handle year rollover
            if prev_month_num is not None:
                if prev_month_num == 12 and month_num == 1:
                    year += 1
            prev_month_num = month_num
            
            try:
                dt_str = f"{year} {month_str} {day_str} {time_str}"
                dt = datetime.strptime(dt_str, "%Y %b %d %H:%M:%S")
                timestamp = dt.timestamp()
            except Exception:
                continue
                
            # Resolve IP and PID
            pid = None
            pid_match = pid_pattern.search(line)
            if pid_match:
                pid = pid_match.group(1)
                
            ip = None
            ip_match = ip_pattern.search(line)
            if ip_match:
                ip = ip_match.group(0)
            elif pid and pid in pid_to_ip:
                ip = pid_to_ip[pid]
                
            # If no IP, we skip since we can't aggregate features by source IP
            if not ip:
                continue
                
            # Extract port
            port = 0
            port_match = port_pattern.search(line)
            if port_match:
                port = int(port_match.group(1))
                
            # Extract username
            username = "unknown"
            # Try matching "user [username]" or "for [username]" or "user=[username]"
            user_match = re.search(r'user\s+(\S+)|for\s+(\S+)|user=(\S+)', line)
            if user_match:
                username = next(u for u in user_match.groups() if u is not None)
                # clean trailing characters
                username = username.strip('[]:,;()')
                
            # Classify event type
            if invalid_re.search(line):
                event_type = 'invalid_user'
            elif failed_re.search(line):
                event_type = 'failed'
            elif success_re.search(line):
                event_type = 'success'
            else:
                event_type = 'other'
                
            raw_events.append({
                'timestamp': timestamp,
                'ip': ip,
                'port': port,
                'username': username,
                'event_type': event_type
            })
            
    print(f"Extracted {len(raw_events)} events.")
    return pd.DataFrame(raw_events)

def aggregate_windows(df, window_size_min):
    print(f"Aggregating events into {window_size_min}-minute windows...")
    
    # Calculate global window ID
    df['window_id'] = (df['timestamp'] // (window_size_min * 60)).astype(int)
    
    # Group by IP and window_id
    grouped = df.groupby(['ip', 'window_id'])
    
    window_samples = []
    
    for (ip, window_id), group in grouped:
        attempt_count = len(group)
        failed_count = group['event_type'].isin(['failed', 'invalid_user']).sum()
        success_count = (group['event_type'] == 'success').sum()
        invalid_user_count = (group['event_type'] == 'invalid_user').sum()
        unique_usernames = group['username'].nunique()
        
        # Unique non-zero ports
        ports = group['port'][group['port'] > 0]
        unique_ports = ports.nunique() if len(ports) > 0 else 1
        
        timestamps = group['timestamp'].values
        duration = float(timestamps.max() - timestamps.min())
        
        # Calculate rates
        attempt_rate = attempt_count / (duration + 1.0)
        failure_rate = failed_count / attempt_count
        invalid_user_rate = invalid_user_count / attempt_count
        success_rate = success_count / attempt_count
        port_diversity = unique_ports / attempt_count
        
        # Define Label:
        # Attack (1) if failed attempts >= 3 (in a 1-min window) or invalid user attempts >= 1
        # Benign (0) otherwise
        if failed_count >= 3 or invalid_user_count >= 1:
            label = 1
        else:
            label = 0
            
        window_samples.append({
            'ip': ip,
            'window_id': window_id,
            'start_time': float(timestamps.min()),
            'attempt_count': float(attempt_count),
            'failed_count': float(failed_count),
            'success_count': float(success_count),
            'invalid_user_count': float(invalid_user_count),
            'unique_usernames': float(unique_usernames),
            'unique_ports': float(unique_ports),
            'duration_seconds': duration,
            'attempt_rate': attempt_rate,
            'failure_rate': failure_rate,
            'invalid_user_rate': invalid_user_rate,
            'success_rate': success_rate,
            'port_diversity': port_diversity,
            'label': label
        })
        
    res_df = pd.DataFrame(window_samples)
    print(f"Generated {len(res_df)} window samples.")
    return res_df

def process_datasets():
    # 1. Parse and aggregate Dataset A (SSH.log)
    ssh_events = parse_log_file(os.path.join(DATA_DIR, "SSH.log"))
    dataset_a = aggregate_windows(ssh_events, WINDOW_SIZE_MINUTES)
    
    # 2. Parse and aggregate Dataset B (auth_secrepo.log)
    secrepo_events = parse_log_file(os.path.join(DATA_DIR, "auth_secrepo.log"))
    dataset_b = aggregate_windows(secrepo_events, WINDOW_SIZE_MINUTES)
    
    # 3. Temporal Split on Dataset A (No Shuffling)
    dataset_a = dataset_a.sort_values(by='start_time').reset_index(drop=True)
    
    n_samples = len(dataset_a)
    n_train = int(n_samples * 0.70)
    n_val = int(n_samples * 0.10)
    
    train_df = dataset_a.iloc[:n_train].copy()
    val_df = dataset_a.iloc[n_train:n_train+n_val].copy()
    test_df = dataset_a.iloc[n_train+n_val:].copy()
    
    print(f"Dataset A Temporal Splits:")
    print(f"  Train: {len(train_df)} samples")
    print(f"  Val: {len(val_df)} samples")
    print(f"  Test: {len(test_df)} samples")
    
    # Feature columns (numerical features only)
    feature_cols = [
        'attempt_count', 'failed_count', 'success_count', 'invalid_user_count',
        'unique_usernames', 'unique_ports', 'duration_seconds',
        'attempt_rate', 'failure_rate', 'invalid_user_rate', 'success_rate', 'port_diversity'
    ]
    
    X_train = train_df[feature_cols].values
    y_train = train_df['label'].values
    
    X_val = val_df[feature_cols].values
    y_val = val_df['label'].values
    
    X_test = test_df[feature_cols].values
    y_test = test_df['label'].values
    
    X_b = dataset_b[feature_cols].values
    y_b = dataset_b['label'].values
    
    # 4. Encoding & Normalization (Fit on Train only!)
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_val_scaled = scaler.transform(X_val)
    X_test_scaled = scaler.transform(X_test)
    X_b_scaled = scaler.transform(X_b)
    
    # Save the splits & metadata
    np.savez(os.path.join(PROCESSED_DIR, "split_raw.npz"),
             X_train=X_train_scaled, y_train=y_train,
             X_val=X_val_scaled, y_val=y_val,
             X_test=X_test_scaled, y_test=y_test)
             
    np.savez(os.path.join(PROCESSED_DIR, "dataset_b.npz"),
             X=X_b_scaled, y=y_b)
             
    # Save feature names and scale parameters for inference/real-time deployment
    pd.DataFrame(feature_cols, columns=['feature_name']).to_csv(os.path.join(PROCESSED_DIR, "feature_names.csv"), index=False)
    
    # Save scaler parameters (mean and scale) for later deployment/evaluation
    pd.DataFrame({
        'feature': feature_cols,
        'mean': scaler.mean_,
        'scale': scaler.scale_
    }).to_csv(os.path.join(PROCESSED_DIR, "scaler_params.csv"), index=False)
    
    # 5. Handle Class Imbalance (Train Set Only)
    # Apply undersampling, oversampling, SMOTE, and ADASYN
    
    # Undersampling (RUS)
    rus = RandomUnderSampler(random_state=42)
    X_train_rus, y_train_rus = rus.fit_resample(X_train_scaled, y_train)
    np.savez(os.path.join(PROCESSED_DIR, "split_rus.npz"), X_train=X_train_rus, y_train=y_train_rus)
    
    # Oversampling (ROS)
    ros = RandomOverSampler(random_state=42)
    X_train_ros, y_train_ros = ros.fit_resample(X_train_scaled, y_train)
    np.savez(os.path.join(PROCESSED_DIR, "split_ros.npz"), X_train=X_train_ros, y_train=y_train_ros)
    
    # SMOTE
    # Ensure we have enough samples to perform SMOTE (requires k_neighbors + 1 samples)
    min_samples = min(np.bincount(y_train))
    k_neighbors = min(5, min_samples - 1) if min_samples > 1 else 1
    if min_samples > 1:
        smote = SMOTE(random_state=42, k_neighbors=k_neighbors)
        X_train_smote, y_train_smote = smote.fit_resample(X_train_scaled, y_train)
        np.savez(os.path.join(PROCESSED_DIR, "split_smote.npz"), X_train=X_train_smote, y_train=y_train_smote)
    else:
        print("Warning: Not enough benign samples in training set to run SMOTE.")
        
    # ADASYN
    if min_samples > 1:
        try:
            adasyn = ADASYN(random_state=42, n_neighbors=k_neighbors)
            X_train_adasyn, y_train_adasyn = adasyn.fit_resample(X_train_scaled, y_train)
            np.savez(os.path.join(PROCESSED_DIR, "split_adasyn.npz"), X_train=X_train_adasyn, y_train=y_train_adasyn)
        except ValueError as e:
            # ADASYN can fail if no benign sample is near the boundary or other numerical issues
            print(f"Warning: ADASYN failed with error: {e}. Skipping ADASYN split.")
            
    print("Preprocessing completed successfully!")
    
    # Print summary statistics of classes
    print("\nSummary of Class Distributions in Training Splits:")
    benign_raw = np.sum(y_train==0)
    attack_raw = np.sum(y_train==1)
    ratio_raw = benign_raw / attack_raw if attack_raw > 0 else 0
    print(f"Raw Train: Benign={benign_raw}, Attack={attack_raw}, Ratio={ratio_raw:.4f}")
    print(f"RUS Train: Benign={np.sum(y_train_rus==0)}, Attack={np.sum(y_train_rus==1)}")
    print(f"ROS Train: Benign={np.sum(y_train_ros==0)}, Attack={np.sum(y_train_ros==1)}")
    if min_samples > 1:
        print(f"SMOTE Train: Benign={np.sum(y_train_smote==0)}, Attack={np.sum(y_train_smote==1)}")
    
if __name__ == "__main__":
    process_datasets()
