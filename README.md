# 🛡️ Honeypot & ELK Integration

Un système de honeypot multi-services complet intégré à une stack ELK (Elasticsearch, Logstash, Kibana) pour capturer, analyser et visualiser les tentatives d'intrusion en temps réel.

## 📋 Vue d'ensemble

Ce projet déploie trois types de honeypots qui simulent des services vulnérables pour attirer et enregistrer les activités malveillantes :

- **🔹 HTTP Honeypot** : Service web simulé avec Flask
- **🔹 SSH Honeypot** : Service SSH factice pour capturer les tentatives d'accès
- **🔹 FTP Honeypot Avancé** : Service FTP avec fonctionnalités étendues

Tous les logs sont centralisés dans la stack ELK pour analyse et visualisation via Kibana.

## 🎯 Fonctionnalités

- ✅ Capture complète des tentatives d'intrusion
- ✅ Stockage structuré des logs dans Elasticsearch
- ✅ Tableau de bord Kibana pour visualisation
- ✅ Interface web de monitoring pour le honeypot HTTP
- ✅ Support multi-protocoles (HTTP, SSH, FTP)
- ✅ Déploiement simplifié via Docker
- ✅ Mode local disponible pour le développement

## 📦 Prérequis

### Option Docker (Recommandé)
- Docker ≥ 20.10
- Docker Compose ≥ 2.0
- 4 GB de RAM minimum
- 2 CPU cores minimum

### Option Local (Développement)
- Python ≥ 3.10
- Virtualenv (optionnel mais recommandé)
- 2 GB de RAM minimum

## 🚀 Installation Rapide

### 1. Cloner le projet
```bash
git clone https://github.com/<TON-USERNAME>/projet_honeypot-elk-integration.git
cd projet_honeypot-elk-integration
```

### 2. Démarrage avec Docker (Recommandé)
```bash
# Lancement complet de la stack
./start_honeypot.sh

# Ou directement avec Docker Compose
docker compose up -d --build
```

### 3. Démarrage en mode local (Développement)
```bash
# Créer et activer l'environnement virtuel
python3 -m venv venv
source venv/bin/activate  # Sur Windows: venv\Scripts\activate

# Installer les dépendances
pip install -r requirements.txt

# Lancer les honeypots
./start_honeypot.sh --local
```

## 🌐 Accès aux Services

| Service | URL | Port | Description |
|---------|-----|------|-------------|
| HTTP Honeypot (Flask) | http://localhost:5000 | 5000 | Interface web du honeypot HTTP |
| Kibana Dashboard | http://localhost:5601 | 5601 | Visualisation des logs et analytics |
| Elasticsearch API | http://localhost:9200 | 9200 | API Elasticsearch pour requêtes |
| SSH Honeypot | ssh://localhost:2222 | 2222 | Honeypot SSH |
| FTP Honeypot | ftp://localhost:2121 | 2121 | Honeypot FTP |

## 🧪 Tester les Honeypots

### Test HTTP
```bash
curl http://localhost:5000/login
curl -X POST http://localhost:5000/login -d "username=admin&password=test"
```

### Test SSH
```bash
ssh test@localhost -p 2222
# Mot de passe: anypassword
```

### Test FTP
```bash
ftp localhost 2121
# Utilisateur: anonymous
# Mot de passe: any@email.com
```

## 📊 Structure du Projet

```
projet_honeypot-elk-integration/
│
├── app/
│   ├── app.py                    # Honeypot HTTP (Flask)
│   ├── ssh_honeypot.py           # Honeypot SSH
│   ├── ftp_honeypot_advanced.py  # Honeypot FTP avancé
│   ├── database.db               # Base de données SQLite
│   ├── static/                   # Assets CSS/JS
│   ├── uploads/                  # Fichiers uploadés (FTP)
│   └── Dockerfile                # Configuration Docker pour Flask
│
├── docker-compose.yml            # Stack Docker ELK + Honeypots
├── logstash.conf                 # Configuration Logstash
├── requirements.txt              # Dépendances Python
├── start_honeypot.sh             # Script de démarrage
├── stop_honeypot.sh              # Script d'arrêt
│
├── logs/                         # Logs bruts capturés
│   ├── ecom_honeypot.log         # Logs HTTP honeypot
│   ├── honeypot_ssh.log          # Logs SSH honeypot
│   └── honeypot_ftp.log          # Logs FTP honeypot
│
└── venv/                         # Environnement virtuel Python
```

