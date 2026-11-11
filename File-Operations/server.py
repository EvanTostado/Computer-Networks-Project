import os
import time
import json
import socket
import threading
import shutil #Used for recursively deleting directories
import serverAuth

#setups the analytics logging for the server
import analytics
analytics.init_metrics_log()

#keeps track of connection amount
active_clients = 0
active_clients_lock = threading.Lock()

#returns the client count
def get_active_client_count() -> int:
    with active_clients_lock:
        return active_clients


HOST = "0.0.0.0"  
PORT = 4450
STORAGE_DIR = os.path.abspath("./server_storage")
BUFFER_SIZE = 64 * 1024  #64 KB chunk size for efficient file transfer

#storage directory
if not os.path.exists(STORAGE_DIR):
    os.makedirs(STORAGE_DIR)

file_locks = {}
file_locks_guard = threading.Lock() #A thread lock protecting when multiple threads try to register a new file lock at the same time

#Retrieves or creates a thread lock for a specific file path
#ensuring two clients cannot modify or delete the same file simultaneously
def get_file_lock(filepath: str) -> threading.Lock: 
    with file_locks_guard:
        if filepath not in file_locks:
            file_locks[filepath] = threading.Lock()
        return file_locks[filepath]

#Sends a JSON-encoded message header with a fixed 4-byte length prefix
#ends it over the socket prefixed with a 4-byte big-endian length header to prevent TCP packet fragmentation
def send_json(conn: socket.socket, data: dict):
    payload = json.dumps(data).encode("utf-8")
    length = len(payload)
    conn.sendall(length.to_bytes(4, byteorder="big") + payload)

#Receives a JSON-encoded message header using a fixed 4-byte length prefix
def recv_json(conn: socket.socket) -> dict:
    raw_length = conn.recv(4)
    if not raw_length:
        return None
    length = int.from_bytes(raw_length, byteorder="big")
    data = bytearray()
    while len(data) < length:
        packet = conn.recv(length - len(data))
        if not packet:
            return None
        data.extend(packet)
    return json.loads(data.decode("utf-8"))

#Initiates connection from client to server with the specified files
def connect(conn: socket.socket, addr: tuple):
    print(f"Client connected from {addr[0]}:{addr[1]}")
    authenticated = False

    #when someone connects add to the client counter
    global active_clients
    with active_clients_lock:
        active_clients += 1
    client_label = f"{addr[0]}:{addr[1]}"

    try:
        while True: #active listening for client cmds
            req = recv_json(conn)
            if not req:
                break

            cmd = req.get("command")

            #cmds
            if cmd == "GET_PUBKEY":
                pub_key = serverAuth.requestPublicKey()
                pub_bytes = pub_key.save_pkcs1().decode("utf-8")
                send_json(conn, {"status": "SUCCESS", "pubkey": pub_bytes})

            elif cmd == "AUTH":
                try:
                    enc_user = bytes.fromhex(req.get("username"))
                    enc_pass = bytes.fromhex(req.get("password"))
                    
                    user = serverAuth.decryptPassword(enc_user)
                    password = serverAuth.decryptPassword(enc_pass)
                    
                    if serverAuth.authenticate(user, password):
                        authenticated = True
                        send_json(conn, {"status": "SUCCESS", "message": "Client joined."})
                    else:
                        send_json(conn, {"status": "ERROR", "message": "Invalid username or password."})
                except Exception as e:
                    send_json(conn, {"status": "ERROR", "message": f"Authentication failed: {str(e)}"})

            elif not authenticated: #blocks the unauthorized
                send_json(conn, {"status": "ERROR", "message": "Unauthorized."})

            elif cmd == "UPLOAD":
                upload(conn, req)

            elif cmd == "DOWNLOAD":
                download(conn, req)

            elif cmd == "DELETE":
                delete(conn, req)

            elif cmd == "DIR":
                dir(conn, req)

            elif cmd == "SUBFOLDER":
                subfolder(conn, req)

            else:
                send_json(conn, {"status": "ERROR", "message": "Unknown command."})

    except (ConnectionResetError, BrokenPipeError):
        print(f"Client {addr[0]}:{addr[1]} disconnected.") #connection lost (prevents server crash)
    except Exception as e:
        print(f"Client {addr[0]}:{addr[1]}: {e}")
    finally:
        #when a connection is over decrement the client counter
        with active_clients_lock:
            active_clients -= 1

        conn.close()
        print(f"Client {addr[0]}:{addr[1]} left.")

