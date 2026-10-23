## Socket-Based Networked File Sharing Cloud Server

The primary objective of this collaborative project is to design, implement, and evaluate a
distributed file-sharing system in the cloud employing a server-client architecture. The
system should facilitate efficient and secure file transfer between multiple clients
connected to a central server.

---

### Project Requirements
- **Server-Client Architecture:** Implement a robust server-client architecture using Python where clients initiate connections to a central server for file requests and transfers. The server and client processes must run on separate computers. A single computer cannot be used to host both the server and clients.
- **File Transfer Protocols:** Utilize appropriate network protocols (e.g., `TCP`, `UDP`) for reliable and efficient file transmission.
- **Multithreading:** Employ multithreading on the server side to handle concurrent client requests and improve system performance.
- **File Types and Sizes:** Support a variety of file types (e.g., `text`, `audio`, `video`) with minimum specified size ranges

---

### File Operations
**Implement the following Client file operations:**
- **Connect [server IP Port]:** Initiates connection from client to server with the specified files.
- **Authentication:** Implement a secure authentication mechanism (e.g., username/password) to restrict access to the file sharing system. Do not transmit password in clear text. Encryption is recommended.
- **Upload [server IP]:** Clients can upload files to the server. Server will prompt client if file already exists and requires user input to be overwritten.
- **Download [filename]:** Clients can download files from the server. Server will respond with error message if file does not exist.
- **Delete:** Clients can delete files from the server. Server will respond with error message if file is currently being processed or does not exist.
- **Dir:** Clients can view a list of files and subdirectories in the server’s file storage path.
- **Subfolder [{create | delete} path/directory]:** Clients can create or subfolders in the server’s file storage path