## 🔧 Configuration

### Variables d'Environnement (Docker)
Les variables peuvent être modifiées dans `docker-compose.yml`:

- `ELASTIC_PASSWORD` : Mot de passe Elasticsearch (par défaut: `changeme`)
- `ELASTICSEARCH_HOST` : URL Elasticsearch (par défaut: `elasticsearch`)
- `KIBANA_SYSTEM_PASSWORD` : Mot de passe Kibana

### Configuration Logstash
Le fichier `logstash.conf` définit comment les logs sont traités et envoyés à Elasticsearch.

## 📈 Visualisation des Données

1. Accédez à Kibana: http://localhost:5601
2. Connectez-vous avec:
   - Utilisateur: `elastic`
   - Mot de passe: `changeme` (ou celui défini dans les variables d'environnement)
3. Créez un index pattern pour `honeypot-*`
4. Explorez les dashboards prédéfinis ou créez vos propres visualisations

## 🛠️ Développement

### Ajouter un nouveau service de honeypot
1. Créez votre script Python dans le dossier `app/`
2. Assurez-vous qu'il écrit les logs au format JSON
3. Ajoutez le service à `docker-compose.yml` si nécessaire
4. Mettez à jour la configuration Logstash pour traiter les nouveaux logs

### Mode Débogage
```bash
# Lancer un honeypot spécifique en mode debug
python app/app.py --debug

# Voir les logs Docker
docker compose logs -f [service_name]
```

## 🛑 Arrêt Propre

### Arrêter tous les services
```bash
./stop_honeypot.sh
```

### Arrêter uniquement Docker
```bash
docker compose down
```

### Arrêter le mode local
```bash
pkill -f "python.*honeypot"
# ou
./stop_honeypot.sh --local
```

## ⚠️ Avertissements de Sécurité

⚠️ **CE PROJET EST UN OUTIL DE SÉCURITÉ OFFENSIF/DÉFENSIF**

- Ne déployez pas sur des réseaux de production sans supervision
- Les honeypots simulent des services vulnérables
- Surveillez régulièrement les logs pour détecter les activités suspectes
- Changez les mots de passe par défaut avant tout déploiement public
- Consultez les lois locales concernant la collecte de données

## 🐛 Dépannage

### Problèmes courants

1. **Ports déjà utilisés**
   ```bash
   # Vérifier les ports en cours d'utilisation
   sudo netstat -tulpn | grep :5000
   # ou changer les ports dans docker-compose.yml
   ```

2. **Elasticsearch ne démarre pas**
   ```bash
   # Augmenter la mémoire virtuelle
   sudo sysctl -w vm.max_map_count=262144
   ```

3. **Permissions Docker**
   ```bash
   # Ajouter votre utilisateur au groupe docker
   sudo usermod -aG docker $USER
   ```

### Logs de débogage
```bash
# Voir tous les logs
docker compose logs

# Suivre les logs d'un service spécifique
docker compose logs -f elasticsearch
```

## 🤝 Contribution

Les contributions sont les bienvenues ! Veuillez :

1. Fork le projet
2. Créer une branche pour votre fonctionnalité
3. Ajouter des tests si applicable
4. Soumettre une Pull Request

## 📄 Licence

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.

## 📚 Ressources

- [Documentation Elastic Stack](https://www.elastic.co/guide/index.html)
- [Honeypot Best Practices](https://github.com/paralax/awesome-honeypots)
- [Flask Documentation](https://flask.palletsprojects.com/)

---

**Note** : Ce projet est à des fins éducatives et de recherche en sécurité. Utilisez-le de manière responsable et conformément aux lois applicables.
