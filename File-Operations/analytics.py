import csv
import os
import time

LOG_FILE = "transfer_metrics.csv"

#initialize the metrics log file on startup if it doesn't exist
def init_metrics_log():
    """Call once on startup (server or client) to initialize the CSV."""
    if not os.path.exists(LOG_FILE): #checks file existence
        with open(LOG_FILE, mode="w", newline="") as f: #makes and wirtes to it
            writer = csv.writer(f)
            writer.writerow([
                "timestamp",
                "client_id",
                "operation",         
                "file_type",         
                "file_size_bytes",
                "elapsed_sec",
                "data_rate_mb_s",
                "concurrent_clients"
            ])

#takes in all the metrics and writes them to the CSV file for later analysis
def record_metric(client_id: str, operation: str, file_type: str, 
                  file_size_bytes: int, elapsed_sec: float, concurrent_clients: int = 1):
    """Computes transfer speed and writes the data point to disk."""
    mb_transferred = file_size_bytes / (1024 * 1024) #transfer calcs in mb
    data_rate = (mb_transferred / elapsed_sec) if elapsed_sec > 0 else 0.0 #rate of transfer in mb/s

    with open(LOG_FILE, mode="a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            time.strftime("%Y-%m-%d %H:%M:%S"),
            client_id,
            operation,
            file_type,
            file_size_bytes,
            round(elapsed_sec, 4),
            round(data_rate, 2),
            concurrent_clients
        ])
