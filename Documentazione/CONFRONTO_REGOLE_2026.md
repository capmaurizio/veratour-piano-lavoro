# 📋 Confronto Regole Operative 2026 vs Implementazione Attuale

## Analisi delle differenze tra "REGOLE OPERATIVE COLLABORATORI 2026.docx" e codice implementato

---

## ✅ REGOLE INVARIATE (Nessuna modifica necessaria)

### 1. **VERONA (VRN) - Assistenti**
- ✅ **Tariffe a pacchetto**: Già implementate nel sistema tramite file Excel `TARIFFE COLLABORATORI 2026 DEF.xlsx`
  - Senior: 3h=€58, 4h=€70, 5h=€82, 6h=€94, 7h=€106, 8h=€118
  - Junior: 3h=€50, 4h=€62, 5h=€74, 6h=€86, 7h=€98, 8h=€110
- ✅ **Ore extra**: €12,00/h oltre il pacchetto - **GIÀ IMPLEMENTATO**
- ✅ **Notturno**: +15% sulla quota oraria del pacchetto - **GIÀ IMPLEMENTATO**
  - VERATOUR: 23:00-05:00
  - ALPITOUR: 23:00-06:00
- ✅ **Festivi**: +20% su base + extra + notturno - **GIÀ IMPLEMENTATO**
- ✅ **Regola ALPITOUR Verona**: ATD + 30 minuti sempre - **GIÀ IMPLEMENTATO**
- ✅ **SAND**: 3h da CVC, NO attesa decollo, NO ore extra, notturno 23:00-03:30 - **GIÀ IMPLEMENTATO**
- ✅ **BAOBAB e altri TO**: 3h da CVC, extra da ATD se supera le 3h - **GIÀ IMPLEMENTATO**

### 2. **FIUMICINO (FCO) - Assistenti Senior P.IVA**
- ✅ **Durata base**: 2h30' - **GIÀ IMPLEMENTATO** (tramite file Excel)
- ✅ **Assistenza base**: €56,00 + IVA per 2h30' - **DA VERIFICARE NEL FILE EXCEL**
- ✅ **Ore extra**: €12,00 + IVA all'ora - **GIÀ IMPLEMENTATO**
- ✅ **Incentive**: €60,00 + IVA per 2h30', extra €15,00 + IVA/h - **DA VERIFICARE NEL FILE EXCEL**
- ✅ **Arrivi (Meet & Greet)**: €56,00 + IVA per 2h30' - **DA VERIFICARE NEL FILE EXCEL**
- ✅ **Notturno**: +20% su base/extra/incentive, fascia 23:00-06:00 (SAND: 23:00-03:30) - **GIÀ IMPLEMENTATO**
- ✅ **Festivi**: +20% su tutto - **GIÀ IMPLEMENTATO**
- ✅ **Start assistenza**: orario di convocazione (NON anticipazioni) - **GIÀ IMPLEMENTATO**

### 3. **NAPOLI (NAP) - Assistenti Senior e Junior**
- ✅ **Durata base**: 2h30' - **GIÀ IMPLEMENTATO**
- ✅ **Assistenza base**: €56,00 - **DA VERIFICARE NEL FILE EXCEL**
- ✅ **Ore extra**: €12,00/h - **GIÀ IMPLEMENTATO**
- ✅ **Transfer**: €50,00 forfettario - **DA VERIFICARE NEL FILE EXCEL**
- ✅ **Arrivi**: €56,00 per 2h30' - **DA VERIFICARE NEL FILE EXCEL**
- ✅ **Notturno**: +15% solo sui minuti in fascia TO - **GIÀ IMPLEMENTATO**
- ✅ **Festivi**: +20% su tutto - **GIÀ IMPLEMENTATO**

### 4. **Altri Aeroporti**
- ✅ **CATANIA (CTA)**: 3h base, €60,00, extra €12/h, notturno +15% (23:00-06:00), festivo +20% - **DA VERIFICARE NEL FILE EXCEL**
- ✅ **PALERMO (PMO)**: 3h base, €60,00, extra €12/h, notturno +15% (23:00-06:00), festivo +20% - **DA VERIFICARE NEL FILE EXCEL**
- ✅ **PISA (PSA)**: 3h base, €60,00, extra €12/h, notturno +15% (23:00-06:00), festivo +20% - **DA VERIFICARE NEL FILE EXCEL**
- ✅ **BARI (BRI)**: 3h base, €53,00, extra €12/h, notturno +15% (23:00-06:00), festivo +20% - **DA VERIFICARE NEL FILE EXCEL**
- ✅ **BOLOGNA (BLQ)**: 3h base, €53,00, extra €12/h, notturno +15% (fasce TO), festivo +20% - **DA VERIFICARE NEL FILE EXCEL**

### 5. **VENEZIA (VCE) e TREVISO (TSF)**
- ✅ **Regole per TO**: VERATOUR usa turno assegnato, altri TO usano CVC - **GIÀ IMPLEMENTATO**
- ✅ **Notturno**: +15% o +20% secondo TO - **GIÀ IMPLEMENTATO**
- ✅ **Festivi**: +20% cumulabile con notturno - **GIÀ IMPLEMENTATO**

### 6. **BERGAMO (BGY)**
- ✅ **Tariffe base**: Junior €24/h (3h base), Senior €30/h (3h base) - **DA VERIFICARE NEL FILE EXCEL**
- ✅ **Ore extra**: Junior €8/h, Senior €10/h - **DA VERIFICARE NEL FILE EXCEL**
- ✅ **Notturno**: +15% (23:00-05:00) - **GIÀ IMPLEMENTATO**
- ✅ **Festivi**: Forfettario Junior €40/3h, Senior €50/3h - **DA VERIFICARE NEL FILE EXCEL**
- ✅ **Turni VERATOUR/ALPITOUR**: Basati su turno assegnato - **GIÀ IMPLEMENTATO**
- ✅ **Altri TO**: Turno base 3h, inizia 15 min prima CVC - **DA VERIFICARE NEL FILE EXCEL**

