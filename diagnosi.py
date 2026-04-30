#!/usr/bin/env python3
"""Script di diagnosi: capisce perché mancano TO nel DettaglioBlocchi."""

import sys, os, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tour_operators import (
    detect_tour_operators, find_tour_operator_folder,
    get_tour_operator_module_name, get_tour_operator_processors,
    ALPITOUR_AVAILABLE, ALISERVICE_AVAILABLE, BAOBAB_AVAILABLE,
    DOMINA_AVAILABLE, MICHELTOURS_AVAILABLE, SAND_AVAILABLE,
    CABOVERDETIME_AVAILABLE, RUSCONI_AVAILABLE,
)
from consuntivoveratour import RoundingPolicy

# ── Trova il file Excel ─────────────────────────────────────────────────────
xlsx_files = glob.glob("*.xlsx") + glob.glob("**/*.xlsx", recursive=False)
if not xlsx_files:
    print("❌ Nessun file .xlsx trovato nella directory corrente.")
    print(f"   CWD: {os.getcwd()}")
    sys.exit(1)

# Prende il più recente
file_path = sorted(xlsx_files, key=os.path.getmtime, reverse=True)[0]
print(f"\n📁 File analizzato: {file_path}")
print("=" * 70)

# ── Moduli disponibili ──────────────────────────────────────────────────────
print("\n📦 Moduli disponibili:")
moduli = {
    'veratour': True,
    'alpitour': ALPITOUR_AVAILABLE,
    'aliservice': ALISERVICE_AVAILABLE,
    'baobab': BAOBAB_AVAILABLE,
    'domina': DOMINA_AVAILABLE,
    'micheltours': MICHELTOURS_AVAILABLE,
    'sand': SAND_AVAILABLE,
    'caboverdetime': CABOVERDETIME_AVAILABLE,
    'rusconi': RUSCONI_AVAILABLE,
}
for nome, avail in moduli.items():
    stato = "✅" if avail else "❌ IMPORT FALLITO"
    print(f"  {stato}  {nome}")

# ── Rileva TO dal file ──────────────────────────────────────────────────────
print("\n🔍 Tour Operator rilevati nel file:")
tour_operators, aliservice_managed = detect_tour_operators(file_path)
print(f"  TOUR OPERATOR colonna: {sorted(tour_operators)}")
print(f"  Gestiti da Aliservice: {sorted(aliservice_managed)}")

tour_operators_to_check = tour_operators - aliservice_managed

# ── Verifica matching cartelle ──────────────────────────────────────────────
print("\n📂 Matching cartelle (find_tour_operator_folder):")
for to_name in sorted(tour_operators_to_check):
    folder = find_tour_operator_folder(to_name)
    module_name = get_tour_operator_module_name(to_name)
    print(f"  TO={repr(to_name):30s} → folder={folder or '❌ NON TROVATA':40s} → module={module_name}")

# ── Test process_func per ogni TO ──────────────────────────────────────────
print("\n🔄 Test process_func per ogni TO:")
processors = get_tour_operator_processors(None, "DIFF5", "NONE", 5, "NONE", 5, None)

for to_name in sorted(tour_operators_to_check):
    folder = find_tour_operator_folder(to_name)
    if not folder:
        print(f"  ⚠️  {to_name}: nessuna cartella → saltato")
        continue
    module_name = get_tour_operator_module_name(to_name)
    if not module_name or module_name not in processors:
        print(f"  ⚠️  {to_name}: module_name={module_name} non in processors")
        continue
    proc = processors[module_name]
    if not proc['available']:
        print(f"  ❌  {to_name}: modulo {module_name} non disponibile (import fallito)")
        continue

    try:
        kw = proc['config_kwargs']()
        kw['to_keyword'] = to_name.lower()
        cfg = proc['config_class'](**kw)
        detail, totals, discr = proc['process_func']([file_path], cfg)
        righe = len(detail) if detail is not None and not detail.empty else 0
        print(f"  {'✅' if righe > 0 else '⚠️ 0 righe'} {to_name}: {righe} blocchi (to_keyword={repr(to_name.lower())})")
        if righe == 0:
            # Prova con il keyword di default del modulo
            kw2 = proc['config_kwargs']()
            cfg2 = proc['config_class'](**kw2)
            detail2, _, _ = proc['process_func']([file_path], cfg2)
            righe2 = len(detail2) if detail2 is not None and not detail2.empty else 0
            print(f"       → con default to_keyword: {righe2} blocchi")
    except Exception as e:
        import traceback
        print(f"  ❌  {to_name}: ERRORE → {e}")
        traceback.print_exc()

print("\n" + "=" * 70)
print("Fine diagnosi.\n")
