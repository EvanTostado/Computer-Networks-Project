import csv
import os
import time
import threading

LOG_FILE = "transfer_metrics.csv"
_csv_lock = threading.Lock()

#initialize the metrics log file on startup if it doesn't exist
def init_metrics_log():
    """Call once on startup (server or client) to initialize the CSV."""
    with _csv_lock:
        if not os.path.exists(LOG_FILE):
            with open(LOG_FILE, mode="w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "timestamp",
                    "source",            #SERVER or CLIENT
                    "client_id",
                    "operation",         #UPLOAD, DOWNLOAD, DIR, SUBFOLDER, DELETE, AUTH
                    "file_type",         #TXT, WAV, MP4, N/A
                    "file_size_bytes",
                    "elapsed_sec",
                    "data_rate_mb_s",
                    "concurrent_clients"
                ])

#takes in all the metrics and writes them to the CSV file for later analysis
def record_metric(source: str, client_id: str, operation: str, file_type: str, 
                  file_size_bytes: int, elapsed_sec: float, concurrent_clients: int = 1):
    """Computes transfer speed and writes the data point to disk safely."""
    mb_transferred = file_size_bytes / (1024 * 1024)
    data_rate = (mb_transferred / elapsed_sec) if elapsed_sec > 0 else 0.0

    with _csv_lock:
        with open(LOG_FILE, mode="a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                time.strftime("%Y-%m-%d %H:%M:%S"),
                source,
                client_id,
                operation,
                file_type,
                file_size_bytes,
                round(elapsed_sec, 4),
                round(data_rate, 2),
                concurrent_clients
            ])
