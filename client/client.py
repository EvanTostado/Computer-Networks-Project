import os
import sys
import socket
import threading
import time
import json
import hashlib
import rsa
from tkinter import filedialog, messagebox
import customtkinter as ctk

AUTH_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "authentication"))
if AUTH_DIR not in sys.path:
    sys.path.insert(0, AUTH_DIR)

ANALYTICS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "analytics"))
if ANALYTICS_DIR not in sys.path:
    sys.path.insert(0, ANALYTICS_DIR)

#import python files from other folders to help with connection and auth and analytics
import clientAuth
import analytics

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")


class ModernNetworkedFileClientGUI(ctk.CTk):

    def __init__(self):
        # analytics initialization
        self.current_path = ""
        self.selected_file = None
        self.client_label = "Unknown_Client"
        analytics.init_metrics_log()

        super().__init__()

        self.title("File Sharing")
        self.geometry("1000x780")

        self.sock = None
        self.connected = False
        self.BUFFER_SIZE = 64 * 1024
        self.current_path = ""
        self.selected_file = None

        self.create_widgets()

    # GUI objects display on screen
    def create_widgets(self):
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=(20, 10))

        title_label = ctk.CTkLabel(
            header_frame,
            text="File Sharing",
            font=ctk.CTkFont(family="Arial", size=22, weight="bold"),
        )
        title_label.pack(side="left")

        self.theme_switch = ctk.CTkSwitch(
            header_frame, text="Dark Mode", command=self.toggle_theme
        )
        self.theme_switch.select()
        self.theme_switch.pack(side="right")

        conn_card = ctk.CTkFrame(self, corner_radius=12)
        conn_card.pack(fill="x", padx=20, pady=10)

        conn_grid = ctk.CTkFrame(conn_card, fg_color="transparent")
        conn_grid.pack(padx=15, pady=15, fill="x")

        # Input boxes to connect to the server
        ctk.CTkLabel(conn_grid, text="Server IP:", font=("Arial", 12)).grid(
            row=0, column=0, padx=5, pady=5, sticky="w"
        )
        self.ip_entry = ctk.CTkEntry(conn_grid, width=120)
        self.ip_entry.insert(0, "172.20.10.2")
        self.ip_entry.grid(row=0, column=1, padx=5, pady=5)

        ctk.CTkLabel(conn_grid, text="Port:", font=("Arial", 12)).grid(
            row=0, column=2, padx=5, pady=5, sticky="w"
        )
        self.port_entry = ctk.CTkEntry(conn_grid, width=70)
        self.port_entry.insert(0, "4450")
        self.port_entry.grid(row=0, column=3, padx=5, pady=5)

        ctk.CTkLabel(conn_grid, text="Username:", font=("Arial", 12)).grid(
            row=0, column=4, padx=5, pady=5, sticky="w"
        )
        self.user_entry = ctk.CTkEntry(conn_grid, width=100)
        self.user_entry.insert(0, "test_user")
        self.user_entry.grid(row=0, column=5, padx=5, pady=5)

        ctk.CTkLabel(conn_grid, text="Password:", font=("Arial", 12)).grid(
            row=0, column=6, padx=5, pady=5, sticky="w"
        )
        self.pass_entry = ctk.CTkEntry(conn_grid, width=100, show="*")
        self.pass_entry.insert(0, "this_is_a_test")
        self.pass_entry.grid(row=0, column=7, padx=5, pady=5)

        self.connect_btn = ctk.CTkButton(
            conn_grid,
            text="Connect",
            width=100,
            command=self.connect_to_server,
            corner_radius=8,
        )
        self.connect_btn.grid(row=0, column=8, padx=10, pady=5)

        body_frame = ctk.CTkFrame(self, fg_color="transparent")
        body_frame.pack(fill="both", expand=True, padx=20, pady=10)

        left_card = ctk.CTkFrame(body_frame, corner_radius=12)
        left_card.pack(side="left", fill="both", expand=True, padx=(0, 10))

        path_frame = ctk.CTkFrame(left_card, fg_color="transparent")
        path_frame.pack(fill="x", padx=15, pady=(15, 5))

        # Dir displays files and folders
        ctk.CTkLabel(
            path_frame,
            text="Server File Storage",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(side="left")

        self.path_label = ctk.CTkLabel(
            path_frame, text="Path: /", font=ctk.CTkFont(size=12, slant="italic")
        )
        self.path_label.pack(side="right")

        self.file_scroll_frame = ctk.CTkScrollableFrame(
            left_card, corner_radius=8, fg_color=("gray92", "gray14")
        )
        self.file_scroll_frame.pack(
            fill="both", expand=True, padx=15, pady=(0, 15)
        )

        right_card = ctk.CTkFrame(body_frame, width=260, corner_radius=12)
        right_card.pack(side="right", fill="y", padx=(10, 0))
        right_card.pack_propagate(False)

        # Right card actions and buttons
        ctk.CTkLabel(
            right_card,
            text="File Actions",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(anchor="w", padx=15, pady=(15, 10))

        btn_width = 210
        ctk.CTkButton(
            right_card,
            text="Refresh Directory",
            width=btn_width,
            command=self.refresh_dir,
        ).pack(pady=5)
        ctk.CTkButton(
            right_card,
            text="Upload File",
            width=btn_width,
            command=self.upload_file,
        ).pack(pady=5)
        ctk.CTkButton(
            right_card,
            text="Continue Upload",
            width=btn_width,
            command=self.resume_upload_file,
        ).pack(pady=5)
        ctk.CTkButton(
            right_card,
            text="Download Selected",
            width=btn_width,
            command=self.download_file,
        ).pack(pady=5)
        ctk.CTkButton(
            right_card,
            text="Delete Selected",
            width=btn_width,
            fg_color="#c0392b",
            hover_color="#962d22",
            command=self.delete_file,
        ).pack(pady=5)

        ctk.CTkLabel(
            right_card,
            text="Subfolder Management",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).pack(anchor="w", padx=15, pady=(15, 2))

        self.subfolder_entry = ctk.CTkEntry(
            right_card, width=btn_width, placeholder_text="Folder name..."
        )
        self.subfolder_entry.pack(padx=15, pady=2)

        ctk.CTkButton(
            right_card,
            text="Create Subfolder",
            width=btn_width,
            fg_color="#27ae60",
            hover_color="#1e8449",
            command=lambda: self.manage_subfolder("create"),
        ).pack(pady=5)
        ctk.CTkButton(
            right_card,
            text="Delete Subfolder",
            width=btn_width,
            fg_color="#d35400",
            hover_color="#b9770e",
            command=lambda: self.manage_subfolder("delete"),
        ).pack(pady=5)

        bottom_card = ctk.CTkFrame(self, corner_radius=12)
        bottom_card.pack(fill="x", padx=20, pady=(0, 20))

        log_top_frame = ctk.CTkFrame(bottom_card, fg_color="transparent")
        log_top_frame.pack(fill="x", padx=15, pady=(10, 0))

        ctk.CTkLabel(
            log_top_frame,
            text="System Log & Transfer Progress",
            font=ctk.CTkFont(size=12, weight="bold"),
        ).pack(side="left")

        self.progress_label = ctk.CTkLabel(
            log_top_frame, text="Idle", font=ctk.CTkFont(size=11)
        )
        self.progress_label.pack(side="right")

        self.progress_bar = ctk.CTkProgressBar(bottom_card, orientation="horizontal")
        self.progress_bar.pack(fill="x", padx=15, pady=5)
        self.progress_bar.set(0)

        self.log_textbox = ctk.CTkTextbox(
            bottom_card, height=90, font=("Consolas", 11)
        )
        self.log_textbox.pack(fill="x", padx=15, pady=(0, 15))
        self.log("System initialized. Ready to connect.")

    def toggle_theme(self):
        if self.theme_switch.get() == 1:
            ctk.set_appearance_mode("Dark")
        else:
            ctk.set_appearance_mode("Light")

    def log(self, message):
        self.log_textbox.insert("end", f"[{time.strftime('%H:%M:%S')}] {message}\n")
        self.log_textbox.see("end")

    # convert bytes into MB/KB strings
    def format_bytes(self, size_bytes):
        if size_bytes == 0:
            return "0 B"
        size_name = ("B", "KB", "MB", "GB")
        i = 0
        p = size_bytes
        while p >= 1024 and i < len(size_name) - 1:
            p /= 1024.0
            i += 1
        return f"{p:.2f} {size_name[i]}"

    # updates the progress bar from background threads
    def update_progress_ui(self, current, total):
        if total > 0:
            fraction = min(max(current / total, 0.0), 1.0)
            percentage = fraction * 100
            curr_str = self.format_bytes(current)
            total_str = self.format_bytes(total)
            text_str = f"{curr_str} / {total_str} ({percentage:.1f}%)"
        else:
            fraction = 0.0
            text_str = "Idle"

        def _apply():
            self.progress_bar.set(fraction)
            self.progress_label.configure(text=text_str)

        self.after(0, _apply)

    # Progress bar changes for connecting/authenticating
    def animate_progress_pulse(self):
        def pulse():
            for i in range(0, 100, 5):
                if not getattr(self, "is_loading", False):
                    break
                self.progress_bar.set(i / 100.0)
                time.sleep(0.03)
            for i in range(100, 0, -5):
                if not getattr(self, "is_loading", False):
                    break
                self.progress_bar.set(i / 100.0)
                time.sleep(0.03)
            if getattr(self, "is_loading", False):
                self.animate_progress_pulse()

        threading.Thread(target=pulse, daemon=True).start()

    def send_json(self, data: dict):
        payload = json.dumps(data).encode("utf-8")
        length = len(payload)
        self.sock.sendall(length.to_bytes(4, byteorder="big") + payload)

    def recv_json(self) -> dict:
        raw_length = self.sock.recv(4)
        if not raw_length:
            return None
        length = int.from_bytes(raw_length, byteorder="big")
        data = bytearray()
        while len(data) < length:
            packet = self.sock.recv(length - len(data))
            if not packet:
                return None
            data.extend(packet)
        return json.loads(data.decode("utf-8"))

    def connect_to_server(self):
        ip = self.ip_entry.get()
        port = self.port_entry.get()
        username = self.user_entry.get()
        password = self.pass_entry.get()

        if self.connected:
            try:
                if self.sock:
                    self.sock.close()
            except Exception:
                pass
            self.sock = None
            self.connected = False
            self.connect_btn.configure(text="Connect", fg_color="#1F6AA5", hover_color="#144870")
            self.log("Disconnected from server.")
            return

        if not ip or not port or not username or not password:
            messagebox.showerror(
                "Error", "Please fill in all connection fields completely."
            )
            return

        self.is_loading = True
        self.progress_label.configure(text="Connecting...")
        self.animate_progress_pulse()
        self.log(f"Connecting to server at {ip}:{port}...")

        def background_connect():
            try:
                self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.sock.connect((ip, int(port)))

                local_ip, local_port = self.sock.getsockname()
                self.client_label = f"{local_ip}:{local_port}"

                self.send_json({"command": "GET_PUBKEY"})
                res = self.recv_json()

                if not res or res.get("status") != "SUCCESS":
                    raise Exception("Failed to retrieve public key from server.")

                pub_bytes = res.get("pubkey").encode("utf-8")
                public_key = rsa.PublicKey.load_pkcs1(pub_bytes)

                enc_user = clientAuth.encryptPassword(username, public_key)
                enc_pass = clientAuth.encryptPassword(password, public_key)

                self.send_json({
                    "command": "AUTH",
                    "username": enc_user.hex(),
                    "password": enc_pass.hex(),
                })

                auth_res = self.recv_json()
                self.is_loading = False
                self.update_progress_ui(1, 1)

                if auth_res and auth_res.get("status") == "SUCCESS":
                    self.connected = True
                    self.connect_btn.configure(text="Disconnect", fg_color="red", hover_color="darkred")
                    self.log("Authentication successful")
                    self.refresh_dir()
                else:
                    msg = (
                        auth_res.get("message", "Unknown error")
                        if auth_res
                        else "No response"
                    )
                    self.log(f"Authentication rejected: {msg}")
                    self.sock.close()
                    self.sock = None
            except Exception as e:
                self.is_loading = False
                self.update_progress_ui(0, 1)
                self.log(f"Connection failure: {str(e)}")

        threading.Thread(target=background_connect, daemon=True).start()

    # Refreshes the Directory
    def refresh_dir(self):
        if not self.sock or not self.connected:
            messagebox.showwarning("Not Connected", "Please connect to the server first.")
            return

        def background_refresh():
            try:
                cmd_start = time.perf_counter()

                self.send_json({"command": "DIR", "path": self.current_path})
                res = self.recv_json()

                elapsed = time.perf_counter() - cmd_start
                analytics.record_metric(
                    source="CLIENT",
                    client_id=self.client_label,
                    operation="DIR",
                    file_type="N/A",
                    file_size_bytes=0,
                    elapsed_sec=elapsed
                )

                for widget in self.file_scroll_frame.winfo_children():
                    widget.destroy()

                if res and res.get("status") == "SUCCESS":
                    items = res.get("items", [])

                    if self.current_path:
                        back_btn = ctk.CTkButton(
                            self.file_scroll_frame,
                            text=".. (Parent Directory)",
                            anchor="w",
                            fg_color="transparent",
                            text_color=("black", "white"),
                            hover_color=("gray80", "gray25"),
                            command=self.navigate_up,
                        )
                        back_btn.pack(fill="x", pady=2)

                    for item in items:
                        name = item["name"]
                        is_dir = item["is_dir"]
                        size = item["size"]

                        if not self.current_path and ("/" in name or "\\" in name):
                            continue

                        display_text = (
                            f"[Folder] {name}"
                            if is_dir
                            else f"{name}  ({size / 1024:.1f} KB)"
                        )

                        btn = ctk.CTkButton(
                            self.file_scroll_frame,
                            text=display_text,
                            anchor="w",
                            fg_color="transparent",
                            text_color=("black", "white"),
                            hover_color=("gray80", "gray25"),
                            command=lambda n=name, d=is_dir: self.handle_item_click(n, d),
                        )
                        btn.pack(fill="x", pady=2)
                    self.path_label.configure(
                        text=f"Path: /{self.current_path}" if self.current_path else "Path: /"
                    )
                    self.log("Directory refreshed successfully.")
                else:
                    self.log("Failed to load directory items.")
            except Exception as e:
                self.log(f"Directory refresh error: {e}")

        threading.Thread(target=background_refresh, daemon=True).start()

    def handle_item_click(self, name, is_dir):
        if is_dir:
            if self.current_path:
                self.current_path = f"{self.current_path}/{name}"
            else:
                self.current_path = name
            self.refresh_dir()
        else:
            self.selected_file = name
            self.log(f"Selected file: {name}")

    def navigate_up(self):
        if "/" in self.current_path:
            self.current_path = self.current_path.rsplit("/", 1)[0]
        else:
            self.current_path = ""
        self.refresh_dir()

    # Upload the file
    def upload_file(self):
        if not self.sock or not self.connected:
            messagebox.showwarning("Not Connected", "Please connect first.")
            return

        file_path = filedialog.askopenfilename()
        if file_path:
            filename = os.path.basename(file_path)
            file_size = os.path.getsize(file_path)

            normalized_path = self.current_path.replace("\\", "/")

            def background_upload():
                try:
                    self.send_json({
                        "command": "UPLOAD",
                        "filename": filename,
                        "filesize": file_size,
                        "path": normalized_path,
                        "overwrite": False,
                    })

                    res = self.recv_json()
                    if res and res.get("status") == "EXISTS":
                        if messagebox.askyesno(
                                "Overwrite?",
                                f"'{filename}' already exists. Do you want to overwrite it?",
                        ):
                            self.send_json({
                                "command": "UPLOAD",
                                "filename": filename,
                                "filesize": file_size,
                                "path": normalized_path,
                                "overwrite": True,
                            })
                            res = self.recv_json()
                        else:
                            self.update_progress_ui(0, 1)
                            self.log("Upload canceled by user.")
                            return

                    if res and res.get("status") == "READY":
                        file_ext = os.path.splitext(filename)[1].replace(".", "").upper() or "UNKNOWN"
                        perf_start = time.perf_counter()

                        with open(file_path, "rb") as f:
                            sent = 0
                            while sent < file_size:
                                chunk = f.read(self.BUFFER_SIZE)
                                if not chunk:
                                    break
                                self.sock.sendall(chunk)
                                sent += len(chunk)
                                self.update_progress_ui(sent, file_size)

                        final_res = self.recv_json()
                        elapsed = time.perf_counter() - perf_start

                        analytics.record_metric(
                            source="CLIENT",
                            client_id=self.client_label,
                            operation="UPLOAD",
                            file_type=file_ext,
                            file_size_bytes=sent,
                            elapsed_sec=elapsed
                        )

                        if final_res and final_res.get("status") == "SUCCESS":
                            self.log(f"Successfully uploaded '{filename}'.")
                            self.refresh_dir()
                        else:
                            self.log("Upload failed during streaming.")
                    else:
                        self.update_progress_ui(0, 1)
                        self.log(
                            f"Server rejected upload: {res.get('message') if res else ''}"
                        )
                except Exception as e:
                    self.update_progress_ui(0, 1)
                    self.log(f"Upload error: {e}")

            threading.Thread(target=background_upload, daemon=True).start()

    # Resumes uploading a local file if interrupted
    def resume_upload_file(self):
        if not self.sock or not self.connected:
            messagebox.showwarning("Not Connected", "Please connect first.")
            return

        file_path = filedialog.askopenfilename(title="Select file to resume uploading")
        if not file_path:
            return

        filename = os.path.basename(file_path)
        total_filesize = os.path.getsize(file_path)
        normalized_path = self.current_path.replace("\\", "/")

        def background_resume_upload():
            try:
                # send RESUME_UPLOAD request to check existing partial size on the server
                self.send_json({
                    "command": "RESUME_UPLOAD",
                    "filename": filename,
                    "path": normalized_path,
                    "filesize": total_filesize
                })

                res = self.recv_json()
                if res and res.get("status") == "READY":
                    server_offset = res.get("offset", 0)
                    file_ext = os.path.splitext(filename)[1].replace(".", "").upper() or "UNKNOWN"
                    perf_start = time.perf_counter()

                    if server_offset >= total_filesize:
                        self.log(f"File '{filename}' is already fully uploaded on server.")
                        self.update_progress_ui(total_filesize, total_filesize)
                        return

                    sent = server_offset
                    self.log(f"Resuming upload for '{filename}' from byte {server_offset}/{total_filesize}...")

                    # open local file in binary read mode
                    with open(file_path, "rb") as f:
                        f.seek(server_offset)
                        while sent < total_filesize:
                            chunk = f.read(self.BUFFER_SIZE)
                            if not chunk:
                                break
                            self.sock.sendall(chunk)
                            sent += len(chunk)
                            self.update_progress_ui(sent, total_filesize)

                    # receive final status from server
                    final_res = self.recv_json()
                    elapsed = time.perf_counter() - perf_start

                    if final_res and final_res.get("status") == "SUCCESS":
                        self.log(f"Successfully resumed and completed upload for '{filename}'.")
                        analytics.record_metric(
                            source="CLIENT",
                            client_id=self.client_label,
                            operation="UPLOAD_RESUME",
                            file_type=file_ext,
                            file_size_bytes=(total_filesize - server_offset),
                            elapsed_sec=elapsed
                        )
                        self.refresh_dir()
                    else:
                        self.log(f"Resume upload failed: {final_res.get('message') if final_res else 'Unknown error'}")
                else:
                    self.update_progress_ui(0, 1)
                    self.log(f"Server rejected resume upload: {res.get('message') if res else 'Unknown error'}")

            except Exception as e:
                self.update_progress_ui(0, 1)
                self.log(f"Resume upload exception: {e}")

        threading.Thread(target=background_resume_upload, daemon=True).start()

    def download_file(self):
        if not self.sock or not self.connected:
            messagebox.showwarning("Not Connected", "Please connect first.")
            return
        if not self.selected_file:
            messagebox.showwarning("Selection Required", "Please select a file first.")
            return

        save_path = filedialog.asksaveasfilename(initialfile=self.selected_file)
        if not save_path:
            return

        def background_download():
            try:
                # determine local file size
                local_bytes = 0
                if os.path.exists(save_path):
                    local_bytes = os.path.getsize(save_path)

                # send RESUME_DOWNLOAD command
                self.send_json({
                    "command": "RESUME_DOWNLOAD",
                    "filename": self.selected_file,
                    "path": self.current_path,
                    "offset": local_bytes
                })

                res = self.recv_json()
                if res and res.get("status") == "READY":
                    total_filesize = res.get("filesize")
                    file_ext = os.path.splitext(self.selected_file)[1].replace(".", "").upper() or "UNKNOWN"
                    perf_start = time.perf_counter()

                    self.send_json({"status": "START"})

                    if local_bytes >= total_filesize:
                        self.log(f"File '{self.selected_file}' is already fully downloaded.")
                        self.update_progress_ui(total_filesize, total_filesize)
                    else:
                        received = local_bytes
                        self.log(
                            f"Resuming download for '{self.selected_file}' from byte {local_bytes}/{total_filesize}...")

                        # open file in append mode save downloaded bytes
                        with open(save_path, "ab") as f:
                            while received < total_filesize:
                                chunk = self.sock.recv(
                                    min(self.BUFFER_SIZE, total_filesize - received)
                                )
                                if not chunk:
                                    break
                                f.write(chunk)
                                received += len(chunk)
                                self.update_progress_ui(received, total_filesize)

                    # receive and verify from server
                    hash_res = self.recv_json()
                    elapsed = time.perf_counter() - perf_start

                    if hash_res and hash_res.get("status") == "HASH":
                        server_sha256 = hash_res.get("sha256")

                        sha256_hash = hashlib.sha256()
                        with open(save_path, "rb") as f:
                            for byte_block in iter(lambda: f.read(4096), b""):
                                sha256_hash.update(byte_block)
                        local_sha256 = sha256_hash.hexdigest()

                        if local_sha256 == server_sha256:
                            self.log(f"Integrity verified (SHA-256 match): {local_sha256[:12]}...")
                            analytics.record_metric(
                                source="CLIENT",
                                client_id=self.client_label,
                                operation="DOWNLOAD_RESUME",
                                file_type=file_ext,
                                file_size_bytes=(total_filesize - local_bytes),
                                elapsed_sec=elapsed
                            )
                            self.log(f"Successfully downloaded/resumed '{self.selected_file}'.")
                        else:
                            self.log("WARNING: SHA-256 integrity check failed! File may be corrupted.")
                            messagebox.showerror("Integrity Error", "Downloaded file hash does not match server hash.")
                    else:
                        self.log("Download completed, but server did not provide a verification hash.")

                else:
                    self.update_progress_ui(0, 1)
                    self.log(f"Download error: {res.get('message') if res else 'Unknown'}")

            except Exception as e:
                self.update_progress_ui(0, 1)
                self.log(f"Download exception (connection lost): {e}")

        threading.Thread(target=background_download, daemon=True).start()

    def delete_file(self):
        if not self.sock or not self.connected:
            messagebox.showwarning("Not Connected", "Please connect first.")
            return
        if not self.selected_file:
            messagebox.showwarning("Selection Required", "Please select a file first.")
            return

        if messagebox.askyesno(
                "Confirm Delete", f"Delete '{self.selected_file}' from server?"
        ):

            def background_delete():
                try:
                    self.send_json({
                        "command": "DELETE",
                        "filename": self.selected_file,
                        "path": self.current_path,
                    })
                    res = self.recv_json()
                    if res and res.get("status") == "SUCCESS":
                        self.log(f"Deleted '{self.selected_file}' successfully.")
                        self.selected_file = None
                        self.refresh_dir()
                    else:
                        self.log(f"Delete failed: {res.get('message') if res else ''}")
                except Exception as e:
                    self.log(f"Delete error: {e}")

            threading.Thread(target=background_delete, daemon=True).start()

    def manage_subfolder(self, action):
        if not self.sock or not self.connected:
            messagebox.showwarning("Not Connected", "Please connect first.")
            return

        folder_name = self.subfolder_entry.get().strip()
        if not folder_name:
            messagebox.showwarning("Input Required", "Enter a subfolder name or path.")
            return

        normalized_folder_path = folder_name.replace("\\", "/")

        if self.current_path:
            target_sub_path = os.path.normpath(os.path.join(self.current_path, normalized_folder_path))
        else:
            target_sub_path = os.path.normpath(normalized_folder_path)

        def background_subfolder():
            try:
                self.send_json({
                    "command": "SUBFOLDER",
                    "action": action,
                    "path": target_sub_path.replace("\\", "/"),
                })
                res = self.recv_json()
                if res and res.get("status") == "SUCCESS":
                    self.log(res.get("message"))
                    self.subfolder_entry.delete(0, "end")
                    self.refresh_dir()
                else:
                    self.log(
                        f"Subfolder action failed: {res.get('message') if res else ''}"
                    )
            except Exception as e:
                self.log(f"Subfolder error: {e}")

        threading.Thread(target=background_subfolder, daemon=True).start()


if __name__ == "__main__":
    app = ModernNetworkedFileClientGUI()
    app.mainloop()
