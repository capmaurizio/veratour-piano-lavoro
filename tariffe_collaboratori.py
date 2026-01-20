#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Modulo per gestire le tariffe dei collaboratori dal file Excel.
Legge e normalizza le tariffe per aeroporto, collaboratore, tour operator e servizio.
"""

import pandas as pd
import re
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass
from pathlib import Path
from datetime import date, timedelta

try:
    from dateutil.easter import easter
except ImportError:
    # Calcolo manuale di Pasqua usando l'algoritmo di Meeus/Jones/Butcher (Gregoriano)
    def easter(year: int) -> date:
        """Calcola la data di Pasqua per un dato anno (algoritmo Gregoriano)"""
        a = year % 19
        b = year // 100
        c = year % 100
        d = (19 * a + b - b // 4 - ((b - (b + 8) // 25 + 1) // 3) + 15) % 30
        e = (32 + 2 * (b % 4) + 2 * (c // 4) - d - (c % 4)) % 7
        f = d + e - 7 * ((a + 11 * d + 22 * e) // 451) + 114
        month = f // 31
        day = (f % 31) + 1
        return date(year, month, day)


def get_italian_holidays_2025() -> set:
    """
    Calcola i festivi italiani per il 2025.
    """
    holidays = set()
    
    # Festivi fissi 2025
    holidays.add(date(2025, 1, 1))   # Capodanno
    holidays.add(date(2025, 1, 6))   # Epifania
    holidays.add(date(2025, 4, 25))  # Liberazione
    holidays.add(date(2025, 5, 1))   # Festa del Lavoro
    holidays.add(date(2025, 6, 2))   # Festa della Repubblica
    holidays.add(date(2025, 11, 1))  # Ognissanti
    holidays.add(date(2025, 8, 15))  # Ferragosto
    holidays.add(date(2025, 12, 8))  # Immacolata
    holidays.add(date(2025, 12, 25)) # Natale
    holidays.add(date(2025, 12, 26)) # Santo Stefano
    
    # Pasqua e Pasquetta 2025 (calcolate dinamicamente)
    easter_2025 = easter(2025)
    holidays.add(easter_2025)              # Pasqua
    holidays.add(easter_2025 + timedelta(days=1))  # Pasquetta
    
    return holidays


@dataclass
class TariffaCollaboratore:
    """Struttura dati per rappresentare le tariffe di un collaboratore"""
    aeroporto: str
    nome: str
    categoria: Optional[str] = None  # Senior, Junior
    regime: Optional[str] = None  # Partita IVA, Ritenuta d'acconto
    
    # Tariffe base
    base_eur: Optional[float] = None
    durata_base_h: Optional[float] = None  # Durata base in ore (es. 2.5, 3.0)
    extra_eur_per_h: Optional[float] = None
    
    # Tariffe servizi speciali
    incentive_base_eur: Optional[float] = None
    incentive_durata_h: Optional[float] = None
    incentive_extra_eur_per_h: Optional[float] = None
    arrivi_eur: Optional[float] = None
    arrivi_durata_h: Optional[float] = None
    transfer_eur: Optional[float] = None
    
    # Maggiorazioni
    notturno_perc: Optional[float] = None  # Percentuale (es. 0.15 per +15%)
    notturno_fascia: Optional[str] = None  # Fascia oraria (es. "23:00-06:00")
    festivo_perc: Optional[float] = None  # Percentuale (es. 0.20 per +20%)
    
    # Note
    note: Optional[str] = None
    
    # Tour operator specifico (se la tariffa è specifica per un TO)
    tour_operator: Optional[str] = None


class TariffeManager:
    """Gestore delle tariffe dei collaboratori"""
    
    def __init__(self, file_path: str):
        """
        Inizializza il gestore delle tariffe leggendo il file Excel.
        
        Args:
            file_path: Percorso del file Excel con le tariffe
        """
        self.file_path = Path(file_path)
        self.tariffe: Dict[Tuple[str, str], TariffaCollaboratore] = {}  # (aeroporto, nome) -> Tariffa
        self.tariffe_per_to: Dict[Tuple[str, str, str], TariffaCollaboratore] = {}  # (aeroporto, nome, to) -> Tariffa
        self.tariffe_default: Dict[str, TariffaCollaboratore] = {}  # aeroporto -> Tariffa default
        
        # Mappatura codici aeroporto
        self.apt_codes = {
            'Bergamo': 'BGY', 'BGY': 'BGY',
            'Verona': 'VRN', 'VRN': 'VRN',
            'Malpensa': 'MXP', 'MXP': 'MXP',
            'Venezia': 'VCE', 'VCE': 'VCE',
            'Treviso': 'TSF', 'TSF': 'TSF',
            'Torino': 'TRN', 'TRN': 'TRN',
            'Bologna': 'BLQ', 'BLQ': 'BLQ',
            'Pisa': 'PSA', 'PSA': 'PSA',
            'Roma': 'FCO', 'FCO': 'FCO', 'Roma Fiumicino': 'FCO', 'Roma Fiumicino (FCO)': 'FCO',
            'Napoli': 'NAP', 'NAP': 'NAP',
            'Bari': 'BRI', 'BRI': 'BRI',
            'Catania': 'CTA', 'CTA': 'CTA',
            'Palermo': 'PMO', 'PMO': 'PMO',
            'Cagliari': 'CAG', 'CAG': 'CAG',
        }
        
        self._load_tariffe()
    
    def _normalize_apt(self, apt: str) -> str:
        """Normalizza il nome dell'aeroporto al codice"""
        if not apt or pd.isna(apt):
            return ''
        apt_str = str(apt).strip()
        return self.apt_codes.get(apt_str, apt_str.upper())
    
    def _parse_eur_value(self, val: Any) -> Optional[float]:
        """Estrae valore numerico da stringhe come '€56 + IVA' o '56'"""
        if pd.isna(val):
            return None
        if isinstance(val, (int, float)):
            return float(val)
        val_str = str(val).strip()
        # Rimuovi "€", "+ IVA", spazi
        val_str = re.sub(r'[€\s]', '', val_str)
        val_str = re.sub(r'\+IVA.*', '', val_str, flags=re.IGNORECASE)
        # Estrai numero
        match = re.search(r'(\d+\.?\d*)', val_str)
        if match:
            return float(match.group(1))
        return None
    
    def _parse_duration_h(self, val: Any) -> Optional[float]:
        """Converte durata in ore (es. '2h30' -> 2.5, '3h' -> 3.0)"""
        if pd.isna(val):
            return None
        if isinstance(val, (int, float)):
            return float(val)
        val_str = str(val).strip()
        # Pattern: "2h30", "3h", "2.5h"
        match = re.search(r'(\d+)(?:h|:)?(?:(\d+))?', val_str)
        if match:
            hours = int(match.group(1))
            minutes = int(match.group(2)) if match.group(2) else 0
            return hours + (minutes / 60.0)
        return None
    
    def _parse_percentage(self, val: Any) -> Optional[float]:
        """Estrae percentuale da stringhe come '+15%', '15%', '0.15'"""
        if pd.isna(val):
            return None
        if isinstance(val, (int, float)):
            # Se è un numero, verifica se è plausibile come percentuale
            # Percentuali tipiche sono tra 0 e 100, o già in formato decimale (0-1)
            if val <= 1.0:
                # Già in formato decimale (es. 0.20 per 20%)
                return float(val)
            elif val <= 100.0:
                # Percentuale in formato intero (es. 20 per 20%)
                return float(val) / 100.0
            else:
                # Valore troppo alto, probabilmente un errore (es. durata in minuti o altro)
                # Ignora valori > 100 che non sono percentuali plausibili
                return None
        val_str = str(val).strip()
        # Rimuovi "+", "%", spazi
        val_str = re.sub(r'[+\s%]', '', val_str)
        match = re.search(r'(\d+\.?\d*)', val_str)
        if match:
            perc = float(match.group(1))
            return perc / 100.0 if perc > 1.0 else perc
        return None
    
    def _normalize_name(self, name: str) -> str:
        """Normalizza il nome del collaboratore (rimuovi spazi extra)"""
        if pd.isna(name):
            return ''
        return ' '.join(str(name).strip().split())
    
    def _load_tariffe(self):
        """Carica tutte le tariffe dal file Excel"""
        if not self.file_path.exists():
            print(f"File tariffe non trovato: {self.file_path}")
            return
        
        xls = pd.ExcelFile(self.file_path)
        
        # Carica da sheet "TUTTI COLLABORATORI"
        if 'TUTTI COLLABORATORI' in xls.sheet_names:
            self._load_tutti_collaboratori(xls)
        
        # Carica da sheet dettaglio per aeroporto
        for sheet_name in xls.sheet_names:
            if '– Dettaglio' in sheet_name or '– Collaboratori' in sheet_name:
                apt_name = sheet_name.split('–')[0].strip()
                self._load_dettaglio_aeroporto(xls, sheet_name, apt_name)
        
        # Carica regole per aeroporto (per tariffe default)
        for sheet_name in xls.sheet_names:
            if '– Regole' in sheet_name:
                apt_name = sheet_name.split('–')[0].strip()
                self._load_regole_aeroporto(xls, sheet_name, apt_name)
    
    def _load_tutti_collaboratori(self, xls: pd.ExcelFile):
        """Carica tariffe dalla sheet 'TUTTI COLLABORATORI'"""
        df = pd.read_excel(xls, sheet_name='TUTTI COLLABORATORI')
        
        # La sheet ha header ripetuti, filtra righe valide
        for _, row in df.iterrows():
            apt = row.get('Aeroporto', '')
            nome = row.get('Nome', '')
            
            # Salta righe header o vuote
            if pd.isna(apt) or pd.isna(nome) or str(apt).strip() == '' or str(nome).strip() == '':
                continue
            
            # Salta righe che sono chiaramente header
            apt_str = str(apt).strip().upper()
            nome_str = str(nome).strip().upper()
            if apt_str in ['AEROPORTO', 'APT'] or nome_str in ['NOME', 'NOME COLLABORATORE', 'COLLABORATORE']:
                continue
            
            apt_code = self._normalize_apt(str(apt))
            nome_norm = self._normalize_name(str(nome))
            
            if apt_code and nome_norm:
                tariffa = TariffaCollaboratore(
                    aeroporto=apt_code,
                    nome=nome_norm,
                    categoria=row.get('Categoria', None),
                    regime=row.get('Regime', None),
                    base_eur=self._parse_eur_value(row.get('Assistenza Base', row.get('Assistenza Base €', None))),
                    durata_base_h=self._parse_duration_h(row.get('Durata', row.get('Durata Base', None))),
                    extra_eur_per_h=self._parse_eur_value(row.get('Extra', row.get('Extra €/h', None))),
                    incentive_base_eur=self._parse_eur_value(row.get('Incentive Base', row.get('Incentive Base €', None))),
                    incentive_durata_h=self._parse_duration_h(row.get('Durata Incentive', None)),
                    incentive_extra_eur_per_h=self._parse_eur_value(row.get('Extra Incentive', row.get('Extra Incentive €/h', None))),
                    arrivi_eur=self._parse_eur_value(row.get('Arrivi', row.get('Arrivi €', None))),
                    transfer_eur=self._parse_eur_value(row.get('Transfer', row.get('Transfer Veratour', None))),
                    notturno_perc=self._parse_notturno_perc(row.get('Notturno', None)),
                    notturno_fascia=self._parse_notturno_fascia(row.get('Notturno', None)),
                    festivo_perc=self._parse_percentage(row.get('Festivo', None)),
                    note=row.get('Note', None)
                )
                
                key = (apt_code, nome_norm)
                self.tariffe[key] = tariffa
    
    def _load_dettaglio_aeroporto(self, xls: pd.ExcelFile, sheet_name: str, apt_name: str):
        """Carica tariffe da sheet dettaglio per aeroporto"""
        df = pd.read_excel(xls, sheet_name=sheet_name)
        apt_code = self._normalize_apt(apt_name)
        
        if df.empty:
            return
        
        # Identifica colonne nome (variano per aeroporto)
        nome_cols = ['Nome Collaboratore', 'Nome', 'Nome Collaboratore']
        nome_col = None
        for col in nome_cols:
            if col in df.columns:
                nome_col = col
                break
        
        if not nome_col:
            return
        
        for _, row in df.iterrows():
            nome = row.get(nome_col, '')
            if pd.isna(nome) or str(nome).strip() == '':
                continue
            
            nome_norm = self._normalize_name(str(nome))
            if not nome_norm:
                continue
            
            # Estrai tariffe in base alle colonne disponibili
            base_eur = None
            durata_base_h = None
            extra_eur_per_h = None
            
            # Cerca colonne base
            for col in ['Assistenza Base €', 'Assistenza Base', 'Base €', 'Base']:
                if col in df.columns:
                    base_eur = self._parse_eur_value(row.get(col))
                    if base_eur is not None:
                        break
            
            for col in ['Durata Base', 'Durata']:
                if col in df.columns:
                    durata_base_h = self._parse_duration_h(row.get(col))
                    if durata_base_h is not None:
                        break
            
            for col in ['Extra €/h', 'Extra', 'Extra €/h']:
                if col in df.columns:
                    extra_eur_per_h = self._parse_eur_value(row.get(col))
                    if extra_eur_per_h is not None:
                        break
            
            # Incentive
            incentive_base_eur = self._parse_eur_value(row.get('Incentive Base €', row.get('Incentive Base', None)))
            incentive_durata_h = self._parse_duration_h(row.get('Durata Incentive', None))
            incentive_extra_eur_per_h = self._parse_eur_value(row.get('Extra Incentive €/h', row.get('Extra Incentive', None)))
            
            # Arrivi e Transfer
            arrivi_eur = self._parse_eur_value(row.get('Arrivi €', row.get('Arrivi', None)))
            arrivi_durata_h = self._parse_duration_h(row.get('Durata Arrivi', None))
            transfer_eur = self._parse_eur_value(row.get('Arrivi+Transfer Veratour €', row.get('Transfer', None)))
            
            # Notturno e Festivo
            notturno_str = row.get('Notturno', None)
            notturno_perc = self._parse_notturno_perc(notturno_str)
            notturno_fascia = self._parse_notturno_fascia(notturno_str)
            festivo_perc = self._parse_percentage(row.get('Festivo', row.get('Festivo %', None)))
            
            # Categoria e Regime
            categoria = row.get('Livello', row.get('Categoria', None))
            regime = row.get('Regime', row.get('P.IVA', None))
            if regime and isinstance(regime, str):
                if 'SI' in str(regime).upper():
                    regime = 'Partita IVA'
                elif 'NO' in str(regime).upper():
                    regime = 'Ritenuta d\'acconto'
            
            tariffa = TariffaCollaboratore(
                aeroporto=apt_code,
                nome=nome_norm,
                categoria=str(categoria).strip() if categoria else None,
                regime=str(regime).strip() if regime else None,
                base_eur=base_eur,
                durata_base_h=durata_base_h,
                extra_eur_per_h=extra_eur_per_h,
                incentive_base_eur=incentive_base_eur,
                incentive_durata_h=incentive_durata_h,
                incentive_extra_eur_per_h=incentive_extra_eur_per_h,
                arrivi_eur=arrivi_eur,
                arrivi_durata_h=arrivi_durata_h,
                transfer_eur=transfer_eur,
                notturno_perc=notturno_perc,
                notturno_fascia=notturno_fascia,
                festivo_perc=festivo_perc,
                note=row.get('Note', None)
            )
            
            key = (apt_code, nome_norm)
            # Se la tariffa esiste già, aggiorna i campi mancanti o sovrascrivi con valori più specifici
            # I valori dai dettagli aeroporto hanno SEMPRE priorità su quelli generici
            if key in self.tariffe:
                existing = self.tariffe[key]
                # Aggiorna campi: i valori dai dettagli aeroporto sovrascrivono sempre
                if base_eur is not None:
                    existing.base_eur = base_eur
                if durata_base_h is not None:
                    existing.durata_base_h = durata_base_h
                if extra_eur_per_h is not None:
                    existing.extra_eur_per_h = extra_eur_per_h
                # Notturno e Festivo: sovrascrivi sempre se presente (i dettagli aeroporto hanno priorità)
                if notturno_perc is not None:
                    existing.notturno_perc = notturno_perc
                if notturno_fascia is not None:
                    existing.notturno_fascia = notturno_fascia
                if festivo_perc is not None:
                    existing.festivo_perc = festivo_perc
                if categoria:
                    existing.categoria = categoria
                if regime:
                    existing.regime = regime
                if incentive_base_eur is not None:
                    existing.incentive_base_eur = incentive_base_eur
                if incentive_durata_h is not None:
                    existing.incentive_durata_h = incentive_durata_h
                if incentive_extra_eur_per_h is not None:
                    existing.incentive_extra_eur_per_h = incentive_extra_eur_per_h
                if arrivi_eur is not None:
                    existing.arrivi_eur = arrivi_eur
                if transfer_eur is not None:
                    existing.transfer_eur = transfer_eur
                if row.get('Note'):
                    existing.note = row.get('Note')
            else:
                # Crea nuova tariffa
                self.tariffe[key] = tariffa
    
    def _load_regole_aeroporto(self, xls: pd.ExcelFile, sheet_name: str, apt_name: str):
        """Carica regole default per aeroporto (per tariffe quando non specificate per collaboratore)"""
        df = pd.read_excel(xls, sheet_name=sheet_name)
        apt_code = self._normalize_apt(apt_name)
        
        if df.empty:
            return
        
        # Per ora salva solo le regole, potrebbero essere usate come fallback
        # TODO: implementare logica per tariffe default per TO
    
    def _parse_notturno_perc(self, val: Any) -> Optional[float]:
        """Estrae percentuale notturno da stringhe come '+15% (23:00-06:00)'"""
        if pd.isna(val):
            return None
        if isinstance(val, (int, float)):
            # Se è un numero, verifica se è plausibile come percentuale
            # Percentuali tipiche sono tra 0 e 100, o già in formato decimale (0-1)
            if val <= 1.0:
                # Già in formato decimale (es. 0.15 per 15%)
                return float(val)
            elif val <= 100.0:
                # Percentuale in formato intero (es. 15 per 15%)
                return float(val) / 100.0
            else:
                # Valore troppo alto, probabilmente un errore (es. 58 potrebbe essere un ID o altro)
                # Ignora valori > 100 che non sono percentuali plausibili
                return None
        val_str = str(val).strip()
        # Cerca pattern come "+15%", "15%"
        match = re.search(r'\+?(\d+\.?\d*)%', val_str)
        if match:
            perc = float(match.group(1))
            return perc / 100.0
        return None
    
    def _parse_notturno_fascia(self, val: Any) -> Optional[str]:
        """Estrae fascia oraria notturna da stringhe come '+15% (23:00-06:00)'"""
        if pd.isna(val):
            return None
        val_str = str(val).strip()
        # Cerca pattern come "23:00-06:00", "23–06", "23-06"
        match = re.search(r'(\d{1,2}):?(\d{2})?[-–](\d{1,2}):?(\d{2})?', val_str)
        if match:
            start_h = match.group(1)
            start_m = match.group(2) if match.group(2) else '00'
            end_h = match.group(3)
            end_m = match.group(4) if match.group(4) else '00'
            return f"{start_h}:{start_m}-{end_h}:{end_m}"
        return None
    
    def get_tariffa(self, aeroporto: str, nome: str, tour_operator: Optional[str] = None) -> Optional[TariffaCollaboratore]:
        """
        Ottiene la tariffa per un collaboratore specifico.
        
        Args:
            aeroporto: Codice aeroporto (es. 'VRN', 'FCO')
            nome: Nome del collaboratore
            tour_operator: Tour operator (opzionale, per tariffe specifiche TO)
        
        Returns:
            TariffaCollaboratore o None se non trovata
        """
        apt_code = self._normalize_apt(aeroporto)
        nome_norm = self._normalize_name(nome)
        
        # Cerca esatta
        key = (apt_code, nome_norm)
        if key in self.tariffe:
            return self.tariffe[key]
        
        # Cerca con match parziale del nome (case-insensitive)
        for (apt, name), tariffa in self.tariffe.items():
            if apt == apt_code and nome_norm.lower() in name.lower() or name.lower() in nome_norm.lower():
                return tariffa
        
        return None
    
    def get_tariffa_base(self, aeroporto: str, nome: str) -> Optional[float]:
        """Ottiene la tariffa base per un collaboratore"""
        tariffa = self.get_tariffa(aeroporto, nome)
        return tariffa.base_eur if tariffa else None
    
    def get_tariffa_extra(self, aeroporto: str, nome: str) -> Optional[float]:
        """Ottiene la tariffa extra per ora per un collaboratore"""
        tariffa = self.get_tariffa(aeroporto, nome)
        return tariffa.extra_eur_per_h if tariffa else None
    
    def get_durata_base(self, aeroporto: str, nome: str) -> Optional[float]:
        """Ottiene la durata base in ore per un collaboratore"""
        tariffa = self.get_tariffa(aeroporto, nome)
        return tariffa.durata_base_h if tariffa else None
    
    def get_notturno_perc(self, aeroporto: str, nome: str) -> Optional[float]:
        """Ottiene la percentuale notturna per un collaboratore"""
        tariffa = self.get_tariffa(aeroporto, nome)
        return tariffa.notturno_perc if tariffa else None
    
    def get_festivo_perc(self, aeroporto: str, nome: str) -> Optional[float]:
        """Ottiene la percentuale festiva per un collaboratore"""
        tariffa = self.get_tariffa(aeroporto, nome)
        return tariffa.festivo_perc if tariffa else None


