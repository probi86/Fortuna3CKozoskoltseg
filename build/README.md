# Build / frissítés — technikai leírás

Az oldal a `szamlak/` mappa havi PDF-jeiből generálódik. A `szamlak/` **nincs a repóban**
(személyes adatot tartalmaz, a `.gitignore` kizárja) — a privát munkamappában van.

## Mappaszerkezet (a repo gyökere = `web/`)
```
index.html            # a kész, publikált oldal (az adat bele van ágyazva, önálló)
build/
  build.py            # index.html újragenerálása a szamlak/ PDF-ekből
  fetch_pdfs.py       # új havi PDF letöltése a homefile.ro-ról (Chrome + Playwright)
  template.html       # az oldal sablonja  ← az ESEMÉNYEK (EVENTS) ITT szerkeszthetők
  deploy.sh           # build + commit + push (publikálás)
szamlak/              # (gitignore) havi kimutatások ÉÉÉÉ-HH.pdf — privát, NEM publikus
```

## Havi teendő — amikor új számla érkezik
1. **`python3 build/fetch_pdfs.py`** — letölti a hiányzó hónap teljes szélességű PDF-jét a
   `szamlak/`-ba, és újraépíti az `index.html`-t. (Első futáskor / lejárt munkamenetnél a
   felugró Chrome-ablakban be kell jelentkezni a homefile.ro-ra — a szkript megvárja.)
2. **Esemény történt?** (szolgáltatóváltás, lakóbizottság, elszámolás-váltás) — írd be a
   `build/template.html` tetején az `EVENTS` tömbbe, majd: `python3 build/build.py`.
3. **`bash build/deploy.sh`** — publikálás (commit + push); a GitHub Pages percek alatt frissül.

> Az `EVENTS`/`CELLNOTES`-t a `build/template.html`-ben szerkeszd, ne az `index.html`-ben — azt a build felülírja.

### Eseménysor (EVENTS) formátuma
```js
const EVENTS = [
  { month:"26-02", kind:"committee", label:"Csatlakozás a közös lakóbizottsághoz…" },
  { month:"26-03", kind:"contract",  label:"Fűtés/melegvíz szolgáltatóváltás: E.ON → Solprim." },
];
```
- `month`: a hónap kódja **`ÉÉ-HH`** alakban (pl. `26-03` = 2026 március).
- `kind`: `contract` (szerződés/szolgáltató) · `admin` (elszámolás/képviselet) · `committee` (lakóbizottság) — ez adja az ikon színét.

### Cella-megjegyzés (CELLNOTES) — egy adott hónap egy tételéhez
Ugyancsak a `build/template.html`-ben, az `EVENTS` alatt. A megjelölt cella `*`-ot kap, rámutatva megjelenik a szöveg.
```js
const CELLNOTES = {
  "Nagy Katalin": { "25-11":"3 havi számla egyben, visszamenőleg (3 × 440 lej)." },
};
```
A tétel kulcsa a román alapnév (pl. `Curent scara`, `Salubritate`, `Futes DIF`, `Stat de plata`, `Nagy Katalin` …).

## Követelmények
- **Python 3**, **pdftotext** (poppler — macOS: `brew install poppler`),
  a `fetch_pdfs.py`-hoz **playwright** (`pip3 install playwright`) + Google Chrome.

## Megjegyzések
- Az adat a tényleges lakás-számlák ellen ellenőrizve (2026 feb./már./ápr.).
- A publikus oldalon a PDF-letöltés ki van kapcsolva (`PDFLINKS = false` a `template.html`-ben).
- A `Nexus` és `Electropower Market` mellett `?` áll — még tisztázandók.
