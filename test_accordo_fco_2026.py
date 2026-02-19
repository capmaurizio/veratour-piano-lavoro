#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test di verifica per l'Accordo Assistenti FCO 2026.
Verifica che le tariffe e regole in tariffe_collaboratori.py
siano allineate al documento Accordo_Assistenti_FCO_Completo_2026.docx
"""

import sys
import os
from datetime import date

# Aggiungi path del progetto
sys.path.insert(0, os.path.dirname(__file__))

from tariffe_collaboratori import (
    calcola_tariffa_collaboratore,
    get_fco_holidays,
    get_italian_holidays_2025
)

PASSED = 0
FAILED = 0

def test(nome_test: str, expected: dict, actual: dict, tolleranza: float = 0.01):
    """Confronta risultato atteso vs effettivo"""
    global PASSED, FAILED
    ok = True
    for key in expected:
        if key not in actual:
            print(f"  ❌ {nome_test}: chiave '{key}' mancante nel risultato")
            ok = False
            continue
        if abs(actual[key] - expected[key]) > tolleranza:
            print(f"  ❌ {nome_test}: {key} = {actual[key]}, atteso {expected[key]}")
            ok = False
    if ok:
        print(f"  ✅ {nome_test}")
        PASSED += 1
    else:
        FAILED += 1


def test_bool(nome_test: str, condition: bool):
    """Test booleano"""
    global PASSED, FAILED
    if condition:
        print(f"  ✅ {nome_test}")
        PASSED += 1
    else:
        print(f"  ❌ {nome_test}")
        FAILED += 1


# ============================================================
# TEST 1: FCO Base Partenze Standard
# Accordo: €56,00 per 2h30', extra €12/h, notturno +20%, festivo +20%
# ============================================================
print("\n" + "="*60)
print("TEST 1: FCO Base Partenze Standard")
print("="*60)

# 1a. Turno base 2h30' senza extra/notturno/festivo
risultato = calcola_tariffa_collaboratore(
    aeroporto='FCO',
    nome='TEST_ASSISTENTE',
    durata_min=150,   # 2h30'
    extra_min=0,
    minuti_notturni=0,
    is_festivo=False,
    tipo_servizio=None
)
test("FCO base 2h30' = €56", {'base_eur': 56.0, 'totale_eur': 56.0}, risultato)

# 1b. Turno con 30 min extra
risultato = calcola_tariffa_collaboratore(
    aeroporto='FCO',
    nome='TEST_ASSISTENTE',
    durata_min=150,
    extra_min=30,      # 30 min ritardo → (30/60)*12 = €6
    minuti_notturni=0,
    is_festivo=False,
    tipo_servizio=None
)
test("FCO base + 30min extra = €62 (€56 + €6)", {'base_eur': 56.0, 'extra_eur': 6.0, 'totale_eur': 62.0}, risultato)

# 1c. Turno con 60 min extra
risultato = calcola_tariffa_collaboratore(
    aeroporto='FCO',
    nome='TEST_ASSISTENTE',
    durata_min=150,
    extra_min=60,      # 60 min ritardo → (60/60)*12 = €12
    minuti_notturni=0,
    is_festivo=False,
    tipo_servizio=None
)
test("FCO base + 1h extra = €68 (€56 + €12)", {'base_eur': 56.0, 'extra_eur': 12.0, 'totale_eur': 68.0}, risultato)


# ============================================================
# TEST 2: FCO Notturno +20%
# ============================================================
print("\n" + "="*60)
print("TEST 2: FCO Notturno +20%")
print("="*60)

# 2a. Turno base con 60 min notturni
# Valore orario = 56/2.5 = 22.4 €/h
# Notturno 60 min = (60/60) * 22.4 * 0.20 = €4.48
risultato = calcola_tariffa_collaboratore(
    aeroporto='FCO',
    nome='TEST_ASSISTENTE',
    durata_min=150,
    extra_min=0,
    minuti_notturni=60,
    is_festivo=False,
    tipo_servizio=None
)
notte_atteso = (60/60) * (56.0/2.5) * 0.20  # = 4.48
test(f"FCO notturno 1h = €{notte_atteso:.2f}", {'notte_eur': notte_atteso}, risultato)


# ============================================================
# TEST 3: FCO Festivo +20%
# ============================================================
print("\n" + "="*60)
print("TEST 3: FCO Festivo +20%")
print("="*60)

# 3a. Turno base festivo: €56 * 1.20 = €67.20
risultato = calcola_tariffa_collaboratore(
    aeroporto='FCO',
    nome='TEST_ASSISTENTE',
    durata_min=150,
    extra_min=0,
    minuti_notturni=0,
    is_festivo=True,
    tipo_servizio=None
)
test("FCO festivo = €67.20 (€56 * 1.20)", {'totale_eur': 67.20}, risultato)

# 3b. Turno con extra + notturno + festivo
# Base = 56, Extra = 6, Notte = 4.48
# Subtotale = 66.48
# Festivo: 66.48 * 1.20 = 79.776 → 79.78
risultato = calcola_tariffa_collaboratore(
    aeroporto='FCO',
    nome='TEST_ASSISTENTE',
    durata_min=150,
    extra_min=30,
    minuti_notturni=60,
    is_festivo=True,
    tipo_servizio=None
)
subtotale = 56.0 + 6.0 + notte_atteso
totale_festivo = subtotale * 1.20
test(f"FCO extra+notte+festivo = €{totale_festivo:.2f}", {'totale_eur': round(totale_festivo, 2)}, risultato)


# ============================================================
# TEST 4: FCO Incentive (Iantra)
# Accordo: €60,00 per 2h30', extra €15/h
# ============================================================
print("\n" + "="*60)
print("TEST 4: FCO Incentive (Iantra)")
print("="*60)

risultato = calcola_tariffa_collaboratore(
    aeroporto='FCO',
    nome='TEST_ASSISTENTE',
    durata_min=150,
    extra_min=0,
    minuti_notturni=0,
    is_festivo=False,
    tipo_servizio='incentive'
)
test("FCO incentive base = €60", {'base_eur': 60.0, 'totale_eur': 60.0}, risultato)

# Incentive con 1h extra
risultato = calcola_tariffa_collaboratore(
    aeroporto='FCO',
    nome='TEST_ASSISTENTE',
    durata_min=150,
    extra_min=60,
    minuti_notturni=0,
    is_festivo=False,
    tipo_servizio='incentive'
)
test("FCO incentive + 1h extra = €75 (€60 + €15)", {'base_eur': 60.0, 'extra_eur': 15.0, 'totale_eur': 75.0}, risultato)


# ============================================================  
# TEST 5: FCO Arrivi (Meet & Greet)
# Accordo: €56,00 per 2h30', extra €12/h
# ============================================================
print("\n" + "="*60)
print("TEST 5: FCO Arrivi (Meet & Greet)")
print("="*60)

risultato = calcola_tariffa_collaboratore(
    aeroporto='FCO',
    nome='TEST_ASSISTENTE',
    durata_min=150,
    extra_min=0,
    minuti_notturni=0,
    is_festivo=False,
    tipo_servizio='arrivi'
)
test("FCO arrivi base = €56", {'base_eur': 56.0, 'totale_eur': 56.0}, risultato)


# ============================================================
# TEST 6: 29/6 (Santi Pietro e Paolo) - Solo FCO
# ============================================================
print("\n" + "="*60)
print("TEST 6: 29/6 Santi Pietro e Paolo - Solo FCO")
print("="*60)

# Verifica che 29/6 è nei festivi FCO
fco_holidays = get_fco_holidays()
test_bool("29/6/2026 è festivo FCO", date(2026, 6, 29) in fco_holidays)
test_bool("29/6/2025 è festivo FCO", date(2025, 6, 29) in fco_holidays)

# Verifica che 29/6 NON è nei festivi standard (nazionali)
standard_holidays = get_italian_holidays_2025()
test_bool("29/6/2026 NON è festivo nazionale", date(2026, 6, 29) not in standard_holidays)

# Verifica altre festività presenti in entrambi
test_bool("25/12/2026 è festivo FCO", date(2026, 12, 25) in fco_holidays)
test_bool("1/1/2026 è festivo FCO", date(2026, 1, 1) in fco_holidays)
test_bool("1/5/2026 è festivo FCO", date(2026, 5, 1) in fco_holidays)


# ============================================================
# TEST 7: FCO Notturno con diversi regimi
# ============================================================
print("\n" + "="*60)
print("TEST 7: Notturno +20% per FCO (non +15% come prima)")
print("="*60)

# FCO standard senza tariffa personalizzata: notturno DEVE essere +20%
# Prima era +15% (default standard), ora DEVE essere +20% per FCO
risultato = calcola_tariffa_collaboratore(
    aeroporto='FCO',
    nome='ASSISTENTE_GENERICO',
    durata_min=150,
    extra_min=0,
    minuti_notturni=60,
    is_festivo=False,
    tipo_servizio=None
)
# Valore orario per FCO standard: 56/2.5 = 22.4
# Notturno 60 min al 20%: (60/60) * 22.4 * 0.20 = 4.48
test("FCO notturno +20% (non +15%)", {'notte_eur': 4.48}, risultato)


# ============================================================
# RISULTATI
# ============================================================
print("\n" + "="*60)
totale = PASSED + FAILED
print(f"RISULTATI: {PASSED}/{totale} test passati, {FAILED} falliti")
print("="*60)

if FAILED > 0:
    print("\n⚠️  Ci sono test falliti! Verificare le implementazioni.")
    sys.exit(1)
else:
    print("\n✅ Tutti i test passati! L'Accordo Assistenti FCO 2026 è correttamente implementato.")
    sys.exit(0)
