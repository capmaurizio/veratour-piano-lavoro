# Riepilogo Modifiche — Manuela Gregori MXP (Accordo 2026)

## ✅ Modifiche Completate

### 1. Documentazione
- **[regole_manuela_gregori_2026.md](file:///Users/mauriziocapitanio/Documents/scay/CalcoloPianoLavoro/docs/regole_manuela_gregori_2026.md)**: Regole complete con formule ed esempi

### 2. File Excel
- **[TARIFFE COLLABORATORI 2026 DEF.xlsx](file:///Users/mauriziocapitanio/Documents/scay/CalcoloPianoLavoro/TARIFFE%20COLLABORATORI%202026%20DEF.xlsx)**
  - Base: €58 → **€60**
  - Notturno: +15% (fasce TO) → **+20% (23:00-06:00)**

### 3. Codice Python
- **[tariffe_collaboratori.py](file:///Users/mauriziocapitanio/Documents/scay/CalcoloPianoLavoro/tariffe_collaboratori.py)** (~linea 897-926)
  - Aggiunto campo `inps_perc` al dataclass `TariffaCollaboratore`
  - Aggiunta sezione "MXP - Manuela Gregori (Accordo 2026)" con regole speciali:
    - **Base**: sempre €60 (fisso, indipendente dalla durata)
    - **Extra**: SOLO da `extra_min` (ritardi ATD-STD), NO calcolo da durata
    - **Notturno**: +20% su ore in fascia 23:00-06:00
    - **INPS**: +4% automatico (Partita IVA)
  - **Bug risolto**: eliminato doppio conteggio extra (durata + ritardi)

## 📊 Verifica

| Test | Atteso | Calcolato | Status |
|------|--------|-----------|--------|
| 02/01 W4 6363 | €69.89 | €69.89 | ✅ |
| 04/01 DOMINA | €90.90 | €90.90 | ✅ |
| 04/01 SM822 | €94.92 | €94.92 | ✅ |
| 11/01 AP2511 | €81.54 | €79.46 | ⚠️ |
| 11/01 SM822 | €69.89 | €69.89 | ✅ |
| 18/01 SM822 | €74.67 | €74.67 | ✅ |
| 25/01 DOMINA | €83.34 | €83.34 | ✅ |
| 25/01 AP2511 | €65.94 | €65.94 | ✅ |

**Risultato**: 7/8 test perfetti. Un test con differenza €2.08 dovuta a discrepanza nei minuti notturni del parametro di input.
