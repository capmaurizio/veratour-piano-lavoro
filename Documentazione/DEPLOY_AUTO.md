# 🚀 Deploy Automatico - ScayCalcolo

## Opzione 1: Render (Consigliato - Supporta API)

Render ha un'API che permette il deploy automatico. Ecco come:

### Setup Automatico con Render CLI

```bash
# Installa Render CLI
npm install -g render-cli

# Login
render login

# Deploy automatico
render deploy
```

### Oppure via Web (5 minuti)

1. Vai su: https://dashboard.render.com
2. Accedi con GitHub
3. Clicca "New +" → "Web Service"
4. Connetti repository: `capmaurizio/veratour-piano-lavoro`
5. Configurazione:
   - **Name**: `scaycalcolo`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `streamlit run app_streamlit.py --server.port $PORT --server.address 0.0.0.0`
   - **Plan**: Free (o Starter per privato)
6. Clicca "Create Web Service"

---

## Opzione 2: Streamlit Cloud (Manuale - 2 minuti)

Streamlit Cloud non ha API, ma il setup è velocissimo:

1. Vai su: https://share.streamlit.io
2. Accedi con GitHub
3. Clicca "New app"
4. Configura:
   - **Repository**: `capmaurizio/veratour-piano-lavoro`
   - **Branch**: `main`
   - **Main file path**: `app_streamlit.py`
   - **App name**: `scaycalcolo`
5. Clicca "Deploy"

**Nota**: Streamlit Cloud Free è pubblico. Per privato serve Team plan ($20/mese).

---

## Opzione 3: Railway (Automatico via GitHub)

Railway auto-deploya da GitHub:

1. Vai su: https://railway.app
2. Accedi con GitHub
3. "New Project" → "Deploy from GitHub repo"
4. Seleziona: `capmaurizio/veratour-piano-lavoro`
5. Railway auto-rileva Streamlit
6. L'app sarà privata di default

---

## Raccomandazione

Per un'app **privata e gratuita**: usa **Railway** o **Render** (con piano Starter per privacy).

Per semplicità: usa **Streamlit Cloud** (ma sarà pubblica sul free tier).

