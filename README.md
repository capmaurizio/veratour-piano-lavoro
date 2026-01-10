# 📊 Calcolo Piano di Lavoro - Sistema Multi-Tour Operatour

Sistema modulare per il calcolo automatico dei consuntivi piano di lavoro per diversi tour operatour. Rileva automaticamente i tour operatour dall'Excel caricato e li elabora dinamicamente.

## 🔐 Autenticazione

L'applicazione è protetta con sistema di login:
- **Username**: `skypemiao`
- **Password**: `jfjdljf3244a?091`

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
├── Aliservice/                # Calcolatore Aliservice (Agenzia)
│   ├── consuntivoaliservice.py
│   └── ...
├── Baobab/                    # Calcolatore Baobab/TH
│   ├── consuntivobaobab.py
│   └── ...
├── Domina/                    # Calcolatore Domina
│   ├── consuntivodomina.py
│   └── ...
├── MICHELTOURS/               # Calcolatore MichelTours
│   ├── consuntivomicheltours.py
│   └── ...
├── Sand/                      # Calcolatore SAND
│   ├── consuntivosand.py
│   └── ...
├── Caboverdetime/             # Calcolatore Caboverdetime
│   ├── consuntivocaboverdetime.py
│   └── ...
├── Rusconi/                   # Calcolatore Rusconi
│   ├── consuntivorusconi.py
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

### 🔐 Sistema di Autenticazione
- Login protetto con username e password
- Logout disponibile in alto al centro della pagina
- Session management integrato

### 🔍 Rilevamento Automatico e Dinamico Tour Operatour
- **Rilevamento intelligente**: Analizza automaticamente tutte le colonne "TOUR OPERATOR" e "AGENZIA" nel file Excel
- **Ricerca dinamica cartelle**: Per ogni tour operator rilevato, cerca automaticamente la cartella corrispondente (es: `Veratour/`, `Alpitour/`, `Aliservice/`, ecc.)
- **Verifica modulo calcolo**: Verifica che la cartella contenga un file `consuntivo*.py` per il calcolo
- **Status reporting**: Mostra chiaramente quali tour operator hanno calcolo disponibile e quali no
- **Nessuna configurazione richiesta**: Il sistema funziona automaticamente senza liste hardcoded

### 📊 Elaborazione Multi-Tour Operatour
- Elabora tutti i tour operatour rilevati in un'unica esecuzione
- Mostra i progressi di elaborazione in formato orizzontale (massimo 4 per riga) per risparmiare spazio
- Combina i risultati in un unico Excel di output
- Gestisce tour operatour non supportati (foglio "TourOperatourRilevati")

### 📋 Fogli Excel Generati
- **TourOperatourRilevati** (primo foglio): Lista completa di tutti i tour operator rilevati con il loro status:
  - "Codificato - Elaborato": Tour operator con modulo presente e dati elaborati
  - "Codificato - Rilevato ma senza dati elaborati": Modulo presente ma nessun dato corrispondente nel file
  - "Modulo presente ma non rilevato nel file": Modulo disponibile ma non trovato nel file Excel
  - "Non codificato": Nessun modulo disponibile
- **DettaglioBlocchi**: Dettaglio completo di tutti i blocchi elaborati con colonna AGENZIA
- **TotaliPeriodo**: Totali raggruppati per periodo (16-31, 1-15, MESE) con colonna AGENZIA
- **Fogli per aeroporto**: Dettaglio per ogni aeroporto (VRN, BGY, NAP, VCE, ecc.) con colonna Agenzia
- **TOTALE**: Riepilogo totale per aeroporto con colonna Agenzia
- **Assistenti_VRN** (se presente): Calcolo stipendi assistenti aeroporto Verona
- **Discrepanze**: Eventuali discrepanze rilevate nei calcoli

### 🏢 Gestione Agenzia (Aliservice)
- **Aliservice come agenzia**: Aliservice gestisce multipli tour operator (BRIXIA, FUTURA, ATALANTA, FLYNESS, ecc.)
- **Filtraggio intelligente**: I tour operator gestiti da Aliservice vengono filtrati dalla lista principale
- **Colonna AGENZIA**: Tutti i fogli Excel includono la colonna AGENZIA per identificare l'agenzia di riferimento
- **Raggruppamento output**: I totali vengono raggruppati per AGENZIA, TOUR OPERATOR e APT quando applicabile

## 📋 Tour Operatour Supportati

### ✅ Veratour
- **Status**: ✅ Operativo
- **Modulo**: `Veratour/consuntivoveratour.py`
- **Calcolo**: Turni, extra, notturno, festivi, assistenti VRN
- **Aeroporti**: VRN, BGY, NAP, VCE
- **Documentazione**: `Veratour/documentazione/INDICE.md`
- **Caratteristiche speciali**: Calcolo automatico stipendi assistenti VRN