# Clients can upload files to the server. Server will prompt
# client if file already exists and requires user input to be overwritten
def upload(conn: socket.socket, req: dict):
    perf_start = time.perf_counter() #changed to be a more reliable system clock
    filename = req.get("filename")
    filesize = req.get("filesize")
    file_ext = os.path.splitext(filename)[1].replace(".", "").upper() or "UNKNOWN"
    rel_path = req.get("path", "")
    overwrite = req.get("overwrite", False)

    target_dir = os.path.abspath(os.path.join(STORAGE_DIR, rel_path))
    if not target_dir.startswith(STORAGE_DIR):
        send_json(conn, {"status": "ERROR", "message": "Path not in directory."})
        return

    os.makedirs(target_dir, exist_ok=True)
    filepath = os.path.join(target_dir, filename)

    if os.path.exists(filepath) and not overwrite:
        send_json(conn, {"status": "EXISTS", "message": "File already exists."})
        return

    lock = get_file_lock(filepath)
    if not lock.acquire(blocking=False):
        send_json(conn, {"status": "ERROR", "message": "File is currently being processed."})
        return

    try:
        send_json(conn, {"status": "READY", "message": "Ready to receive file."})
        received = 0
        with open(filepath, "wb") as f:
            while received < filesize:
                chunk = conn.recv(min(BUFFER_SIZE, filesize - received))
                if not chunk:
                    break
                f.write(chunk)
                received += len(chunk)
        
        elapsed = time.perf_counter() - perf_start
        rate = (received / (1024 * 1024)) / elapsed if elapsed > 0 else 0

        #save these upload metrics to the analytics log
        analytics.record_metric(
            client_id="Client",
            operation="UPLOAD",
            file_type=file_ext,
            file_size_bytes=received,
            elapsed_sec=elapsed,
            concurrent_clients=get_active_client_count()
        )
        
        send_json(conn, {
            "status": "SUCCESS",
            "message": f"Uploaded {received} bytes successfully.",
            "metrics": {"time_sec": round(elapsed, 4), "rate_mbps": round(rate, 2)}
        })
    finally:
        lock.release()

# Clients can download files from the server. Server
# will respond with error message if file does not exist
def download(conn: socket.socket, req: dict):
    filename = req.get("filename")
    rel_path = req.get("path", "")
    file_ext = os.path.splitext(filename)[1].replace(".", "").upper() or "UNKNOWN"

    filepath = os.path.abspath(os.path.join(STORAGE_DIR, rel_path, filename))
    if not filepath.startswith(STORAGE_DIR) or not os.path.exists(filepath):
        send_json(conn, {"status": "ERROR", "message": "File does not exist."})
        return

    lock = get_file_lock(filepath)
    if not lock.acquire(blocking=False):
        send_json(conn, {"status": "ERROR", "message": "File is currently being processed."})
        return

    try:
        total_size = os.path.getsize(filepath)
        send_json(conn, {
            "status": "READY",
            "filesize": total_size
        })

        # Wait for client confirmation to begin streaming
        ack = recv_json(conn)
        if ack and ack.get("status") == "START":
            perf_start = time.perf_counter() #record time here for analytics

            sent = 0
            with open(filepath, "rb") as f:
                while chunk := f.read(BUFFER_SIZE):
                    conn.sendall(chunk)
                    sent += len(chunk)

            elapsed = time.perf_counter() - perf_start
            rate = (sent / (1024 * 1024)) / elapsed if elapsed > 0 else 0

            #save these download metrics to the analytics log
            analytics.record_metric(
                client_id="Client",
                operation="DOWNLOAD",
                file_type=file_ext,
                file_size_bytes=sent,
                elapsed_sec=elapsed,
                concurrent_clients=get_active_client_count()
            )

            print(f"Sent {sent} bytes at {rate:.2f} MB/s")
    finally:
        lock.release()

