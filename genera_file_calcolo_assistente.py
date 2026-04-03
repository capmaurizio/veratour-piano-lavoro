#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Genera un file Python per ogni assistente con le formule di calcolo
basate sulle regole del documento REGOLE OPERATIVE COLLABORATORI 2026.docx
"""

import os
import sys
from pathlib import Path

# Aggiungi path per importare tariffe_collaboratori
sys.path.insert(0, os.path.dirname(__file__))
from tariffe_collaboratori import get_tariffe_manager

CALCOLI_ASSISTENTI_DIR = "calcoli_assistenti"
os.makedirs(CALCOLI_ASSISTENTI_DIR, exist_ok=True)

def genera_file_calcolo_assistente(nome_assistente: str) -> str:
    """
    Genera un file Python per un assistente con le formule di calcolo
    
    Args:
        nome_assistente: Nome dell'assistente
    
    Returns:
        Path del file generato
    """
    
    nome_safe = nome_assistente.replace(" ", "_").replace("/", "_").upper()
    file_path = os.path.join(CALCOLI_ASSISTENTI_DIR, f"calcolo_{nome_safe}.py")
    
    # Carica tariffe per questo assistente
    tm = get_tariffe_manager()
    
    # Cerca tariffe per questo assistente (prova diversi aeroporti)
    aeroporti_test = ['VRN', 'FCO', 'NAP', 'CTA', 'PMO', 'PSA', 'BRI', 'VCE', 'TSF', 'BGY', 'MXP']
    tariffe_trovate = {}
    
    for apt in aeroporti_test:
        tariffa = tm.get_tariffa(apt, nome_assistente, None)
        if tariffa:
            tariffe_trovate[apt] = tariffa
    
    # Genera il contenuto del file
    contenuto = f'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
File di calcolo tariffe per: {nome_assistente}
Generato automaticamente - Modificare secondo necessità
Basato su: REGOLE OPERATIVE COLLABORATORI 2026.docx
"""

from datetime import date, time, datetime
from typing import Optional, Dict


def calcola_tariffa_turno(
    aeroporto: str,
    durata_effettiva_min: int,
    extra_min: int = 0,
    notte_min: int = 0,
    is_festivo: bool = False,
    tour_operator: Optional[str] = None,
    tipo_servizio: Optional[str] = None  # 'incentive', 'arrivi', 'transfer', None
) -> Dict[str, float]:
    """
    Calcola la tariffa per un turno secondo le regole operative 2026.
    
    Args:
        aeroporto: Codice aeroporto (VRN, FCO, NAP, ecc.)
        durata_effettiva_min: Durata effettiva del turno in minuti
        extra_min: Minuti extra (ritardi ATD)
        notte_min: Minuti lavorati in fascia notturna
        is_festivo: Se il giorno è festivo
        tour_operator: Tour operator (opzionale)
        tipo_servizio: Tipo servizio (opzionale)
    
    Returns:
        Dict con: base_eur, extra_eur, notte_eur, totale_eur
    """
    apt_upper = aeroporto.upper().strip()
    
    # TARIFFE BASE PER AEROPORTO
    # Modificare questi valori secondo le tariffe specifiche dell'assistente