### ✅ Alpitour
- **Status**: ✅ Operativo
- **Modulo**: `Alpitour/consuntivoalpitour.py`
- **Calcolo**: Logica specifica Alpitour con tariffe per aeroporto
- **Aeroporti**: Tutti gli aeroporti supportati
- **Funzione speciale**: Usato come funzione di output principale quando ci sono multipli tour operator

### ✅ Aliservice
- **Status**: ✅ Operativo
- **Modulo**: `Aliservice/consuntivoaliservice.py`
- **Tipo**: Agenzia che gestisce multipli tour operator
- **Tour operator gestiti**: BRIXIA, FUTURA, ATALANTA, FLYNESS, ecc.
- **Filtraggio**: Basato su colonna "AGENZIA" invece di "TOUR OPERATOR"
- **Servizi speciali**: Supporta "Meet & Greet" (M&G) identificato dalla colonna "arrivi/trf"
- **Regole**: Documentate in `Aliservice/REGOLE CHAT GPT SCAYGROUP_PEOPLE ON THE MOVE_2025.docx`

### ✅ Baobab/TH
- **Status**: ✅ Operativo
- **Modulo**: `Baobab/consuntivobaobab.py`
- **Caratteristiche speciali**:
  - Baobab e TH sono parte dello stesso pacchetto
  - Logica speciale per Wizzair (W4) a Fiumicino (FCO): START = STD - 3:00 (mezzora extra)
  - Supporto per minuti extra CVC: cerca pattern "CVCxx" nelle colonne NOTE/TURNI
- **Regole**: Documentate in `Baobab/TARIFFE BAOBAB TH 26.docx`

### ✅ Domina
- **Status**: ✅ Operativo
- **Modulo**: `Domina/consuntivodomina.py`
- **Caratteristiche speciali**:
  - Costi parcheggio: NAP (€1/ora), BRI (€6/3 ore, arrotondato per eccesso)
- **Regole**: Documentate in `Domina/Regoledicalcolodomina.txt`

### ✅ MichelTours
- **Status**: ✅ Operativo
- **Modulo**: `MICHELTOURS/consuntivomicheltours.py`
- **Caratteristiche**: Base 3 ore (180 minuti)
- **Regole**: Documentate in `MICHELTOURS/RegoleCalcoloMichelTours.txt`

### ✅ SAND
- **Status**: ✅ Operativo
- **Modulo**: `Sand/consuntivosand.py`
- **Caratteristiche speciali**:
  - **Nessun extra**: SAND non prevede ore extra (sempre 0)
  - **Calcolo notturno speciale**: Finestra 22:00-03:59
  - **Calcolo notturno basato su CVC**: Il notturno decorre dall'orario di convocazione (CVC) fino a STD
  - **Fine turno = STD**: L'END del turno è sempre STD (non ATD)
- **Regole**: Documentate in `Sand/CalcoloSand.txt`

### ✅ Caboverdetime
- **Status**: ✅ Operativo
- **Modulo**: `Caboverdetime/consuntivocaboverdetime.py`
- **Caratteristiche speciali**:
  - **Base**: Calcolata da CVC (convocazione) a STD (scheduled departure)
  - **Extra**: Calcolata da STD (scheduled) a ATD (actual departure)
- **Regole**: Documentate in `Caboverdetime/CalcoloTurnicapoverdetime.txt`

### ✅ Rusconi
- **Status**: ✅ Operativo
- **Modulo**: `Rusconi/consuntivorusconi.py`
- **Caratteristiche speciali**:
  - **Base fissa**: €100 per aeroporti nazionali, €110 per FCO e VCE
  - **Extra solo su ritardo**: Solo per ATD > STD (ritardo volo)
  - **Notturno**: +20% su (Base + Extra), calcolato proporzionalmente ai minuti notturni
  - **Servizi accessori**: Costo carte imbarco basato su numero passeggeri (soglia 20)
- **Regole**: Documentate in `Rusconi/CalcolatariffeRusconi.txt`

## 🎯 Come Funziona

### 1. Login
- Accedi con username e password
- Il pulsante Logout è disponibile in alto al centro della pagina

### 2. Carica File Excel
- Carica il file Excel contenente il piano di lavoro
- Il sistema rileva automaticamente tutti i tour operator presenti nelle colonne "TOUR OPERATOR" e "AGENZIA"

