#!/bin/bash

# GiglioTube Bot - Deploy Script per Unix/Linux/Mac
# Script automatico per configurare e deployare il bot

set -e

# Colori per output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_banner() {
    echo -e "${BLUE}"
    echo "🎧✨ ================================================ ✨🎧"
    echo "🚀        GIGLIOTUBE BOT - DEPLOY AUTOMATICO        🚀"
    echo "🎧✨ ================================================ ✨🎧"
    echo -e "${NC}"
    echo ""
}

check_requirements() {
    echo -e "${YELLOW}🔍 Controllo requisiti...${NC}"
    
    # Controlla Python
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}❌ Python3 non installato!${NC}"
        echo "   Installa con: sudo apt install python3 (Ubuntu/Debian)"
        echo "   Oppure: brew install python3 (Mac)"
        exit 1
    fi
    echo -e "${GREEN}✅ Python3 installato${NC}"
    
    # Controlla pip
    if ! command -v pip3 &> /dev/null; then
        echo -e "${RED}❌ pip3 non installato!${NC}"
        echo "   Installa con: sudo apt install python3-pip (Ubuntu/Debian)"
        exit 1
    fi
    echo -e "${GREEN}✅ pip3 installato${NC}"
    
    # Controlla Git
    if ! command -v git &> /dev/null; then
        echo -e "${RED}❌ Git non installato!${NC}"
        echo "   Installa con: sudo apt install git (Ubuntu/Debian)"
        echo "   Oppure: brew install git (Mac)"
        exit 1
    fi
    echo -e "${GREEN}✅ Git installato${NC}"
    
    # Controlla file necessari
    required_files=("gigliotube.py" "start_render.py" "requirements.txt" "render.yaml" "config_render.py")
    for file in "${required_files[@]}"; do
        if [ ! -f "$file" ]; then
            echo -e "${RED}❌ File mancante: $file${NC}"
            exit 1
        fi
    done
    echo -e "${GREEN}✅ Tutti i file necessari trovati${NC}"
}

install_dependencies() {
    echo -e "${YELLOW}📦 Installazione dipendenze...${NC}"
    pip3 install -r requirements.txt
    echo -e "${GREEN}✅ Dipendenze installate${NC}"
}

setup_git() {
    echo -e "${YELLOW}🔧 Configurazione Git...${NC}"
    
    # Controlla se siamo in un repository git
    if [ ! -d ".git" ]; then
        echo "Inizializzazione repository Git..."
        git init
        git add .
        git commit -m "Initial commit"
    fi
    
    # Controlla se esiste un remote
    if ! git remote get-url origin &> /dev/null; then
        echo -e "${YELLOW}⚠️  Nessun remote GitHub configurato!${NC}"
        echo "   Configura GitHub:"
        echo "   1. Crea repository su GitHub"
        echo "   2. Esegui: git remote add origin https://github.com/tuo-username/repo.git"
        echo "   3. Esegui: git push -u origin main"
        echo ""
        read -p "Premi INVIO dopo aver configurato GitHub..."
    fi
    
    echo -e "${GREEN}✅ Git configurato${NC}"
}

deploy_to_render() {
    echo -e "${YELLOW}🚀 Deploy su Render...${NC}"
    
    # Commit modifiche
    git add .
    git commit -m "Deploy ready for Render" || true
    
    # Push su GitHub
    git push origin main
    
    echo -e "${GREEN}✅ Push su GitHub completato${NC}"
    
    # Apri browser
    if command -v xdg-open &> /dev/null; then
        xdg-open "https://render.com/dashboard"
    elif command -v open &> /dev/null; then
        open "https://render.com/dashboard"
    else
        echo "Apri manualmente: https://render.com/dashboard"
    fi
}

print_instructions() {
    echo -e "${BLUE}"
    echo "🎯 ISTRUZIONI DEPLOY SU RENDER:"
    echo ""
    echo "1. 🌐 Vai su https://render.com (già aperto nel browser)"
    echo "2. 🔐 Fai login con GitHub"
    echo "3. ➕ Clicca 'New +' → 'Web Service'"
    echo "4. 🔗 Connetti il tuo repository GitHub"
    echo "5. ⚙️  Configura:"
    echo "   - Name: gigliotube-bot"
    echo "   - Environment: Python 3"
    echo "   - Build Command: pip install -r requirements.txt"
    echo "   - Start Command: python start_render.py"
    echo "6. 🔑 Environment Variables:"
    echo "   - BOT_TOKEN: [il tuo token]"
    echo "   - PYTHONUNBUFFERED: 1"
    echo "   - TZ: Europe/Rome"
    echo "   - RENDER: true"
    echo "7. 🚀 Clicca 'Create Web Service'"
    echo "8. ⏳ Aspetta 5-10 minuti per il deploy"
    echo "9. 🎉 Il bot sarà online!"
    echo -e "${NC}"
}

main() {
    print_banner
    
    check_requirements
    install_dependencies
    setup_git
    deploy_to_render
    
    print_instructions
    
    echo -e "${GREEN}🎉 Setup completato! Segui le istruzioni sopra per completare il deploy.${NC}"
    echo -e "${BLUE}📚 Per maggiori dettagli, leggi DEPLOYMENT_GUIDE.md${NC}"
}

# Esegui script
main "$@"
