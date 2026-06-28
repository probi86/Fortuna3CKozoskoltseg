#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fortuna 3C — közös költségek weboldal újragenerálása.

Mit csinál:
  1. Beolvassa a  ../szamlak/ÉÉÉÉ-HH.pdf  havi közös kimutatásokat (homefile „Tabel cheltuieli").
  2. Kinyeri minden PDF-ből a KÖZÖS tételeket (a víz/melegvíz/csatorna/fűtés-fogyasztás = egyéni, kimarad).
  3. CSAK az adatot frissíti: az ../index.html-ben a DATA:START…DATA:END jelölők közötti
     `const DATA = {…}` blokkot cseréli ki helyben. A megjelenítést (HTML/CSS/JS, EVENTS,
     CELLNOTES) közvetlenül az ../index.html-ben szerkeszd — nincs külön sablon.

Havi teendő:  tedd be az új PDF-et ../szamlak/-ba (pl. 2026-05.pdf), majd:  python3 build.py
Részletek:    lásd ../README.md
"""
import subprocess, re, json, os, glob, sys

HERE = os.path.dirname(os.path.abspath(__file__))
WEB  = os.path.dirname(HERE)
SZAMLAK = os.path.join(WEB, "szamlak")
INDEX = os.path.join(WEB, "index.html")
DATA_START = "/* === DATA:START (auto: build.py — ne szerkeszd kézzel) === */"
DATA_END   = "/* === DATA:END === */"

# Ahol a havi PDF-export LEVÁGTA a fond oszlopokat (jobb szél), itt add meg kézzel a
# havi „Lună" befizetést:  "ÉÉÉÉ-HH": (fond_rulment, fond_reparatii).  A teljes szöveges
# kimutatás Total sorából olvasható ki.
FOND_OVERRIDE = {"2026-05": (440.0, 344.30)}

HUMON = ['jan','feb','már','ápr','máj','jún','júl','aug','szept','okt','nov','dec']

# A 16 KÖZÖS tétel: kulcs -> (megjelenített név, magyar megjegyzés, elosztás: apt|pers|cpi)
META = [
 ("Curent scara",   ("Curent scara","közös villany — Harghita Energy","apt")),
 ("Salubritate",    ("Salubritate","szemét, heti többszöri — RDE Harghita","pers")),
 ("Futes DIF",      ("Încălzire diferență","fűtés-elszámolás — Solprim","cpi")),
 ("Lift",           ("Lift","OTIS Lift","apt")),
 ("Administrare",   ("Administrare","","apt")),
 ("Stat de plata",  ("Stat de plată","bérek (vezetőség + takarítás)","apt")),
 ("Curatenie",      ("Curățenie","takarítás","apt")),
 ("Curatare teren", ("Curățare teren","terület-rendezés","apt")),
 ("Tombhaz felelos",("Tömbház-felelős","","apt")),
 ("Contambees",     ("Contambees","csíki könyvelő iroda","apt")),
 ("Bariera",        ("Barieră","sorompó – javítás","apt")),
 ("Acumulator lift",("Acumulator lift","felvonó akkumulátor","apt")),
 ("Homefile",       ("Homefile","számlázó rendszer","apt")),
 ("Nexus",          ("PSI","tűzvédelem (előtte Nexus)","apt")),
 ("Comision",       ("Comision","kezelési díj","apt")),
 ("Electropower",   ("Electropower Market","Electropower Market SRL","apt")),
 ("Fond rulment",   ("Fond rulment","tartalékalap, ~10 lej/befizetés","fund")),
 ("Fond reparatii", ("Fond de reparații","javítási alap, terület szerint","fund")),
]
ROWS = [k for k,_ in META]
FUNDS = {"Fond rulment","Fond reparatii"}      # lakásonkénti alap-befizetés, NEM szétosztott közös költség
COST_ROWS = [r for r in ROWS if r not in FUNDS]
COMMON = set(ROWS) - {"Futes DIF"} - FUNDS
SPLITNAME = {"apt":"Lakásonként (fix)","pers":"Személyenként","cpi":"Terület szerint (CPI)",
             "fund":"Lakásonkénti alap-befizetés"}

def classify(d, c):
    d=d.upper(); c=c.upper()
    if "CURATARE TEREN" in d: return "Curatare teren"
    if "KATALIN" in d: return "Tombhaz felelos"
    if "STAT DE PLATA" in d: return "Stat de plata"
    if "BARIERA" in d: return "Bariera"
    if "COMISION" in d: return "Comision"
    if "CONTAMBEES" in d or "CONTABIL" in d: return "Contambees"
    if "HOMEFILE" in d: return "Homefile"
    if "NEXUS" in d or "PSI" in d: return "Nexus"
    if "ELECTROPOWER" in d: return "Electropower"
    if "ACUMULATOR" in d: return "Acumulator lift"
    if "CURATENIE" in d: return "Curatenie"
    if d.strip().startswith("ADMINISTRARE"): return "Administrare"
    if c.startswith(("APA CANAL","CANALIZ")): return "Canalizare"
    if c.startswith("APA RECE"): return "Apa rece"
    if c.startswith("APA CALDA"): return "Apa calda"
    if c.startswith("INCALZIRE"): return "Incalzire"
    if c.startswith("CURENT"): return "Curent scara"
    if c.startswith("SALUBRITATE"): return "Salubritate"
    if c.startswith("LIFT"): return "Lift"
    if c.startswith("CURATENIE"): return "Curatenie"
    if c.startswith("ADMINISTRARE"): return "Administrare"
    if "CANAL" in d: return "Canalizare"
    if "HARVIZ" in d: return "Apa rece"
    if "SALUBR" in d: return "Salubritate"
    if "INCALZIR" in d: return "Incalzire"
    if "APA CALDA" in d: return "Apa calda"
    if "APA RECE" in d: return "Apa rece"
    if "ELECTRICA" in d or "CURENT SCARA" in d: return "Curent scara"
    if "E.ON" in d or "EON" in d: return "Incalzire"
    if "OTIS" in d or "LIFT" in d: return "Lift"
    if "APA" in d: return "Apa rece"
    return "x"

ROMON = {"IANUARIE":"január","FEBRUARIE":"február","MARTIE":"március","APRILIE":"április","MAI":"május",
         "IUNIE":"június","IULIE":"július","AUGUST":"augusztus","SEPTEMBRIE":"szeptember",
         "OCTOMBRIE":"október","NOIEMBRIE":"november","DECEMBRIE":"december"}

def heat_note(heat_denums, dif_denums):
    """A fűtés-elszámoláshoz: szolgáltató + elszámolt időszak a sorok megnevezéséből."""
    blob = " ".join(heat_denums).upper()
    sup = "Solprim" if ("SOLPRIM" in blob or "SOPLRIM" in blob) else ("E.ON" if ("E.ON" in blob or "EON" in blob) else None)
    text = " ".join(dif_denums or heat_denums).upper()
    toks = re.findall(r"IANUARIE|FEBRUARIE|MARTIE|APRILIE|MAI|IUNIE|IULIE|AUGUST|SEPTEMBRIE|OCTOMBRIE|NOIEMBRIE|DECEMBRIE", text)
    seen=[]
    for t in toks:
        if t not in seen: seen.append(t)
    months_hu = [ROMON[t] for t in seen]
    bits=[]
    if sup: bits.append("Szolgáltató: "+sup)
    if months_hu: bits.append("elszámolt időszak: "+"–".join(months_hu))
    return " · ".join(bits)

def extract(pdf):
    """Egy havi PDF-ből a közös tételek {kulcs: érték} + a fűtés-jegyzet."""
    txt = subprocess.run(["pdftotext","-layout",pdf,"-"],
                         capture_output=True, text=True).stdout
    out = {r:0.0 for r in ROWS}
    heat_denums=[]; dif_denums=[]
    for line in txt.splitlines():
        if " lei" not in line: continue
        parts=[p for p in re.split(r"\s{2,}", line.strip()) if p]
        if len(parts)<2: continue
        nums=re.findall(r"-?\d[\d.]*", line)
        if not nums: continue
        d=parts[0]; val=float(nums[-1]); cat=classify(d, parts[1])
        if cat in COMMON:
            out[cat]+=val
        elif cat=="Incalzire":
            heat_denums.append(d)
            if ("CPI" in line.upper()) or ("DIF" in d.upper()):
                out["Futes DIF"]+=val   # csak a terület-arányos elszámolás (közös), a fogyasztás egyéni
                dif_denums.append(d)
    return out, heat_note(heat_denums, dif_denums)

def extract_fonds(pdf):
    """Fond rulment / fond de reparații havi összege a lakáslista Total sorából.
    pdftotext -tsv koordinátákból: fond-fejléc x-tartomány -> Lună aloszlop ->
    a Total sor odaeső száma. Régi (fond nélküli) PDF-nél (0.0, 0.0)."""
    tsv = subprocess.run(["pdftotext","-tsv",pdf,"-"], capture_output=True, text=True).stdout
    words=[]
    for ln in tsv.splitlines()[1:]:
        p=ln.split("\t")
        if len(p)<12 or p[11].startswith("###"): continue
        words.append((int(p[1]), float(p[6]), float(p[7]), float(p[8]), p[11]))
    # (page, x, y, szélesség, szöveg); a fond-fejlécek oldala (a lakáslista oldala)
    fpages={w[0] for w in words if w[4].upper() in ("RULMENT","REPARATII")}
    if not fpages: return 0.0, 0.0
    pg=min(fpages)
    W=[w for w in words if w[0]==pg]
    heads=[w for w in W if w[4].upper() in ("RULMENT","REPARATII")]
    lunas=[w for w in W if w[4]=="Lună"]
    # a lakáslista Total sora: bal szélső "Total" szó (a fejléc Total-jai jobbra esnek)
    tots=[w for w in W if w[4]=="Total" and w[1]<100]
    if not tots or not lunas: return 0.0, 0.0
    ty=tots[0][2]
    rownums=[w for w in W if abs(w[2]-ty)<6 and re.fullmatch(r"-?\d[\d.]*", w[4])]
    cx=lambda w: w[1]+w[3]/2
    out={"RULMENT":0.0, "REPARATII":0.0}
    seen=set()
    for h in heads:
        # a fejléchez x-ben legközelebbi Lună aloszlop
        lu=min(lunas, key=lambda w: abs(cx(w)-cx(h)))
        if abs(cx(lu)-cx(h))>60 or id(lu) in seen: continue
        seen.add(id(lu))
        # a Total sorban a Lună oszlopra eső szám
        if not rownums: continue
        v=min(rownums, key=lambda w: abs(cx(w)-cx(lu)))
        if abs(cx(v)-cx(lu))<=30:
            out[h[4].upper()]+=float(v[4])
    return round(out["RULMENT"],2), round(out["REPARATII"],2)

def main():
    pdfs = sorted(glob.glob(os.path.join(SZAMLAK, "[0-9][0-9][0-9][0-9]-[0-9][0-9].pdf")))
    if not pdfs:
        sys.exit("Nincs PDF a szamlak/ mappában (ÉÉÉÉ-HH.pdf néven kell).")
    months=[]; M=[]; heat=[]
    for p in pdfs:
        full = os.path.splitext(os.path.basename(p))[0]   # ÉÉÉÉ-HH
        yyyy, mm = full.split("-"); yy = yyyy[2:]; mi=int(mm)-1
        months.append({"code":f"{yy}-{mm}","abbr":HUMON[mi],"year":"’"+yy,
                       "full":f"{yyyy}. {HUMON[mi]}","file":full})
        vals, hn = extract(p)
        vals["Fond rulment"], vals["Fond reparatii"] = extract_fonds(p)
        if full in FOND_OVERRIDE:
            vals["Fond rulment"], vals["Fond reparatii"] = FOND_OVERRIDE[full]
        M.append(vals); heat.append(hn)

    codes=[mo["code"] for mo in months]
    rows=[]
    for key,(name,note,sp) in META:
        vals=[round(m[key],2) for m in M]
        row={"key":key,"name":name,"note":note,"split":sp,
             "splitName":SPLITNAME[sp],"vals":vals,"total":round(sum(vals),2)}
        if key=="Futes DIF":   # szolgáltató + időszak tooltip a nem-nulla elszámolás-celláknál
            row["cellnotes"]={codes[i]:heat[i] for i in range(len(M)) if abs(vals[i])>=0.5 and heat[i]}
        rows.append(row)
    colTot=[round(sum(m[r] for r in COST_ROWS),2) for m in M]   # közös költség (fondok nélkül)
    grand=round(sum(colTot),2)
    top=max(rows,key=lambda x:x["total"])
    today = subprocess.run(["date","+%Y-%m-%d"],capture_output=True,text=True).stdout.strip()
    data={"apts":44,"generated":today,"months":months,"rows":rows,"colTot":colTot,"grand":grand,
          "topName":top["name"],"topNote":top["note"],"topTotal":top["total"],
          "topPct":round(top["total"]/grand*100)}

    # A const DATA blokk helyben cseréje az index.html-ben (a megjelenítést közvetlenül szerkesztjük).
    html=open(INDEX,encoding="utf-8").read()
    if DATA_START not in html or DATA_END not in html:
        sys.exit("Hiányzó DATA:START / DATA:END jelölő az index.html-ben — nem tudom hova illeszteni az adatot.")
    block=DATA_START+"\nconst DATA = "+json.dumps(data,ensure_ascii=False)+";\n"+DATA_END
    i=html.index(DATA_START); j=html.index(DATA_END)+len(DATA_END)
    html=html[:i]+block+html[j:]
    with open(INDEX,"w",encoding="utf-8") as f:
        f.write(html)

    print(f"OK · {len(months)} hónap ({months[0]['file']} … {months[-1]['file']})")
    print(f"   közös összesen: {grand:,.0f} lej · legnagyobb: {top['name']} ({data['topPct']}%)")
    print(f"   frissítve: index.html (const DATA blokk)")

if __name__=="__main__":
    main()
