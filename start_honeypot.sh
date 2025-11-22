#!/bin/bash

# --- VARIABLES ---
PROJECT_DIR="$(pwd)"
REQUIREMENTS_FILE="$PROJECT_DIR/requirements.txt"
VENV_DIR="$PROJECT_DIR/venv"
PYTHON_EXEC="$VENV_DIR/bin/python"

echo "======================================================"
echo "🚀 Démarrage du projet Honeypot & ELK Stack (V. FINALE)"
echo "======================================================"

# 1. Démarrer le service Docker (toujours nécessaire pour le mode Docker)
# -----------------------------------------------------------------------------
echo "✅ Étape 1/3: Vérification et démarrage du service Docker..."
if sudo systemctl is-active --quiet docker; then
    echo "   -> Le service Docker est déjà actif."
else
    echo "   -> Le service Docker est arrêté. Tentative de démarrage..."
    sudo systemctl start docker
    if sudo systemctl is-active --quiet docker; then
        echo "   -> Le service Docker a été démarré avec succès."
    else
        echo "   ❌ ERREUR: Impossible de démarrer le service Docker. Vérifiez les permissions."
        exit 1
    fi
fi

# 2. Installer les dépendances Python dans un Environnement Virtuel (LOCAL)
# -----------------------------------------------------------------------------
echo ""
echo "✅ Étape 2/3: Gestion des dépendances Python locales (dans 'venv')..."
if [ -f "$REQUIREMENTS_FILE" ]; then
    echo "   -> Fichier $REQUIREMENTS_FILE trouvé."
    
    if [ ! -d "$VENV_DIR" ]; then
        echo "   -> Création de l'environnement virtuel ($VENV_DIR)..."
        python3 -m venv "$VENV_DIR"
    fi
    
    source "$VENV_DIR/bin/activate"
    
    echo "   -> Installation/Mise à jour des dépendances avec pip..."
    pip install -r "$REQUIREMENTS_FILE"
    
    if [ $? -eq 0 ]; then
        echo "   -> Dépendances installées/mises à jour avec succès dans 'venv'."
    else
        echo "   ⚠️ AVERTISSEMENT: Échec de l'installation des dépendances Python. Le mode local ou les conteneurs pourraient être affectés."
    fi
    # On laisse l'environnement activé pour la suite si besoin, mais le mode Docker le gère seul.
    deactivate 2>/dev/null 
else
    echo "   ⚠️ AVERTISSEMENT: Fichier $REQUIREMENTS_FILE non trouvé. Installation locale ignorée."
fi

# 3. Lancement des services (Docker Compose ou Local)
# -----------------------------------------------------------------------------
echo ""

if [ "$1" == "--local" ]; then
    # --- MODE LOCAL : Lancement des 3 scripts Python ---
    echo "======================================================"
    echo "🧪 MODE LOCAL : Lancement des Honeypots Python"
    echo "======================================================"

    if [ ! -f "$PYTHON_EXEC" ]; then
        echo "   ❌ ERREUR: L'exécutable Python dans 'venv' est introuvable. Étape 2 a échoué."
        exit 1
    fi

    # Lancement des scripts en arrière-plan
    echo "   -> Démarrage de l'E-commerce (app.py) en arrière-plan (PID enregistré)..."
    (cd "$PROJECT_DIR/app" && "$PYTHON_EXEC" app.py > /tmp/honeypot_app.log 2>&1 &)
    APP_PID=$!

    echo "   -> Démarrage du Honeypot FTP (ftp_honeypot_advanced.py) en arrière-plan (PID enregistré)..."
    (cd "$PROJECT_DIR/app" && "$PYTHON_EXEC" ftp_honeypot_advanced.py > /tmp/honeypot_ftp.log 2>&1 &)
    FTP_PID=$!

    echo "   -> Démarrage du Honeypot SSH (ssh_honeypot.py) en arrière-plan (PID enregistré)..."
    (cd "$PROJECT_DIR/app" && "$PYTHON_EXEC" ssh_honeypot.py > /tmp/honeypot_ssh.log 2>&1 &)
    SSH_PID=$!
    
    echo ""
    echo "🎉 Les 3 services sont démarrés en arrière-plan."
    echo "   -> Logs enregistrés dans /tmp/honeypot_*.log"
    echo "   -> PID des processus: Web: $APP_PID, FTP: $FTP_PID, SSH: $SSH_PID"
    echo "   -> Pour les arrêter : kill $APP_PID $FTP_PID $SSH_PID"
    echo "======================================================"
else
    # --- MODE DOCKER COMPOSE : Lancement de l'environnement ELK complet ---
    echo "✅ Étape 3/3: Lancement des services Honeypot et ELK avec Docker Compose..."
    echo "   -> Exécution de 'docker compose up -d --build'."

    # Utilisation de la syntaxe moderne 'docker compose'
    docker compose up -d --build
    if [ $? -eq 0 ]; then
        echo ""
        echo "🎉 Tous les services Docker ont été démarrés avec succès en mode détaché."
        echo "--- Statut des Conteneurs ---"
        docker compose ps
    else
        echo ""
        echo "❌ ÉCHEC DU LANCEMENT: Une erreur s'est produite lors de l'exécution de docker compose."
        echo "   Veuillez vérifier si le plugin 'docker-compose-plugin' est installé."
    fi
fi

echo "======================================================"
