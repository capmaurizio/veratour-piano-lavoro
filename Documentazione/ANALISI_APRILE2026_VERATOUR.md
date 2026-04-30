# 📋 Analisi Piano Lavoro APRILE 2026 — Veratour
> Data analisi: 30/04/2026 | File: `APRILE-2026_NUOVO.xlsx` | Commit: `f3373c8`

---

## 🗂️ File analizzato

| Campo | Valore |
|-------|--------|
| **File** | `APRILE-2026_NUOVO.xlsx` |
| **Percorso** | `/CalcoloPianoLavoro/APRILE-2026_NUOVO.xlsx` |
| **Foglio principale** | `PIANO VOLI` |
| **Righe totali** | 1.123 |
| **Colonne** | 107 |

---

## 🏢 Tour Operator presenti nel file

| Tour Operator | Righe | Modulo disponibile |
|--------------|-------|-------------------|
| VERATOUR | 98 | ✅ veratour |
| ALPITOUR | 46 | ✅ alpitour |
| BAOBAB | 44 | ✅ baobab |
| BAOBAB/TH | 19 | ✅ baobab |
| RUSCONI VIAGGI | 7 | ✅ rusconi |
| SAND | 7 | ✅ sand |
| DOMINA | 1 | ✅ domina |
| CAPOVERDE TIME | 4 | ✅ caboverdetime *(fix applicato)* |
| MICHELTOUR | 3 | ✅ micheltours *(fix applicato)* |
| BRIXIA | — | ⚠️ non codificato |
| FUTURA | — | ⚠️ non codificato |
| ATALANTA | — | ⚠️ non codificato |
| FLYNESS | — | ⚠️ non codificato |
| TRAVEL DESIGN STUDIO | — | ⚠️ non codificato |
| GATTINONI MICE | — | ⚠️ non codificato |
| IOT | — | ⚠️ non codificato |
| NEW BEETLE | — | ⚠️ non codificato |
| RODOCANACHI | — | ⚠️ non codificato |
| MISTER GO | — | ⚠️ non codificato |
| VIRTUS | — | ⚠️ non codificato |
| ANVIDEAS | — | ⚠️ non codificato |
| KUONI | — | ⚠️ non codificato |
| B-ITALIAN | — | ⚠️ non codificato |

---

## ✈️ VERATOUR — Riepilogo per Aeroporto

| Apt | Turni | Confermati | PAX tot. | PAX mancanti | N° Assistenti |
|-----|-------|-----------|---------|-------------|--------------|
| **BGY** | 19 | 19/19 ✅ | ~535 | 2 righe | 8 |
| **NAP** | 15 | 15/15 ✅ | ~130 | 2 righe | 4 |
| **VCE** | 1 | 1/1 ✅ | ⚠️ mancante | 1 riga | 1 |
| **VRN** | 63 | 63/63 ✅ | ~1.450 | 1 riga | 6 |
| **TOTALE** | **98** | **98/98** | **~2.115** | **6 righe** | — |

### Assistenti per aeroporto

**BGY:** Filippo Bonfanti, Giorgio Moserle, Lisa Foresti, Ludovica Bonfanti, Matilde Oliveti, Nikla Coscia, Silvia Mascheretti, Valeria Balzo

**NAP:** Angela Giorgio, Paolo Imperato, Roberta Casciello, Sara Merenda

**VCE:** Geri Casciello

**VRN:** Alessandra Consolini, Luca De Laurentis, Manuela Monese, Marcella Rusu, Marta Lucchetti, Rosita Cavallaro

---

## ✈️ VENEZIA (VCE) — Unico Turno Veratour Aprile 2026

> [!IMPORTANT]
> Nel piano lavoro aprile è presente **UN SOLO turno Veratour a Venezia** (15/04/2026).

| Campo | Valore |
|-------|--------|
| **Riga Excel** | 144 |
| **Data** | 15/04/2026 |
| **Convocazione** | 13:55 |
| **Volo** | W46765 |
| **Destinazione** | SSH – Sharm el-Sheikh |
| **STD** | 16:25 |
| **ATD** | 16:47 (+22 min ritardo) |
| **PAX** | ⚠️ **MANCANTE** |
| **Assistente** | GERI CASCIELLO |
| **Cellulare** | 338 832 8572 |
| **Inizio Turno** | 13:25 |
| **Fine Turno** | 16:47 |
| **Ore Turno** | 3h 22min (202 min) |
| **Confermato** | ✅ CONFERMATO |
| **Completo** | ✅ SI |

### ✅ Verifica Calcolo Ore — CORRETTO

| | Valore |
|--|--------|
| Inizio turno | 13:25 → 805 min |
| Fine turno | 16:47 → 1007 min |
| Differenza | **202 min = 3h 22min** |
| Ore nel file | 03:22:00 ✅ |
| **Risultato** | ✅ **CALCOLO CORRETTO** |

### ✅ Verifica Tariffa Veratour — CORRETTA

