# Consuntivo Alpitour 2025

Calcolatore automatico per il consuntivo mensile delle assistenze aeroportuali Alpitour secondo le linee guida 2025.

## Cosa fa

Il programma legge il file Excel del piano lavoro (default: `PianoLavoroOTTOBRE 25 .xlsx`), filtra le righe relative ad **Alpitour**, raggruppa i dati per blocchi (DATA + APT + TURNO) e calcola automaticamente:

- **Costo turno** secondo le tariffe Alpitour 2025 (diverse per BGY e VRN)
- **Ore extra** oltre il turno pianificato (ATD/STD + 30 minuti)
- **Notturno** nella fascia 23:00-06:00
- **Festivi** con maggiorazione del 20% su turno e extra

Genera un file Excel di output con:
- **DettaglioBlocchi**: tutti i blocchi calcolati con tutti i dettagli
- **TotaliPeriodo**: riepilogo per periodo (1-15 e 16-31) e totale mensile
- **Discrepanze**: eventuali differenze con valori forniti nel file originale

## Requisiti

```bash
pip install pandas openpyxl python-dateutil
```

## Utilizzo

### Comando base (tutti gli aeroporti)
```bash
python consuntivoalpitour.py -o "OUT_ALPITOUR.xlsx"
```

### Filtro per aeroporto specifico
```bash
python consuntivoalpitour.py -o "OUT_ALPITOUR_BGY.xlsx" --apt BGY
python consuntivoalpitour.py -o "OUT_ALPITOUR_VRN.xlsx" --apt VRN
```

### File di input personalizzato
```bash
python consuntivoalpitour.py -i "altro_file.xlsx" -o "OUT.xlsx"
```

### Opzioni disponibili
- `-i, --input`: File Excel in input (default: `PianoLavoroOTTOBRE 25 .xlsx`)
- `-o, --output`: File Excel in output (obbligatorio)
- `--apt`: Filtro aeroporti (es. `--apt BGY VRN`)
- `--holiday-list`: File con lista festivi personalizzata (una data per riga)

## Regole di calcolo Alpitour 2025

### Tariffe turno

**Bergamo (BGY)**:
- 3 ore: €75,00
- 4 ore: €90,00
- 5 ore: €105,00
- 6 ore: €120,00
- 7 ore: €135,00
- 8 ore: €150,00
- Oltre 3h: +€15,00/ora (pro-rata al minuto)

**Verona (VRN)**:
- 3 ore: €80,00
- 4 ore: €95,00
- 5 ore: €110,00
- 6 ore: €125,00
- 7 ore: €140,00
- 8 ore: €155,00
- Oltre 3h: +€15,00/ora (pro-rata al minuto)

### Ore extra

- **Tariffa**: €20,00/ora
- **Calcolo**: `(ATD + 30 minuti) - fine_turno`
  - Se ATD è **dopo** fine turno: extra = (ATD + 30 min) - fine turno
  - Se ATD è **prima** fine turno: dei 30 minuti post-ATD, solo la parte che va oltre fine turno conta come extra
  - Esempio: ATD 10:24, fine turno 10:25 → 1 min dentro turno, 29 min extra (10:25-10:54)
- Se ATD non disponibile, usa **STD** come fallback
- **Arrotondamento**: **NESSUNO** - si usano i minuti esatti calcolati
- Se nel TURNO compare "NO DEC", le ore extra sono forzate a 0

### Notturno

- **Fascia oraria**: 23:00 - 06:00
- **Calcolo**: Applicato solo ai minuti effettivamente nella fascia notturna (su turno + extra)
- **Arrotondamento**: **NESSUNO** - si usano i minuti esatti calcolati

**Bergamo (BGY)**:
- Base: €75,00 per 3h = €25,00/ora
- Maggiorazione 15%: €25,00/ora × 1.15 = €28,75/ora
- Differenza notturna: €28,75/ora - €25,00/ora = **€3,75/ora = €0,0625/minuto**

**Verona (VRN)**:
- Base: €80,00 per 3h = €26,67/ora
- Maggiorazione 15%: €26,67/ora × 1.15 = €30,67/ora
- Differenza notturna: €30,67/ora - €26,67/ora = **€4,00/ora = €0,0667/minuto**
- **Nessun minimo**: calcolo proporzionale puro