'''
    
    # Aggiungi tariffe trovate
    if tariffe_trovate:
        contenuto += "    # Tariffe caricate dal file Excel:\n"
        for apt, tariffa in tariffe_trovate.items():
            contenuto += f"    # {apt}: Base={tariffa.base_eur}€, Durata={tariffa.durata_base_h}h, Extra={tariffa.extra_eur_per_h}€/h\n"
        contenuto += "\n"
    
    contenuto += '''    # REGOLE SPECIFICHE PER AEROPORTO (da REGOLE OPERATIVE COLLABORATORI 2026.docx)
    
    # BGY - Festive Forfettarie (REGOLE OPERATIVE BGY 2026)
    # Tutte le tariffe BGY sono già NETTE — nessuno scorporo
    if apt_upper == 'BGY' and is_festivo:
        # Junior: €40 netti/3h | Senior: €50 netti/3h
        # TODO: Sostituire con categoria corretta dell'assistente (Junior/Senior)
        base_eur = 40.0      # Modificare a 50.0 se Senior
        durata_base_h = 3.0
        extra_eur_per_h = 8.0   # €8/h netti (junior) — modificare a 10.0 se Senior
        notturno_perc = 0.15    # +15% BGY (NON 20%)
    # BGY - Standard (non festivo) (REGOLE OPERATIVE BGY 2026)
    elif apt_upper == 'BGY':
        # Junior: €72 netti (€24/h × 3h) | Senior: €90 netti (€30/h × 3h)
        # TODO: Sostituire con categoria corretta dell'assistente (Junior/Senior)
        base_eur = 72.0      # Modificare a 90.0 se Senior
        durata_base_h = 3.0
        extra_eur_per_h = 8.0   # €8/h netti (junior) — modificare a 10.0 se Senior
        notturno_perc = 0.15    # +15% BGY
    # FCO - Tariffe Incentive (Accordo Assistenti FCO 2026)
    elif apt_upper == 'FCO' and tipo_servizio == 'incentive':
        base_eur = 60.0
        durata_base_h = 2.5
        extra_eur_per_h = 15.0
        notturno_perc = 0.20
    # FCO - Tariffe Arrivi (Meet & Greet) (Accordo Assistenti FCO 2026)
    elif apt_upper == 'FCO' and tipo_servizio == 'arrivi':
        base_eur = 56.0
        durata_base_h = 2.5
        extra_eur_per_h = 12.0
        notturno_perc = 0.20
    # FCO - Tariffe Standard Partenze (Accordo Assistenti FCO 2026)
    elif apt_upper == 'FCO' and (tipo_servizio is None or tipo_servizio == 'standard'):
        base_eur = 56.0
        durata_base_h = 2.5
        extra_eur_per_h = 12.0
        notturno_perc = 0.20
    # NAP - Tariffe Transfer
    elif apt_upper == 'NAP' and tipo_servizio == 'transfer':
        base_eur = 50.0
        durata_base_h = 2.5
        extra_eur_per_h = 12.0  # Senior transfer
        notturno_perc = 0.15
    # NAP - Tariffe Arrivi (Meet & Greet)
    elif apt_upper == 'NAP' and tipo_servizio == 'arrivi':
        base_eur = 56.0
        durata_base_h = 2.5
        extra_eur_per_h = 12.0  # Senior meet&greet
        notturno_perc = 0.15
    # NAP - Tariffe Standard Senior (Accordo NAP 2026)
    elif apt_upper == 'NAP':
        base_eur = 56.0   # Senior: €56/3h  (Junior: €50/3h - modificare se junior)
        durata_base_h = 3.0
        extra_eur_per_h = 12.0  # Senior: €12/h  (Junior: €10/h - modificare se junior)
        notturno_perc = 0.15  # +15% NAP
    # REGOLE STANDARD per altri aeroporti
    else:
        # Valori di default - MODIFICARE secondo tariffe specifiche
        if apt_upper in ['CTA', 'PMO', 'PSA']:
            base_eur = 60.0
        elif apt_upper in ['BRI', 'BLQ']:
            base_eur = 53.0
        else:
            base_eur = 58.0
        
        durata_base_h = 3.0
        extra_eur_per_h = 12.0
        # Notturno default per tutti gli altri è +15% (FCO è già gestito sopra)
        notturno_perc = 0.15
    
    festivo_perc = 0.20  # +20% per festivi (NON usato per BGY che ha forfait fisso)
    
    # CALCOLO BASE
    durata_h = durata_effettiva_min / 60.0
    base = base_eur
    
    # CALCOLO EXTRA
    # Ore oltre la durata base
    ore_extra_base = max(0, durata_h - durata_base_h)
    extra_ore = ore_extra_base * extra_eur_per_h
    
    # Minuti extra (ritardi ATD)
    extra_minuti = (extra_min / 60.0) * extra_eur_per_h
    
    extra = extra_ore + extra_minuti
    
    # CALCOLO NOTTURNO
    # Calcola tariffa base oraria per proporzione notturna
    tariffa_base_h = base_eur / durata_base_h
    notte_eur_per_h = tariffa_base_h * notturno_perc
    notte_eur_per_min = notte_eur_per_h / 60.0
    notte = notte_min * notte_eur_per_min
    
    # TOTALE LORDO
    totale_lordo = base + extra + notte
    
    # APPLICA FESTIVO (solo per aeroporti NON BGY — BGY ha già forfait fisso festivo)
    if is_festivo and apt_upper != 'BGY':
        totale_lordo = totale_lordo * (1 + festivo_perc)
    
    # SCORPORO NETTO
    # BGY: tariffe già espresse in NETTI — nessuno scorporo
    if apt_upper == 'BGY':
        base_netto = base
        extra_netto = extra
        notte_netto = notte
        totale_netto = totale_lordo
    else:
        # REGIME (Partita IVA vs Ritenuta d'acconto)
        # TODO: Verificare regime dell'assistente
        regime = "Ritenuta d'acconto"  # Modificare se Partita IVA
        if regime and ('PARTITA IVA' in regime.upper() or 'P.IVA' in regime.upper()):
            # Partita IVA: tariffe già al netto
            base_netto = base
            extra_netto = extra
            notte_netto = notte
            totale_netto = totale_lordo
        else:
            # Ritenuta d'acconto: applica 20%
            base_netto = base * 0.80
            extra_netto = extra * 0.80
            notte_netto = notte * 0.80
            totale_netto = totale_lordo * 0.80
    
    return {{
        'base_eur': round(base_netto, 2),
        'extra_eur': round(extra_netto, 2),
        'notte_eur': round(notte_netto, 2),
        'totale_eur': round(totale_netto, 2)
    }}


