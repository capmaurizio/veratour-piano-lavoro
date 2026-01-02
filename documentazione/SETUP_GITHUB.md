# 🔐 Setup GitHub per Deploy

## Passo 1: Crea un Personal Access Token (PAT)

1. Vai su GitHub: https://github.com
2. Accedi con: `aristoteleitaca@gmail.com` / `Yumamessico1`
3. Vai su: **Settings** → **Developer settings** → **Personal access tokens** → **Tokens (classic)**
   - Oppure vai direttamente: https://github.com/settings/tokens
4. Clicca **"Generate new token"** → **"Generate new token (classic)"**
5. Compila:
   - **Note**: `Veratour Piano Lavoro`
   - **Expiration**: Scegli (es. 90 giorni o No expiration)
   - **Scopes**: Seleziona almeno `repo` (tutti i permessi del repository)
6. Clicca **"Generate token"**
7. **COPIA IL TOKEN** (lo vedrai solo una volta!)

## Passo 2: Crea il Repository su GitHub

1. Vai su: https://github.com/new
2. **Repository name**: `veratour-piano-lavoro`
3. **Description**: `Calcolatore Veratour 2025 con interfaccia Streamlit`
4. Scegli **Private** o **Public**
5. **NON** inizializzare con README, .gitignore o license
6. Clicca **"Create repository"**

## Passo 3: Push del Codice

Dopo aver creato il token, esegui questi comandi:

```bash
cd /Users/mauriziocapitanio/Documents/scay/VeratourPianoLavoro

# Sostituisci YOUR_TOKEN con il token che hai copiato
git remote set-url origin https://YOUR_TOKEN@github.com/aristoteleitaca/veratour-piano-lavoro.git

git push -u origin main
```

**OPPURE** usa questo comando (ti chiederà il token):

```bash
git remote set-url origin https://github.com/aristoteleitaca/veratour-piano-lavoro.git
git push -u origin main
# Quando richiesto:
# Username: aristoteleitaca
# Password: INCOLLA_IL_TOKEN_QUI
```

## Passo 4: Deploy su Streamlit Cloud

1. Vai su: https://share.streamlit.io
2. Accedi con GitHub
3. Clicca **"New app"**
4. Seleziona:
   - **Repository**: `aristoteleitaca/veratour-piano-lavoro`
   - **Branch**: `main`
   - **Main file path**: `app_streamlit.py`
5. Clicca **"Deploy"**

---

## Alternativa: Usa GitHub CLI (più semplice)

Se hai `gh` installato:

```bash
gh auth login
# Segui le istruzioni, scegli GitHub.com e token

gh repo create veratour-piano-lavoro --private --source=. --remote=origin --push
```

