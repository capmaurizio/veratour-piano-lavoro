# 📊 Riepilogo di Sintesi — CalcoloPianoLavoro

**Ultimo aggiornamento**: Marzo 2026  
**Versione**: 2.1 — Multi-Tour Operator con Rilevamento Dinamico  
**Deploy**: https://veratour-piano-lavoro-8ahkfuaued3a59zwb5dwsb.streamlit.app  
**Repository**: https://github.com/capmaurizio/veratour-piano-lavoro

---

## 🎯 Scopo

Sistema **Streamlit multi-tour operator** per il calcolo automatico dei consuntivi del piano di lavoro delle assistenze aeroportuali. Caricato un file Excel con il Piano Lavoro, il sistema:

1. Rileva automaticamente i tour operator presenti
2. Applica le regole tariffarie specifiche di ciascuno
3. Genera un file Excel di output con tutti i dettagli e i totali

---

## 🔐 Accesso

| Campo | Valore |
|-------|--------|
| Username | `silvia` |
| Password | `1` |

---

## 🏗️ Architettura — File Principali

| File | Ruolo |
|------|-------|
| `app_streamlit.py` | Entry point Streamlit: login, upload file, UI a step |
| `tour_operators.py` | Import moduli TO, rilevamento dinamico, dizionario processori |
| `processing.py` | Logica di calcolo, combinazione risultati, generazione Excel |
| `ui_styles.py` | CSS professionale + componenti UI (top bar, stepper, stat card) |

---

## 🏢 Tour Operator Supportati (9)

| Tour Operator | Cartella | Modulo | Note speciali |
|---------------|----------|--------|---------------|
| **Veratour** | `Veratour/` | `consuntivoveratour.py` | Calcolo assistenti VRN, tariffe proprie BGY/VRN |
| **Alpitour** | `Alpitour/` | `consuntivoalpitour.py` | Tariffe fisse per ore intere (3h→8h), BGY vs VRN |
| **Aliservice** | `Aliservice/` | `consuntivoaliservice.py` | **Agenzia** che gestisce più TO (BRIXIA, FUTURA, ecc.) |
| **Baobab/TH** | `Baobab/` | `consuntivobaobab.py` | Baobab e TH stesso pacchetto; W4 a FCO: STD−3h |
| **Domina** | `Domina/` | `consuntivodomina.py` | Costi parcheggio NAP €1/h, BRI €6/3h |
| **MichelTours** | `MICHELTOURS/` | `consuntivomicheltours.py` | Base fissa 3 ore (180 min) |
| **SAND** | ` Sand/` *(spazio nel nome)* | `consuntivosand.py` | No extra; notturno 22:00–03:59; END=STD |
| **Caboverdetime** | `Caboverdetime/` | `consuntivocaboverdetime.py` | Base da CVC a STD; Extra da STD ad ATD |
| **Rusconi** | `Rusconi/` | `consuntivorusconi.py` | Base fissa per APT; extra solo su ritardo; notturno +20% |

### Gestione Aliservice
Aliservice è un'**agenzia** (non un tour operator diretto): filtra sulla colonna **AGENZIA** invece di TOUR OPERATOR. I TO che gestisce vengono automaticamente esclusi dalla lista principale.

---

## ⚙️ Architettura Calcolo

### Interfaccia comune — ogni modulo TO implementa:

```python
# Config con tariffe specifiche
@dataclass
class CalcConfig:
    apt_filter: Optional[List[str]]
    rounding_extra: RoundingPolicy
    rounding_night: RoundingPolicy
    holiday_dates: Optional[set]
    # ... parametri specifici del TO

# Elaborazione
def process_files(input_files, cfg) -> Tuple[detail_df, totals_df, discr_df]: ...

# Scrittura output
def write_output_excel(output_path, detail_df, totals_df, discr_df) -> None: ...
```

### Flusso elaborazione

```
Excel upload
    │
    ├─ detect_tour_operators()       ← legge colonne TOUR OPERATOR + AGENZIA
    │
    ├─ find_tour_operator_folder()   ← cerca cartella con consuntivo*.py
    │
    ├─ per ogni TO trovato:
    │       process_files([tmp_path], cfg)
    │           └─ iter_excel_sheets → normalize → filter → forward-fill TURNO
    │              → parse blocchi → calcola turno/extra/notturno/festivo
    │
    ├─ pd.concat(all_detail_dfs)     ← combina tutto
    │
    └─ write_output_excel()          ← genera Excel finale
           └─ _add_tour_operator_sheet()  ← aggiunge foglio riepilogo TO
```

### Logica di calcolo comune (Veratour come riferimento)

| Voce | Formula |
|------|---------|
| **Turno base** | `75€ + max(0, durata_h − 3) × 15€/h` |
| **Extra** | `(ATD_max − fine_turno) / 60 × 18€/h` — solo se DEC |
| **Notturno** | `minuti_notturni × 0.083333 €/min` (fascia 23:00–05:00) |
| **Festivo** | `(Turno + Extra + Notturno) × 1.20` |

