import socket
import threading
import os
import datetime
import json
import errno

# ===================== SECCOMP FIX (Block only STOR) =====================
try:
    from pyseccomp import SyscallFilter, ALLOW, ERRNO
    SECCOMP_AVAILABLE = True
except:
    print("[!] pyseccomp non installé — seccomp désactivé")
    SECCOMP_AVAILABLE = False


def enable_seccomp_block_put():
    """
    Version compatible avec toutes les versions pyseccomp.
    """
    if not SECCOMP_AVAILABLE:
        print("[!] Seccomp non actif")
        return

    try:
        flt = SyscallFilter(default=ALLOW)
    except TypeError:
        try:
            flt = SyscallFilter()
        except Exception as e:
            print(f"[!] Version pyseccomp incompatible → seccomp OFF ({e})")
            return

    # Syscalls interdits → impossible d’écrire un fichier (PUT / STOR)
    blocked = [
        "write",
        "pwrite64",
        "truncate",
        "unlink",
        "rename",
        "openat",
        "creat"
    ]

    for sc in blocked:
        try:
            flt.add_rule(ERRNO(errno.EACCES), sc)
        except Exception as e:
            print(f"[!] Impossible de bloquer {sc}: {e}")

    try:
        flt.load()
        print("[+] Seccomp actif : ÉCRITURE bloquée → PUT interdit")
    except Exception as e:
        print(f"[!] Seccomp load() échec : {e}")


# ===================== CONFIG =====================
HOST = "0.0.0.0"
PORT = 2121

LOG_DIR = "/home/kali/Downloads/projet_honeypot-elk-integration/logs/"
HONEYPOT_DIR = "/home/kali/Downloads/projet_honeypot-elk-integration/app/honeypot"

os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(HONEYPOT_DIR, exist_ok=True)

LOG_FILE = os.path.join(LOG_DIR, "honeypot_ftp.log")

FLAG = os.path.join(HONEYPOT_DIR, "flag.txt")
with open(FLAG, "w") as f:
    f.write("FLAG{FTP_HONEYPOT_OK}\n")


# ===================== LOG =====================
def log_event(event_type, session, ip, command=None, extra=None):
    event = {
        "timestamp": datetime.datetime.now().isoformat(),
        "honeypot_type": "ftp",
        "event_type": event_type,
        "source_ip": ip,
        "session_id": session,
        "command": command,
        "extra": extra or {}
    }
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(event) + "\n")
    print(json.dumps(event, indent=2))


# ===================== PASV =====================
def passive_socket(ip, session):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((HOST, 0))
    s.listen(1)
    port = s.getsockname()[1]

    ip_format = "127,0,0,1"
    p1 = port // 256
    p2 = port % 256

    log_event("pasv_open", session, ip)
    return s, f"227 Entering Passive Mode ({ip_format},{p1},{p2})\r\n"


# ===================== CLIENT HANDLER =====================
def handle_client(conn, addr):
    session = os.urandom(8).hex()
    ip_client = addr[0]

    log_event("connection_opened", session, ip_client)
    conn.sendall(b"220 FakeFTP Honeypot Ready\r\n")

    pasv_sock = None
    buffer_cmd = ""

    # ACTIVER SECCOMP
    enable_seccomp_block_put()

    while True:
        try:
            data = conn.recv(4096).decode(errors="ignore")
        except:
            break

        if not data:
            break

        buffer_cmd += data

        while "\r\n" in buffer_cmd:
            line, buffer_cmd = buffer_cmd.split("\r\n", 1)
            line = line.strip()
            if not line:
                continue

            parts = line.split(" ")
            cmd = parts[0].upper()
            arg = " ".join(parts[1:]) if len(parts) > 1 else None

            if cmd not in ["STOR", "RETR"]:
                log_event("command", session, ip_client, command=line)

            # AUTH
            if cmd == "USER":
                conn.sendall(b"331 Password required\r\n")
                continue

            if cmd == "PASS":
                conn.sendall(b"230 Login OK\r\n")
                continue

            if cmd == "TYPE":
                conn.sendall(b"200 Type set\r\n")
                continue

            if cmd == "PWD":
                conn.sendall(b'257 "/" is the current directory\r\n')
                continue

            # PASV
            if cmd == "PASV":
                if pasv_sock:
                    pasv_sock.close()
                pasv_sock, response = passive_socket(ip_client, session)
                conn.sendall(response.encode())
                continue

            # LIST
            if cmd == "LIST":
                if not pasv_sock:
                    conn.sendall(b"425 Use PASV first.\r\n")
                    continue

                conn.sendall(b"150 OK\r\n")
                data_conn, _ = pasv_sock.accept()

                listing = ""
                for f in os.listdir(HONEYPOT_DIR):
                    fp = os.path.join(HONEYPOT_DIR, f)
                    size = os.path.getsize(fp)
                    listing += f"-rw-r--r-- 1 root root {size} Jan 1 00:00 {f}\r\n"

                data_conn.sendall(listing.encode())
                data_conn.close()

                pasv_sock.close()
                pasv_sock = None
                conn.sendall(b"226 List complete\r\n")
                continue

            # RETR (GET)
            if cmd == "RETR":
                if not pasv_sock:
                    conn.sendall(b"425 Use PASV first.\r\n")
                    continue

                fp = os.path.join(HONEYPOT_DIR, arg or "")
                if not os.path.exists(fp):
                    conn.sendall(b"550 File not found\r\n")
                    continue

                conn.sendall(b"150 Opening data connection\r\n")
                data_conn, _ = pasv_sock.accept()

                with open(fp, "rb") as f:
                    while chunk := f.read(4096):
                        data_conn.sendall(chunk)

                data_conn.close()
                pasv_sock.close()
                pasv_sock = None

                conn.sendall(b"226 Transfer complete\r\n")
                log_event("get", session, ip_client, extra={"file": arg})
                continue

            # ===================== STOR BLOQUÉ =====================
            if cmd == "STOR":
                print("⛔ STOR reçu, blocage seccomp :", arg)
                conn.sendall(b"550 Permission denied (seccomp)\r\n")
                log_event("put_blocked", session, ip_client, extra={"file": arg})
                continue

            # QUIT
            if cmd == "QUIT":
                conn.sendall(b"221 Goodbye\r\n")
                log_event("connection_closed", session, ip_client)
                conn.close()
                return

            conn.sendall(b"502 Command not implemented\r\n")


# ===================== SERVER =====================
def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen(5)

    print(f"[+] FTP Honeypot running on port {PORT}")

    while True:
        conn, addr = server.accept()
        threading.Thread(target=handle_client, args=(conn, addr)).start()


if __name__ == "__main__":
    start_server()