### Festivi

- **Maggiorazione**: +20% su **turno, extra E notturno** (applicato a tutto)
- Festivi italiani 2025 automaticamente riconosciuti:
  - 1 Gennaio, 6 Gennaio, Pasqua, Pasquetta
  - 25 Aprile, 1 Maggio, 2 Giugno
  - 15 Agosto, 1 Novembre, 8 Dicembre, 25 Dicembre, 26 Dicembre

## Struttura file Excel input

Il programma cerca automaticamente queste colonne:
- **data**: Data del servizio
- **tour operator**: Filtra per "alpitour" (case insensitive)
- **apt**: Codice aeroporto (BGY, VRN)
- **turno** o **TURNO ASSISTENTE**: Orario turno (es. "SC1 7:10-11:10", "11:00-16:30")
- **atd**: Orario decollo effettivo (usato per calcolo extra)
- **std**: Orario decollo programmato (fallback se ATD non disponibile)

## Parsing del campo TURNO

Il programma riconosce automaticamente vari formati:
- `SC1 7:10-11:10` → 07:10-11:10
- `SC2: 11-16:30` → 11:00-16:30
- `11.00-16:30` → 11:00-16:30
- `SC1:16-19:30` → 16:00-19:30
- `3-6:30` → 03:00-06:30
- `23:30-02:30` → 23:30-02:30 (giorno successivo)

Ignora prefissi come "SC1", "SC2", "AB" e si concentra solo sulla parte oraria.

## Output

Il file Excel generato contiene:

### Foglio "DettaglioBlocchi"
Ogni riga rappresenta un blocco (DATA + APT + TURNO) con:
- Data, APT, TURNO normalizzato
- Inizio/fine turno, durata
- ATD scelto, minuti extra (raw e arrotondato)
- Minuti notturno (raw e arrotondato)
- Importi: Turno €, Extra €, Notturno €, Totale €
- Flag festivo
- Riferimenti al file/sheet/riga originale

### Foglio "TotaliPeriodo"
Riepilogo per:
- Periodo 1-15
- Periodo 16-31
- Totale MESE

Con colonne: Turno €, Extra (minuti e €), Notturno (minuti e €), Totale €

### Foglio "Discrepanze"
Solo se nel file originale erano presenti valori di:
- Importo
- Ore extra
- Notturno

Mostra i valori calcolati vs forniti e le differenze.

## Esempi di output

### Tabella riassuntiva per aeroporto

```
Aeroporto  Blocchi Assistenze            Extra        Notturno    TOTALE
      BGY       13  1.215,00€ 205,33€ (10,27h) 46,87€ (12,50h) 1.467,20€
      VRN       24  2.478,50€  103,00€ (5,15h) 38,06€ (10,15h) 2.619,56€
   TOTALE       37  3.693,50€ 308,33€ (15,42h) 84,93€ (22,65h) 4.086,76€
```

## Note importanti

1. **Blocchi**: Il programma raggruppa automaticamente le righe con stessa DATA + APT + TURNO in un unico blocco, unendo tutti gli ATD/STD presenti.

2. **Forward-fill TURNO**: Se una riga non ha TURNO ma ha la stessa DATA, viene usato il TURNO della riga precedente (rispettando l'ordine del file).

3. **Arrotondamenti**: 
   - Extra: **NESSUNO** - si usano i minuti esatti calcolati
   - Notturno: **NESSUNO** - si usano i minuti esatti calcolati
   - Importi: arrotondati ai centesimi

4. **Mezzanotte**: I turni che attraversano la mezzanotte (es. 23:30-02:30) sono gestiti automaticamente.

5. **NO DEC**: Se nel TURNO compare "NO DEC", le ore extra sono forzate a 0, ma il notturno dentro il turno viene comunque calcolato.

## File correlati

- `consuntivoalpitour.py`: Script principale
- `2025_12_RegoleAlpitour.txt`: Regole complete Alpitour 2025
- `PianoLavoroOTTOBRE 25 .xlsx`: File di input di default

## Autore

Script sviluppato per SCAY GROUP S.n.c. - Calcolo consuntivo Alpitour 2025