def genera_formula_excel_extra(minuti_extra: int, tariffa_extra_per_h: float = 12.0) -> str:
    """
    Genera formula Excel per calcolo extra basata sulla tariffa oraria corretta.
    
    TARIFFE EXTRA PER AEROPORTO (Accordo 2026):
      NAP Senior: €12/h  |  NAP Junior: €10/h
      FCO standard: €12/h  |  FCO incentive: €15/h
      VRN Senior/Junior: €12/h
      BGY Junior: €8/h  |  BGY Senior: €10/h
    
    Args:
        minuti_extra: Minuti extra (ritardi ATD oltre STD)
        tariffa_extra_per_h: Tariffa oraria extra (default €12/h = NAP Senior / FCO standard)
    
    Returns:
        Formula Excel (es. "=12/60*30" per 30 min a NAP Senior)
    """
    # Usa la tariffa corretta per aeroporto, NON sempre 8/60 (che era BGY Junior)
    tariff_str = int(tariffa_extra_per_h) if tariffa_extra_per_h == int(tariffa_extra_per_h) else tariffa_extra_per_h
    return f"={tariff_str}/60*{minuti_extra}"


def genera_formula_excel_totale(riga: int) -> str:
    """
    Genera formula Excel per totale: =K[riga]+M[riga]+O[riga]
    
    Args:
        riga: Numero riga Excel
    
    Returns:
        Formula Excel (es. "=K2+M2+O2")
    """
    return f"=K{riga}+M{riga}+O{riga}"


def genera_formula_excel_totale_parziale(riga_inizio: int, riga_fine: int, colonna: str = 'P') -> str:
    """
    Genera formula Excel per totale parziale: =SUM([colonna][riga_inizio]:[colonna][riga_fine])
    
    Args:
        riga_inizio: Prima riga
        riga_fine: Ultima riga
        colonna: Colonna (default 'P')
    
    Returns:
        Formula Excel (es. "=SUM(P2:P6)")
    """
    return f"=SUM({colonna}{riga_inizio}:{colonna}{riga_fine})"


if __name__ == "__main__":
    # Test
    print("Test calcolo tariffe per", nome_assistente)
    risultato = calcola_tariffa_turno(
        aeroporto="VRN",
        durata_effettiva_min=180,
        extra_min=30,
        notte_min=60,
        is_festivo=False
    )
    print("Risultato:", risultato)
'''
    
    # Scrivi il file
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(contenuto)
    
    return file_path

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        nome = sys.argv[1]
        output = genera_file_calcolo_assistente(nome)
        print(f"File generato: {output}")
    else:
        print("Uso: python genera_file_calcolo_assistente.py <nome_assistente>")
