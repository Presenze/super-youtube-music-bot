# 🚀 Deploy GiglioTube su Render

## 📋 Configurazione Render per GiglioTube

### 1. **Vai su Render.com**
- Apri [render.com](https://render.com)
- Accedi o registrati

### 2. **Crea un nuovo Web Service**
- Clicca **"New +"**
- Seleziona **"Web Service"**

### 3. **Configura il Repository**
- **Connect a repository:** GitHub
- **Repository:** `Presenze/super-youtube-music-bot`
- **Branch:** `main`

### 4. **Configurazione del Service**
- **Name:** `gigliotube-bot`
- **Environment:** `Python 3`
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `python gigliotube.py`

### 5. **Variabili d'Ambiente**
Aggiungi queste variabili:
- **BOT_TOKEN:** `8237710386:AAF9MmADLR0PfihDtK8ZTmeDRi884MbV8HM`
- **PYTHON_VERSION:** `3.10.0`

### 6. **Configurazione Avanzata**
- **Plan:** Free (per iniziare)
- **Auto-Deploy:** Yes
- **Health Check Path:** `/`

### 7. **Deploy**
- Clicca **"Create Web Service"**
- Render inizierà il deployment automaticamente

---

## 🔧 File di Configurazione Creati

### `render.yaml`
```yaml
services:
  - type: web
    name: gigliotube-bot
    env: python
    plan: free
    buildCommand: pip install -r requirements.txt
    startCommand: python gigliotube.py
    envVars:
      - key: BOT_TOKEN
        sync: false
      - key: PYTHON_VERSION
        value: 3.10.0
    healthCheckPath: /
    autoDeploy: true
    branch: main
    repo: https://github.com/Presenze/super-youtube-music-bot
```

### `Procfile`
```
worker: python gigliotube.py
```

### `runtime.txt`
```
python-3.10.0
```

---

## ⚠️ **IMPORTANTE: Modifiche Necessarie**

### 1. **Aggiorna config.py per Render**
Il file `config.py` deve essere modificato per usare le variabili d'ambiente:

```python
import os

# Token del bot Telegram (da variabile d'ambiente su Render)
BOT_TOKEN = os.getenv('BOT_TOKEN', '8237710386:AAF9MmADLR0PfihDtK8ZTmeDRi884MbV8HM')

# Percorso per i download
DOWNLOAD_PATH = "downloads"

# Impostazioni download
MAX_DURATION = 3600  # 60 minuti in secondi
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB in bytes

# Impostazioni qualità
DEFAULT_QUALITY = "320"
DEFAULT_FORMAT = "mp3"

# Impostazioni pulizia file
CLEANUP_INTERVAL = 3600  # 1 ora in secondi
FILE_RETENTION = 24  # 24 ore

# Impostazioni playlist
MAX_PLAYLIST_ITEMS = 5
```

### 2. **Aggiorna requirements.txt**
Assicurati che includa tutte le dipendenze:

```
python-telegram-bot==20.7
yt-dlp==2024.12.13
python-dotenv==1.0.0
aiofiles==23.2.1
mutagen==1.47.0
APScheduler==3.10.4
httpx==0.25.2
```

---

## 🚀 **Deploy su Render**

### **Metodo 1: Automatico (Raccomandato)**
1. Vai su [render.com](https://render.com)
2. Clicca **"New Web Service"**
3. Connetti il repository GitHub
4. Render userà automaticamente `render.yaml`

### **Metodo 2: Manuale**
1. Vai su [render.com](https://render.com)
2. Clicca **"New Web Service"**
3. Connetti `Presenze/super-youtube-music-bot`
4. Configura manualmente:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python gigliotube.py`
   - **Environment Variables:** `BOT_TOKEN=8237710386:AAF9MmADLR0PfihDtK8ZTmeDRi884MbV8HM`

---

## 📊 **Monitoraggio**

### **Logs**
- Vai su Render Dashboard
- Clicca sul tuo service
- Vai su **"Logs"** per vedere i log del bot

### **Health Check**
- Render monitorerà automaticamente la salute del bot
- Se il bot si ferma, Render lo riavvierà

### **Uptime**
- Render garantisce 99.9% uptime
- Il bot sarà sempre online

---

## 💰 **Piani Render**

### **Free Plan**
- ✅ Gratuito
- ✅ 750 ore/mese
- ✅ Auto-deploy
- ✅ HTTPS
- ⚠️ Si ferma dopo 15 minuti di inattività

### **Starter Plan ($7/mese)**
- ✅ Sempre online
- ✅ 0.1 CPU, 512MB RAM
- ✅ Custom domains
- ✅ Auto-deploy

### **Professional Plan ($25/mese)**
- ✅ 0.5 CPU, 1GB RAM
- ✅ Priority support
- ✅ Advanced monitoring

---

## 🔧 **Troubleshooting**

### **Bot non si avvia**
1. Controlla i logs su Render
2. Verifica che BOT_TOKEN sia configurato
3. Controlla che tutte le dipendenze siano installate

### **Errori di dipendenze**
1. Verifica `requirements.txt`
2. Controlla che Python 3.10 sia supportato
3. Aggiorna le versioni se necessario

### **Bot si ferma**
1. Su Free Plan è normale dopo 15 minuti di inattività
2. Considera l'upgrade a Starter Plan
3. Implementa un keep-alive endpoint

---

## 🎯 **Prossimi Passi**

1. ✅ **Crea account Render**
2. ✅ **Connetti repository GitHub**
3. ✅ **Configura variabili d'ambiente**
4. ✅ **Deploy del bot**
5. 🔄 **Testa il bot su Telegram**
6. 🔄 **Monitora i logs**
7. 🔄 **Configura dominio personalizzato (opzionale)**

---

**🎧 GiglioTube sarà online 24/7 su Render!** 🚀

*Fatto con ❤️ da Domenico Gigliotti* ✨
