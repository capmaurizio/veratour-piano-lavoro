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
            return "📌 BGY Senior (Forfait 30€/3h, Extra 10€/h, Festivo 50€/3h, Notturno +15%)"
        if 'senior' in categoria_str:
            return "📌 BGY Senior (Forfait 30€/3h, Extra 10€/h, Festivo 50€/3h, Notturno +15%)"
        return "🔷 BGY Junior (Forfait 24€/3h, Extra 8€/h, Festivo 40€/3h, Notturno +15%)"
        
    elif apt_upper == 'MXP':
        if 'manuela' in name_norm and 'gregori' in name_norm:
            return "📌 MXP Eccezione (Base fissa 60€, Extra solo ATD 12€/h, Notturno +20%, Festivo +20%, INPS +4%)"
        if 'martina' in name_norm and 'nettis' in name_norm:
            return "🔷 MXP Eccezione (Equiparata a BGY Junior: Forfait 24€/3h, Extra 8€/h, ecc.)"
        return "⚙️ MXP Standard Generico (Da verificare)"
        
    elif apt_upper == 'NAP':
        if any(n in name_norm for n in ['rita', 'sara', 'camilla']):
            return "🔷 NAP Junior (Forfait 50€/3h lordi, Extra 10€/h lordi, no doppio extra, Notturno +15%)"
        return "📌 NAP Senior/Standard (Forfait 56€/3h lordi, Extra 12€/h lordi, Notturno +15%)"
        
    elif apt_upper == 'VRN':
        return "⚙️ VRN Standard (Logica blocchi forfettari completi 56€, Extra arrotondato 3h, Notte fissa +11.20€)"
        
    elif apt_upper == 'FCO':
        return "⚙️ FCO Standard (Base 53.6€/2.5h, Extra 9.5€/h, Incentive 70€/2.5h, Notturno Split 22:00-06:00)"
        
    elif apt_upper in ['CTA', 'TRN', 'PMO', 'PSA']:
        return f"⚙️ {apt_upper} Standard (Base 60€/3h, Extra 12€/h, Notturno +15%, Festivo +20%)"
        
    elif apt_upper in ['BRI', 'BLQ']:
        return f"⚙️ {apt_upper} Standard (Base 53€/3h, Extra 12€/h, Notturno +15%, Festivo +20%)"
        
    return "🌐 Standard/Generico (Regola base letta da foglio Excel principale)"


def render_regolamento_page():
    st.title("📚 Regolamenti Operativi e Tariffe")
    st.markdown("Consulta l'elenco degli assistenti e le relative regole di calcolo impostate in sistema.")
    
    tab_collaboratori, tab_dettagli = st.tabs(["👥 Elenco Collaboratori", "📜 Dettaglio Regole per Aeroporto"])
    
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
            df_display = st.dataframe(df, use_container_width=True, hide_index=True)
            
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
        """)
        
        st.divider()
        
        st.subheader("Malpensa (MXP)")
        st.markdown("""
        * **Eccezione Manuela Gregori:** Base fissa a corpo intero di **60€** a chiamata. Nessun extra per orario protratto prima del decollo; gli extra maturano **esclusivamente** sul reale "Ritardo ATD" pagati a **€ 12,00/h**. Notturno +20%, applicato anche in festività il +20%, calcolo addizionale Cassa INPS del **+4%**.
        * **Eccezione Martina Nettis:** Identificata a codice come *equiparata alla base Junior Bergamo* (24€ forfait, extra 8€/h, festivo +20%, Notturno +15%).
        """)
        
        st.divider()
        
        st.subheader("Napoli (NAP)")
        st.markdown("""
        * **Turno Base:** 3 ore per voli Standard. (2h30 per specifici altri pacchetti su cui matura la sesta mezz'ora in extra).
        * **Junior (es. Rita, Sara, Camilla):** Forfait contrattuale di **50€ lordi** in ritenuta d'acconto (equivalenti a circa 40€ netti). Le ore extra salgono a **€ 10,00 lorde**. Non matura doppio rimborso ritardo ATD. Notturno +15%.
        * **Senior (Standard):** Forfait di **56€ lordi** (equivalenti calcolati base 44,80 netti), extra € 12,00 lordi/h.
        * L'esportazione excel decurta il 20% ove previsto il regime di Ritenuta/Acconto e scompone i minuti extra su formula fissa per singolo assistente.
        """)
        
        st.divider()

        st.subheader("Verona (VRN)")
        st.markdown("""
        * **Logica a Blocchi:** Un turno standard è di 3 ore (Forfait € 56 lordo). Qualsiasi extra scatta esclusivamente per tranche intere da 3 ore (se si supera l'orario base).
        * **Notte Fissa:** Il notturno è un bonus forfettario rigido di **€ 11,20 lordi** e scatta se in turno si intercetta parzialmente la fascia 22:00-06:00.
        """)
        
        st.divider()

        st.subheader("Roma (FCO)")
        st.markdown("""
        * **Turno base:** 2 ore e 30 min (150 min) a **€ 53,60 lordi**.
        * **Extra:** Rateo effettivo € 9,50 lordi / ora.
        * **Incentive:** Trattamento base innalzato a € 70,00 lordi e ore extra riconosciute a € 15,00/ora.
        * **Split Notturno:** Il calcolo divide puntualmente le ore notturne svolte **dentro al blocco base** (+15% applicato sui 53.6€ rateizzati per ora/minuto) e quelle **svolte nelle ore extra** (+15% applicato sui 9.5€).
        """)
