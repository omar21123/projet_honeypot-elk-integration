#!/bin/bash

# --- VARIABLES ---
PROJECT_DIR="$(pwd)"

echo "======================================================"
echo "🛑 Arrêt et Nettoyage de l'environnement Honeypot"
echo "======================================================"

# 1. Tentative d'arrêt du Mode Docker Compose
# ---------------------------------------------------
echo "✅ Étape 1/2: Arrêt des conteneurs Docker (si en cours)..."

# Vérifie si la commande docker compose est disponible et si des services sont actifs
if command -v docker > /dev/null && docker compose ps &> /dev/null; then
    docker compose down -v
    if [ $? -eq 0 ]; then
        echo "   -> Les services Docker ont été arrêtés et nettoyés avec succès."
    else
        echo "   ⚠️ AVERTISSEMENT: Échec de l'arrêt Docker Compose. Des conteneurs pourraient être encore actifs."
    fi
else
    echo "   -> Docker Compose non trouvé ou aucun service actif. Passé."
fi


# 2. Tentative d'arrêt des Processus Python Locaux
# ---------------------------------------------------
echo ""
echo "✅ Étape 2/2: Arrêt des processus Python locaux (si en cours)..."

# Recherche des processus spécifiques dans le répertoire 'app' et tue-les
PIDS=$(ps aux | grep "$PROJECT_DIR/app" | grep -v grep | awk '{print $2}')

if [ -n "$PIDS" ]; then
    echo "   -> Processus Python trouvés : $PIDS"
    kill $PIDS
    if [ $? -eq 0 ]; then
        echo "   -> Processus locaux (app, ssh, ftp) arrêtés avec succès."
    else
        echo "   ⚠️ AVERTISSEMENT: Certains processus n'ont pas pu être arrêtés. Vérifiez manuellement."
    fi
else
    echo "   -> Aucun processus Python local trouvé en arrière-plan. Passé."
fi

echo "======================================================"
