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

## 👤 App Assistenti (`app_assistenti.py`)

App Streamlit separata avviata sulla porta `:8502`. Permette agli assistenti di
consultare i propri turni e compilare gli orari effettivi per il calcolo automatico del compenso.

### Flusso
```
Login → Carica Piano Lavoro → Tabella turni → Form compilazione → Salva JSON
```

### Componenti
| Componente | Descrizione |
|-----------|-------------|
| **Login** | Nome assistente + password (`12345`) |
| **File uploader** | Carica il piano lavoro, filtra i turni dell'assistente |
| **Tabella riepilogativa** | Tutti i turni con stato ⏳/✅ e ore prestate |
| **Form turni** (expander) | Un expander per ogni turno con campi orario |
| **Download template** | Excel personalizzato con dati piano lavoro |

### Form di compilazione turno (nuovo — v2.3)

Ogni turno ha un expander che mostra:
1. **Info turno** dal piano lavoro (data, APT, volo, TO, STD)
2. **Campi inserimento**:
   - `🕐 Orario inizio servizio` — default = STD dal piano lavoro
   - `🕐 Orario fine effettivo` — gestisce cambio giorno automatico
   - `⏱️ Extra ritardo ATD (min)`
3. **Anteprima calcolo** (live, aggiornato ad ogni modifica):
   - Durata totale, Min notturni, Min extra
   - Per FCO: split **notte forfait** / **notte extra** (Regola B)
4. **Compenso**: €base + €extra + €notte = totale
5. **Salva** → JSON in `dati_assistenti/<NOME>.json`

### Data model JSON (per turno)
```json
{
  "orario_inizio":     "03:10",
  "orario_fine":       "05:40",
  "extra_ritardo_min": 53,
  "extra_min":         53,
  "notte_min":         170,
  "notte_forfait_min": 150,
  "notte_extra_min":   20,
  "durata_effettiva_h": 3.383,
  "apt": "FCO",  "tour_operator": "BAOBAB",
  "base_eur": 56.0,  "extra_eur": 10.6,  "notte_eur": 12.0,  "totale_eur": 78.6
}
```

### Fix calcolo notturno FCO (v2.3)
Il form passa `inizio_dt` e `fine_dt` reali a `calcola_tariffa_collaboratore()`,
evitando il fallback che poteva sovrastimare di €2,08 in scenari misto giorno→notte.

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

## 📅 Versioni

| Versione | Data | Novità principali |
|---------|------|-------------------|
| **1.0** | 2025-09 | Sistema mono-TO Veratour |
| **2.0** | 2026-01 | Multi-TO, rilevamento dinamico |
| **2.1** | 2026-02 | Refactoring tariffe FCO/NAP, fix notturno |
| **2.2** | 2026-03-30 | Diagnostica struttura file Excel a video |
| **2.3** | 2026-03-30 | Form turni assistenti + fix notturno FCO esatto |


---

*Documento generato automaticamente — Marzo 2026*