# Istanza globale (lazy loading)
_tariffe_manager: Optional[TariffeManager] = None


def get_tariffe_manager(file_path: Optional[str] = None) -> TariffeManager:
    """
    Ottiene l'istanza globale del gestore tariffe.
    
    Args:
        file_path: Percorso del file Excel. Se None, usa il percorso di default.
    
    Returns:
        TariffeManager
    """
    global _tariffe_manager
    
    if _tariffe_manager is None:
        if file_path is None:
            # Percorso di default relativo a questo file
            default_path = Path(__file__).parent / 'TARIFFE COLLABORATORI 2026 DEF.xlsx'
            file_path = str(default_path)
        _tariffe_manager = TariffeManager(file_path)
    
    return _tariffe_manager


def calcola_tariffa_collaboratore(
    aeroporto: str,
    nome: str,
    durata_min: float,
    extra_min: float = 0.0,
    minuti_notturni: float = 0.0,
    is_festivo: bool = False,
    tour_operator: Optional[str] = None
) -> Dict[str, float]:
    """
    Calcola le tariffe per un collaboratore basandosi sulle tariffe specifiche.
    
    Args:
        aeroporto: Codice aeroporto (es. 'VRN', 'FCO')
        nome: Nome del collaboratore
        durata_min: Durata totale del turno in minuti
        extra_min: Minuti extra oltre la durata base
        minuti_notturni: Minuti lavorati in fascia notturna
        is_festivo: Se il giorno è festivo
        tour_operator: Tour operator (opzionale, per tariffe specifiche TO)
    
    Returns:
        Dizionario con: base_eur, extra_eur, notte_eur, totale_eur
    """
    tm = get_tariffe_manager()
    tariffa = tm.get_tariffa(aeroporto, nome, tour_operator)
    
    # Fallback a tariffe default se non trovata
    if tariffa is None:
        # Usa tariffe default per aeroporto (se disponibili) o tariffe generiche
        base_eur = 58.0  # Default
        durata_base_h = 3.0  # Default
        extra_eur_per_h = 12.0  # Default
        notturno_perc = 0.15  # Default +15%
        festivo_perc = 0.20  # Default +20%
    else:
        base_eur = tariffa.base_eur or 58.0
        durata_base_h = tariffa.durata_base_h or 3.0
        extra_eur_per_h = tariffa.extra_eur_per_h or 12.0
        notturno_perc = tariffa.notturno_perc or 0.15
        festivo_perc = tariffa.festivo_perc or 0.20
    
    # Calcola base: se durata <= durata_base, usa base_eur, altrimenti pro-rata
    durata_h = durata_min / 60.0
    if durata_h <= durata_base_h:
        base = base_eur
    else:
        # Pro-rata: base + (durata_extra) * (base_eur / durata_base_h)
        base = base_eur + (durata_h - durata_base_h) * (base_eur / durata_base_h)
    
    # Calcola extra
    if extra_min > 0:
        extra = (extra_min / 60.0) * extra_eur_per_h
    else:
        extra = 0.0
    
    # Calcola notturno: proporzionale alla parte notturna
    if minuti_notturni > 0:
        # Valore orario del turno
        valore_orario = base / durata_base_h if durata_base_h > 0 else 0.0
        ore_notturne = minuti_notturni / 60.0
        valore_parte_notturna = valore_orario * ore_notturne
        notte = valore_parte_notturna * notturno_perc
    else:
        notte = 0.0
    
    # Calcola totale lordo
    subtotale = base + extra + notte
    if is_festivo:
        totale_lordo = subtotale * (1 + festivo_perc)
    else:
        totale_lordo = subtotale
    
    # Applica scorporo in base al regime per ottenere il netto
    # Le tariffe nel file Excel sono sempre al lordo
    regime = tariffa.regime if tariffa else None
    
    def scorpora_netto(lordo: float, regime_val: Optional[str]) -> float:
        """
        Scorpora il lordo per ottenere il netto in base al regime.
        
        IMPORTANTE: Le tariffe nel file Excel hanno significati diversi per regime:
        - Partita IVA: le tariffe sono già al NETTO (non serve scorporo) -> Netto = Lordo
        - Ritenuta d'acconto: le tariffe sono al lordo, applica ritenuta 20% -> Netto = Lordo * 0.80
        - Altro/None: assume ritenuta d'acconto 20%
        """
        if not regime_val:
            # Default: assume ritenuta d'acconto 20%
            return lordo * 0.80
        
        regime_str = str(regime_val).strip().upper()
        
        if 'PARTITA IVA' in regime_str or 'P.IVA' in regime_str or 'P IVA' in regime_str:
            # Partita IVA: le tariffe nel file Excel sono già al NETTO
            # Non serve scorporo IVA, restituisci il valore così com'è
            return lordo
        elif 'RITENUTA' in regime_str or 'ACCONTO' in regime_str:
            # Ritenuta d'acconto: le tariffe sono al lordo, applica ritenuta 20%
            return lordo * 0.80
        else:
            # Default: assume ritenuta d'acconto 20%
            return lordo * 0.80
    
    # Calcola valori netti
    base_netto = scorpora_netto(base, regime)
    extra_netto = scorpora_netto(extra, regime)
    notte_netto = scorpora_netto(notte, regime)
    totale_netto = scorpora_netto(totale_lordo, regime)
    
    return {
        'base_eur': round(base_netto, 2),
        'extra_eur': round(extra_netto, 2),
        'notte_eur': round(notte_netto, 2),
        'totale_eur': round(totale_netto, 2)
    }


