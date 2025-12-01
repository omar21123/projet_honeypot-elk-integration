🛡️ Honeypot & ELK Integration

Ce projet met en place un honeypot multi‑services intégré à une stack ELK :

🔹 HTTP Honeypot via Flask (app.py)

🔹 SSH Honeypot (ssh_honeypot.py)

🔹 FTP Honeypot avancé (ftp_honeypot_advanced.py)

L’objectif est de capturer les tentatives d’intrusion, stocker les logs et les visualiser via Kibana.

📦 Prérequis

Docker ≥ 20

Docker Compose ≥ 2

Python ≥ 3.10 (optionnel pour le mode local)

Virtualenv (optionnel)

🔧 Installation
Cloner le projet
git clone https://github.com/<TON-USERNAME>/projet_honeypot-elk-integration.git
cd projet_honeypot-elk-integration

Installer les dépendances Python (optionnel, mode local)
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

🚀 Lancer le projet
Mode Docker (recommandé)
./start_honeypot.sh


ou directement :

docker compose up -d --build

Mode Local (Python uniquement)
./start_honeypot.sh --local


Les scripts Python sont alors lancés en arrière-plan :

app.py → Honeypot HTTP

ftp_honeypot_advanced.py → Honeypot FTP

ssh_honeypot.py → Honeypot SSH

Les logs sont stockés dans /tmp/honeypot_*.log et dans logs/ecom_honeypot.log pour le HTTP.

🌐 Accès aux services
Service	URL
HTTP Honeypot (Flask)	http://localhost:5000

Kibana (ELK Dashboard)	http://localhost:5601

Elasticsearch API	http://localhost:9200
🗂️ Structure du projet
projet_honeypot-elk-integration/
│── app/
│   ├── app.py                   # HTTP Honeypot (Flask)
│   ├── ssh_honeypot.py          # SSH Honeypot
│   ├── ftp_honeypot_advanced.py # FTP Honeypot
│   ├── database.db              # Base SQLite
│   ├── static/                  # Fichiers CSS/JS
│   ├── uploads/                 # Fichiers uploadés
│   └── Dockerfile               # Build Flask
│
│── docker-compose.yml           # Stack Docker ELK + Honeypots
│── logstash.conf                # Configuration Logstash
│── requirements.txt             # Dépendances Python
│── start_honeypot.sh            # Script de démarrage (Docker ou local)
│── stop_honeypot.sh             # Script d'arrêt
│── logs/                        # Logs bruts capturés
│── venv/                        # Environnement Python

🧪 Tester les Honeypots
HTTP
curl http://localhost:5000/login

SSH
ssh test@<IP_MACHINE>

FTP
ftp <IP_MACHINE>

🛑 Arrêter le projet
./stop_honeypot.sh


ou (Docker uniquement) :

docker compose down
