# 🚀 Deploy su Streamlit Cloud

**Il repository del progetto è su GitHub** (non su GitLab): https://github.com/capmaurizio/veratour-piano-lavoro

## Opzione 1: Streamlit Cloud (Consigliato)

Segui questi passaggi:

### Passo 1: Accedi a Streamlit Cloud
1. Vai su https://share.streamlit.io
2. Accedi con il tuo account (puoi usare Google o GitHub)

### Passo 2: Deploy dall'App
1. Clicca su "New app"
2. Seleziona "Deploy from GitHub repository"
3. Collega il tuo account GitHub se necessario
4. Seleziona il repository: `capmaurizio/veratour-piano-lavoro`
5. Branch: `main`
6. Main file path: `app_streamlit.py` (per l'app nella root del progetto multi-TO usa il file `app_streamlit.py` nella root)
7. Clicca su "Deploy"

### Passo 3: Configurazione (Opzionale)
- L'app sarà disponibile su: `https://veratour-piano-lavoro.streamlit.app`
- Puoi personalizzare l'URL nelle impostazioni

### Vantaggi
- ✅ Completamente gratuito
- ✅ Deploy automatico ad ogni push su GitHub
- ✅ SSL incluso
- ✅ Nessuna configurazione server

---

## Opzione 2: Render (Alternativa)

Se preferisci Render:

### Passo 1: Crea nuovo Web Service
1. Vai su https://render.com
2. Accedi e clicca "New +" → "Web Service"
3. Collega il repository GitHub: `capmaurizio/veratour-piano-lavoro`

### Passo 2: Configurazione
- **Name**: `veratour-piano-lavoro`
- **Environment**: `Python 3`
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `streamlit run app_streamlit.py --server.port $PORT --server.address 0.0.0.0`
- **Plan**: Free

### Passo 3: Deploy
- Clicca "Create Web Service"
- L'app sarà disponibile su: `https://veratour-piano-lavoro.onrender.com`

---

## Opzione 3: Railway (Alternativa)

1. Vai su https://railway.app
2. "New Project" → "Deploy from Git repo"
3. Collega GitHub
4. Seleziona il repository `capmaurizio/veratour-piano-lavoro`
5. Railway auto-rileva Streamlit e deploy automatico

---

## File Necessari (Già Presenti)

✅ `app_streamlit.py` - File principale dell'app
✅ `requirements.txt` - Dipendenze Python
✅ `consuntivoveratour.py` - Modulo di calcolo
✅ `.streamlit/config.toml` - Configurazione Streamlit

---

## Note Importanti

- **Repository**: Il codice è su **GitHub** (https://github.com/capmaurizio/veratour-piano-lavoro). Ogni push su `main` aggiorna il deploy se hai collegato l'app al repo.
- **File Excel**: Gli utenti caricheranno i file tramite l'interfaccia web
- **Memoria**: Streamlit Cloud Free ha 1GB RAM (sufficiente per questa app)
- **Timeout**: 2 ore di inattività su Free tier (l'app si riavvia automaticamente)

---

## Troubleshooting

Se il deploy fallisce:
1. Verifica che `requirements.txt` contenga tutte le dipendenze
2. Controlla i log su Streamlit Cloud
3. Assicurati che il file principale sia `app_streamlit.py`