def create_collaboratori_sheet(
    detail_df: pd.DataFrame,
    holiday_dates: Optional[set] = None
) -> pd.DataFrame:
    """
    Crea foglio con calcoli per collaboratori per tutti gli aeroporti.
    Usa le tariffe specifiche dal file Excel.
    
    Args:
        detail_df: DataFrame con i dettagli dei blocchi (deve avere colonne: APT, ASSISTENTE, DATA, 
                   DURATA_TURNO_MIN, EXTRA_MIN, NOTTE_MIN, TOUR OPERATOR)
        holiday_dates: Set di date festive (opzionale, se None usa festivi italiani 2025)
    
    Returns:
        DataFrame con i totali per collaboratore
    """
    if detail_df.empty:
        return pd.DataFrame()
    
    if 'ASSISTENTE' not in detail_df.columns:
        return pd.DataFrame()
    
    # Rimuovi righe senza assistente
    df_with_assist = detail_df[detail_df['ASSISTENTE'].notna() & (detail_df['ASSISTENTE'] != '')].copy()
    
    if df_with_assist.empty:
        return pd.DataFrame()
    
    # Festivi
    if holiday_dates is None:
        # Usa festivi italiani 2025
        try:
            from dateutil.easter import easter
        except ImportError:
            def easter(year: int) -> date:
                a = year % 19
                b = year // 100
                c = year % 100
                d = (19 * a + b - b // 4 - ((b - (b + 8) // 25 + 1) // 3) + 15) % 30
                e = (32 + 2 * (b % 4) + 2 * (c // 4) - d - (c % 4)) % 7
                f = d + e - 7 * ((a + 11 * d + 22 * e) // 451) + 114
                month = f // 31
                day = (f % 31) + 1
                return date(year, month, day)
        
        holiday_dates = {
            date(2025, 1, 1), date(2025, 1, 6), date(2025, 4, 25),
            date(2025, 5, 1), date(2025, 6, 2), date(2025, 8, 15),
            date(2025, 11, 1), date(2025, 12, 8), date(2025, 12, 25), date(2025, 12, 26)
        }
        easter_2025 = easter(2025)
        holiday_dates.add(easter_2025)
        holiday_dates.add(easter_2025 + timedelta(days=1))
    
    def is_festivo(data_str):
        """Verifica se la data è festiva"""
        try:
            dt = pd.to_datetime(data_str, dayfirst=True)
            return dt.date() in holiday_dates
        except:
            return False
    
    # Calcola per ogni riga
    rows_collaboratori = []
    for _, row in df_with_assist.iterrows():
        assistente = str(row['ASSISTENTE']).strip()
        apt = str(row['APT']).strip() if 'APT' in row.index else ''
        tour_operator = str(row.get('TOUR OPERATOR', '')).strip() if 'TOUR OPERATOR' in row.index else None
        
        # Estrai valori numerici
        try:
            durata_min = float(row.get('DURATA_TURNO_MIN', 0)) if pd.notna(row.get('DURATA_TURNO_MIN')) else 0.0
        except (ValueError, TypeError):
            durata_min = 0.0
        
        try:
            extra_min = float(row.get('EXTRA_MIN', 0)) if pd.notna(row.get('EXTRA_MIN')) else 0.0
        except (ValueError, TypeError):
            extra_min = 0.0
        
        try:
            minuti_notturni = float(row.get('NOTTE_MIN', 0)) if pd.notna(row.get('NOTTE_MIN')) else 0.0
        except (ValueError, TypeError):
            minuti_notturni = 0.0
        
        data_str = row.get('DATA', '')
        is_fest = is_festivo(data_str) if data_str else False
        
        # Calcola tariffe usando il modulo
        tariffe = calcola_tariffa_collaboratore(
            aeroporto=apt,
            nome=assistente,
            durata_min=durata_min,
            extra_min=extra_min,
            minuti_notturni=minuti_notturni,
            is_festivo=is_fest,
            tour_operator=tour_operator
        )
        
        rows_collaboratori.append({
            'DATA': data_str,
            'APT': apt,
            'TOUR OPERATOR': tour_operator if tour_operator else '',
            'ASSISTENTE': assistente,
            'BASE_EUR': tariffe['base_eur'],
            'EXTRA_EUR': tariffe['extra_eur'],
            'EXTRA_MIN': int(extra_min),
            'NOTTE_MIN': int(minuti_notturni),
            'NOTTE_EUR': tariffe['notte_eur'],
            'TOTALE_EUR': tariffe['totale_eur'],
        })
    
    df_calc = pd.DataFrame(rows_collaboratori)
    
    if df_calc.empty:
        return pd.DataFrame()
    
    # Raggruppa per DATA, APT, TOUR OPERATOR (se presente) e ASSISTENTE per dettaglio giorno per giorno
    groupby_cols = ['DATA', 'APT', 'ASSISTENTE']
    if 'TOUR OPERATOR' in df_calc.columns and df_calc['TOUR OPERATOR'].notna().any():
        groupby_cols = ['DATA', 'APT', 'TOUR OPERATOR', 'ASSISTENTE']
    
    collaboratori_totals = df_calc.groupby(groupby_cols).agg({
        'BASE_EUR': 'sum',
        'EXTRA_EUR': 'sum',
        'EXTRA_MIN': 'sum',
        'NOTTE_EUR': 'sum',
        'NOTTE_MIN': 'sum',
        'ASSISTENTE': 'count'  # Numero di blocchi
    }).round(2)
    
    # Calcola il totale come somma dei componenti (non sommare TOTALE_EUR)
    collaboratori_totals['TOTALE_EUR'] = (
        collaboratori_totals['BASE_EUR'] + 
        collaboratori_totals['EXTRA_EUR'] + 
        collaboratori_totals['NOTTE_EUR']
    ).round(2)
    
    collaboratori_totals.columns = ['Turno (€)', 'Extra (€)', 'Extra (min)', 'Notturno (€)', 'Notturno (min)', 'Blocchi', 'TOTALE (€)']
    collaboratori_totals = collaboratori_totals.reset_index()
    
    # Formatta Extra e Notturno in ore:minuti
    def format_hmm(minutes):
        if pd.isna(minutes) or minutes == 0:
            return "0:00"
        h = int(minutes // 60)
        m = int(minutes % 60)
        return f"{h}:{m:02d}"
    
    collaboratori_totals['Extra (h:mm)'] = collaboratori_totals['Extra (min)'].apply(format_hmm)
    collaboratori_totals['Notturno (h:mm)'] = collaboratori_totals['Notturno (min)'].apply(format_hmm)
    
    # Mantieni anche le colonne Extra (min) e Notturno (min) per i calcoli successivi
    # (le rimuoveremo solo alla fine se necessario)
    
    # Riordina colonne (mantieni anche Extra (min) e Notturno (min) per i calcoli)
    if 'TOUR OPERATOR' in collaboratori_totals.columns:
        result = collaboratori_totals[[
            'DATA', 'APT', 'TOUR OPERATOR', 'ASSISTENTE', 'Blocchi', 'Turno (€)', 'Extra (h:mm)', 'Extra (€)', 
            'Extra (min)', 'Notturno (h:mm)', 'Notturno (€)', 'Notturno (min)', 'TOTALE (€)'
        ]].copy()
    else:
        result = collaboratori_totals[[
            'DATA', 'APT', 'ASSISTENTE', 'Blocchi', 'Turno (€)', 'Extra (h:mm)', 'Extra (€)', 
            'Extra (min)', 'Notturno (h:mm)', 'Notturno (€)', 'Notturno (min)', 'TOTALE (€)'
        ]].copy()
    
    # Calcola totali per tour operator + aeroporto (anche righe senza collaboratore)
    # Questo include tutte le righe del detail_df originale
    df_all = detail_df.copy()
    
    # Calcola totali per DATA + APT + TOUR OPERATOR di tutte le righe (per dettaglio giorno per giorno)
    groupby_cols_tot = ['DATA', 'APT']
    if 'TOUR OPERATOR' in df_all.columns and df_all['TOUR OPERATOR'].notna().any():
        groupby_cols_tot = ['DATA', 'APT', 'TOUR OPERATOR']
    
    # Estrai totali dal detail_df (usando TOTALE_BLOCCO_EUR se disponibile)
    if 'TOTALE_BLOCCO_EUR' in df_all.columns:
        totali_per_to_apt = df_all.groupby(groupby_cols_tot).agg({
            'TOTALE_BLOCCO_EUR': 'sum',
            'TURNO_EUR': 'sum' if 'TURNO_EUR' in df_all.columns else lambda x: 0,
            'EXTRA_EUR': 'sum' if 'EXTRA_EUR' in df_all.columns else lambda x: 0,
            'NOTTE_EUR': 'sum' if 'NOTTE_EUR' in df_all.columns else lambda x: 0,
            'EXTRA_MIN': 'sum' if 'EXTRA_MIN' in df_all.columns else lambda x: 0,
            'NOTTE_MIN': 'sum' if 'NOTTE_MIN' in df_all.columns else lambda x: 0,
        }).round(2)
    else:
        # Se non c'è TOTALE_BLOCCO_EUR, calcola da TURNO_EUR + EXTRA_EUR + NOTTE_EUR
        totali_per_to_apt = df_all.groupby(groupby_cols_tot).agg({
            'TURNO_EUR': 'sum' if 'TURNO_EUR' in df_all.columns else lambda x: 0,
            'EXTRA_EUR': 'sum' if 'EXTRA_EUR' in df_all.columns else lambda x: 0,
            'NOTTE_EUR': 'sum' if 'NOTTE_EUR' in df_all.columns else lambda x: 0,
            'EXTRA_MIN': 'sum' if 'EXTRA_MIN' in df_all.columns else lambda x: 0,
            'NOTTE_MIN': 'sum' if 'NOTTE_MIN' in df_all.columns else lambda x: 0,
        }).round(2)
        if 'TURNO_EUR' in totali_per_to_apt.columns:
            totali_per_to_apt['TOTALE_BLOCCO_EUR'] = (
                totali_per_to_apt.get('TURNO_EUR', 0) + 
                totali_per_to_apt.get('EXTRA_EUR', 0) + 
                totali_per_to_apt.get('NOTTE_EUR', 0)
            )
    
    totali_per_to_apt = totali_per_to_apt.reset_index()
    
    # Calcola totali assegnati ai collaboratori (per DATA + APT + TOUR OPERATOR)
    if 'TOUR OPERATOR' in result.columns:
        totali_assegnati = result.groupby(['DATA', 'APT', 'TOUR OPERATOR']).agg({
            'TOTALE (€)': 'sum',
            'Turno (€)': 'sum',
            'Extra (€)': 'sum',
            'Notturno (€)': 'sum',
            'Extra (min)': 'sum',
            'Notturno (min)': 'sum',
            'Blocchi': 'sum',
        }).round(2).reset_index()
    else:
        totali_assegnati = result.groupby(['DATA', 'APT']).agg({
            'TOTALE (€)': 'sum',
            'Turno (€)': 'sum',
            'Extra (€)': 'sum',
            'Notturno (€)': 'sum',
            'Extra (min)': 'sum',
            'Notturno (min)': 'sum',
            'Blocchi': 'sum',
        }).round(2).reset_index()
    
    # Calcola differenze (non assegnate) per DATA + APT + TOUR OPERATOR
    if 'TOUR OPERATOR' in totali_per_to_apt.columns:
        # Merge per trovare differenze
        merged = totali_per_to_apt.merge(
            totali_assegnati,
            on=['DATA', 'APT', 'TOUR OPERATOR'],
            how='left',
            suffixes=('_tot', '_ass')
        )
    else:
        merged = totali_per_to_apt.merge(
            totali_assegnati,
            on=['DATA', 'APT'],
            how='left',
            suffixes=('_tot', '_ass')
        )
    
    # Calcola differenze (gestisci NaN correttamente)
    if 'TOTALE_BLOCCO_EUR' in merged.columns:
        totale_tot = merged['TOTALE_BLOCCO_EUR'].fillna(0)
    else:
        totale_tot = pd.Series([0] * len(merged))
    
    if 'TOTALE (€)' in merged.columns:
        totale_ass = merged['TOTALE (€)'].fillna(0)
    else:
        totale_ass = pd.Series([0] * len(merged))
    
    merged['TOTALE_NON_ASSEGNATO'] = (totale_tot - totale_ass).round(2)
    
    # Filtra solo le righe con differenza > 0.01 (per evitare errori di arrotondamento)
    non_assegnate = merged[merged['TOTALE_NON_ASSEGNATO'] > 0.01].copy()
    
    # Aggiungi righe per non assegnati (con DATA per dettaglio giorno per giorno)
    if not non_assegnate.empty:
        for _, row in non_assegnate.iterrows():
            data_str = row.get('DATA', '')
            apt = row['APT']
            tour_op = row.get('TOUR OPERATOR', '') if 'TOUR OPERATOR' in row.index else ''
            
            # Calcola i valori non assegnati (gestisci NaN correttamente)
            def safe_get(row, key, default=0):
                """Ottiene valore da row gestendo NaN"""
                val = row.get(key, default)
                if pd.isna(val):
                    return default
                try:
                    return float(val)
                except (ValueError, TypeError):
                    return default
            
            # Cerca colonne con suffissi dopo merge
            turno_tot_key = 'TURNO_EUR_tot' if 'TURNO_EUR_tot' in row.index else 'TURNO_EUR'
            turno_ass_key = 'Turno (€)_ass' if 'Turno (€)_ass' in row.index else 'Turno (€)'
            turno_tot = safe_get(row, turno_tot_key, 0)
            turno_ass = safe_get(row, turno_ass_key, 0)
            turno_non_ass = round(turno_tot - turno_ass, 2)
            
            extra_tot_key = 'EXTRA_EUR_tot' if 'EXTRA_EUR_tot' in row.index else 'EXTRA_EUR'
            extra_ass_key = 'Extra (€)_ass' if 'Extra (€)_ass' in row.index else 'Extra (€)'
            extra_tot = safe_get(row, extra_tot_key, 0)
            extra_ass = safe_get(row, extra_ass_key, 0)
            extra_non_ass = round(extra_tot - extra_ass, 2)
            
            notte_tot_key = 'NOTTE_EUR_tot' if 'NOTTE_EUR_tot' in row.index else 'NOTTE_EUR'
            notte_ass_key = 'Notturno (€)_ass' if 'Notturno (€)_ass' in row.index else 'Notturno (€)'
            notte_tot = safe_get(row, notte_tot_key, 0)
            notte_ass = safe_get(row, notte_ass_key, 0)
            notte_non_ass = round(notte_tot - notte_ass, 2)
            
            extra_min_tot_key = 'EXTRA_MIN_tot' if 'EXTRA_MIN_tot' in row.index else 'EXTRA_MIN'
            extra_min_ass_key = 'Extra (min)_ass' if 'Extra (min)_ass' in row.index else 'Extra (min)'
            extra_min_tot = safe_get(row, extra_min_tot_key, 0)
            extra_min_ass = safe_get(row, extra_min_ass_key, 0)
            extra_min_non_ass = int(extra_min_tot - extra_min_ass)
            
            notte_min_tot_key = 'NOTTE_MIN_tot' if 'NOTTE_MIN_tot' in row.index else 'NOTTE_MIN'
            notte_min_ass_key = 'Notturno (min)_ass' if 'Notturno (min)_ass' in row.index else 'Notturno (min)'
            notte_min_tot = safe_get(row, notte_min_tot_key, 0)
            notte_min_ass = safe_get(row, notte_min_ass_key, 0)
            notte_min_non_ass = int(notte_min_tot - notte_min_ass)
            
            blocchi_key = 'Blocchi_ass' if 'Blocchi_ass' in row.index else 'Blocchi'
            blocchi_non_ass = int(safe_get(row, blocchi_key, 0))
            
            # Inizializza variabili nette
            turno_non_ass_netto = 0.0
            extra_non_ass_netto = 0.0
            notte_non_ass_netto = 0.0
            extra_min_non_ass_tot = 0
            notte_min_non_ass_tot = 0
            
            # Conta blocchi non assegnati dal detail_df originale per quella data
            if 'TOUR OPERATOR' in df_all.columns:
                df_non_ass = df_all[
                    (df_all['DATA'].astype(str) == str(data_str)) &
                    (df_all['APT'] == apt) & 
                    (df_all['TOUR OPERATOR'].fillna('') == tour_op) &
                    (df_all['ASSISTENTE'].isna() | (df_all['ASSISTENTE'] == ''))
                ]
            else:
                df_non_ass = df_all[
                    (df_all['DATA'].astype(str) == str(data_str)) &
                    (df_all['APT'] == apt) &
                    (df_all['ASSISTENTE'].isna() | (df_all['ASSISTENTE'] == ''))
                ]
            
            if not df_non_ass.empty:
                blocchi_non_ass = len(df_non_ass)
                
                # Calcola valori NETTI per blocchi non assegnati usando le tariffe collaboratori
                # Per ogni blocco non assegnato, calcola il netto usando una tariffa di default per l'aeroporto
                turno_non_ass_netto = 0.0
                extra_non_ass_netto = 0.0
                notte_non_ass_netto = 0.0
                extra_min_non_ass_tot = 0
                notte_min_non_ass_tot = 0
                
                tm = get_tariffe_manager()
                for _, blocco_row in df_non_ass.iterrows():
                    durata_blocco = float(blocco_row.get('DURATA_TURNO_MIN', 0)) if pd.notna(blocco_row.get('DURATA_TURNO_MIN')) else 0.0
                    extra_blocco = float(blocco_row.get('EXTRA_MIN', 0)) if pd.notna(blocco_row.get('EXTRA_MIN')) else 0.0
                    notte_blocco = float(blocco_row.get('NOTTE_MIN', 0)) if pd.notna(blocco_row.get('NOTTE_MIN')) else 0.0
                    
                    # Cerca una tariffa di default per l'aeroporto (prima tariffa disponibile)
                    # Oppure usa la tariffa del primo collaboratore assegnato per quella data/aeroporto
                    tariffa_default = None
                    if 'TOUR OPERATOR' in result.columns:
                        df_ass_same_day = result[
                            (result['DATA'].astype(str) == str(data_str)) &
                            (result['APT'] == apt) &
                            (result['TOUR OPERATOR'] == tour_op) &
                            (result['ASSISTENTE'] != 'NON ASSEGNATO')
                        ]
                    else:
                        df_ass_same_day = result[
                            (result['DATA'].astype(str) == str(data_str)) &
                            (result['APT'] == apt) &
                            (result['ASSISTENTE'] != 'NON ASSEGNATO')
                        ]
                    
                    if not df_ass_same_day.empty:
                        # Usa la tariffa del primo collaboratore assegnato per quella data
                        primo_assistente = df_ass_same_day.iloc[0]['ASSISTENTE']
                        tariffa_default = tm.get_tariffa(apt, primo_assistente, tour_op if tour_op else None)
                    
                    if not tariffa_default:
                        # Cerca qualsiasi tariffa per quell'aeroporto
                        for (apt_key, nome_key), tariffa in tm.tariffe.items():
                            if apt_key == apt:
                                tariffa_default = tariffa
                                break
                    
                    if tariffa_default:
                        # Calcola netto usando la tariffa trovata
                        is_fest_blocco = is_festivo(data_str) if data_str else False
                        tariffe_blocco = calcola_tariffa_collaboratore(
                            aeroporto=apt,
                            nome=tariffa_default.nome,  # Usa il nome della tariffa di default
                            durata_min=durata_blocco,
                            extra_min=extra_blocco,
                            minuti_notturni=notte_blocco,
                            is_festivo=is_fest_blocco,
                            tour_operator=tour_op if tour_op else None
                        )
                        turno_non_ass_netto += tariffe_blocco['base_eur']
                        extra_non_ass_netto += tariffe_blocco['extra_eur']
                        notte_non_ass_netto += tariffe_blocco['notte_eur']
                        extra_min_non_ass_tot += int(extra_blocco)
                        notte_min_non_ass_tot += int(notte_blocco)
                    else:
                        # Se non trovi tariffa, usa la differenza lorda (fallback)
                        turno_non_ass_netto += turno_non_ass
                        extra_non_ass_netto += extra_non_ass
                        notte_non_ass_netto += notte_non_ass
                        extra_min_non_ass_tot += int(extra_min_non_ass)
                        notte_min_non_ass_tot += int(notte_min_non_ass)
            else:
                # Se non ci sono blocchi non assegnati nel detail_df, usa la differenza
                # ma converti in netto usando una tariffa media
                tm = get_tariffe_manager()
                tariffa_media = None
                if 'TOUR OPERATOR' in result.columns:
                    df_ass_same_day = result[
                        (result['DATA'].astype(str) == str(data_str)) &
                        (result['APT'] == apt) &
                        (result['TOUR OPERATOR'] == tour_op) &
                        (result['ASSISTENTE'] != 'NON ASSEGNATO')
                    ]
                else:
                    df_ass_same_day = result[
                        (result['DATA'].astype(str) == str(data_str)) &
                        (result['APT'] == apt) &
                        (result['ASSISTENTE'] != 'NON ASSEGNATO')
                    ]
                
                if not df_ass_same_day.empty:
                    primo_assistente = df_ass_same_day.iloc[0]['ASSISTENTE']
                    tariffa_media = tm.get_tariffa(apt, primo_assistente, tour_op if tour_op else None)
                
                if tariffa_media and 'Partita IVA' in str(tariffa_media.regime):
                    # Se Partita IVA, i valori sono già netti, quindi usa direttamente la differenza
                    turno_non_ass_netto = turno_non_ass
                    extra_non_ass_netto = extra_non_ass
                    notte_non_ass_netto = notte_non_ass
                else:
                    # Se Ritenuta d'acconto, applica scorporo
                    turno_non_ass_netto = turno_non_ass * 0.80
                    extra_non_ass_netto = extra_non_ass * 0.80
                    notte_non_ass_netto = notte_non_ass * 0.80
                
                extra_min_non_ass_tot = extra_min_non_ass
                notte_min_non_ass_tot = notte_min_non_ass
            
            if row['TOTALE_NON_ASSEGNATO'] > 0.01:  # Solo se c'è una differenza significativa
                # Per NON ASSEGNATO, tutti i valori sono zero perché non possiamo calcolare senza sapere il collaboratore
                row_non_ass = {
                    'DATA': data_str,
                    'APT': apt,
                    'ASSISTENTE': 'NON ASSEGNATO',
                    'Blocchi': blocchi_non_ass if 'blocchi_non_ass' in locals() else 0,
                    'Turno (€)': 0.00,
                    'Extra (h:mm)': '0:00',
                    'Extra (€)': 0.00,
                    'Notturno (h:mm)': '0:00',
                    'Notturno (€)': 0.00,
                    'TOTALE (€)': 0.00,
                }
                if 'TOUR OPERATOR' in result.columns:
                    row_non_ass['TOUR OPERATOR'] = tour_op
                
                # Aggiungi come nuovo DataFrame e concatena
                result = pd.concat([result, pd.DataFrame([row_non_ass])], ignore_index=True)
    
    # Ordina per data, aeroporto, tour operator e totale decrescente
    sort_cols = ['DATA', 'APT']
    if 'TOUR OPERATOR' in result.columns:
        sort_cols = ['DATA', 'APT', 'TOUR OPERATOR']
    sort_cols.append('TOTALE (€)')
    result = result.sort_values(sort_cols, ascending=[True, True, True, False] if len(sort_cols) > 3 else [True, True, False])
    
    # Rimuovi colonne Extra (min) e Notturno (min) dal risultato finale (mantieni solo h:mm)
    cols_to_keep = ['DATA', 'APT', 'ASSISTENTE', 'Blocchi', 'Turno (€)', 'Extra (h:mm)', 'Extra (€)', 
                    'Notturno (h:mm)', 'Notturno (€)', 'TOTALE (€)']
    if 'TOUR OPERATOR' in result.columns:
        # Inserisci TOUR OPERATOR dopo APT
        idx = cols_to_keep.index('APT') + 1
        cols_to_keep.insert(idx, 'TOUR OPERATOR')
    
    # Mantieni solo le colonne presenti
    cols_to_keep = [c for c in cols_to_keep if c in result.columns]
    result = result[cols_to_keep].copy()
    
    return result


def create_airport_complete_sheets(
    detail_df: pd.DataFrame,
    totals_df: pd.DataFrame,
    discr_df: pd.DataFrame,
    holiday_dates: Optional[set] = None
) -> Dict[str, Dict[str, pd.DataFrame]]:
    """
    Crea fogli completi per ogni aeroporto con tutti i dati corretti.
    
    Per ogni aeroporto crea:
    - DettagliBlocchi: tutti i blocchi per quell'aeroporto
    - Totali: totali aggregati per quell'aeroporto
    - Collaboratori: calcoli collaboratori per quell'aeroporto
    - Riepilogo: riepilogo giornaliero per quell'aeroporto
    
    Args:
        detail_df: DataFrame con i dettagli dei blocchi
        totals_df: DataFrame con i totali del periodo
        discr_df: DataFrame con le discrepanze
        holiday_dates: Set di date festive (opzionale)
    
    Returns:
        Dizionario {aeroporto: {nome_foglio: DataFrame}}
    """
    if detail_df.empty:
        return {}
    
    if holiday_dates is None:
        holiday_dates = get_italian_holidays_2025()
    
    result = {}
    
    # Ottieni lista aeroporti unici
    aeroporti = sorted(detail_df['APT'].dropna().unique())
    
    for apt in aeroporti:
        apt_dict = {}
        
        # Filtra dati per aeroporto
        df_apt = detail_df[detail_df['APT'] == apt].copy()
        
        if df_apt.empty:
            continue
        
        # 1. DETTAGLI BLOCCHI per aeroporto
        # Ordina colonne per leggibilità
        cols_dettaglio = [
            "DATA", "TOUR OPERATOR", "ASSISTENTE", "TURNO_NORMALIZZATO",
            "INIZIO_DT", "FINE_DT", "DURATA_TURNO_MIN",
            "TURNO_EUR", "EXTRA_MIN", "EXTRA_EUR", "NOTTE_MIN", "NOTTE_EUR",
            "FESTIVO", "TOTALE_BLOCCO_EUR"
        ]
        
        # Aggiungi colonne opzionali se presenti
        optional_cols = ["COMPAGNIA", "ATD_SCELTO", "STD_SCELTO", "NO_DEC", "ERRORE"]
        for col in optional_cols:
            if col in df_apt.columns:
                cols_dettaglio.append(col)
        
        # Mantieni solo colonne presenti
        cols_dettaglio = [c for c in cols_dettaglio if c in df_apt.columns]
        df_dettaglio = df_apt[cols_dettaglio].copy()
        
        # Ordina per data
        df_dettaglio = df_dettaglio.sort_values(['DATA', 'TOUR OPERATOR'] if 'TOUR OPERATOR' in df_dettaglio.columns else ['DATA'])
        
        apt_dict['DettagliBlocchi'] = df_dettaglio
        
        # 2. TOTALI per aeroporto
        # Raggruppa per tour operator e calcola totali
        if 'TOUR OPERATOR' in df_apt.columns:
            groupby_cols = ['TOUR OPERATOR']
        else:
            groupby_cols = []
        
        if not df_apt.empty:
            # Se non ci sono colonne per raggruppare, crea un totale unico
            if not groupby_cols:
                # Crea un totale unico senza raggruppamento
                totals_apt = pd.DataFrame({
                    'TURNO_EUR': [df_apt['TURNO_EUR'].sum()],
                    'EXTRA_EUR': [df_apt['EXTRA_EUR'].sum()],
                    'NOTTE_EUR': [df_apt['NOTTE_EUR'].sum()],
                    'TOTALE_BLOCCO_EUR': [df_apt['TOTALE_BLOCCO_EUR'].sum()],
                    'EXTRA_MIN': [df_apt['EXTRA_MIN'].sum()],
                    'NOTTE_MIN': [df_apt['NOTTE_MIN'].sum()],
                    'DURATA_TURNO_MIN': [df_apt['DURATA_TURNO_MIN'].sum()],
                }).round(2)
            else:
                totals_apt = df_apt.groupby(groupby_cols).agg({
                'TURNO_EUR': 'sum',
                'EXTRA_EUR': 'sum',
                'NOTTE_EUR': 'sum',
                'TOTALE_BLOCCO_EUR': 'sum',
                'EXTRA_MIN': 'sum',
                'NOTTE_MIN': 'sum',
                'DURATA_TURNO_MIN': 'sum',
            }).round(2)
            
            totals_apt = totals_apt.reset_index()
            
            # Formatta minuti in h:mm
            def format_hmm(minutes):
                if pd.isna(minutes) or minutes == 0:
                    return "0:00"
                h = int(minutes // 60)
                m = int(minutes % 60)
                return f"{h}:{m:02d}"
            
            totals_apt['EXTRA_H:MM'] = totals_apt['EXTRA_MIN'].apply(format_hmm)
            totals_apt['NOTTE_H:MM'] = totals_apt['NOTTE_MIN'].apply(format_hmm)
            totals_apt['DURATA_H:MM'] = totals_apt['DURATA_TURNO_MIN'].apply(format_hmm)
            
            # Riordina colonne
            cols_totals = ['TURNO_EUR', 'EXTRA_H:MM', 'EXTRA_EUR', 'NOTTE_H:MM', 'NOTTE_EUR', 'TOTALE_BLOCCO_EUR']
            if 'TOUR OPERATOR' in totals_apt.columns:
                cols_totals = ['TOUR OPERATOR'] + cols_totals
            
            totals_apt.columns = ['Tour Operator' if c == 'TOUR OPERATOR' else 
                                 'Turno (€)' if c == 'TURNO_EUR' else
                                 'Extra (h:mm)' if c == 'EXTRA_H:MM' else
                                 'Extra (€)' if c == 'EXTRA_EUR' else
                                 'Notturno (h:mm)' if c == 'NOTTE_H:MM' else
                                 'Notturno (€)' if c == 'NOTTE_EUR' else
                                 'TOTALE (€)' if c == 'TOTALE_BLOCCO_EUR' else c
                                 for c in totals_apt.columns]
            
            cols_totals = [c for c in cols_totals if c in totals_apt.columns]
            apt_dict['Totali'] = totals_apt[cols_totals].copy()
        else:
            apt_dict['Totali'] = pd.DataFrame()
        
        # 3. COLLABORATORI per aeroporto
        try:
            collaboratori_sheet = create_collaboratori_sheet(df_apt, holiday_dates=holiday_dates)
            if not collaboratori_sheet.empty:
                apt_dict['Collaboratori'] = collaboratori_sheet
            else:
                apt_dict['Collaboratori'] = pd.DataFrame()
        except Exception as e:
            # In caso di errore, crea DataFrame vuoto
            apt_dict['Collaboratori'] = pd.DataFrame()
        
        # 4. RIEPILOGO GIORNALIERO per aeroporto
        if not df_apt.empty:
            groupby_cols_riep = ['DATA']
            if 'TOUR OPERATOR' in df_apt.columns:
                groupby_cols_riep.append('TOUR OPERATOR')
            
            riepilogo = df_apt.groupby(groupby_cols_riep).agg({
                'TURNO_EUR': 'sum',
                'EXTRA_EUR': 'sum',
                'NOTTE_EUR': 'sum',
                'TOTALE_BLOCCO_EUR': 'sum',
                'EXTRA_MIN': 'sum',
                'NOTTE_MIN': 'sum',
            }).round(2)
            
            riepilogo = riepilogo.reset_index()
            
            # Formatta minuti
            riepilogo['EXTRA_H:MM'] = riepilogo['EXTRA_MIN'].apply(format_hmm)
            riepilogo['NOTTE_H:MM'] = riepilogo['NOTTE_MIN'].apply(format_hmm)
            
            # Riordina colonne
            cols_riep = ['DATA', 'Turno (€)', 'Extra (h:mm)', 'Extra (€)', 'Notturno (h:mm)', 'Notturno (€)', 'TOTALE (€)']
            if 'TOUR OPERATOR' in riepilogo.columns:
                cols_riep = ['DATA', 'TOUR OPERATOR'] + [c for c in cols_riep if c != 'DATA']
                riepilogo.columns = ['Data' if c == 'DATA' else
                                    'Tour Operator' if c == 'TOUR OPERATOR' else
                                    'Turno (€)' if c == 'TURNO_EUR' else
                                    'Extra (h:mm)' if c == 'EXTRA_H:MM' else
                                    'Extra (€)' if c == 'EXTRA_EUR' else
                                    'Notturno (h:mm)' if c == 'NOTTE_H:MM' else
                                    'Notturno (€)' if c == 'NOTTE_EUR' else
                                    'TOTALE (€)' if c == 'TOTALE_BLOCCO_EUR' else c
                                    for c in riepilogo.columns]
            else:
                riepilogo.columns = ['Data' if c == 'DATA' else
                                    'Turno (€)' if c == 'TURNO_EUR' else
                                    'Extra (h:mm)' if c == 'EXTRA_H:MM' else
                                    'Extra (€)' if c == 'EXTRA_EUR' else
                                    'Notturno (h:mm)' if c == 'NOTTE_H:MM' else
                                    'Notturno (€)' if c == 'NOTTE_EUR' else
                                    'TOTALE (€)' if c == 'TOTALE_BLOCCO_EUR' else c
                                    for c in riepilogo.columns]
            
            cols_riep = [c for c in cols_riep if c in riepilogo.columns]
            apt_dict['Riepilogo'] = riepilogo[cols_riep].copy()
        else:
            apt_dict['Riepilogo'] = pd.DataFrame()
        
        # 5. DISCREPANZE per aeroporto (se presenti)
        if not discr_df.empty and 'APT' in discr_df.columns:
            discr_apt = discr_df[discr_df['APT'] == apt].copy()
            if not discr_apt.empty:
                apt_dict['Discrepanze'] = discr_apt
            else:
                apt_dict['Discrepanze'] = pd.DataFrame()
        else:
            apt_dict['Discrepanze'] = pd.DataFrame()
        
        result[apt] = apt_dict
    
    return result