### 3. Rilevamento Dinamico
Il sistema:
- Analizza tutte le colonne "TOUR OPERATOR" e "AGENZIA" in tutti i fogli Excel
- Per ogni valore unico trovato:
  - Normalizza il nome (rimuove caratteri speciali, converte in lowercase)
  - Cerca una cartella corrispondente nella root del progetto
  - Verifica che la cartella contenga un file `consuntivo*.py`
  - Classifica il tour operator come:
    - ✅ **Con calcolo disponibile**: Cartella e modulo trovati
    - ⚠️ **Senza calcolo**: Nessuna cartella trovata
- Mostra i risultati in modo chiaro all'utente

### 4. Elaborazione
- Il sistema elabora automaticamente tutti i tour operator con calcolo disponibile
- I messaggi di elaborazione vengono mostrati in formato orizzontale (massimo 4 per riga)
- Ogni tour operator viene elaborato con le sue regole specifiche

### 5. Output
- Genera un unico file Excel con:
  - Foglio "TourOperatourRilevati" (primo foglio) con lo status di tutti i tour operator
  - Foglio "DettaglioBlocchi" con tutti i dettagli, incluso colonna AGENZIA
  - Foglio "TotaliPeriodo" con totali per periodo, incluso colonna AGENZIA
  - Fogli per ogni aeroporto, incluso colonna Agenzia
  - Foglio "TOTALE" con riepilogo per aeroporto, incluso colonna Agenzia
  - Altri fogli tecnici se necessari

## 🎨 Interfaccia Utente

### Navigazione Card-Based
L'interfaccia utilizza un sistema di navigazione basato su card cliccabili:
- **Carica File Excel del Piano di Lavoro**: Upload del file e rilevamento tour operator
- **Esegui Calcolo**: Esecuzione dell'elaborazione
- **Risultati**: Visualizzazione dei risultati (solo discrepanze se presenti)
- **Scarica Risultati**: Download del file Excel generato

### Sezioni Rimosse (Ottimizzazione Spazio)
Le seguenti sezioni sono state rimosse per ottimizzare lo spazio:
- ❌ Sidebar con opzioni di calcolo (valori di default usati automaticamente)
- ❌ Sezione "Validazione File"
- ❌ Sezione "Anteprima Dettaglio Blocchi"
- ❌ Sezione "Dettaglio Giorno per Giorno - Assistenti VRN"
- ❌ Sezione "Totali per Aeroporto" (disponibile nel file Excel scaricabile)

## 🔧 Aggiungere un Nuovo Tour Operatour

### Passo 1: Crea la Struttura
1. **Crea la cartella**: `[NomeTourOperatour]/` (es: `Neos/`)
2. **Crea il modulo**: `[NomeTourOperatour]/consuntivo[nome].py` (es: `Neos/consuntivoneos.py`)

### Passo 2: Implementa le Funzioni
Il modulo deve implementare le seguenti funzioni:

```python
from dataclasses import dataclass
from typing import List, Tuple
import pandas as pd

@dataclass
class CalcConfig:
    apt_filter: Optional[List[str]] = None
    rounding_extra: RoundingPolicy = field(default_factory=lambda: RoundingPolicy("NONE", 5))
    rounding_night: RoundingPolicy = field(default_factory=lambda: RoundingPolicy("NONE", 5))
    holiday_dates: Optional[set] = None
    to_keyword: str = "nome_tour_operator"  # Nome normalizzato per il matching

def process_files(input_files: List[str], cfg: CalcConfig) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Elabora i file Excel di input
    
    Returns:
        Tuple[detail_df, totals_df, discr_df]:
        - detail_df: DataFrame con dettaglio di tutti i blocchi
        - totals_df: DataFrame con totali per periodo
        - discr_df: DataFrame con eventuali discrepanze
    """
    # Implementazione logica di calcolo
    pass

def write_output_excel(output_path: str, detail_df: pd.DataFrame, totals_df: pd.DataFrame, discr_df: pd.DataFrame) -> None:
    """
    Scrive il file Excel di output con tutti i fogli necessari
    """
    pass
```

### Passo 3: Aggiungi Import in app_streamlit.py
Aggiungi l'import nella sezione appropriata:

```python
try:
    from consuntivo[nome] import (
        CalcConfig as [Nome]CalcConfig,
        process_files as process_files_[nome],
        write_output_excel as write_output_excel_[nome],
    )
    [NOME]_AVAILABLE = True
except ImportError as e:
    [NOME]_AVAILABLE = False
    [Nome]CalcConfig = None
    process_files_[nome] = None
    write_output_excel_[nome] = None
```

### Passo 4: Aggiungi al Mapping
Aggiungi il tour operator al dizionario `tour_operator_processors` in `app_streamlit.py`:

