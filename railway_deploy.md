# 🚂 Deploy su Railway.app

## Vantaggi Railway:
- ✅ $5 crediti gratuiti/mese (più che sufficienti!)
- ✅ Deploy automatico da GitHub
- ✅ Database PostgreSQL incluso
- ✅ Monitoring avanzato
- ✅ Molto veloce e stabile

## Passaggi:

### 1. **Prepara il Repository:**
```bash
git add .
git commit -m "Ready for Railway deployment"
git push origin main
```

### 2. **Deploy su Railway:**
1. Vai su [railway.app](https://railway.app)
2. Login con GitHub
3. "New Project" → "Deploy from GitHub repo"
4. Seleziona il tuo repository
5. Railway rileverà automaticamente `railway.json`

### 3. **Configura Environment Variables:**
- Vai su "Variables" tab
- Aggiungi:
  ```
  BOT_TOKEN=il_tuo_token_telegram
  PYTHONUNBUFFERED=1
  TZ=Europe/Rome
  ```

### 4. **Deploy:**
- Clicca "Deploy"
- Aspetta 2-3 minuti
- Il bot sarà online! 🎉

## Monitoraggio:
- Dashboard Railway → Logs per vedere i log
- Metrics per monitorare performance
- Database incluso per statistiche

## Costi:
- **Gratuito:** $5 crediti/mese
- **Il tuo bot userà ~$1-2/mese**
- **Rimanenti $3-4 per altri progetti!**
