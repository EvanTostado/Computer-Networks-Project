import os
import socket
import threading
import time
from tkinter import filedialog, messagebox
import customtkinter as ctk

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")


class ModernNetworkedFileClientGUI(ctk.CTk):

    def __init__(self):
        super().__init__()

        self.title("Secure Cloud File Sharing Client")
        self.geometry("950x700")

        self.sock = None
        self.connected = False
        self.SIZE = 1024
        self.FORMAT = "utf-8"

        self.create_widgets()

    def create_widgets(self):
        # Header Frame
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=(20, 10))

        title_label = ctk.CTkLabel(
            header_frame,
            text="Secure Cloud File Sharing Client",
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
        self.user_entry = ctk.CTkEntry(conn_grid, width=110)
        self.user_entry.grid(row=0, column=5, padx=5, pady=5)

        ctk.CTkLabel(conn_grid, text="Password:", font=("Arial", 12)).grid(
            row=0, column=6, padx=5, pady=5, sticky="w"
        )
        self.pass_entry = ctk.CTkEntry(conn_grid, width=110, show="*")
        self.pass_entry.grid(row=0, column=7, padx=5, pady=5)

        self.connect_btn = ctk.CTkButton(
            conn_grid,
            text="Connect",
            width=110,
            command=self.connect_to_server,
            corner_radius=8,
        )
        self.connect_btn.grid(row=0, column=8, padx=10, pady=5)

        body_frame = ctk.CTkFrame(self, fg_color="transparent")
        body_frame.pack(fill="both", expand=True, padx=20, pady=10)

        left_card = ctk.CTkFrame(body_frame, corner_radius=12)
        left_card.pack(side="left", fill="both", expand=True, padx=(0, 10))

        ctk.CTkLabel(
            left_card,
            text="Server File Storage",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(anchor="w", padx=15, pady=(15, 5))

        self.file_scroll_frame = ctk.CTkScrollableFrame(
            left_card, corner_radius=8, fg_color=("gray92", "gray14")
        )
        self.file_scroll_frame.pack(
            fill="both", expand=True, padx=15, pady=(0, 15)
        )

        self.selected_file = None

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
        ).pack(pady=6)
        ctk.CTkButton(
            right_card,
            text="Upload File...",
            width=btn_width,
            command=self.upload_file,
        ).pack(pady=6)
        ctk.CTkButton(
            right_card,
            text="Download Selected",
            width=btn_width,
            command=self.download_file,
        ).pack(pady=6)
        ctk.CTkButton(
            right_card,
            text="Delete Selected",
            width=btn_width,
            fg_color="#c0392b",
            hover_color="#962d22",
            command=self.delete_file,
        ).pack(pady=6)

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
            bottom_card, height=100, font=("Consolas", 11)
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

        def background_connect():
            try:
                self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.sock.connect((ip, int(port)))


                auth_payload = f"AUTH@{username}@{password}"
                self.sock.sendall(auth_payload.encode(self.FORMAT))

                response = self.sock.recv(self.SIZE).decode(self.FORMAT)
                self.is_loading = False
                self.progress_bar.set(1.0)

                if "OK" in response or "AUTH_SUCCESS" in response:
                    self.connected = True
                    self.connect_btn.configure(text="Connected", fg_color="#27ae60")
                    self.log("Authentication successful! Secure session established.")
                    self.refresh_dir()
                else:
                    self.log("Authentication rejected by server.")
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
                self.sock.sendall("LIST@".encode(self.FORMAT))
                response = self.sock.recv(self.SIZE).decode(self.FORMAT)


                for widget in self.file_scroll_frame.winfo_children():
                    widget.destroy()


                if "@" in response:
                    cmd, msg = response.split("@", 1)
                    if cmd == "OK" and msg.strip():
                        files = msg.split(",")
                        for fname in files:
                            if fname:
                                btn = ctk.CTkButton(
                                    self.file_scroll_frame,
                                    text=fname.strip(),
                                    anchor="w",
                                    fg_color="transparent",
                                    text_color=("black", "white"),
                                    hover_color=("gray80", "gray25"),
                                    command=lambda fn=fname.strip(): self.select_file(fn),
                                )
                                btn.pack(fill="x", pady=2)
                self.log("Directory refreshed successfully.")
            except Exception as e:
                self.log(f"Failed to refresh directory: {e}")

        threading.Thread(target=background_refresh, daemon=True).start()

    def select_file(self, filename):
        self.selected_file = filename
        self.log(f"Selected file: {filename}")

    def upload_file(self):
        if not self.sock or not self.connected:
            messagebox.showwarning("Not Connected", "Please connect to the server first.")
            return

        file_path = filedialog.askopenfilename()
        if file_path:
            filename = os.path.basename(file_path)
            file_size = os.path.getsize(file_path)

            def background_upload():
                try:
                    self.is_loading = True
                    self.animate_progress_pulse()


                    header = f"UPLOAD@{filename}@{file_size}"
                    self.sock.sendall(header.encode(self.FORMAT))


                    with open(file_path, "rb") as f:
                        while chunk := f.read(self.SIZE):
                            self.sock.sendall(chunk)

                    response = self.sock.recv(self.SIZE).decode(self.FORMAT)
                    self.is_loading = False
                    self.progress_bar.set(1.0)
                    self.log(f"Successfully uploaded '{filename}' ({file_size / (1024 * 1024):.2f} MB).")
                    self.refresh_dir()
                except Exception as e:
                    self.is_loading = False
                    self.progress_bar.set(0)
                    self.log(f"Upload failed: {e}")

            threading.Thread(target=background_upload, daemon=True).start()

    def download_file(self):
        if not self.sock or not self.connected:
            messagebox.showwarning("Not Connected", "Please connect to the server first.")
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

                    command = f"DOWNLOAD@{self.selected_file}"
                    self.sock.sendall(command.encode(self.FORMAT))


                    with open(save_path, "wb") as f:
                        data = self.sock.recv(self.SIZE)
                        f.write(data)

                    self.is_loading = False
                    self.progress_bar.set(1.0)
                    self.log(f"Downloaded '{self.selected_file}' successfully.")
                except Exception as e:
                    self.is_loading = False
                    self.progress_bar.set(0)
                    self.log(f"Download failed: {e}")

            threading.Thread(target=background_download, daemon=True).start()

    def delete_file(self):
        if not self.sock or not self.connected:
            messagebox.showwarning("Not Connected", "Please connect to the server first.")
            return
        if not self.selected_file:
            messagebox.showwarning("Selection Required", "Please select a file first.")
            return

        if messagebox.askyesno("Confirm Delete", f"Delete {self.selected_file} from server?"):
            def background_delete():
                try:
                    command = f"DELETE@{self.selected_file}"
                    self.sock.sendall(command.encode(self.FORMAT))
                    response = self.sock.recv(self.SIZE).decode(self.FORMAT)
                    self.log(f"Delete response: {response}")
                    self.refresh_dir()
                except Exception as e:
                    self.log(f"Delete failed: {e}")

            threading.Thread(target=background_delete, daemon=True).start()


if __name__ == "__main__":
    app = ModernNetworkedFileClientGUI()
    app.mainloop()