| Voce | Calcolo | Importo |
|------|---------|---------|
| Base turno (3h) | € 75,00 fissi | € 75,00 |
| Extra ore (22min oltre 3h) | 22/60 × 15 = | € 5,50 |
| Extra ATD | ATD = Fine turno → 0 min | € 0,00 |
| Notturno | Turno 13:25-16:47 → nessuna ora notturna | € 0,00 |
| Festivo | 15/04 non è festivo | — |
| **TOTALE** | | **€ 80,50** |

> Regola applicata: €75 base (prime 3h) + €15/h per ogni ora oltre le 3h (pro-rata al minuto)

---

## ⚠️ Anomalie Veratour rilevate (21 totali)

### PAX Mancante (6 righe)

| Riga | Data | Apt | Volo | Assistente |
|------|------|-----|------|-----------|
| 4 | 01/04 | BGY | NO3865 | Giorgio Moserle |
| 7 | 02/04 | BGY | NO4254 | Lisa Foresti |
| 55 | 05/04 | NAP | NO7938 | Paolo Imperato |
| 56 | 05/04 | NAP | SM810 | *(anche assistente mancante)* |
| **144** | **15/04** | **VCE** | **W46765** | **Geri Casciello** |
| 152 | 16/04 | VRN | NO4508 | Marcella Rusu |

### Assistente Mancante (16 righe)

| Riga | Data | Apt | Volo |
|------|------|-----|------|
| 34 | 04/04 | BGY | VR631 |
| 38 | 04/04 | VRN | NO6022 |
| 51 | 05/04 | VRN | NO7026 |
| 56 | 05/04 | NAP | SM810 |
| 67 | 06/04 | VRN | NO1350 |
| 80 | 09/04 | VRN | NO4432 |
| 81 | 09/04 | VRN | NO4357 |
| 101 | 11/04 | BGY | VR631 |
| 104 | 11/04 | VRN | NO6022 |
| 119 | 12/04 | VRN | NO7026 |
| 136 | 13/04 | VRN | NO1764 |
| 149 | 16/04 | VRN | NO4357 |
| 150 | 16/04 | VRN | NO4723 |
| 158 | 17/04 | VRN | NO5347 |
| 175 | 18/04 | VRN | NO6022 |
| 295 | 30/04 | VRN | NO4723 |

---

## 🐛 Bug rilevati e corretti in `tour_operators.py`

### Bug 1 — CAPOVERDE TIME non rilevato

**Causa:** Il TO nel file è scritto `CAPOVERDE TIME` → dopo pulizia diventa `"capoverdetime"`.
La cartella si chiama `Caboverdetime` → cleaned = `"caboverdetime"`.
`"caboverdetime"` non è contenuto in `"capoverdetime"` (differenza: **cap** vs **cab**) → cartella non trovata.

**Fix applicato:**
```python
# Aggiunto dizionario alias
_FOLDER_ALIASES: Dict[str, str] = {
    'capoverdetime': 'caboverdetime',
    'capoverde':     'caboverdetime',
}

# find_tour_operator_folder ora usa l'alias risolto
to_clean_resolved = _FOLDER_ALIASES.get(to_clean, to_clean)

# get_tour_operator_module_name: aggiunta condizione
elif 'caboverdetime' in to_clean or 'capoverde' in to_clean:
    return 'caboverdetime'
```

### Bug 2 — MICHELTOUR (senza 's') non rilevato

**Causa:** Nel file è scritto `MICHELTOUR` (senza 's').
Il codice cercava `'micheltours' in to_clean` → `'micheltours' in 'micheltour'` = **False** → modulo non trovato.

**Fix applicato:**
```python
# Prima (bug):
elif 'micheltours' in to_clean or 'michel tours' in to_clean:

# Dopo (fix): 'micheltour' cattura sia MICHELTOUR che MICHELTOURS
elif 'micheltour' in to_clean:
    return 'micheltours'
```

### Risultato dopo i fix

| Tour Operator | Prima | Dopo |
|--------------|-------|------|
| CAPOVERDE TIME | ❌ non elaborato | ✅ elaborato |
| MICHELTOUR | ❌ non elaborato | ✅ elaborato |
| **TO elaborabili** | **7** | **9** |

---

## 🔀 Git

```
Commit: f3373c8
Branch: main
Messaggio: fix: risolti bug rilevamento CAPOVERDE TIME e MICHELTOUR in tour_operators.py
Repository: https://github.com/capmaurizio/veratour-piano-lavoro
Auto-deploy: Streamlit Cloud (ogni push aggiorna automaticamente l'app)
```

---

## 🌐 Link

| Risorsa | URL |
|---------|-----|
| **App online** | https://veratour-piano-lavoro-8ahkfuaued3a59zwb5dwsb.streamlit.app |
| **GitHub** | https://github.com/capmaurizio/veratour-piano-lavoro |
| **Streamlit Cloud dashboard** | https://share.streamlit.io |

**Login app:** Username `silvia` / Password `1`

---

*Generato il 30/04/2026*
