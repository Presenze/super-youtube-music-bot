# 🚀 Guida Completa per Deploy Gratuito - GiglioTube Bot

## 🎯 Opzioni di Deploy Gratuito

### 1. **Render.com (RACCOMANDATO) ⭐**

**Vantaggi:**
- ✅ Gratuito per sempre
- ✅ FFmpeg preinstallato
- ✅ Deploy automatico da GitHub
- ✅ Logs in tempo reale
- ✅ Uptime 99.9%

**Passaggi:**

1. **Prepara il Repository GitHub:**
   ```bash
   git add .
   git commit -m "Deploy ready for Render"
   git push origin main
   ```

2. **Crea Account su Render.com:**
   - Vai su [render.com](https://render.com)
   - Registrati con GitHub

3. **Deploy il Bot:**
   - Clicca "New +" → "Web Service"
   - Connetti il tuo repository GitHub
   - Seleziona il branch `main`
   - Configura:
     - **Name:** `gigliotube-bot`
     - **Environment:** `Python 3`
     - **Build Command:** `pip install -r requirements.txt`
     - **Start Command:** `python start_render.py`

4. **Configura Environment Variables:**
   - Vai su "Environment"
   - Aggiungi:
     ```
     BOT_TOKEN=il_tuo_token_bot_telegram
     PYTHONUNBUFFERED=1
     TZ=Europe/Rome
     RENDER=true
     ```

5. **Deploy:**
   - Clicca "Create Web Service"
   - Aspetta 5-10 minuti per il deploy
   - Il bot sarà online! 🎉

---

### 2. **Railway.app (Alternativa) 🚂**

**Vantaggi:**
- ✅ Gratuito con limiti generosi
- ✅ Deploy automatico
- ✅ Database incluso
- ✅ Monitoring integrato

**Passaggi:**

1. **Installa Railway CLI:**
   ```bash
   npm install -g @railway/cli
   ```

2. **Login e Deploy:**
   ```bash
   railway login
   railway init
   railway up
   ```

3. **Configura Environment:**
   ```bash
   railway variables set BOT_TOKEN=il_tuo_token
   railway variables set PYTHONUNBUFFERED=1
   ```

---

### 3. **Heroku (Backup) 🟣**

**Vantaggi:**
- ✅ Gratuito con limiti
- ✅ Molto stabile
- ✅ Add-ons disponibili

**Passaggi:**

1. **Installa Heroku CLI:**
   ```bash
   # Windows
   winget install Heroku.HerokuCLI
   
   # Mac
   brew tap heroku/brew && brew install heroku
   ```

2. **Login e Deploy:**
   ```bash
   heroku login
   heroku create gigliotube-bot
   git push heroku main
   ```

3. **Configura Environment:**
   ```bash
   heroku config:set BOT_TOKEN=il_tuo_token
   heroku config:set PYTHONUNBUFFERED=1
   ```

---

## 🔧 Configurazione Pre-Deploy

### 1. **Prepara il Token Bot Telegram:**

1. Vai su [@BotFather](https://t.me/BotFather) su Telegram
2. Crea un nuovo bot con `/newbot`
3. Scegli un nome e username
4. Copia il token (es: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)

### 2. **Verifica i File di Configurazione:**

✅ **File necessari:**
- `gigliotube.py` - Bot principale
- `start_render.py` - Script di avvio per Render
- `requirements.txt` - Dipendenze Python
- `render.yaml` - Configurazione Render
- `config_render.py` - Configurazione per produzione

### 3. **Test Locale (Opzionale):**

```bash
# Installa dipendenze
pip install -r requirements.txt

# Installa FFmpeg
# Windows: choco install ffmpeg
# Mac: brew install ffmpeg
# Linux: sudo apt install ffmpeg

# Testa il bot
python gigliotube.py
```

---

## 🚀 Deploy Rapido con Render

### **Metodo 1: Deploy Automatico (Raccomandato)**

1. **Push su GitHub:**
   ```bash
   git add .
   git commit -m "Ready for Render deployment"
   git push origin main
   ```

2. **Deploy su Render:**
   - Vai su [render.com](https://render.com)
   - "New +" → "Web Service"
   - Connetti GitHub → Seleziona repository
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python start_render.py`
   - **Environment Variables:**
     ```
     BOT_TOKEN=il_tuo_token_qui
     PYTHONUNBUFFERED=1
     TZ=Europe/Rome
     RENDER=true
     ```
   - Clicca "Create Web Service"

3. **Aspetta 5-10 minuti** ⏰
4. **Il bot è online!** 🎉

### **Metodo 2: Deploy con render.yaml**

Se hai già `render.yaml` configurato:

1. Push su GitHub
2. Vai su Render.com
3. "New +" → "Blueprint"
4. Connetti repository
5. Render rileverà automaticamente `render.yaml`
6. Configura solo `BOT_TOKEN`
7. Deploy automatico! 🚀

---

## 🔍 Monitoraggio e Debug

### **Logs in Tempo Reale:**

**Render:**
- Dashboard → Il tuo servizio → "Logs"
- Logs in tempo reale con colori

**Railway:**
```bash
railway logs --follow
```

**Heroku:**
```bash
heroku logs --tail
```

### **Test del Bot:**

1. **Avvia il bot su Telegram:**
   - Cerca il tuo bot su Telegram
   - Invia `/start`
   - Dovresti vedere il messaggio di benvenuto

2. **Test Download:**
   - Invia un URL YouTube
   - Scegli formato e qualità
   - Verifica che il download funzioni

---

## 🛠️ Risoluzione Problemi

### **Problemi Comuni:**

#### **Bot non risponde:**
- ✅ Verifica che il token sia corretto
- ✅ Controlla i logs per errori
- ✅ Assicurati che il bot sia attivo su Telegram

#### **Deploy fallisce:**
- ✅ Verifica che tutti i file siano committati
- ✅ Controlla che `requirements.txt` sia corretto
- ✅ Verifica che il branch sia `main`

#### **Download non funziona:**
- ✅ Verifica che FFmpeg sia installato (Render lo fa automaticamente)
- ✅ Controlla i logs per errori specifici
- ✅ Testa con un video più corto

#### **Errori di memoria:**
- ✅ Riduci `MAX_CONCURRENT_DOWNLOADS` in config
- ✅ Riduci `MAX_FILE_SIZE` se necessario
- ✅ Usa qualità più basse (128k invece di 320k)

---

## 📊 Monitoraggio Performance

### **Metriche Importanti:**

- **Uptime:** Dovrebbe essere >99%
- **Response Time:** <2 secondi per comando
- **Memory Usage:** <512MB (limite Render free)
- **CPU Usage:** <1 core (limite Render free)

### **Ottimizzazioni:**

1. **Riduci file size:**
   ```python
   MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB invece di 100MB
   ```

2. **Limita download simultanei:**
   ```python
   MAX_CONCURRENT_DOWNLOADS = 2  # Invece di 5
   ```

3. **Pulisci file più spesso:**
   ```python
   CLEANUP_AFTER_HOURS = 12  # Invece di 24
   ```

---

## 🎉 Congratulazioni!

Il tuo bot è ora online e gratuito! 🚀

### **Prossimi Passi:**

1. **Condividi il bot** con amici e famiglia
2. **Monitora le performance** nei primi giorni
3. **Raccogli feedback** dagli utenti
4. **Considera upgrade** se superi i limiti gratuiti

### **Link Utili:**

- 🔗 **Render Dashboard:** [render.com/dashboard](https://render.com/dashboard)
- 🔗 **Telegram Bot:** [t.me/il_tuo_bot](https://t.me/il_tuo_bot)
- 🔗 **GitHub Repository:** [github.com/tuo-username/repo](https://github.com/tuo-username/repo)

---

**Buon deploy! 🎧✨🚀**

*Fatto con ❤️ per gli amanti della musica ovunque!*