```python
'[nome_normalizzato]': {
    'available': globals().get('[NOME]_AVAILABLE', False),
    'config_class': [Nome]CalcConfig,
    'process_func': process_files_[nome],
    'write_func': write_output_excel_[nome],
    'config_kwargs': lambda: {
        'apt_filter': apt_filter if apt_filter else None,
        'rounding_extra': RoundingPolicy("NONE", 5),
        'rounding_night': RoundingPolicy("NONE", 5),
        'holiday_dates': holiday_dates,
    }
}
```

### Passo 5: Normalizzazione Nome
Aggiorna la funzione `get_tour_operator_module_name` in `app_streamlit.py` se necessario:

```python
elif '[nome]' in to_clean:
    return '[nome_normalizzato]'
```

**Il sistema rileverà automaticamente il nuovo tour operatour se presente nell'Excel!**

## 📚 Documentazione

### Documentazione Generale
- **README.md** (questo file): Panoramica sistema multi-tour operatour

### Documentazione Tour Operator Specifici
- **Veratour**: `Veratour/documentazione/INDICE.md`
- **Aliservice**: `Aliservice/REGOLE CHAT GPT SCAYGROUP_PEOPLE ON THE MOVE_2025.docx`
- **Baobab**: `Baobab/TARIFFE BAOBAB TH 26.docx`
- **Domina**: `Domina/Regoledicalcolodomina.txt`
- **MichelTours**: `MICHELTOURS/RegoleCalcoloMichelTours.txt`
- **SAND**: `Sand/CalcoloSand.txt`
- **Caboverdetime**: `Caboverdetime/CalcoloTurnicapoverdetime.txt`
- **Rusconi**: `Rusconi/CalcolatariffeRusconi.txt`

### Accordi e Tariffe
- `Veratour/Assistenti/`: Documenti accordi assistenti VRN
- `Aliservice/ACCORDO DI COLLABORAZIONE SCAY-PEOPLE 2025.pdf`: Accordo Aliservice

## 🌐 Deploy

L'applicazione è deployata su **Streamlit Cloud**:
- **URL**: https://veratour-piano-lavoro-8ahkfuaued3a59zwb5dwsb.streamlit.app
- **Repository**: https://github.com/capmaurizio/veratour-piano-lavoro
- **Auto-deploy**: Ogni push su GitHub aggiorna automaticamente l'app

## 🛠️ Tecnologie

- **Python 3.10+**
- **Streamlit**: Interfaccia web
- **Pandas**: Elaborazione dati Excel
- **OpenPyXL**: Lettura/scrittura Excel (.xlsx)
- **xlrd**: Lettura file Excel legacy (.xls)
- **python-dateutil**: Gestione date e parsing
- **re (regex)**: Pattern matching per colonne dinamiche
- **Streamlit Cloud**: Hosting gratuito

## 📝 Note Importanti

### Rilevamento Tour Operator
- Il sistema rileva automaticamente i tour operator dalle colonne "TOUR OPERATOR" e "AGENZIA"
- La normalizzazione del nome rimuove caratteri speciali e converte in lowercase per il matching
- Il matching è flessibile: cerca corrispondenze parziali tra nome cartella e nome tour operator

### Colonna AGENZIA
- La colonna AGENZIA viene inclusa in tutti i fogli Excel quando presente nei dati
- Per Aliservice, AGENZIA = "Aliservice" e TOUR OPERATOR = nome del tour operator gestito (es: "BRIXIA", "FUTURA")
- Per altri tour operator, AGENZIA sarà vuota o None

### Gestione Aliservice
- Aliservice è un'**agenzia** che gestisce multipli tour operator
- Il filtro avviene sulla colonna **AGENZIA** (non TOUR OPERATOR) per Aliservice
- I tour operator gestiti da Aliservice vengono automaticamente esclusi dalla lista principale quando Aliservice è disponibile
- I totali vengono raggruppati per AGENZIA, TOUR OPERATOR e APT

### Valori di Default
Le opzioni di calcolo (precedentemente nella sidebar) ora usano valori di default:
- Filtro aeroporti: Nessuno (tutti gli aeroporti)
- Modalità notturno Veratour: DIFF5
- Arrotondamenti: NONE (nessun arrotondamento) per tutti i tour operator tranne Veratour

### Output Excel
- Il file Excel generato contiene sempre la colonna AGENZIA quando disponibile
- Il foglio "TourOperatourRilevati" fornisce una panoramica completa dello status di tutti i tour operator rilevati
- I fogli per aeroporto includono sempre le colonne "Agenzia" e "Tour Operator" per chiarezza

---

**Ultimo aggiornamento**: Gennaio 2025  
**Versione**: 2.0 - Multi-Tour Operatour con Rilevamento Dinamico
