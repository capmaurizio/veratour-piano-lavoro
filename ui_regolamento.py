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
        return "VRN Standard (Logica blocchi forfettari completi 56€, Extra arrotondato 3h, Notte fissa +11.20€)"
        
    elif apt_upper == 'FCO':
        return "FCO Standard (Base 53.6€/2.5h, Extra 9.5€/h, Incentive 70€/2.5h, Notturno Split 22:00-06:00)"
        
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
        
        > **💡 Esempio di calcolo Junior**: Turno feriale durata 4 ore (dalle 20:00 alle 24:00).
        > * Base 3h: **€ 24,00**
        > * Extra 1h: **€ 8,00**
        > * Notturno (1 ora post-23:00): +15% su 8€ rateo h = **€ 1,20**
        > * **Totale: € 33,20 netto forfait**
        """)
        
        st.divider()
        
        st.subheader("Malpensa (MXP)")
        st.markdown("""
        * **Eccezione Manuela Gregori:** Base fissa a corpo intero di **60€** a chiamata. Nessun extra per orario protratto prima del decollo; gli extra maturano **esclusivamente** sul reale "Ritardo ATD" pagati a **€ 12,00/h**. Notturno +20%, applicato anche in festività il +20%, calcolo addizionale Cassa INPS del **+4%**.
        * **Eccezione Martina Nettis:** Identificata a codice come *equiparata alla base Junior Bergamo* (24€ forfait, extra 8€/h, festivo +20%, Notturno +15%).
        
        > **💡 Esempio di calcolo (Manuela)**: Turno durato molto a lungo pre-partenza, poi ritardo ATD di 1 ora. Feriale diurno.
        > * Base fissa: **€ 60,00** (nessun extra per la normale durata estesa del turno)
        > * Ritardo ATD 1h: **€ 12,00**
        > * INPS +4%: calcolata sul subtotale generato (72 * 4%) = **€ 2,88**
        > * **Totale: € 74,88 lorde (P.IVA, no ritenuta)**
        """)
        
        st.divider()
        
        st.subheader("Napoli (NAP)")
        st.markdown("""
        * **Turno Base:** 3 ore per voli Standard. (2h30 per specifici altri pacchetti su cui matura la sesta mezz'ora in extra).
        * **Junior (es. Rita, Sara, Camilla):** Forfait contrattuale di **50€ lordi** in ritenuta d'acconto (equivalenti a circa 40€ netti). Le ore extra salgono a **€ 10,00 lorde**. Non matura doppio rimborso ritardo ATD. Notturno +15%.
        * **Senior (Standard):** Forfait di **56€ lordi** (equivalenti calcolati base 44,80 netti), extra € 12,00 lordi/h.
        * L'esportazione excel decurta il 20% ove previsto il regime di Ritenuta/Acconto e scompone i minuti extra su formula fissa per singolo assistente.
        
        > **💡 Esempio di calcolo (Junior)**: Rita fa turno Standard di 4 ore (Regime Ritenuta 20%).
        > * Base lorda 3h: **€ 50,00**
        > * Extra lordo 1h: **€ 10,00**
        > * Subtotale lordo: **€ 60,00**
        > * *Il simulatore esegue direttamente l'applicativo netto decurtando il 20%.*
        > * **Totale simulato: € 48,00 netti.**
        """)
        
        st.divider()

        st.subheader("Verona (VRN)")
        st.markdown("""
        * **Logica a Blocchi:** Un turno standard è di 3 ore (Forfait € 56 lordo). Qualsiasi extra scatta esclusivamente per tranche intere da 3 ore (se si supera l'orario base).
        * **Notte Fissa:** Il notturno è un bonus forfettario rigido di **€ 11,20 lordi** e scatta se in turno si intercetta parzialmente la fascia 22:00-06:00.
        
        > **💡 Esempio di calcolo**: Turno durato in totale 4 ore e 30 minuti, orario diurno.
        > * Superate le prime 3h, scatta l'intero blocco rigido del secondo turno (+3 ore).
        > * Valutazione: 2 Blocchi base = **€ 56,00 x 2 = € 112,00 lordi**.
        """)
        
        st.divider()

        st.subheader("Roma (FCO)")
        st.markdown("""
        * **Turno base:** 2 ore e 30 min (150 min) a **€ 53,60 lordi**.
        * **Extra:** Rateo effettivo € 9,50 lordi / ora.
        * **Incentive:** Trattamento base innalzato a € 70,00 lordi e ore extra riconosciute a € 15,00/ora.
        * **Split Notturno:** Il calcolo divide puntualmente le ore notturne svolte **dentro al blocco base** (+15% applicato sui 53.6€ rateizzati per ora/minuto) e quelle **svolte nelle ore extra** (+15% applicato sui 9.5€).
        
        > **💡 Esempio di calcolo**: Turno Standard 3 ore totali diurne.
        > * Base 2.5h: **€ 53,60**
        > * Extra rata 30min: **€ 4,75** (la metà del valore orario).
        > * **Totale: € 58,35 lordi**.
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

        st.divider()

        st.subheader("Venezia (VCE) / Treviso (TSF) / Altri (es. CAG)")
        st.markdown("""
        * Le logiche specifiche di questi aeroporti sono interamente **gestite in via dinamica tramite il listino prezzi**.
        * I limiti orari e i tetti per il calcolo non presentano blocchi forfettari cablati o stringenti in applicazione, si adeguano a quanto depositato in \`tariffe_collaboratori.xlsx\` (Foglio Regole/Collaboratori).
        """)

