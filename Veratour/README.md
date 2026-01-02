# 📊 Veratour 2025 - Calcolatore Piano di Lavoro

Sistema completo per il calcolo automatico dei consuntivi Veratour 2025 con interfaccia web Streamlit.

## 🚀 Quick Start

### Interfaccia Web (Consigliato)
L'applicazione è disponibile online su: **https://veratour-piano-lavoro-8ahkfuaued3a59zwb5dwsb.streamlit.app**

1. Carica il file Excel del piano di lavoro
2. Configura le opzioni (opzionale)
3. Clicca "Esegui Calcolo"
4. Scarica il file Excel con i risultati

### Uso Locale
```bash
# Installa dipendenze
pip install -r requirements.txt

# Avvia interfaccia web
streamlit run app_streamlit.py

# Oppure usa da riga di comando
python3 consuntivoveratour.py -i "Piano lavoro DICEMBRE 25.xlsx" -o "OUT_DIC.xlsx"
```

## ✨ Funzionalità

- ✅ **Calcolo Automatico**: Turni, Extra, Notturno, Festivi
- ✅ **Interfaccia Web**: Upload file, anteprima risultati, download Excel
- ✅ **Multi-Aeroporto**: VRN, BGY, NAP, VCE
- ✅ **Formato Ore Leggibile**: "25 ore e 55 minuti" invece di decimali
- ✅ **Dettaglio Giornaliero**: Breakdown per ogni aeroporto
- ✅ **Export Excel**: Fogli separati per aeroporto + totale

## 📋 Cosa Calcola

### Assistenze (Turni)
- **75€** base per le prime 3 ore
- **15€/ora** per ogni ora oltre le 3 ore
- Calcolo pro-rata al minuto

### Extra
- **18€/ora** per ore lavorate oltre la fine del turno
- Basato su ATD (Actual Time of Departure)

### Notturno
- Maggiorazione per ore tra **23:00 e 05:00**
- Modalità DIFF5: 5€/h (maggiorazione differenziale)
- Modalità FULL30: 30€/h (tariffa piena)

### Festivi
- Maggiorazione **+20%** su turno + extra + notturno
- Rilevamento automatico festivi italiani 2025

## 🔧 Configurazione

### Opzioni Disponibili
- **Filtro Aeroporti**: Seleziona aeroporti specifici
- **Modalità Notturno**: DIFF5 o FULL30
- **Arrotondamenti**: Configura arrotondamento Extra e Notturno
- **File Festivi**: Carica lista festivi personalizzati

## 📚 Documentazione

Tutta la documentazione dettagliata è nella cartella `documentazione/`:
- **[INDICE.md](documentazione/INDICE.md)**: Indice completo
- **[README_calcolo.md](documentazione/README_calcolo.md)**: Metodo di calcolo completo
- **[README_STREAMLIT.md](documentazione/README_STREAMLIT.md)**: Guida interfaccia web
- **[DEPLOY.md](documentazione/DEPLOY.md)**: Guida deploy su Streamlit Cloud

## 🌐 Deploy

L'applicazione è deployata su **Streamlit Cloud**:
- URL: https://veratour-piano-lavoro-8ahkfuaued3a59zwb5dwsb.streamlit.app
- Repository: https://github.com/capmaurizio/veratour-piano-lavoro
- Auto-deploy: Ogni push su GitHub aggiorna automaticamente l'app

## 🛠️ Tecnologie

- **Python 3.11**
- **Streamlit**: Interfaccia web
- **Pandas**: Elaborazione dati
- **OpenPyXL**: Lettura/scrittura Excel
- **Streamlit Cloud**: Hosting gratuito

---

**Ultimo aggiornamento**: Gennaio 2025

