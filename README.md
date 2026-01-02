# 📊 Calcolo Piano di Lavoro - Sistema Multi-Cliente

Sistema modulare per il calcolo automatico dei consuntivi piano di lavoro per diversi clienti.

## 🏗️ Struttura Progetto

```
CalcoloPianoLavoro/
├── Veratour/              # Calcolatore Veratour 2025
│   ├── app_streamlit.py
│   ├── consuntivoveratour.py
│   ├── requirements.txt
│   ├── documentazione/
│   └── ...
├── Alpitour/             # Calcolatore Alpitour (futuro)
│   └── ...
└── README.md            # Questo file
```

## 🚀 Quick Start

### Veratour 2025
Vai nella cartella `Veratour/` e consulta il README specifico:
- **Interfaccia Web**: https://veratour-piano-lavoro-8ahkfuaued3a59zwb5dwsb.streamlit.app
- **Documentazione**: `Veratour/documentazione/`

```bash
cd Veratour
streamlit run app_streamlit.py
```

## 📋 Clienti Supportati

### ✅ Veratour
- Calcolo turni, extra, notturno, festivi
- Interfaccia web Streamlit
- Export Excel multi-foglio
- **Status**: ✅ Operativo

### 🔜 Alpitour
- **Status**: 🚧 In sviluppo

### 🔜 Altri Clienti
- **Status**: 📋 Pianificato

## 🎯 Obiettivo

Sistema unificato per gestire i calcoli piano di lavoro di diversi clienti, mantenendo logiche specifiche per ciascuno ma condividendo l'infrastruttura comune.

## 📚 Documentazione

Ogni cliente ha la propria documentazione nella cartella `[Cliente]/documentazione/`:
- **Veratour**: `Veratour/documentazione/INDICE.md`

## 🔧 Sviluppo

Per aggiungere un nuovo cliente:
1. Crea la cartella `[NomeCliente]/`
2. Copia la struttura base da un cliente esistente
3. Adatta la logica di calcolo alle specifiche del cliente
4. Aggiungi la documentazione

---

**Ultimo aggiornamento**: Gennaio 2025
