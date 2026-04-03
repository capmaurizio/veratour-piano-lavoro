import streamlit as st
import pandas as pd
from tariffe_collaboratori import get_tariffe_manager

def get_assigned_rule(apt: str, name: str, categoria: str) -> str:
    """Ritorna una stringa human-readable che descrive la regola applicata."""
    apt_upper = str(apt).upper().strip()
    name_norm = str(name).lower().strip()
    categoria_str = str(categoria).upper().strip() if pd.notna(categoria) else ''
    
    if apt_upper == 'BGY':
        if 'filippo' in name_norm and 'bonfanti' in name_norm:
            return "BGY Senior (Forfait 30€/3h, Extra 10€/h, Festivo 50€/3h, Notturno +15%)"
        if 'senior' in categoria_str:
            return "BGY Senior (Forfait 30€/3h, Extra 10€/h, Festivo 50€/3h, Notturno +15%)"
        return "BGY Junior (Forfait 24€/3h, Extra 8€/h, Festivo 40€/3h, Notturno +15%)"
        
    elif apt_upper == 'MXP':
        if 'manuela' in name_norm and 'gregori' in name_norm:
            return "MXP Eccezione (Base fissa 60€, Extra solo ATD 12€/h, Notturno +20%, Festivo +20%, INPS +4%)"
        if 'martina' in name_norm and 'nettis' in name_norm:
            return "MXP Eccezione (Equiparata a BGY Junior: Forfait 24€/3h, Extra 8€/h)"
        return "MXP Standard Generico (Da verificare)"
        
    elif apt_upper == 'NAP':
        if any(n in name_norm for n in ['rita', 'sara', 'camilla']):
            return "NAP Junior (Forfait 50€/3h lordi, Extra 10€/h lordi, no doppio extra, Notturno +15%)"
        return "NAP Senior/Standard (Forfait 56€/3h lordi, Extra 12€/h lordi, Notturno +15%)"
        
    elif apt_upper == 'VRN':
        return "VRN a Scalini (Junior 50€/3h o Senior 58€/3h, scalini da +12€/ora, Notturno +15%)"
        
    elif apt_upper == 'FCO':
        return "FCO Standard (Forfait 56€/2h30, Extra 12€/h, Notturno Split +20% 23:00-06:00)"
        
    elif apt_upper in ['CTA', 'TRN', 'PMO', 'PSA']:
        return f"{apt_upper} Standard (Base 60€/3h, Extra 12€/h, Notturno +15%, Festivo +20%)"
        
    elif apt_upper in ['BRI', 'BLQ']:
        return f"{apt_upper} Standard (Base 53€/3h, Extra 12€/h, Notturno +15%, Festivo +20%)"
        
    return "Standard/Generico (Regola base letta da foglio Excel principale)"


