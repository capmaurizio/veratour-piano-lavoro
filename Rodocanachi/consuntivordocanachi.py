#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IOT VIAGGI SRL — Calcolatore blocchi
Contratto 2025: convocazione STD-2h30, extra €18/h da STD, notturno 22-06 +20%, festivo +30%
"""
from __future__ import annotations
import re
from dataclasses import dataclass, field
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Tuple, Iterable
import numpy as np
import pandas as pd

try:
    from dateutil.easter import easter
except ImportError:
    def easter(year):
        a=year%19; b=year//100; c=year%100; d=b//4; e=b%4
        f=(b+8)//25; g=(b-f+1)//3; h=(19*a+b-d-g+15)%30
        i=c//4; k=c%4; l=(32+2*e+2*i-h-k)%7; m=(a+11*h+22*l)//451
        month=(h+l-7*m+114)//31; day=((h+l-7*m+114)%31)+1
        return date(year,month,day)

# ── Tariffe IOT ──────────────────────────────────────────────────────────────
TARIFFE_BASE = {
    "BGY":90.0,"VRN":90.0,"BLQ":90.0,"LIN":90.0,"MXP":90.0,
    "TRN":90.0,"NAP":90.0,"BRI":90.0,"CTA":90.0,"PMO":90.0,
    "VCE":100.0,"FCO":100.0,"PSA":100.0,
}
# Tariffa notturna €/min = tariffa_base / 150 min * 20%
TARIFFE_NOTTE = {k: round(v/150*0.20, 6) for k,v in TARIFFE_BASE.items()}

@dataclass
class RoundingPolicy:
    mode: str; step_min: int
    def apply(self, minutes):
        if minutes is None: return None
        m=self.mode.upper(); x=float(minutes)
        if m=="NONE" or self.step_min<=0: return int(x)
        s=float(self.step_min)
        if m=="FLOOR": return int(np.floor(x/s)*s)
        if m=="CEIL":  return int(np.ceil(x/s)*s)
        if m=="NEAREST": return int(np.round(x/s)*s)
        return int(x)

@dataclass
class CalcConfig:
    apt_filter: Optional[List[str]] = None
    to_keyword: str = "rodocanachi"
    rounding_extra: RoundingPolicy = field(default_factory=lambda: RoundingPolicy("NONE",5))
    rounding_night: RoundingPolicy = field(default_factory=lambda: RoundingPolicy("NONE",5))
    holiday_dates: Optional[set] = None
    rate_extra_per_h: float = 18.0
    durata_base_min: int = 150
    festivo_multiplier: float = 1.30
    include_4oct: bool = True  # Rodocanachi include 4 ottobre

# ── Utilities ────────────────────────────────────────────────────────────────
def _ns(s): return re.sub(r"\s+"," ",str(s).strip())

def parse_excel_date(x):
    if pd.isna(x): return None
    if isinstance(x,pd.Timestamp): return x
    if isinstance(x,(datetime,date)): return pd.Timestamp(x)
    s=str(x).strip()
    if not s or s.lower() in ("nan","none",""): return None
    for fmt in ("%d/%m/%Y","%d-%m-%Y","%Y-%m-%d","%d.%m.%Y","%d/%m/%y"):
        try: return pd.Timestamp(datetime.strptime(s,fmt))
        except: pass
    try: return pd.to_datetime(s,dayfirst=True)
    except: return None

def parse_time_value(x):
    if x is None: return None
    try:
        if pd.isna(x): return None
    except: pass
    from datetime import time as _time
    if isinstance(x,_time): return (x.hour,x.minute)
    if isinstance(x,datetime): return (x.hour,x.minute)
    if hasattr(x,"total_seconds"):
        ts=int(x.total_seconds()); return (ts//3600,(ts%3600)//60)
    s=str(x).strip().replace(" ","")
    if not s or s.lower() in ("nan","none",""): return None
    m=re.match(r"^(\d{1,2})[.:](\d{2})$",s)
    if m:
        h,mm=int(m.group(1)),int(m.group(2))
        if 0<=h<=23 and 0<=mm<=59: return (h,mm)
    m=re.match(r"^(\d{3,4})$",s)
    if m:
        n=int(m.group(1)); h=n//100; mm=n%100
        if 0<=h<=23 and 0<=mm<=59: return (h,mm)
    return None

def to_dt(d,ts):
    h,m=map(int,ts.split(":")); return d.replace(hour=h,minute=m,second=0,microsecond=0)

def night_minutes(start,end):
    if pd.isna(start) or pd.isna(end) or start>=end: return 0
    total=0; cur=start
    while cur<end:
        nxt=min(cur+pd.Timedelta(minutes=1),end)
        if cur.hour>=22 or cur.hour<6: total+=1
        cur=nxt
    return total

def _add_holidays(h,year,include_4oct=False):
    for m,d in ((1,1),(1,6),(4,25),(5,1),(6,2),(8,15),(11,1),(12,8),(12,25),(12,26)):
        h.add(date(year,m,d))
    if include_4oct: h.add(date(year,10,4))
    e=easter(year); h.add(e); h.add(e+timedelta(days=1))

def get_holidays(include_4oct=False):
    h=set()
    for y in (2025,2026,2027): _add_holidays(h,y,include_4oct)
    return h

def normalize_cols(df):
    df=df.copy(); df.columns=[_ns(str(c)).upper() for c in df.columns]; return df

def find_col(df,patterns):
    cols=list(df.columns)
    for pat in patterns:
        rx=re.compile(pat,re.IGNORECASE)
        for c in cols:
            if rx.search(c): return c
    return None

def detect_columns(df):
    return {
        "data":      find_col(df,[r"^DATA$",r"\bDATE\b"]),
        "tour_operator": find_col(df,[r"TOUR\s*OPERATOR",r"^TO$",r"\bOPERATORE\b"]),
        "volo":      find_col(df,[r"^VOLO$",r"NUMERO\s*VOLO",r"FLIGHT"]),
        "destinazione": find_col(df,[r"^DEST\.?NE$",r"DESTINAZIONE"]),
        "apt":       find_col(df,[r"^APT$",r"\bAEROPORTO\b"]),
        "turno":     find_col(df,[r"^TURNO$",r"^TURNO\s*ASSISTENTE$"]),
        "inizio_turno": find_col(df,[r"inizio\s*turno",r"^inizio$"]),
        "fine_turno":   find_col(df,[r"fine\s*turno"]),
        "atd":       find_col(df,[r"^ATD$",r"\bORARIO\s*ATD\b"]),
        "std":       find_col(df,[r"^STD$",r"\bORARIO\s*STD\b"]),
        "importo":   find_col(df,[r"^IMPORTO$",r"\bTOTALE\b",r"^COSTO\s*$"]),
        "ore_extra": find_col(df,[r"\bORE\s*EXTRA\b",r"^EXTRA$"]),
        "notturno":  find_col(df,[r"^NOTTURNO$"]),
        "festivo":   find_col(df,[r"^FESTIVO$"]),
        "assistente":find_col(df,[r"^ASSISTENTE$"]),
    }

def is_truthy_festivo(v):
    if v is None: return False
    try:
        if pd.isna(v): return False
    except: pass
    s=str(v).strip().upper()
    return s in ("1","TRUE","SI","SÌ","YES","X","S")

def parse_eur(v):
    try:
        if pd.isna(v): return None
    except: pass
    s=re.sub(r"[€\s]","",str(v)).replace(",",".")
    try: return float(s)
    except: return None

@dataclass
class SourceRowRef:
    file:str; sheet:str; row_index:int; original_order:int

@dataclass
class BlockAgg:
    date:pd.Timestamp; apt:str
    turno_raw_ffill:str; turno_norm:str
    start_dt:pd.Timestamp; end_dt:pd.Timestamp
    no_dec:bool; first_source:SourceRowRef
    atd_list:List[pd.Timestamp]
    std_list:List[pd.Timestamp]
    atd_raw_list:List[str]=field(default_factory=list)
    festivo_flag:bool=False
    assistente:Optional[str]=None
    volo:Optional[str]=None
    destinazione:Optional[str]=None

def iter_sheets(fp):
    xls=pd.ExcelFile(fp)
    tgt=next((s for s in xls.sheet_names if s.upper().strip()=="PIANO VOLI"),None)
    for s in ([tgt] if tgt else xls.sheet_names):
        yield s, pd.read_excel(fp,sheet_name=s)

def _ss(v):
    try:
        if pd.isna(v): return ""
    except: pass
    s=str(v).strip()
    return "" if s.lower() in ("nan","none") else s

def process_files(input_files:List[str], cfg:CalcConfig):
    blocks:Dict={}; global_order=0
    for fp in input_files:
        for sheet,sdf0 in iter_sheets(fp):
            if sdf0 is None or sdf0.empty: continue
            sdf=normalize_cols(sdf0); cols=detect_columns(sdf)
            has_orario=(cols.get("inizio_turno") and cols.get("fine_turno")) or cols.get("turno")
            if not cols["data"] or not cols["apt"] or not has_orario: continue
            # Filter TO (case-insensitive)
            if cols["tour_operator"]:
                kw=cfg.to_keyword.strip().lower()
                mask=sdf[cols["tour_operator"]].astype(str).str.strip().str.lower().str.contains(kw,na=False)
                sdf=sdf[mask].copy()
                if sdf.empty: continue
            # Filter APT
            if cfg.apt_filter and cols["apt"]:
                pat="|".join(re.escape(a) for a in cfg.apt_filter)
                sdf=sdf[sdf[cols["apt"]].astype(str).str.contains(rf"\b({pat})\b",case=False,na=False)].copy()
                if sdf.empty: continue
            sdf["__date"]=sdf[cols["data"]].apply(parse_excel_date)
            sdf=sdf[sdf["__date"].notna()].copy()
            if sdf.empty: continue
            sdf["__sheet_row_order"]=np.arange(len(sdf),dtype=int)
            sdf["__global_order"]=np.arange(global_order,global_order+len(sdf),dtype=int)
            global_order+=len(sdf)

            # ── FORMATO 2026 (INIZIO TURNO / FINE TURNO) ──────────────────
            if cols.get("inizio_turno") and cols.get("fine_turno"):
                _ic=cols["inizio_turno"]; _fc=cols["fine_turno"]
                _tc=cols.get("tour_operator"); _ac=cols.get("assistente"); _sc=cols.get("std")
                sdf["__to_s"]=sdf[_tc].apply(_ss) if _tc else ""
                sdf["__as_s"]=sdf[_ac].apply(_ss) if _ac else ""
                sdf["__apt_s"]=sdf[cols["apt"]].apply(_ss)

                # Order-based slave pairing
                def _is_m(row):
                    v=row[_ic]
                    try:
                        if pd.isna(v): return False
                    except: pass
                    return str(v).strip().lower() not in ("","nan","none","nat")

                _last_m={}; _ini_v=[]; _fin_v=[]; _ass_v=[]
                for _,_row in sdf.iterrows():
                    _gb=str(_row["__date"])+"|"+_row["__to_s"]+"|"+_row["__apt_s"]
                    if _is_m(_row):
                        _last_m[_gb]={"ass":_row["__as_s"],"ini":_row[_ic],"fin":_row[_fc]}
                        _ini_v.append(_row[_ic]); _fin_v.append(_row[_fc]); _ass_v.append(_row["__as_s"])
                    else:
                        _m=_last_m.get(_gb)
                        if _m:
                            _ini_v.append(_m["ini"]); _fin_v.append(_m["fin"])
                            _ass_v.append(_m["ass"] if _m["ass"] else _row["__as_s"])
                        else:
                            _fb_i=np.nan; _fb_f=np.nan
                            if _sc and _sc in _row.index:
                                _sp=parse_time_value(_row[_sc])
                                if _sp:
                                    import datetime as _dt2
                                    _sm2=(_sp[0]*60+_sp[1]-150)%1440
                                    _fb_i=_dt2.time(_sm2//60,_sm2%60); _fb_f=_dt2.time(_sp[0],_sp[1])
                            _ini_v.append(_fb_i); _fin_v.append(_fb_f); _ass_v.append(_row["__as_s"])

                sdf["__ini_f"]=_ini_v; sdf["__fin_f"]=_fin_v; sdf["__as_s"]=_ass_v
                sdf=sdf[sdf["__ini_f"].notna()&sdf["__fin_f"].notna()].copy()
                if sdf.empty: continue

                def _ptc(v):
                    try:
                        if pd.isna(v): return None
                    except: pass
                    return parse_time_value(v)

                sdf["__shm"]=sdf["__ini_f"].apply(_ptc)
                sdf["__ehm"]=sdf["__fin_f"].apply(_ptc)
                sdf=sdf[sdf["__shm"].notna()&sdf["__ehm"].notna()].copy()
                if sdf.empty: continue

                sdf["__start_dt"]=sdf.apply(lambda r:to_dt(r["__date"],f"{r['__shm'][0]:02d}:{r['__shm'][1]:02d}"),axis=1)
                sdf["__end_dt"]=sdf.apply(lambda r:to_dt(r["__date"],f"{r['__ehm'][0]:02d}:{r['__ehm'][1]:02d}"),axis=1)
                ov=sdf["__end_dt"]<sdf["__start_dt"]
                sdf.loc[ov,"__end_dt"]+=pd.Timedelta(days=1)
                _fvc=cols.get("festivo")
                sdf["__festivo"]=sdf[_fvc].apply(is_truthy_festivo) if _fvc else False

                for _i,_r in sdf.iterrows():
                    _d=_r["__date"]; _apt=_ss(_r[cols["apt"]])
                    _to=_ss(_r[_tc]) if _tc else ""; _as=_r["__as_s"]
                    _sh,_sm=_r["__shm"]; _eh,_em=_r["__ehm"]
                    _tn=f"{_sh:02d}:{_sm:02d}-{_eh:02d}:{_em:02d}"
                    _key=(_d,_to,_apt,_as,f"{_sh:02d}:{_sm:02d}")

                    _atdt=[]
                    atd_raw_val = ""
                    if cols.get("atd"):
                        atd_raw_val = _ss(_r[cols["atd"]])
                        for _hh,_mm in _extract_atd(_r[cols["atd"]]):
                            _tdt=_d+pd.Timedelta(hours=_hh,minutes=_mm)
                            if _tdt<_r["__start_dt"]: _tdt+=pd.Timedelta(days=1)
                            _atdt.append(_tdt)
                    _stdt=[]
                    if _sc and _sc in _r.index:
                        _sp=parse_time_value(_r[_sc])
                        if _sp:
                            _tdt=_d+pd.Timedelta(hours=_sp[0],minutes=_sp[1])
                            if _tdt<_r["__start_dt"]: _tdt+=pd.Timedelta(days=1)
                            _stdt.append(_tdt)

                    _src=SourceRowRef(fp,sheet,int(_r["__sheet_row_order"]),int(_r["__global_order"]))
                    _vc=cols.get("volo"); _dc=cols.get("destinazione")
                    if _key not in blocks:
                        blocks[_key]=BlockAgg(
                            date=_d,apt=_apt,turno_raw_ffill=_tn,turno_norm=_tn,
                            start_dt=_r["__start_dt"],end_dt=_r["__end_dt"],
                            no_dec=False,first_source=_src,
                            atd_list=_atdt.copy(),std_list=_stdt.copy(),
                            atd_raw_list=[atd_raw_val] if atd_raw_val else [],
                            festivo_flag=bool(_r["__festivo"]),
                            assistente=_as or None,
                            volo=_ss(_r[_vc]) if _vc and _vc in _r.index else None,
                            destinazione=_ss(_r[_dc]) if _dc and _dc in _r.index else None,
                        )
                    else:
                        b=blocks[_key]
                        if atd_raw_val and atd_raw_val not in b.atd_raw_list:
                            b.atd_raw_list.append(atd_raw_val)
                        b.atd_list.extend(_atdt); b.std_list.extend(_stdt)
                        b.festivo_flag=b.festivo_flag or bool(_r["__festivo"])
                        if _src.original_order<b.first_source.original_order: b.first_source=_src
                continue  # nuovo formato processato

            # ── VECCHIO FORMATO (TURNO stringa) ───────────────────────────
            _tc2=cols.get("turno")
            if not _tc2: continue
            sdf["__tffill"]=sdf[_tc2].replace("",np.nan).ffill()
            for idx,r in sdf.iterrows():
                d=r["__date"]; apt=_ss(r[cols["apt"]])
                tf=_ss(r.get("__tffill",""))
                ini,fin=_parse_turno_str(tf)
                if not ini or not fin: continue
                sdt=to_dt(d,ini); edt=to_dt(d,fin)
                if edt<sdt: edt+=pd.Timedelta(days=1)
                ass=_ss(r[cols["assistente"]]) if cols.get("assistente") else ""
                to_s=_ss(r[cols["tour_operator"]]) if cols.get("tour_operator") else ""
                key=(d,to_s,apt,ass,ini)
                src=SourceRowRef(fp,sheet,int(r["__sheet_row_order"]),int(r["__global_order"]))
                atd_list=[]
                atd_raw_val = ""
                if cols.get("atd"):
                    atd_raw_val = _ss(r[cols["atd"]])
                    for hh,mm in _extract_atd(r[cols["atd"]]):
                        t=d+pd.Timedelta(hours=hh,minutes=mm)
                        if t<sdt: t+=pd.Timedelta(days=1)
                        atd_list.append(t)
                std_list=[]
                if cols.get("std"):
                    sp=parse_time_value(r[cols["std"]])
                    if sp:
                        t=d+pd.Timedelta(hours=sp[0],minutes=sp[1])
                        if t<sdt: t+=pd.Timedelta(days=1)
                        std_list.append(t)
                if key not in blocks:
                    blocks[key]=BlockAgg(date=d,apt=apt,turno_raw_ffill=tf,turno_norm=f"{ini}-{fin}",
                        start_dt=sdt,end_dt=edt,no_dec=False,first_source=src,
                        atd_list=atd_list,std_list=std_list,assistente=ass or None,
                        atd_raw_list=[atd_raw_val] if atd_raw_val else [])
                else:
                    b=blocks[key]; b.atd_list.extend(atd_list); b.std_list.extend(std_list)
                    if atd_raw_val and atd_raw_val not in b.atd_raw_list:
                        b.atd_raw_list.append(atd_raw_val)
                    if src.original_order<b.first_source.original_order: b.first_source=src

    # ── Calcola output ────────────────────────────────────────────────────
    hols=cfg.holiday_dates if cfg.holiday_dates else get_holidays(cfg.include_4oct)
    rows=[]
    for key,b in sorted(blocks.items(),key=lambda kv:kv[1].first_source.original_order if kv[1].first_source else 0):
        # end_dt = FINE TURNO (= STD), start_dt = INIZIO TURNO (= STD-2h30)
        # extra = max(0, ATD - end_dt)
        end_dt=b.end_dt; start_dt=b.start_dt
        # Seleziona ATD: il massimo che supera end_dt
        atd_candidates=[a for a in b.atd_list if pd.notna(a) and a>end_dt]
        atd_sel=max(atd_candidates) if atd_candidates else None
        if atd_sel is None and b.atd_list:
            atd_sel=max(b.atd_list)  # usa comunque il max se nessuno supera
        extra_min=max(0,int((atd_sel-end_dt).total_seconds()/60)) if atd_sel and atd_sel>end_dt else 0
        extra_min=cfg.rounding_extra.apply(extra_min)
        extra_eur=round(extra_min*(cfg.rate_extra_per_h/60.0),2)
        # Turno base
        tariff=TARIFFE_BASE.get(b.apt.upper().strip(),90.0)
        turno_eur=tariff
        # Notturno: sul periodo effettivo (start → ATD o end)
        eff_end=atd_sel if atd_sel and atd_sel>end_dt else end_dt
        notte_min=cfg.rounding_night.apply(night_minutes(start_dt,eff_end))
        notte_rate=TARIFFE_NOTTE.get(b.apt.upper().strip(),round(90.0/150*0.20,6))
        notte_eur=round(notte_min*notte_rate,2)
        # Festivo
        is_fes=b.festivo_flag or (pd.notna(b.date) and b.date.date() in hols)
        totale=round((turno_eur+extra_eur+notte_eur)*(cfg.festivo_multiplier if is_fes else 1.0),2)
        tn=b.turno_norm
        rows.append({
            "DATA":b.date.strftime("%d/%m/%Y") if pd.notna(b.date) else "",
            "APT":b.apt,"TOUR OPERATOR":b.apt,
            "ASSISTENTE":b.assistente or "","VOLO":b.volo or "",
            "DEST.NE":b.destinazione or "",
            "TURNO_FFILL":b.turno_raw_ffill,"TURNO_NORMALIZZATO":tn,
            "INIZIO_DT":start_dt,"FINE_DT":end_dt,
            "DURATA_TURNO_MIN":int((end_dt-start_dt).total_seconds()/60) if pd.notna(end_dt) and pd.notna(start_dt) else 0,
            "NO_DEC":"No","ATD": ", ".join(filter(None, b.atd_raw_list)),
            "ATD_SCELTO":atd_sel,
            "TURNO_EUR":round(turno_eur,2),"EXTRA_MIN":extra_min,"EXTRA_EUR":extra_eur,
            "NOTTE_MIN":notte_min,"NOTTE_EUR":notte_eur,
            "FESTIVO":is_fes,"TOTALE_BLOCCO_EUR":totale,
            "SRC_FILE":b.first_source.file,"SRC_SHEET":b.first_source.sheet,
            "SRC_ROW0":b.first_source.row_index+2,
        })
    detail_df=pd.DataFrame(rows)

    if detail_df.empty:
        totals_df=pd.DataFrame(columns=["APT","BLOCCHI","TURNO_EUR","EXTRA_EUR","NOTTE_EUR","TOTALE_EUR"])
        discr_df=pd.DataFrame()
        return detail_df,totals_df,discr_df

    detail_df["__DTS"]=pd.to_datetime(detail_df["DATA"],dayfirst=True)
    detail_df["PERIODO"]=np.where(detail_df["__DTS"].dt.day<=15,"1–15","16–31")

    grp=detail_df.groupby("APT").agg(
        BLOCCHI=("TURNO_EUR","count"),
        TURNO_EUR=("TURNO_EUR","sum"),
        EXTRA_EUR=("EXTRA_EUR","sum"),
        NOTTE_EUR=("NOTTE_EUR","sum"),
        TOTALE_EUR=("TOTALE_BLOCCO_EUR","sum"),
    ).round(2).reset_index()
    tot_row=pd.DataFrame([{"APT":"TOTALE","BLOCCHI":grp["BLOCCHI"].sum(),
        "TURNO_EUR":grp["TURNO_EUR"].sum(),"EXTRA_EUR":grp["EXTRA_EUR"].sum(),
        "NOTTE_EUR":grp["NOTTE_EUR"].sum(),"TOTALE_EUR":grp["TOTALE_EUR"].sum()}])
    totals_df=pd.concat([grp,tot_row],ignore_index=True)

    discr_df=pd.DataFrame()
    return detail_df,totals_df,discr_df


def _extract_atd(v):
    if v is None: return []
    try:
        if pd.isna(v): return []
    except: pass
    r=parse_time_value(v)
    return [r] if r else []

def _parse_turno_str(s):
    if not s: return None,None
    m=re.search(r"(\d{1,2})[.:]?(\d{2})?\s*[-–—]\s*(\d{1,2})[.:]?(\d{2})?",s)
    if m:
        h1=int(m.group(1)); m1=int(m.group(2) or 0)
        h2=int(m.group(3)); m2=int(m.group(4) or 0)
        return f"{h1:02d}:{m1:02d}",f"{h2:02d}:{m2:02d}"
    return None,None


def write_output_excel(output_path:str, detail_df:pd.DataFrame, totals_df:pd.DataFrame, discr_df:pd.DataFrame):
    with pd.ExcelWriter(output_path,engine="openpyxl") as writer:
        if not detail_df.empty:
            cols=["DATA","APT","ASSISTENTE","VOLO","DEST.NE","TURNO_NORMALIZZATO",
                  "INIZIO_DT","FINE_DT","ATD", "ATD_SCELTO","TURNO_EUR","EXTRA_MIN","EXTRA_EUR",
                  "NOTTE_MIN","NOTTE_EUR","FESTIVO","TOTALE_BLOCCO_EUR","SRC_FILE","SRC_SHEET","SRC_ROW0"]
            w=detail_df[[c for c in cols if c in detail_df.columns]].copy()
            w.to_excel(writer,sheet_name="DettaglioBlocchi",index=False)
        else:
            pd.DataFrame().to_excel(writer,sheet_name="DettaglioBlocchi",index=False)
        totals_df.to_excel(writer,sheet_name="TotaliPeriodo",index=False)
        if not detail_df.empty:
            for apt in sorted(detail_df["APT"].dropna().unique()):
                sub=detail_df[detail_df["APT"]==apt]
                sub.to_excel(writer,sheet_name=str(apt)[:31],index=False)
