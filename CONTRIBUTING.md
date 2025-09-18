# 🤝 Contribuire al Super YouTube Music Bot

Grazie per il tuo interesse a contribuire al Super YouTube Music Bot! Questo documento fornisce linee guida per contribuire al progetto.

## 📋 Come Contribuire

### 🐛 Segnalare Bug
1. Controlla se il bug è già stato segnalato negli [Issues](https://github.com/yourusername/super-youtube-music-bot/issues)
2. Se non esiste, crea un nuovo issue con:
   - Descrizione dettagliata del bug
   - Passaggi per riprodurre il problema
   - Screenshot se applicabile
   - Informazioni sul sistema (OS, Python version, etc.)

### ✨ Richiedere Funzioni
1. Controlla se la funzione è già stata richiesta
2. Crea un nuovo issue con:
   - Descrizione della funzione richiesta
   - Caso d'uso e benefici
   - Esempi se applicabile

### 🔧 Contribuire al Codice
1. **Fork** il repository
2. **Crea** un branch per la tua feature (`git checkout -b feature/AmazingFeature`)
3. **Commit** le tue modifiche (`git commit -m 'Add some AmazingFeature'`)
4. **Push** al branch (`git push origin feature/AmazingFeature`)
5. **Apri** una Pull Request

## 🛠️ Setup Sviluppo

### Prerequisiti
- Python 3.8+
- Git
- FFmpeg
- Token Bot Telegram

### Installazione
```bash
# Clona il repository
git clone https://github.com/yourusername/super-youtube-music-bot.git
cd super-youtube-music-bot

# Installa dipendenze
pip install -r requirements.txt

# Copia config di esempio
cp config_example.py config.py

# Modifica config.py con il tuo token
```

### Test
```bash
# Test unitari
python -m pytest tests/

# Test integrazione
python test_bot.py

# Test linting
flake8 bot_finale_perfetto.py
```

## 📝 Linee Guida Codice

### Stile Codice
- Segui [PEP 8](https://www.python.org/dev/peps/pep-0008/)
- Usa type hints quando possibile
- Documenta funzioni e classi
- Scrivi test per nuove funzioni

### Struttura Progetto
```
super-youtube-music-bot/
├── bot_finale_perfetto.py    # Bot principale
├── config.py                 # Configurazione
├── requirements.txt          # Dipendenze
├── README.md                 # Documentazione
├── tests/                    # Test
├── docs/                     # Documentazione
└── scripts/                  # Script utility
```

### Commit Messages
Usa il formato:
```
tipo(scope): descrizione

Corpo del messaggio (opzionale)

Footer (opzionale)
```

Tipi:
- `feat`: Nuova funzione
- `fix`: Bug fix
- `docs`: Documentazione
- `style`: Formattazione
- `refactor`: Refactoring
- `test`: Test
- `chore`: Manutenzione

## 🎯 Aree di Contributo

### 🐛 Bug Fixes
- Risolvi problemi esistenti
- Migliora gestione errori
- Ottimizza performance

### ✨ Nuove Funzioni
- Aggiungi nuovi formati audio
- Implementa nuove funzioni premium
- Migliora interfaccia utente

### 📚 Documentazione
- Migliora README
- Aggiungi esempi
- Traduci documentazione

### 🌍 Traduzioni
- Aggiungi nuove lingue
- Migliora traduzioni esistenti
- Corregge errori di traduzione

### 🎨 UI/UX
- Migliora interfaccia
- Aggiungi nuovi pulsanti
- Ottimizza esperienza utente

## 🧪 Test

### Test Unitari
```python
import unittest
from bot_finale_perfetto import SuperYouTubeDownloader

class TestDownloader(unittest.TestCase):
    def test_clean_text(self):
        # Test funzione clean_text
        pass
    
    def test_url_validation(self):
        # Test validazione URL
        pass
```

### Test Integrazione
```python
# Test completo del bot
python test_bot.py
```

## 📋 Checklist Pull Request

Prima di inviare una PR, assicurati di:

- [ ] Codice segue le linee guida
- [ ] Test passano
- [ ] Documentazione aggiornata
- [ ] Commit messages chiari
- [ ] Nessun file sensibile incluso
- [ ] Codice commentato appropriatamente

## 🔒 Sicurezza

### File Sensibili
Non includere mai:
- Token bot
- Chiavi API
- Password
- File di configurazione personali

### Vulnerabilità
Se trovi una vulnerabilità di sicurezza:
1. **NON** aprire un issue pubblico
2. Invia email a: security@example.com
3. Includi dettagli della vulnerabilità

## 📞 Supporto

### Ottenere Aiuto
- 💬 [Telegram Group](https://t.me/yourgroup)
- 📧 [Email](mailto:support@example.com)
- 🐛 [Issues](https://github.com/yourusername/super-youtube-music-bot/issues)

### Community
- Unisciti alla community Telegram
- Partecipa alle discussioni
- Aiuta altri sviluppatori

## 🏆 Riconoscimenti

I contributori saranno riconosciuti in:
- README del progetto
- Release notes
- Documentazione
- Community

## 📄 Licenza

Contribuendo al progetto, accetti che il tuo codice sarà distribuito sotto la licenza MIT.

---

**Grazie per il tuo contributo!** 🎉

*Insieme rendiamo il Super YouTube Music Bot ancora migliore!* 🎧🚀