def render_regolamento_page():
    st.title("Regolamenti Operativi e Tariffe")
    st.markdown("Consulta l'elenco degli assistenti e le relative regole di calcolo impostate in sistema.")
    
    tab_collaboratori, tab_dettagli = st.tabs(["Elenco Collaboratori", "Dettaglio Regole per Aeroporto"])
    
    with tab_collaboratori:
        st.subheader("Elenco Collaboratori e Regole Assegnate")
        st.markdown("Questa tabella carica tutti i collaboratori iscritti su file Excel `tariffe_collaboratori.xlsx` e indica quale logica tariffaria applicherà automaticamente il simulatore secondo le regole impostate ad Aprile 2026.")
        
        # Recupera la lista dal manager singleton
        tm = get_tariffe_manager()
        all_collabs = sorted(tm.tariffe.values(), key=lambda x: (x.aeroporto, x.nome))
        
        data = []
        for c in all_collabs:
            rule_desc = get_assigned_rule(c.aeroporto, c.nome, c.categoria)
            data.append({
                "Aeroporto": c.aeroporto.upper(),
                "Collaboratore": c.nome,
                "Categoria Config.": str(c.categoria) if pd.notna(c.categoria) else "-",
                "Regime Config.": str(c.regime) if pd.notna(c.regime) else "-",
                "Logica Assegnata nel Calcolatore": rule_desc
            })
            
        if data:
            df = pd.DataFrame(data)
            
            # Utilizza column_config per allargare al massimo la visualizzazione 
            # e permettere la lettura dell'intera regola.
            st.dataframe(
                df, 
                use_container_width=True, 
                hide_index=True,
                column_config={
                    "Logica Assegnata nel Calcolatore": st.column_config.TextColumn(
                        "Logica Assegnata",
                        width="large",
                    ),
                    "Aeroporto": st.column_config.TextColumn("APT", width="small")
                }
            )
            
            st.info(f"Totale collaboratori censiti a sistema: **{len(data)}**")
        else:
            st.warning("Impossibile caricare l'elenco collaboratori. Assicurarsi che `tariffe_collaboratori.xlsx` sia presente.")

    with tab_dettagli:
        st.subheader("Bergamo (BGY)")
        st.markdown("""
        **Regole BGY 2026 (Forfait già Netti – non subiscono decurtazione)**
        * **Turno Base:** 3 ore.
        * **Junior:** € 24,00 netti forfait (pari a 8€/ora).
        * **Senior (Filippo Bonfanti):** € 30,00 netti forfait (pari a 10€/ora).
        * **Ore Extra:** Pagate a rateo netto sui minuti effettivi (€ 8/h per Junior, € 10/h per Senior).
        * **Maggiorazione Notturna (+15%):** Riconosciuta tra le **23:00 e le 05:00**, distribuita in bolletta anche sulle ore extra maturanti nella notte.
        * **Festività:** Nel giorno festivo lo stipendio base sale a € 40 netti (Junior) o € 50 netti (Senior). Inoltre il valore di ogni minuto extra lavorato subisce un rincaro del **+20%**.
        * **SAND:** Per voli SAND non maturano ore extra sui ritardi.
        
        > **💡 Junior (Feriale)**: Turno durata 4 ore (dalle 20:00 alle 24:00).
        > * Base 3h: **€ 24,00** | Extra 1h: **€ 8,00** | Notte (1h post-23:00): +15% su 8€ = **€ 1,20** | **Totale: € 33,20 netto**
        >
        > **💡 Junior (Festivo)**: Stesso turno di 4 ore ma in giorno Festivo rosso sul calendario.
        > * Base 3h: sale a **€ 40,00** | Extra 1h: **€ 9,60** (+20%) | Notte (1h post-23:00 su 9.60€): **€ 1,44** | **Totale: € 51,04 netto**
        >
        > **💡 Senior (Feriale)**: Filippo Bonfanti, 4 ore (dalle 20:00 alle 24:00).
        > * Base 3h: **€ 30,00** | Extra 1h: **€ 10,00** | Notte (1h post-23:00): +15% su 10€ = **€ 1,50** | **Totale: € 41,50 netto**
        >
        > **💡 Senior (Festivo)**: Filippo Bonfanti, 4 ore in Festivo.
        > * Base 3h: sale a **€ 50,00** | Extra 1h: **€ 12,00** (+20%) | Notte: ristima proporzionale **€ 1,80** | **Totale: € 63,80 netto**
        """)
        
        with st.expander("🍎 Spiegazione Semplice (per i non addetti ai lavori)"):
            st.markdown("""
            Immagina di andare dal fruttivendolo e comprare un cesto con **3 mele** assicurate. 
            A Bergamo il cesto lo paghi pulito **24 €** (quindi **8 € a mela**). Questa è la base "Junior". Filippo invece ha le mele più grandi (Senior) e il cesto gli costa **30 €** (quindi **10 € a mela**).
            Se compri mele fuori dal cesto base (le famose "ore extra"), il fruttivendolo te le mette nel sacchetto rispettivamente a 8 € o a 10 € l'una.
            *Cosa succede di Domenica?* Il fruttivendolo sa che c'è meno gente e per tenere aperto ti fa pagare il cestino base **40 €** (invece di 24), e ogni mela singola oltre le prime tre te la fa pagare il 20% in più.
            """)
        
        st.divider()
        
        st.subheader("Malpensa (MXP)")
        st.markdown("""
        * **Eccezione Manuela Gregori:** Base fissa a corpo intero di **60€** a chiamata. Nessun extra per orario protratto prima del decollo; gli extra maturano **esclusivamente** sul reale "Ritardo ATD" pagati a **€ 12,00/h**. Notturno +20%, applicato anche in festività il +20%, calcolo addizionale Cassa INPS del **+4%**.
        * **Eccezione Martina Nettis:** Identificata a codice come *equiparata alla base Junior Bergamo* (24€ forfait, extra 8€/h, festivo +20%, Notturno +15%).
        
        > **💡 Manuela Eccezione (Feriale con Ritardo)**: Turno diurno feriale, si protrae poi subisce un Ritardo ATD di 1 ora.
        > * Base: **€ 60,00** | Extra ATD 1h: **€ 12,00** | Subtotale 72,00 | + 4% INPS (**€ 2,88**) | **Totale: € 74,88 lordo**
        >
        > **💡 Manuela Eccezione (Festivo Standard)**: Turno senza ritardo, diurno ma scatta la festività.
        > * Base: **€ 60,00** (+20% festivo globale sulle basi) = **€ 72,00** | + 4% INPS (**€ 2,88**) | **Totale: € 74,88 lordo**
        """)
        
        with st.expander("🍎 Spiegazione Semplice (per i non addetti ai lavori)"):
            st.markdown("""
            A Malpensa Manuela ha una specie di "abbonamento Premium". Il suo distributore costa fisso **60 €**, indipendentemente da quante mele ci siano dentro. Non importa se aspetta per ore. 
            Viene pagata un extra solo se succede un imprevisto gravissimo certificato all'ultimo minuto ("il Ritardo ATD"), per cui riceve 12€ addizionali. Sopra a qualsiasi spesa batte sullo scontrino, il governo le aggiunge sempre il 4% di previdenza (INPS) e lei incassa l'importo tutto lordo, mettendosi le tasse in tasca da gestirsi poi da sola (Partita IVA).
            """)
        
        st.divider()
        
        st.subheader("Napoli (NAP)")
        st.markdown("""
        * **Turno Base:** 3 ore per voli Standard. (2h30 per specifici altri pacchetti su cui matura la sesta mezz'ora in extra).
        * **Junior (es. Rita, Sara, Camilla):** Forfait contrattuale di **50€ lordi** in ritenuta d'acconto (equivalenti a circa 40€ netti). Le ore extra salgono a **€ 10,00 lorde**. Non matura doppio rimborso ritardo ATD. Notturno +15%.
        * **Senior (Standard):** Forfait di **56€ lordi** (equivalenti calcolati base 44,80 netti), extra € 12,00 lordi/h.
        * L'esportazione excel decurta il 20% ove previsto il regime di Ritenuta/Acconto e scompone i minuti extra su formula fissa per singolo assistente.
        * **Festivi:** In caso di festivo l'intero lordo maturato è maggiorato in automatico del **+20%**.
        
        > **💡 NAP Junior (Feriale)**: Rita turno Standard di 4 ore diurno (Ritenuta 20%).
        > * Base 3h: **€ 50,00 lordi** | Extra 1h: **€ 10,00 lordi** | Subtotale **60€ lordi** | Simulato al netto **(-20%) = € 48,00 netti**.
        > 
        > **💡 NAP Junior (Festivo)**: Rita turno Standard in giornata festiva rosa sul calendario.
        > * Subtotale base 60€ riceve subito il **+20%** festività diventando **€ 72,00 lordi**. | Simulato netto **(-20%) = € 57,60 netti**.
        >
        > **💡 NAP Senior (Feriale)**: Giorno feriale 4 ore diurne per tariffa base.
        > * Base 3h: **€ 56,00 lordi** | Extra 1h: **€ 12,00 lordi** | Subtotale **68€ lordi** | Simulato netto **(-20%) = € 54,40 netti**.
        """)
        
        with st.expander("🍎 Spiegazione Semplice (per i non addetti ai lavori)"):
            st.markdown("""
            A Napoli il fruttivendolo vende la sua cesta di mele per **50 €**. Il problema è che all'uscita dal negozio passa sempre l'esattore delle tasse che trattiene brutalmente 1/5 della spesa (il **20% di ritenuta**). Quindi te ne torni a casa con solo **40 € netti** in tasca. Inoltre, se decidi di comprare le mele nel giorno di Natale (Festivo), il cartellino sul prezzo indica subito un +20% di partenza.
            """)
        
        st.divider()

        st.subheader("Verona (VRN)")
        st.markdown("""
        * **Logica a Scalini (Pacchetti):** A Verona il compenso non matura a minuti, ma a ore intere assegnate.
        * **Pacchetto Junior:** Base 3 ore = **€ 50,00 lorde**. Ogni ora successiva programmata o maturata costa +€ 12,00 (es: 4h=62€, 5h=74€... fino a 8h=110€).
        * **Pacchetto Senior:** Base 3 ore = **€ 58,00 lorde**. Ogni ora successiva programmata o maturata costa +€ 12,00 (es: 4h=70€, 5h=82€... fino a 8h=118€).
        * **Transfer:** Forfait € 45,00 lorde per 2 ore (Junior), extra € 12/h. 
        * **Notturno:** Maggiorazione parziale del **+15%** proporzionale alle ore di notte.
        * **Festivi:** In caso di giorno festivo l'intero lordo subisce in pieno il rincaro **+20%**.
        
        > **💡 Turno VRN Junior (Feriale)**: Turno durato 4 ore e 15 minuti.
        > * Il sistema arrotonda al pacchetto delle 4 ore + extra. Pacchetto 4h = **€ 62,00 lorde**. I 15 minuti extra causano un'ulteriore frazione a 12€/h (**€ 3,00**). Totale **65,00€ lordi**.
        >
        > **💡 Turno VRN Senior (Festivo)**: Turno di 5 ore esatte.
        > * Pacchetto Senior 5 ore = **€ 82,00 lorde**. Giorno festivo: **+20%** (= € 16,40). Totale **98,40€ lordi**.
        """)
        
        with st.expander("🍎 Spiegazione Semplice (per i non addetti ai lavori)"):
            st.markdown("""
            A Verona il fruttivendolo ha preparato dei **cestini a grandezza fissa (da 3, 4, 5 o 6 ore)**.
            Se sei Junior il cestino base costa 50 €, e ogni volta che vuoi una scatola più grande ci aggiunge sempre 12 €. (4 fette=62€, 5 fette=74€...). Se sei Senior il cesto base parte più caro (58 €) e cresce sempre di 12 €. 
            E se il tuo turno finisce a "metà" tra una scatola e l'altra? Il sistema ti fa pagare la grandezza della scatola intera più vicina che hai superato, più le briciole che hai fatto rimborsandole a peso (12€ al kg). Di Domenica, tutto il negozio rincara le etichette del 20%.
            """)
        
        st.divider()

        st.subheader("Roma (FCO)")
        st.markdown("""
        * **Turno base (Forfait):** Euro **56,00 lorde** per 2 ore e 30 minuti (2h30). L'equivalente orario è 22,40 €/h.
        * **Extra:** Rateo effettivo **€ 12,00 lordi/h**. Il tempo successivo alle 2h30 è matematicamente considerato ora extra.
        * **Maggiorazione Notturna (Regola B):** Scatta al +20% (fascia 23:00-06:00 / SAND 23:00-03:30). La piattaforma calcola separatamente:
            * Sulle ore notturne svolte *dentro le 2h30 di base*, paga +4,48 €/h di maggiorazione (22,40 x 20%).
            * Sulle ore notturne svolte *negli extra*, paga +2,40 €/h (12,00 x 20%) da sommarsi ai 12 € che riceve già come extra diurno.
        
        > **💡 Turno FCO Pratico**: Caso Baobab / TH (03:10 - 06:33).
        > * Turno base 2h30 forfait -> **€ 56,00**
        > * Extra 53/60 min (dalle 05:40 alle 06:33) x 12,00 -> **€ 10,60**
        > * Maggiorazione Notturna (su 2h30 forfait piene in notturna) x 4,48 -> **€ 11,20**
        > * Magg. Extra Notturni (20/60 min da 5:40 a 6:00) x 2,40 -> **€ 0,80**
        > * **Totale complessivo:** 56,00 + 10,60 + 11,20 + 0,80 = **€ 78,60 lordi**.
        """)
        
        with st.expander("🍎 Spiegazione Semplice (per i non addetti ai lavori)"):
            st.markdown("""
            A Fiumicino, il cesto piccolo del fruttivendolo ha **2,5 mele** in totale e ti costa fisso **56 €**.
            E se vuoi comprare mele in abbondanza? Nessun problema, ogni mela sfusa in più te la vende a **12 €**. 
            Essendo aeroporto, lui vende anche di notte (dalle 23:00 alle 06:00): ma di notte è costretto a mettere un rincaro del 20% *solo sulle frazioni in cui acquisti col buio*. Se compravi il cesto fisso di notte paghi la tassa sulla base (+4,48 a mela), se aggiungevi mele sfuse di notte paghi la tassa sugli extra sfusi (+2,40 a mela). Tutto viene spezzato al centesimo minuto dal simulatore per non confondersi!
            """)
        
        st.divider()

        st.subheader("Catania (CTA) / Torino (TRN) / Palermo (PMO) / Pisa (PSA)")
        st.markdown("""
        * **Turno base:** Forfait di 3 ore valutate **€ 60,00 lorde**.
        * **Extra:** Valutati sugli sforamenti o ritardi a **€ 12,00 lordi/h**.
        * **Notturno:** Riconosciuto applicando **+15%** sull'equivalente orario.
        * **Festività:** Nel giorno festivo lo stipendio base e gli extra maturati ricevono una maggiorazione fissa a corpo del **+20%**.
        
        > **💡 Esempio di calcolo**: Turno diurno ferale di 4 ore.
        > * Base 3h: **€ 60,00**
        > * Extra 1h: **€ 12,00**.
        > * **Totale: € 72,00 lordi**.
        """)
        
        with st.expander("🍎 Spiegazione Semplice (per i non addetti ai lavori)"):
            st.markdown("""
            Nelle isole e in alcune città (Catania, Palermo, Torino, Pisa) il fruttivendolo vende la solita cesta da 3 mele, ma la fa pagare un po' di più: **60 €** in totale. 
            Se però decidi di comprare una mela in più (o se il corriere tarda ad arrivare), te la vende sempre allo stesso prezzo nazionale degli sciolti: **12 € a mela**. C'è la classica tassa del 15% in più se compri di notte, e nelle feste il conto alla cassa lievita sempre del 20%.
            """)
        
        st.divider()

        st.subheader("Bari (BRI) / Bologna (BLQ)")
        st.markdown("""
        * **Turno base:** Forfait di 3 ore valutate **€ 53,00 lorde**.
        * **Extra:** Valutati a **€ 12,00 lordi/h**.
        * **Notturno e Festivo:** Stesse regole tariffarie della fascia CTA (+15% notte, +20% nei giorni rossi).
        
        > **💡 Esempio di calcolo**: Turno diurno feriale di 3h e 30 minuti.
        > * Base 3h: **€ 53,00**
        > * Extra 30m: **€ 6,00** (rateo sui minuti effettivi).
        > * **Totale: € 59,00 lordi**.
        """)
        
        with st.expander("🍎 Spiegazione Semplice (per i non addetti ai lavori)"):
            st.markdown("""
            A Bari e Bologna il fruttivendolo è un filo più economico: ti vende la cesta da 3 mele a soli **53 €**. 
            Ma attenzione! Come tutti gli altri, quando chiedi un "extra" o hai un ritardo, ti fa pagare la tariffa nazionale fissa per lo sfuso (cioè **12 € per ogni mela singola** in più). Regole solite per notturno e feste: +15% per il buio e +20% a Natale o Pasqua.
            """)

        st.divider()

        st.subheader("Venezia (VCE) / Treviso (TSF) / Altri (es. CAG)")
        st.markdown("""
        * **Turno base:** Valore di riferimento del listino impostato a **€ 58,00 lorde** per 3 ore.
        * **Extra:** Valutati sugli sforamenti o ritardi a **€ 12,00 lordi/h**.
        * **Notturno e Festivo:** Si applicano le consuete regole di maggiorazione generale: +15% per le ore notturne, e maggiorazione fissa a corpo del **+20%** nei giorni festivi.
        * Le logiche specifiche di questi aeroporti sono comunque modulabili dinamicamente depositando configurazioni contrattuali personali in \`tariffe_collaboratori.xlsx\` (Foglio Regole/Collaboratori).
        
        > **💡 Esempio VCE (Feriale)**: Turno diurno feriale di 4 ore.
        > * Base 3h: **€ 58,00**
        > * Extra 1h: **€ 12,00**
        > * **Totale: € 70,00 lordi**.
        """)
        
        with st.expander("🍎 Spiegazione Semplice (per i non addetti ai lavori)"):
            st.markdown("""
            A Venezia (o negli altri aeroporti non citati sopra) si usa il "listino prezzi standard" nazionale di SCAY. 
            Il fruttivendolo ha una normalissima cesta di 3 mele a **58 €**. Se gli chiedi un'altra mela, l'aggiunge al conto per 12 €. Niente blocchi obbligatori enormi o regole strane. C'è solo il rincaro notturno standard del 15% sul buio, o il 20% aggiuntivo se è il giorno di Natale!
            """)


