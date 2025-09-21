# ⚡ Deploy su Cyclic.sh

## Vantaggi Cyclic:
- ✅ Completamente gratuito
- ✅ Deploy automatico da GitHub
- ✅ Molto veloce
- ✅ Serverless
- ✅ Perfetto per bot Telegram

## Passaggi:

### 1. **Prepara il Repository:**
```bash
git add .
git commit -m "Ready for Cyclic deployment"
git push origin main
```

### 2. **Deploy su Cyclic:**
1. Vai su [cyclic.sh](https://cyclic.sh)
2. Login con GitHub
3. "Deploy Now" → Seleziona repository
4. Cyclic rileverà automaticamente i file Python

### 3. **Configura Environment Variables:**
- Vai su "Environment" tab
- Aggiungi:
  ```
  BOT_TOKEN=il_tuo_token_telegram
  PYTHONUNBUFFERED=1
  TZ=Europe/Rome
  ```

### 4. **Deploy:**
- Clicca "Deploy"
- Aspetta 1-2 minuti
- Il bot sarà online! 🎉

## Vantaggi Cyclic:
- **Serverless:** Si adatta automaticamente al carico
- **Velocissimo:** Deploy in meno di 2 minuti
- **Gratuito:** Nessun limite di tempo
- **Automatico:** Si riavvia se si blocca

## Perfetto per:
- Bot Telegram
- API semplici
- Progetti Python
- Test e sviluppo
