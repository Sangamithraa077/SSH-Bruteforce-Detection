# Dataset Justification and Suitability Report

This document evaluates the suitability of the datasets collected for the **SSH Brute Force Detection** project. In accordance with the project guidelines, multiple datasets have been analyzed and selected to mitigate dataset-specific bias and ensure the generalizability of the detection solutions.

---

## Summary of Evaluated Datasets

| Dataset File | Source / Origin | Samples (Lines) | Unique IPs | Failed Auth Events | Successful Auth Events | Temporal Span |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| [`SSH.log`](file:///c:/SSH_BRUTEFORCE_DETECTION/data/SSH.log) | Loghub Benchmark (LabSZ OpenSSH) | 655,147 | 1,243 | 477,926 | 364 | ~2 Months (Dec - Jan) |
| [`auth_secrepo.log`](file:///c:/SSH_BRUTEFORCE_DETECTION/data/auth_secrepo.log) | SecRepo.com (AWS EC2 Linux Instance) | 86,839 | 1,920 | 34,863 | 796 | ~1 Month (Nov 30 - Dec 31) |

---

## Dataset 1: SSH.log (Loghub)

### 1. Source and Origin
* **Provider/Source:** [Loghub](https://github.com/logpai/loghub), a widely recognized benchmark repository for system log analytics and anomaly detection.
* **Environment:** Collected from an OpenSSH server running on a system named `LabSZ` in a laboratory environment.
* **File Reference:** Located in the workspace at [`data/SSH.log`](file:///c:/SSH_BRUTEFORCE_DETECTION/data/SSH.log).

### 2. Attack Categories Present
* **SSH Brute Force / Dictionary Attacks:** The log is dominated by intense, repeated dictionary attack patterns targeting various usernames (e.g., `root`, `admin`, `webmaster`, `chen`, `pgadmin`, `utsims`).
* **Connection Scans:** Port scanning and connection probes that close immediately before or after entering the pre-authentication phase.

### 3. Number of Samples
* **Total Log Lines:** 655,147 lines.
* **sshd Process Logs:** 655,147 lines (100% of logs are from the OpenSSH daemon).
* **Unique IP Addresses:** 1,243 source IPs.
* **Detected Failed Authentications:** 477,926 lines (matching keywords such as `failed`, `invalid user`, `authentication failure`).
* **Detected Successful Authentications:** 364 lines (matching keywords such as `accepted` or `session opened`).

### 4. Feature Description
As a raw syslog text file, the features are implicitly embedded in the text. An automated parser or regex extractor can extract the following structured features:
* **Timestamp (`datetime`):** Date and time of the event (e.g., `Dec 10 06:55:46`).
* **Hostname (`string`):** The reporting host, consistently `LabSZ`.
* **Process Daemon (`string`):** Always `sshd`.
* **Process ID (`int`):** The system PID assigned to the session (e.g., `24200`), which is critical for linking multi-line event sequences.
* **Event Type / Action (`string`):** Categorized based on OpenSSH log formats (e.g., `Failed password`, `Invalid user`, `Connection closed`, `pam_unix authentication failure`).
* **Target User (`string`):** The username being targeted (e.g., `root`, `webmaster`).
* **Source IP Address (`string`):** The external IP address initiating the connection.
* **Source Port (`int`):** The source TCP port used by the client.
* **SSH Protocol Version (`string`):** In this log, typically `ssh2`.

### 5. Label Quality and Reliability
* **Type:** Semi-labeled / Implicitly self-labeled.
* **Reliability:** **Very High**. Since these logs are generated directly by the operating system’s OpenSSH daemon (`sshd`) and PAM subsystem, the authentication success or failure messages are highly standardized and deterministic. For example:
  * A line containing `Failed password for...` represents a guaranteed failure.
  * A line containing `Accepted publickey for...` or `Accepted password for...` represents a guaranteed success.
* There is no manual annotation noise; the logs record true system behavior.

### 6. Availability of Temporal Information
* **Temporal Data:** Every entry begins with a standard syslog timestamp containing month, day, hour, minute, and second (e.g., `Dec 10 07:13:56`).
* **Span:** Spans across two months: **December** (302,277 logs) and **January** (352,870 logs).
* **Granularity:** Sub-second logging (sequential lines with identical or millisecond-level time intervals, demonstrating the high speed of brute force attempts).
* *Note: Syslog formatting omits the year, which is standard. For analysis, a dummy year or sequence ordering can be used.*

### 7. Presence of Duplicate Samples
* **Exact Duplicate Lines:** **0 (0.00%)** out of 655,147 lines.
* **Justification:** Every line has a unique combination of timestamps, process IDs, source ports, or targeted usernames. This shows the log represents a clean, continuous stream of unique events.

### 8. Relevance of Features to the Selected Attack
* **Relevance:** **Extremely High**.
* **Justification:** SSH brute force attacks are defined by high-frequency authentication attempts, high numbers of failed logins, and connections targeting standard or random usernames. The dataset features allow tracking:
  * **Failed Login Rate per IP:** Calculating the density of failures over short time windows.
  * **Port Scanning Behavior:** Tracking rapid sequences of source port variations from the same IP.
  * **Target Username Diversity:** High ratio of invalid or unknown usernames.

---

## Dataset 2: auth_secrepo.log (SecRepo)

### 1. Source and Origin
* **Provider/Source:** Curated by Mike Sconzo at [SecRepo.com](http://www.secrepo.com), a well-known community repository for cybersecurity datasets.
* **Environment:** Collected from a live, internet-facing Linux AWS EC2 instance (`ip-172-31-27-153`).
* **File Reference:** Located in the workspace at [`data/auth_secrepo.log`](file:///c:/SSH_BRUTEFORCE_DETECTION/data/auth_secrepo.log).

### 2. Attack Categories Present
* **SSH Brute Force / Scanning Attacks:** Captures real-world internet background scanning, brute force attempts, and user enumeration.
* **Administrative / Normal Background Activity:** Unlike the lab dataset, this log contains background cron activity (`CRON[21882]`) and normal administrative logins, providing a natural baseline for benign user behavior.

### 3. Number of Samples
* **Total Log Lines:** 86,839 lines.
* **sshd Process Logs:** 85,246 lines (98.17%).
* **cron Process Logs:** 1,593 lines (1.83%).
* **Unique IP Addresses:** 1,920 source IPs.
* **Detected Failed Authentications:** 34,863 lines.
* **Detected Successful Authentications:** 796 lines.

### 4. Feature Description
Similar to standard Unix authentication logs (`auth.log`), the following structured features can be parsed:
* **Timestamp (`datetime`):** Date and time of the event (e.g., `Nov 30 06:39:00`).
* **Hostname (`string`):** The server name (`ip-172-31-27-153`).
* **Process Daemon (`string`):** `sshd` or `CRON`.
* **Process ID (`int`):** The system PID (e.g., `22087`).
* **Event Type / Action (`string`):** e.g., `Invalid user`, `Connection closed`, `session opened/closed`, `Did not receive identification string`.
* **Target User (`string`):** Targeted account (e.g., `root`, `admin`).
* **Source IP Address (`string`):** The connecting IP address.
* **State tag (`string`):** Connection state modifiers like `[preauth]`.

### 5. Label Quality and Reliability
* **Type:** Semi-labeled / Implicitly self-labeled.
* **Reliability:** **Very High**. Standard syslog outputs directly from OpenSSH and the system PAM module guarantee highly reliable indicators of authentication attempts and results.
* Benign baseline behavior is reliably categorized via `CRON` session messages and successful administrator logins.

### 6. Availability of Temporal Information
* **Temporal Data:** Standard syslog timestamps on all lines.
* **Span:** Spans from **November 30** (688 logs) to **December 31** (86,151 logs).
* **Granularity:** Second-level timestamp accuracy.

### 7. Presence of Duplicate Samples
* **Exact Duplicate Lines:** **0 (0.00%)** out of 86,839 lines.
* **Justification:** Every log entry represents a unique timestamp, PID, or message parameter combination.

### 8. Relevance of Features to the Selected Attack
* **Relevance:** **Extremely High**.
* **Justification:** It provides real-world context for SSH security monitoring. The inclusion of `CRON` session logs and actual successful administrator logins represents a diverse set of benign/baseline actions. This makes it highly relevant for training classification models that must distinguish between normal administrative operations and brute force attacks without producing high false-positive rates.

---

## Generalizability & Bias Reduction Justification

Using **both** datasets provides significant advantages for developing a robust SSH brute force detection solution:

1. **Host-Specific Bias Reduction:**
   * `SSH.log` is from `LabSZ`.
   * `auth_secrepo.log` is from `ip-172-31-27-153`.
   * A detection model trained on only one host might overfit to the hostname, specific PID sequences, or system-specific timing anomalies.
2. **Attacker Behavior Diversity:**
   * `SSH.log` features a lower IP-to-log ratio (1,243 IPs for 655k logs), indicating long, persistent brute-force campaigns from a smaller set of high-volume bots.
   * `auth_secrepo.log` features a higher IP-to-log ratio (1,920 IPs for 86k logs), indicating short, distributed scanning probes (low-and-slow / horizontal brute force).
   * Combining these datasets ensures that the detector can identify both persistent brute force and stealthier, distributed probes.
3. **Benign Baseline Modeling:**
   * The inclusion of non-SSH events (CRON logs) and valid user actions in the SecRepo dataset enables testing how well the detection system filters out everyday server management operations.
