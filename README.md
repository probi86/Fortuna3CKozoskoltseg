# Fortuna Brand 3C — közös költségek (weboldal)

Interaktív kimutatás a **3C tömb közös költségeiről** havi bontásban. Táblázat- és grafikon-nézet,
„épület összesen ⇄ egy lakásra" kapcsoló, az idővonalon eseményjelölők (szolgáltatóváltás, lakóbizottság stb.),
és minden hónapnál letölthető az eredeti közös kimutatás (PDF).

Csak a **közös** tételek szerepelnek — a víz, melegvíz, csatorna és a fűtés-fogyasztás (egyéni, saját mérőóra
szerinti) **nincs** benne. A fűtésből csak a terület-arányos **elszámolás** (regularizáció) közös.

---

## Mappaszerkezet

```
web/
├── index.html          # a kész oldal (önálló: az adat bele van ágyazva, duplakattra megnyílik)
├── data.json           # ugyanaz az adat nyersen (export, nem kötelező)
├── szamlak/            # a havi közös kimutatások: ÉÉÉÉ-HH.pdf  (ezek a letölthető fájlok)
│   ├── 2024-10.pdf … 2026-04.pdf
└── build/
    ├── build.py        # újragenerálja az index.html-t a szamlak/ mappából
    └── template.html   # az oldal sablonja  ← AZ ESEMÉNYEK (EVENTS) ITT szerkeszthetők
```

## Hogyan működik

- A **`build/build.py`** beolvassa a `szamlak/` mappa összes `ÉÉÉÉ-HH.pdf` fájlját, mindegyik **2. oldaláról**
  kinyeri a tételeket, kiszűri a közöseket, és az adatot beágyazza a `build/template.html` sablonba → `index.html`.
- Az `index.html` **önálló** (nincs külső adatfájl-függése), így dupla kattintással is megnyílik, és bárhol hosztolható.
- Az **eseménysort** (szolgáltatóváltás, lakóbizottság, elszámolás-változás) a `build/template.html` tetején lévő
  `EVENTS` tömb adja.

### Megtekintés helyben
Csak nyisd meg a `web/index.html`-t a böngészőben (dupla kattintás).

---

## ⭐ Havi teendő — amikor új számla érkezik

1. **Futtasd az exportot:**
   ```bash
   cd web/build
   python3 fetch_pdfs.py
   ```
   Ez a homefile-ból magától lementi a hiányzó hónap(ok) teljes szélességű PDF-jét
   a `szamlak/` mappába, majd lefuttatja a `build.py`-t (frissül az `index.html`
   és a `data.json`; az új hónap magától megjelenik a táblázatban, a grafikonon
   és letölthető PDF-ként). Első futáskor / lejárt munkamenetnél a felugró
   Chrome-ablakban be kell jelentkezni a homefile.ro-ra — a szkript megvárja.
   *(Kézi tartalék: mentsd a homefile „Tabel cheltuieli” oldalát fekvő A4,
   50% méretarányú PDF-ként `web/szamlak/ÉÉÉÉ-HH.pdf` néven, majd `python3 build.py`.)*
2. **Esemény történt?** (pl. szolgáltatóváltás, csatlakozás a lakóbizottsághoz, képviselő-/elszámolás-váltás)
   nyisd meg a `build/template.html`-t, és írd be az `EVENTS` tömbbe (lásd lent), majd futtasd újra a `build.py`-t.
3. **Ellenőrizd:** nyisd meg az `index.html`-t.
4. **Tedd közzé:** `git add -A && git commit -m "2026-05" && git push` — a GitHub Pages percek alatt frissül.

> ⚠️ Az `EVENTS`-et **a `build/template.html`-ben** szerkeszd, ne az `index.html`-ben — az utóbbit a `build.py` felülírja.

### Eseménysor (EVENTS) formátuma
```js
const EVENTS = [
  { month:"26-02", kind:"admin",     label:"Új közös elszámolás (homefile): Stat de plată és Contambees megjelenik." },
  { month:"26-03", kind:"contract",  label:"Fűtés/melegvíz szolgáltatóváltás: E.ON → Solprim." },
  // { month:"25-XX", kind:"committee", label:"Csatlakozás a közös lakóbizottsághoz." },  // <- töltsd ki a hónapot
];
```
- `month`: a hónap kódja **`ÉÉ-HH`** alakban (pl. `26-03` = 2026 március).
- `kind`: `contract` (szerződés/szolgáltató) · `admin` (elszámolás/képviselet) · `committee` (lakóbizottság) — ez adja a zászló színét.

### Cella-megjegyzés (CELLNOTES) — egy adott hónap egy tételéhez
Ugyancsak a `build/template.html`-ben, az `EVENTS` alatt. A megjelölt cella `*`-ot kap, rámutatva megjelenik a szöveg, és lent a „Megjegyzések" listában is.
```js
const CELLNOTES = {
  "Nagy Katalin": { "25-11":"3 havi számla egyben, visszamenőleg (3 × 440 lej)." },
  // "<tétel kulcsa>": { "ÉÉ-HH":"szöveg" },
};
```
A tétel kulcsa a román alapnév (pl. `Curent scara`, `Salubritate`, `Futes DIF`, `Stat de plata`, `Nagy Katalin` …).

---

## Közzététel GitHub Pages-en (egyszer)

1. Hozz létre egy repót, és tedd be a `web/` mappa tartalmát (vagy az egészet).
2. A repó **Settings → Pages** alatt: *Source = Deploy from a branch*, branch = `main`, mappa = `/root` (vagy `/web`, ahova tetted).
3. Pár perc múlva elérhető a `https://<felhasználó>.github.io/<repo>/` címen. Oszd meg a lakókkal.

## Követelmények
- **Python 3** és **pdftotext** (poppler). Telepítés macOS-en, ha hiányzik: `brew install poppler`.

## Megjegyzések
- Az adat a tényleges lakás-számlák ellen ellenőrizve (2026. feb./már./ápr.).
- A `Nexus` és `Electropower Market` tételek mellett `?` áll — ezek még tisztázandók; ha kiderül, mit takarnak,
  a `build/template.html` `META`/megjegyzés részében pótolható (vagy szólj, és frissítjük).
