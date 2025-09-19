# 🟣 Deploy su Heroku

## Vantaggi Heroku:
- ✅ Hobby plan gratuito
- ✅ Molto stabile
- ✅ Add-ons disponibili
- ✅ Community grande
- ✅ Documentazione completa

## Passaggi:

### 1. **Installa Heroku CLI:**
```bash
# Windows
winget install Heroku.HerokuCLI

# Mac
brew tap heroku/brew && brew install heroku

# Linux
curl https://cli-assets.heroku.com/install.sh | sh
```

### 2. **Login e Setup:**
```bash
heroku login
heroku create gigliotube-bot
```

### 3. **Configura Environment Variables:**
```bash
heroku config:set BOT_TOKEN=il_tuo_token_telegram
heroku config:set PYTHONUNBUFFERED=1
heroku config:set TZ=Europe/Rome
```

### 4. **Deploy:**
```bash
git push heroku main
```

### 5. **Avvia il Bot:**
```bash
heroku ps:scale worker=1
```

## Vantaggi Heroku:
- **Stabile:** Uptime 99.9%
- **Add-ons:** Database, monitoring, etc.
- **Community:** Molto supporto online
- **Professionale:** Usato da grandi aziende

## Limitazioni:
- Hobby plan ha limiti di tempo (si spegne dopo 30 min di inattività)
- Per bot 24/7 serve piano a pagamento
- Più complesso da configurare
