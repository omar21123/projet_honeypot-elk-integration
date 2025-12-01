#!/usr/bin/env python3
# -- coding: utf-8 --

import os
import paramiko
import threading
import json
import time
import socket
import sys
import uuid
import select
import logging
import pty

import seccomp_config

# ============================================================
#   CONFIG & CHEMINS
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(_file_))
LOG_DIR = os.path.join(os.path.dirname(BASE_DIR), "logs")
os.makedirs(LOG_DIR, exist_ok=True)

SSH_LOG_FILE = os.path.join(LOG_DIR, "honeypot_ssh.log")
HOST_KEY_PATH = os.path.join(BASE_DIR, "host_rsa.key")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)


# ============================================================
#   LOGGING JSON
# ============================================================

def log_event(
    event_type, source_ip,
    username=None, password=None,
    command=None, message="",
    session_id=None, cwd=None,
    local_port=None, remote_port=None,
    raw_data=None, extra=None,
):
    entry = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "honeypot_type": "ssh_real",
        "event_type": event_type,
        "source_ip": source_ip,
        "username": username,
        "password": password,
        "command": command,
        "message": message,
        "session_id": session_id,
        "cwd": cwd,
        "local_port": local_port,
        "remote_port": remote_port,
        "raw_data": raw_data,
        "extra": extra or {},
    }
    try:
        with open(SSH_LOG_FILE, "a") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception as e:
        logging.error("Erreur d'écriture log SSH: %s", e)


# ============================================================
#   PARAMIKO SERVER INTERFACE
# ============================================================

class SSHHoneypot(paramiko.ServerInterface):
    def _init_(self, addr, session_id):
        self.event = threading.Event()
        self.addr = addr
        self.session_id = session_id
        self.username = None

    def check_auth_password(self, username, password):
        self.username = username
        log_event(
            "login_attempt", self.addr[0],
            username=username, password=password,
            message="Tentative d'authentification par mot de passe",
            session_id=self.session_id,
            local_port=self.addr[1]
        )
        return paramiko.AUTH_SUCCESSFUL

    def get_allowed_auths(self, username):
        return "password"

    def check_channel_request(self, kind, chanid):
        if kind == "session":
            return paramiko.OPEN_SUCCEEDED
        return paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED

    def check_channel_shell_request(self, channel):
        self.event.set()
        return True

    def check_channel_pty_request(self, channel, term, w, h, pw, ph, modes):
        return True


# ============================================================
#   SHELL RÉEL AVEC PTY (PROMPT HONEYPOT)
# ============================================================

def interactive_bash_shell(chan, client_addr, session_id):
    """
    Lance /bin/bash interactif dans un PTY local, avec cwd = "/",
    ENV et PS1 customisés pour ressembler à un vrai SSH
    root@ssh-honeypot:/# (et pas ton prompt Kali).
    """
    master_fd = None
    try:
        banner = (
            "Welcome to the SSH Honeypot (REAL SHELL)\r\n"
            "WARNING: Everything is logged.\r\n"
        )
        chan.send(banner.encode("utf-8", errors="ignore"))

        # fork un pseudo-terminal
        pid, master_fd = pty.fork()

        if pid == 0:
            # ==============================
            #   PROCESSUS ENFANT (SHELL)
            # ==============================
            try:
                os.chdir("/")
            except Exception:
                pass

            # Environnement "propre" de faux root
            env = os.environ.copy()
            env["HOME"] = "/root"
            env["USER"] = "root"
            env["LOGNAME"] = "root"
            env["SHELL"] = "/bin/bash"
            env["TERM"] = "xterm"
            env["PATH"] = "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"

            # Prompt explicite pour ne pas confondre avec ton vrai Kali
            # \w = répertoire courant
            env["PS1"] = "root@ssh-honeypot:\\w# "

            try:
                # --noprofile/--norc pour éviter ton .bashrc/.profile réels
                os.execve(
                    "/bin/bash",
                    ["/bin/bash", "--noprofile", "--norc", "-i"],
                    env
                )
            except Exception as e:
                os.write(1, f"Erreur execve /bin/bash: {e}\n".encode())
                os._exit(1)

        # ==============================
        #   PROCESSUS PARENT (PONT)
        # ==============================
        while True:
            r, _, _ = select.select([chan, master_fd], [], [])

            # Données venant du client SSH
            if chan in r:
                data = chan.recv(1024)
                if not data:
                    break

                try:
                    decoded = data.decode("utf-8", errors="ignore")
                    if decoded.strip():
                        log_event(
                            "raw_input", client_addr[0],
                            message=decoded,
                            session_id=session_id,
                            local_port=client_addr[1]
                        )
                except Exception:
                    pass

                os.write(master_fd, data)

            # Données venant du shell local
            if master_fd in r:
                out = os.read(master_fd, 1024)
                if not out:
                    break
                chan.send(out)

    except Exception as e:
        log_event(
            "session_error", client_addr[0],
            message=f"Erreur interactive_bash_shell: {e}",
            session_id=session_id,
            local_port=client_addr[1]
        )
    finally:
        try:
            if master_fd is not None:
                os.close(master_fd)
        except Exception:
            pass
        try:
            chan.close()
        except Exception:
            pass


# ============================================================
#   GESTION DES CONNEXIONS
# ============================================================

def handle_ssh_connection(conn, addr, host_key):
    session_id = str(uuid.uuid4())
    transport = paramiko.Transport(conn)
    transport.add_server_key(host_key)

    try:
        log_event(
            "connection_established", addr[0],
            message="Nouvelle connexion SSH entrante",
            session_id=session_id,
            local_port=addr[1]
        )

        server = SSHHoneypot(addr, session_id)
        transport.start_server(server=server)

        chan = transport.accept(20)
        if chan is None:
            log_event(
                "connection_error", addr[0],
                message="Timeout ouverture channel",
                session_id=session_id,
                local_port=addr[1]
            )
            return

        interactive_bash_shell(chan, addr, session_id)

        log_event(
            "connection_closed", addr[0],
            message="Connexion SSH fermée",
            session_id=session_id,
            local_port=addr[1]
        )

    except Exception as e:
        log_event(
            "connection_error", addr[0],
            message=f"Erreur gestion connexion: {e}",
            session_id=session_id,
            local_port=addr[1]
        )
    finally:
        try:
            transport.close()
        except Exception:
            pass


# ============================================================
#   SERVEUR SSH
# ============================================================

def start_ssh_honeypot(host="0.0.0.0", port=2222):
    try:
        host_key = paramiko.RSAKey(filename=HOST_KEY_PATH)

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((host, port))
        sock.listen(100)

        print(f"[*] SSH Honeypot réel en écoute sur {host}:{port}")

        while True:
            conn, addr = sock.accept()
            t = threading.Thread(
                target=handle_ssh_connection,
                args=(conn, addr, host_key),
                daemon=True
            )
            t.start()

    except FileNotFoundError:
        print(f"[-] ERREUR: clé hôte SSH non trouvée. Génère-la avec :", file=sys.stderr)
        print(f"    ssh-keygen -t rsa -b 2048 -f {HOST_KEY_PATH}", file=sys.stderr)
    except Exception as e:
        print(f"[-] Erreur fatale serveur SSH : {e}", file=sys.stderr)
        time.sleep(3)


# ============================================================
#   MAIN
# ============================================================

if _name_ == "_main_":
    print("[*] Application du filtre Seccomp (via SECCOMP_MODE)...")
    seccomp_config.apply_from_env()

    print("[*] Démarrage du SSH Honeypot...")
    start_ssh_honeypot()