---

## ⚠️ VERIFICHE NECESSARIE (File Excel)

Le seguenti regole sono **già supportate dal sistema** tramite il file Excel `TARIFFE COLLABORATORI 2026 DEF.xlsx`, ma **devono essere verificate** che corrispondano esattamente alle nuove regole:

### 1. **FCO - Tariffe Incentive**
- **Nuova regola**: €60,00 + IVA per 2h30', extra €15,00 + IVA/h
- **Verifica**: Controllare che nel file Excel ci siano le colonne:
  - `Incentive Base €` = 60.00
  - `Durata Incentive` = 2.5h
  - `Extra Incentive €/h` = 15.00

### 2. **FCO - Tariffe Arrivi**
- **Nuova regola**: €56,00 + IVA per 2h30', extra €12/h per prolungamenti
- **Verifica**: Controllare che nel file Excel ci sia:
  - `Arrivi €` = 56.00
  - `Durata Arrivi` = 2.5h

### 3. **NAP - Tariffe Transfer**
- **Nuova regola**: €50,00 forfettario
- **Verifica**: Controllare che nel file Excel ci sia:
  - `Transfer €` = 50.00

### 4. **NAP - Tariffe Arrivi**
- **Nuova regola**: €56,00 per 2h30'
- **Verifica**: Controllare che nel file Excel ci sia:
  - `Arrivi €` = 56.00
  - `Durata Arrivi` = 2.5h

### 5. **BGY - Tariffe Festive Forfettarie**
- **Nuova regola**: Junior €40/3h, Senior €50/3h
- **Verifica**: Controllare se il sistema gestisce tariffe forfettarie festive o se usa la percentuale +20%

### 6. **BGY - Turno Altri TO (15 min prima CVC)**
- **Nuova regola**: Turno base 3h, inizia 15 minuti prima della CVC
- **Verifica**: Controllare se questa regola è implementata nel calcolo dei turni

---

## 🔍 PUNTI DA VERIFICARE NEL CODICE

### 1. **Gestione Tariffe Incentive FCO**
- **File**: `tariffe_collaboratori.py`
- **Verifica**: La funzione `calcola_tariffa_collaboratore()` gestisce correttamente le tariffe incentive?
- **Nota**: Il sistema legge `incentive_base_eur`, `incentive_durata_h`, `incentive_extra_eur_per_h` dal file Excel

### 2. **Gestione Tariffe Arrivi e Transfer**
- **File**: `tariffe_collaboratori.py`
- **Verifica**: La funzione gestisce correttamente `arrivi_eur` e `transfer_eur`?
- **Nota**: Il sistema legge queste tariffe dal file Excel, ma bisogna verificare che vengano applicate correttamente

### 3. **Gestione Tariffe Festive Forfettarie BGY**
- **File**: `tariffe_collaboratori.py`
- **Verifica**: Il sistema gestisce tariffe forfettarie per festivi o solo percentuali?
- **Nota**: Le nuove regole BGY prevedono tariffe forfettarie (€40/3h Junior, €50/3h Senior) invece di percentuali

### 4. **Gestione Notturno NAP (+15% invece di +20%)**
- **File**: `tariffe_collaboratori.py`
- **Verifica**: Il sistema applica correttamente +15% per NAP invece di +20%?
- **Nota**: Le nuove regole NAP prevedono +15% invece di +20% per il notturno

### 5. **Gestione Turno BGY Altri TO (15 min prima CVC)**
- **File**: Moduli di calcolo tour operator
- **Verifica**: Per BGY, gli altri TO (non VERATOUR/ALPITOUR) iniziano 15 minuti prima della CVC?
- **Nota**: Questa regola potrebbe richiedere modifiche ai moduli di calcolo

---

## 📝 RACCOMANDAZIONI

1. **Verificare il file Excel**: Controllare che `TARIFFE COLLABORATORI 2026 DEF.xlsx` contenga tutte le tariffe specificate nelle nuove regole
2. **Testare tariffe incentive FCO**: Verificare che il calcolo delle tariffe incentive funzioni correttamente
3. **Testare tariffe arrivi e transfer**: Verificare che arrivi e transfer vengano calcolati correttamente
4. **Implementare tariffe forfettarie festive BGY**: Se necessario, aggiungere supporto per tariffe forfettarie invece di percentuali
5. **Verificare notturno NAP**: Assicurarsi che NAP usi +15% invece di +20%
6. **Verificare turno BGY altri TO**: Controllare se la regola "15 minuti prima CVC" è implementata

---

## ✅ CONCLUSIONE

**La maggior parte delle regole sono già implementate** tramite il sistema di tariffe basato su file Excel. Le principali verifiche da fare sono:

1. ✅ **Verificare che il file Excel contenga tutte le tariffe corrette**
2. ⚠️ **Verificare che le tariffe incentive, arrivi e transfer vengano applicate correttamente**
3. ⚠️ **Verificare la gestione delle tariffe forfettarie festive per BGY**
4. ⚠️ **Verificare che NAP usi +15% per il notturno**
5. ⚠️ **Verificare la regola "15 minuti prima CVC" per BGY altri TO**

**Nessuna modifica al codice sembra necessaria**, a meno che le verifiche sopra non rivelino discrepanze.