> Ogni TO ha le proprie tariffe — vedi documentazione specifica nella cartella del TO.

---

## 📤 Output Excel — Fogli Generati

| Foglio | Contenuto |
|--------|-----------|
| `TourOperatourRilevati` | Lista completa TO rilevati con status (1° foglio) |
| `DettaglioBlocchi` | Ogni blocco con AGENZIA, VOLO, DEST.NE, turno, extra, notturno, totale |
| `TotaliPeriodo` | Totali per periodo (1–15, 16–31, MESE) con colonna AGENZIA |
| `VRN`, `BGY`, `NAP`... | Dettaglio per ogni aeroporto con colonne Agenzia e Tour Operator |
| `TOTALE` | Riepilogo totale per aeroporto |
| `Assistenti_VRN` | Calcolo stipendi assistenti Verona *(se presente)* |
| `Discrepanze` | Eventuali discrepanze rilevate nei calcoli |

### Status TO nel foglio riepilogo

| Status | Significato |
|--------|-------------|
| `Codificato - Elaborato` | Modulo presente, dati trovati ed elaborati |
| `Codificato - Rilevato ma senza dati elaborati` | Modulo presente, ma nessun dato corrispondente |
| `Modulo presente ma non rilevato nel file` | Modulo disponibile, assente nel file caricato |
| `Non codificato` | Nessun modulo disponibile |

---

## 🖥️ UI — Interfaccia Utente

### Step flow (stepper orizzontale)
```
[1] Caricamento → [2] Rilevamento → [3] Elaborazione → [4] Completato
```

### Componenti
- **Login card** con logo SCAY, username/password
- **File uploader** Excel (.xlsx / .xls)
- **🔍 Diagnostica struttura file** (nuova) — espanso automaticamente se il file ha problemi:
  - ⚠️ Foglio non chiamato `"PIANO VOLI"` → mostra fogli trovati
  - ⚠️ Colonne con nomi alternativi (es. `"H"` invece di `"DATA"`)
  - 🔴 Colonne obbligatorie completamente assenti (DATA, APT, TURNO, STD, ATD, TOUR OPERATOR)
  - 💡 Suggerimento su come correggere il file
- **Status lines** colorate (info / success / warn / error)
- **Stat cards** — Tour Operator elaborati, Blocchi calcolati, Discrepanze
- **Download button** Excel risultati (in alto e in basso)

---

## 🚀 Deploy

| Voce | Dettaglio |
|------|-----------|
| **Piattaforma** | Streamlit Cloud (gratuito) |
| **URL** | https://veratour-piano-lavoro-8ahkfuaued3a59zwb5dwsb.streamlit.app |
| **Auto-deploy** | Ogni push su GitHub aggiorna automaticamente |
| **Avvio locale** | `streamlit run app_streamlit.py` oppure `./avvia_app.sh` |
| **Porta locale** | http://localhost:8501 |

---

## 🛠️ Stack Tecnologico

| Libreria | Uso |
|----------|-----|
| **Streamlit** | Interfaccia web |
| **Pandas** | Elaborazione dati Excel |
| **OpenPyXL** | Lettura/scrittura .xlsx |
| **xlrd** | Lettura file .xls legacy |
| **python-dateutil** | Gestione date e festivi (calcolo Pasqua) |
| **NumPy** | Arrotondamenti e calcoli numerici |
| **re (regex)** | Pattern matching colonne dinamiche e parsing turni |

---

## 📚 Documentazione per TO

| Tour Operator | File di riferimento |
|---------------|---------------------|
| Veratour | `Documentazione/README_calcolo.md` + `Documentazione/INDICE.md` |
| Alpitour | `Alpitour/PROSPETTO_CALCOLO_ALPITOUR.md` + `Alpitour/2025_12_RegoleAlpitour.txt` |
| Aliservice | `Aliservice/REGOLE CHAT GPT SCAYGROUP_PEOPLE ON THE MOVE_2025.docx` |
| Baobab | `Baobab/TARIFFE BAOBAB TH 26.docx` |
| Domina | `Domina/Regoledicalcolodomina.txt` |
| MichelTours | `MICHELTOURS/RegoleCalcoloMichelTours.txt` |
| SAND | `Sand/CalcoloSand.txt` |
| Caboverdetime | `Caboverdetime/CalcoloTurnicapoverdetime.txt` |
| Rusconi | `Rusconi/CalcolatariffeRusconi.txt` |

---

## ➕ Aggiungere un Nuovo Tour Operator

1. Crea cartella `NomeTO/` con file `consuntivoNomeTO.py`
2. Implementa `CalcConfig`, `process_files()`, `write_output_excel()`
3. Aggiungi import in `tour_operators.py` con try/except
4. Aggiungi entry nel dizionario `get_tour_operator_processors()`
5. Aggiungi mapping in `get_tour_operator_module_name()` se necessario

> Il sistema rileverà automaticamente il nuovo TO se presente nel file Excel caricato.

---

*Documento generato automaticamente — Marzo 2026*
