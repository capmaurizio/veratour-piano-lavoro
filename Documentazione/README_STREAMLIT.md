# 🚀 Interfaccia Web Streamlit - Veratour 2025

Interfaccia web user-friendly per il calcolatore Veratour 2025.

## 📋 Requisiti

Installa le dipendenze:

```bash
pip install -r requirements.txt
```

## 🎯 Avvio Applicazione

Per avviare l'interfaccia web:

```bash
streamlit run app_streamlit.py
```

L'applicazione si aprirà automaticamente nel browser all'indirizzo `http://localhost:8501`

## 📖 Come Usare

1. **Carica File Excel**: Clicca su "Browse files" e seleziona il file Excel del piano di lavoro
2. **Configura Opzioni** (opzionale): Usa la sidebar per:
   - Filtrare aeroporti specifici
   - Modificare la modalità notturno
   - Configurare arrotondamenti
   - Caricare un file con lista festivi
3. **Esegui Calcolo**: Clicca sul pulsante "🚀 Esegui Calcolo"
4. **Scarica Risultati**: Dopo il calcolo, clicca su "📥 Scarica File Excel Completo"

## 🎨 Funzionalità

- ✅ Upload file Excel semplice e intuitivo
- ✅ Anteprima risultati in tempo reale
- ✅ Download immediato del file Excel generato
- ✅ Visualizzazione totali per aeroporto
- ✅ Gestione errori con messaggi chiari
- ✅ Interfaccia responsive e moderna

## 🔧 Opzioni Avanzate

### Filtro Aeroporti
Seleziona uno o più aeroporti per limitare il calcolo solo a quelli specificati.

### Modalità Notturno
- **DIFF5**: Maggiorazione differenziale (€5/h = €0.0833/min)
- **FULL30**: Tariffa piena (€30/h = €0.5/min)

### Arrotondamenti
Configura come arrotondare i minuti di Extra e Notturno:
- **NONE**: Nessun arrotondamento
- **FLOOR**: Arrotonda per difetto
- **CEIL**: Arrotonda per eccesso
- **NEAREST**: Arrotonda al più vicino

### File Festivi
Carica un file di testo con una data per riga (formato YYYY-MM-DD) per definire giorni festivi personalizzati.

## 📝 Note

- Il file Excel generato mantiene la stessa struttura del calcolatore da riga di comando
- Tutti i fogli sono inclusi: dettagli per aeroporto, totali, e fogli tecnici
- Le discrepanze vengono evidenziate se presenti