# Clients can delete files from the server. Server will respond with
# error message if file is currently being processed or does not exist
def delete(conn: socket.socket, req: dict):
    filename = req.get("filename")
    rel_path = req.get("path", "")
    filepath = os.path.abspath(os.path.join(STORAGE_DIR, rel_path, filename))

    if not filepath.startswith(STORAGE_DIR) or not os.path.exists(filepath):
        send_json(conn, {"status": "ERROR", "message": "File does not exist."})
        return

    lock = get_file_lock(filepath)
    if not lock.acquire(blocking=False):
        send_json(conn, {"status": "ERROR", "message": "File is currently being processed."})
        return

    try: 
        if os.path.isdir(filepath): #os.remove for files, shutil.rmtree for directories
            shutil.rmtree(filepath)
        else:
            os.remove(filepath)
        send_json(conn, {"status": "SUCCESS", "message": f"Deleted {filename} successfully."})
    except Exception as e:
        send_json(conn, {"status": "ERROR", "message": f"Failed to delete: {str(e)}"})
    finally:
        lock.release()

#Clients can view a list of files and subdirectories in the server’s file storage path.
def dir(conn: socket.socket, req: dict):
    cmd_start = time.perf_counter() #record latency for analytics

    rel_path = req.get("path", "")
    target_dir = os.path.abspath(os.path.join(STORAGE_DIR, rel_path))

    if not target_dir.startswith(STORAGE_DIR) or not os.path.exists(target_dir):
        send_json(conn, {"status": "ERROR", "message": "Invalid storage path."})
        return

    items = []
    for entry in os.scandir(target_dir):
        items.append({
            "name": entry.name,
            "is_dir": entry.is_dir(),
            "size": entry.stat().st_size if not entry.is_dir() else 0
        })
    send_json(conn, {"status": "SUCCESS", "items": items})

    #directory listing latency metrics for analytics
    analytics.record_metric(
        client_id="Client",
        operation="DIR_LATENCY",
        file_type="N/A",
        file_size_bytes=0,
        elapsed_sec=time.perf_counter() - cmd_start,
        concurrent_clients=get_active_client_count()
    )

#Clients can create or delete subfolders in the server’s file storage path
def subfolder(conn: socket.socket, req: dict):
    action = req.get("action")  #create or delete
    folder_path = req.get("path", "")
    target_path = os.path.abspath(os.path.join(STORAGE_DIR, folder_path))

    if not target_path.startswith(STORAGE_DIR):
        send_json(conn, {"status": "ERROR", "message": "Access denied."})
        return

    if action == "create":
        os.makedirs(target_path, exist_ok=True)
        send_json(conn, {"status": "SUCCESS", "message": f"Directory '{folder_path}' created."})
    elif action == "delete":
        if os.path.exists(target_path) and os.path.isdir(target_path):
            shutil.rmtree(target_path)
            send_json(conn, {"status": "SUCCESS", "message": f"Directory '{folder_path}' deleted."})
        else:
            send_json(conn, {"status": "ERROR", "message": "Directory does not exist."})
    else:
        send_json(conn, {"status": "ERROR", "message": "Invalid action."})

def start_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((HOST, PORT))
    server_socket.listen(10)
    print(f"Server active")
    print(f"Storage Directory: {STORAGE_DIR}")

    try:
        while True:
            conn, addr = server_socket.accept() #Continuously accepts incoming client connections
            client_thread = threading.Thread(target=connect, args=(conn, addr), daemon=True)
            client_thread.start()
    except KeyboardInterrupt:
        print("Closing server.")
    finally:
        server_socket.close()

if __name__ == "__main__":
    start_server()
