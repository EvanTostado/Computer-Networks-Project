import os
import socket
import threading
import time
import json
import rsa
from tkinter import filedialog, messagebox
import customtkinter as ctk

import clientAuth
import analytics

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class ModernNetworkedFileClientGUI(ctk.CTk):

    def __init__(self):
        #analytics initialization
        self.current_path = ""
        self.selected_file = None
        self.client_label = "Unknown_Client"
        analytics.init_metrics_log()


        super().__init__()

        self.title("File Sharing")
        self.geometry("1000x750")

        self.sock = None
        self.connected = False
        self.BUFFER_SIZE = 64 * 1024
        self.current_path = ""
        self.selected_file = None

        self.create_widgets()

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
            text="System Log",
            font=ctk.CTkFont(size=12, weight="bold"),
        ).pack(side="left")

        self.progress_bar = ctk.CTkProgressBar(bottom_card, orientation="horizontal")
        self.progress_bar.pack(fill="x", padx=15, pady=5)
        self.progress_bar.set(0)

        self.log_textbox = ctk.CTkTextbox(
            bottom_card, height=90, font=("Consolas", 11)
        )
        self.log_textbox.pack(fill="x", padx=15, pady=(0, 15))
        self.log("System initialized. Ready to connect.")

    # def clear_cells(self):
    #     # self.ip_entry.insert(0, "")
    #     # self.port_entry.insert(0, "")
    #     self.user_entry.delete(0, "end")
    #     self.pass_entry.delete(0, "end")

    # def toggle_connection(self):
    #     self.connected_to_server = not self.connected_to_server
    #
    #     if self.connected_to_server:
    #         self.connect_btn.config(text="Disconnect", fg="red")
    #     else:
    #         self.connect_btn.config(text="Connect", fg="#1f538d")

    def toggle_theme(self):
        if self.theme_switch.get() == 1:
            ctk.set_appearance_mode("Dark")
        else:
            ctk.set_appearance_mode("Light")

    def log(self, message):
        self.log_textbox.insert("end", f"[{time.strftime('%H:%M:%S')}] {message}\n")
        self.log_textbox.see("end")

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

        if not ip or not port or not username or not password:
            messagebox.showerror(
                "Error", "Please fill in all connection fields completely."
            )
            return

        self.is_loading = True
        self.animate_progress_pulse()
        self.log(f"Connecting to server at {ip}:{port}...")
        self.log(f"Sock is {self.sock}")

        def background_connect():
            try:
                self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.sock.connect((ip, int(port)))

                #get personel ip to match the metric scheme of the server
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
                self.progress_bar.set(1.0)

                if self.connected and self.sock != None:
                    self.connected = False
                    self.sock = None
                    self.connect_btn.configure(text="Connect", fg_color="#1F6AA5", hover_color="#144870")
                    # self.clear_cells()
                else:
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
                        # CONNECTED_TO_SERVER = False
                        self.log(f"Authentication rejected: {msg}")
                        self.sock.close()
                        self.sock = None
            except Exception as e:
                self.is_loading = False
                self.progress_bar.set(0)
                self.log(f"Connection failure: {str(e)}")

        threading.Thread(target=background_connect, daemon=True).start()

    def refresh_dir(self):
        if not self.sock or not self.connected:
            messagebox.showwarning("Not Connected", "Please connect to the server first.")
            return

        def background_refresh():
            try:
                #start time for analytics metrics for directory refresh latency
                cmd_start = time.perf_counter()

                self.send_json({"command": "DIR", "path": self.current_path})
                res = self.recv_json()

                #store the directory refresh latency metrics for analytics
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

                    # Add back button if inside a subfolder
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
                self.current_path = os.path.join(self.current_path, name)
            else:
                self.current_path = name
            self.refresh_dir()
        else:
            self.selected_file = name
            self.log(f"Selected file: {name}")

    def navigate_up(self):
        self.current_path = os.path.dirname(self.current_path)
        self.refresh_dir()

    def upload_file(self):
        if not self.sock or not self.connected:
            messagebox.showwarning("Not Connected", "Please connect first.")
            return

        file_path = filedialog.askopenfilename()
        if file_path:
            filename = os.path.basename(file_path)
            file_size = os.path.getsize(file_path)

            def background_upload():
                try:
                    self.is_loading = True
                    self.animate_progress_pulse()

                    self.send_json({
                        "command": "UPLOAD",
                        "filename": filename,
                        "filesize": file_size,
                        "path": self.current_path,
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
                                "path": self.current_path,
                                "overwrite": True,
                            })
                            res = self.recv_json()
                        else:
                            self.is_loading = False
                            self.progress_bar.set(0)
                            self.log("Upload canceled by user.")
                            return

                    if res and res.get("status") == "READY":
                        #information gathering for analytics
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

                        final_res = self.recv_json()

                        elapsed = time.perf_counter() - perf_start #time it took to upload the file
                        
                        #make a record of the upload metrics for later analysis
                        analytics.record_metric(
                                source="CLIENT",
                                client_id=self.client_label,
                                operation="UPLOAD",
                                file_type=file_ext,
                                file_size_bytes=sent,
                                elapsed_sec=elapsed
                        )

                        self.is_loading = False
                        self.progress_bar.set(1.0)
                        if final_res and final_res.get("status") == "SUCCESS":
                            self.log(f"Successfully uploaded '{filename}'.")
                            self.refresh_dir()
                        else:
                            self.log("Upload failed during streaming.")
                    else:
                        self.is_loading = False
                        self.progress_bar.set(0)
                        self.log(
                            f"Server rejected upload: {res.get('message') if res else ''}"
                        )
                except Exception as e:
                    self.is_loading = False
                    self.progress_bar.set(0)
                    self.log(f"Upload error: {e}")

            threading.Thread(target=background_upload, daemon=True).start()

    def download_file(self):
        if not self.sock or not self.connected:
            messagebox.showwarning("Not Connected", "Please connect first.")
            return
        if not self.selected_file:
            messagebox.showwarning("Selection Required", "Please select a file first.")
            return

        save_path = filedialog.asksaveasfilename(initialfile=self.selected_file)
        if save_path:

            def background_download():
                try:
                    self.is_loading = True
                    self.animate_progress_pulse()

                    self.send_json({
                        "command": "DOWNLOAD",
                        "filename": self.selected_file,
                        "path": self.current_path,
                    })

                    res = self.recv_json()
                    if res and res.get("status") == "READY":
                        filesize = res.get("filesize")

                        #start gathering analytics data for the download
                        file_ext = os.path.splitext(self.selected_file)[1].replace(".", "").upper() or "UNKNOWN"
                        perf_start = time.perf_counter()

                        
                        self.send_json({"status": "START"})

                        received = 0
                        with open(save_path, "wb") as f:
                            while received < filesize:
                                chunk = self.sock.recv(
                                    min(self.BUFFER_SIZE, filesize - received)
                                )
                                if not chunk:
                                    break
                                f.write(chunk)
                                received += len(chunk)

                        #store analytics data for the download operation
                        elapsed = time.perf_counter() - perf_start
                        analytics.record_metric(
                            source="CLIENT",
                            client_id=self.client_label,
                            operation="DOWNLOAD",
                            file_type=file_ext,
                            file_size_bytes=received,
                            elapsed_sec=elapsed
                        )

                        self.is_loading = False
                        self.progress_bar.set(1.0)
                        self.log(f"Downloaded '{self.selected_file}' successfully.")
                    else:
                        self.is_loading = False
                        self.progress_bar.set(0)
                        self.log(
                            f"Download error: {res.get('message') if res else 'Unknown'}"
                        )
                except Exception as e:
                    self.is_loading = False
                    self.progress_bar.set(0)
                    self.log(f"Download exception: {e}")

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
            messagebox.showwarning("Input Required", "Enter a subfolder name.")
            return

        target_sub_path = (
            os.path.join(self.current_path, folder_name)
            if self.current_path
            else folder_name
        )

        def background_subfolder():
            try:
                self.send_json({
                    "command": "SUBFOLDER",
                    "action": action,
                    "path": target_sub_path,
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
