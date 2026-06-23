# Build / frissítés — technikai leírás

Az `index.html` **maga a forrás** (HTML/CSS/JS + a beágyazott adat, önálló oldal) — a megjelenítést
közvetlenül ebben szerkeszted. A `build.py` **csak az adatot** frissíti: a `szamlak/` havi PDF-jeiből
kinyert értékeket az `index.html`-ben a `DATA:START … DATA:END` jelölők közötti `const DATA = {…}`
blokkba írja (helyben, mindent mást érintetlenül hagyva). A `szamlak/` **nincs a repóban**
(személyes adatot tartalmaz, a `.gitignore` kizárja) — a privát munkamappában van.

## Mappaszerkezet (a repo gyökere = `web/`)
```
index.html            # a forrás ÉS a publikált oldal — ITT szerkeszd a megjelenítést (EVENTS, CELLNOTES, CSS/JS)
build/
  build.py            # CSAK az index.html const DATA blokkját frissíti a szamlak/ PDF-ekből
  fetch_pdfs.py       # új havi PDF letöltése a homefile.ro-ról (Chrome + Playwright)
  deploy.sh           # build + commit + push (publikálás)
szamlak/              # (gitignore) havi kimutatások ÉÉÉÉ-HH.pdf — privát, NEM publikus
```

## Havi teendő — amikor új számla érkezik
1. **`python3 build/fetch_pdfs.py`** — letölti a hiányzó hónap teljes szélességű PDF-jét a
   `szamlak/`-ba, és frissíti az `index.html` adatát. (Első futáskor / lejárt munkamenetnél a
   felugró Chrome-ablakban be kell jelentkezni a homefile.ro-ra — a szkript megvárja.)
2. **Esemény történt?** (szolgáltatóváltás, lakóbizottság, elszámolás-váltás) — írd be az
   `index.html`-ben az `EVENTS` tömbbe (a `DATA:END` jelölő alatt), majd: `python3 build/build.py`.
3. **`bash build/deploy.sh`** — publikálás (commit + push); a GitHub Pages percek alatt frissül.

> Az `EVENTS`/`CELLNOTES`/CSS/JS-t közvetlenül az `index.html`-ben szerkeszd — a `build.py` csak a
> `DATA:START … DATA:END` közötti adatot írja felül, a többit nem bántja.

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
Ugyancsak az `index.html`-ben, az `EVENTS` alatt. A megjelölt cella `*`-ot kap, rámutatva megjelenik a szöveg.
```js
const CELLNOTES = {
  "Tombhaz felelos": { "25-11":"3 havi számla egyben, visszamenőleg (3 × 440 lej)." },
};
```
A tétel kulcsa a `const DATA` sorok `key` mezője (pl. `Curent scara`, `Salubritate`, `Futes DIF`, `Stat de plata`, `Tombhaz felelos` …).

## Követelmények
- **Python 3**, **pdftotext** (poppler — macOS: `brew install poppler`),
  a `fetch_pdfs.py`-hoz **playwright** (`pip3 install playwright`) + Google Chrome.

## Megjegyzések
- Az adat a tényleges lakás-számlák ellen ellenőrizve (2026 feb./már./ápr.).
- A publikus oldalon a PDF-letöltés ki van kapcsolva (`PDFLINKS = false` az `index.html`-ben).
- A `Nexus` és `Electropower Market` mellett `?` áll — még tisztázandók.
