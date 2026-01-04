# 📊 Calcolo Piano di Lavoro - Sistema Multi-Tour Operatour

Sistema modulare per il calcolo automatico dei consuntivi piano di lavoro per diversi tour operatour. Rileva automaticamente i tour operatour dall'Excel caricato e li elabora dinamicamente.

## 🏗️ Struttura Progetto

```
CalcoloPianoLavoro/
├── app_streamlit.py           # 🚀 Interfaccia web principale (ROOT)
├── requirements.txt           # Dipendenze Python
├── Veratour/                  # Calcolatore Veratour 2025
│   ├── consuntivoveratour.py  # Logica calcolo Veratour
│   ├── requirements.txt
│   ├── Assistenti/            # Documenti accordi assistenti VRN
│   └── documentazione/
├── Alpitour/                  # Calcolatore Alpitour
│   ├── consuntivoalpitour.py  # Logica calcolo Alpitour
│   └── ...
└── README.md                  # Questo file
```

## 🚀 Quick Start

### Interfaccia Web Online
**URL**: https://veratour-piano-lavoro-8ahkfuaued3a59zwb5dwsb.streamlit.app

### Uso Locale
```bash
# Installa dipendenze
pip install -r requirements.txt

# Avvia interfaccia web
streamlit run app_streamlit.py

# Oppure usa lo script helper
./avvia_app.sh
```

L'app si aprirà su `http://localhost:8501`

## ✨ Funzionalità Principali

### 🔍 Rilevamento Automatico Tour Operatour
- Rileva automaticamente i tour operatour dall'Excel caricato
- Cerca dinamicamente la cartella corrispondente (es: `Veratour/`, `Alpitour/`)
- Carica il modulo di calcolo specifico (es: `consuntivoveratour.py`)

### 📊 Elaborazione Multi-Tour Operatour
- Elabora tutti i tour operatour rilevati in un'unica esecuzione
- Combina i risultati in un unico Excel di output
- Gestisce tour operatour non supportati (foglio "TourOperatourNonElaborati")

### 📋 Fogli Excel Generati
- **Fogli per aeroporto**: Dettaglio per ogni aeroporto (VRN, BGY, NAP, VCE, ecc.)
- **TOTALE**: Riepilogo totale per aeroporto
- **Assistenti_VRN** (solo Veratour): Calcolo stipendi assistenti aeroporto Verona
- **TourOperatourNonElaborati**: Lista tour operatour rilevati ma non supportati

### 👥 Calcolo Assistenti VRN (Veratour)
- Calcolo automatico stipendi assistenti per aeroporto Verona
- Tariffe basate su accordi (58€ base/3h per Senior, 12€/h extra, notturno proporzionale 15%, festivi +20%)
- Dettaglio giorno per giorno disponibile nell'interfaccia web

## 📋 Tour Operatour Supportati

### ✅ Veratour
- **Status**: ✅ Operativo
- **Modulo**: `Veratour/consuntivoveratour.py`
- **Calcolo**: Turni, extra, notturno, festivi, assistenti VRN
- **Aeroporti**: VRN, BGY, NAP, VCE
- **Documentazione**: `Veratour/documentazione/INDICE.md`

### ✅ Alpitour
- **Status**: ✅ Operativo
- **Modulo**: `Alpitour/consuntivoalpitour.py`
- **Calcolo**: Logica specifica Alpitour

### 📝 Altri Tour Operatour
- **Status**: Rilevati automaticamente se presenti nell'Excel
- Se la cartella/modulo non esiste, vengono aggiunti al foglio "TourOperatourNonElaborati"

## 🎯 Come Funziona

1. **Carica Excel**: L'utente carica un file Excel contenente il piano di lavoro
2. **Rilevamento**: Il sistema rileva automaticamente i tour operatour presenti (analisi colonne Excel)
3. **Caricamento Dinamico**: Per ogni tour operatour:
   - Cerca la cartella corrispondente (es: `Veratour/`)
   - Carica il modulo di calcolo (es: `consuntivoveratour.py`)
   - Esegue il calcolo con le regole specifiche
4. **Combinazione**: I risultati vengono combinati in un unico Excel
5. **Output**: File Excel con fogli separati per aeroporto, totali, assistenti, e tour operatour non elaborati

## 🔧 Aggiungere un Nuovo Tour Operatour

1. **Crea la cartella**: `[NomeTourOperatour]/` (es: `Neos/`)
2. **Crea il modulo**: `[NomeTourOperatour]/consuntivo[nome].py` (es: `Neos/consuntivoneos.py`)
3. **Implementa le funzioni richieste**:
   - `process_files(input_path, output_path, config)` - Elabora i file
   - `write_output_excel(detail_df, totals_df, discr_df, output_path)` - Scrive Excel
4. **Test**: Carica un Excel con il nuovo tour operatour e verifica il funzionamento

Il sistema rileverà automaticamente il nuovo tour operatour se presente nell'Excel!

## 📚 Documentazione

### Documentazione Generale
- **README.md** (questo file): Panoramica sistema multi-tour operatour

### Documentazione Veratour
- `Veratour/documentazione/INDICE.md`: Indice documentazione Veratour
- `Veratour/documentazione/README_calcolo.md`: Metodo di calcolo Veratour
- `Veratour/documentazione/README_STREAMLIT.md`: Guida interfaccia web
- `Veratour/documentazione/DEPLOY.md`: Guida deploy Streamlit Cloud

### Accordi e Tariffe
- `Veratour/Assistenti/`: Documenti accordi assistenti VRN
  - `Accordo_Assistenti_VRN 26_Completo .docx`: Tariffe complete assistenti

## 🌐 Deploy

L'applicazione è deployata su **Streamlit Cloud**:
- **URL**: https://veratour-piano-lavoro-8ahkfuaued3a59zwb5dwsb.streamlit.app
- **Repository**: https://github.com/capmaurizio/veratour-piano-lavoro
- **Auto-deploy**: Ogni push su GitHub aggiorna automaticamente l'app

## 🛠️ Tecnologie

- **Python 3.10+**
- **Streamlit**: Interfaccia web
- **Pandas**: Elaborazione dati
- **OpenPyXL**: Lettura/scrittura Excel
- **python-dateutil**: Gestione date
- **Streamlit Cloud**: Hosting gratuito

## 📝 Note Importanti

- Il file Excel di input deve contenere una colonna che identifica il tour operatour
- Il sistema normalizza i nomi dei tour operatour per il matching (rimuove anni, caratteri speciali)
- I tour operatour non supportati vengono comunque rilevati e listati nel foglio "TourOperatourNonElaborati"
- Per Veratour: il calcolo assistenti VRN è automatico se presenti dati per l'aeroporto VRN con assistenti associati

---

**Ultimo aggiornamento**: Gennaio 2025
