#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
homefile.ro havi kimutatás → teljes szélességű PDF-export + weboldal-build.

Használat:
  python3 fetch_pdfs.py                # hiányzó hónapok + aktuális hónap
  python3 fetch_pdfs.py --all          # minden hónap újra (2024-10-től)
  python3 fetch_pdfs.py --month 2026-05

Első használat: a szkript maga indítja a dedikált Chrome-ot
(~/.homefile-chrome profil); abban egyszer be kell jelentkezni a homefile.ro-ra.
Részletek: docs/superpowers/specs/2026-06-12-homefile-export-design.md
"""
import argparse, base64, datetime, os, shutil, subprocess, sys, tempfile, time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
WEB = os.path.dirname(HERE)
SZAMLAK = os.path.join(WEB, "szamlak")
BACKUP = os.path.join(SZAMLAK, "_backup_csonka")
PROFILE = os.path.expanduser("~/.homefile-chrome")
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
CDP_URL = "http://127.0.0.1:9222"
START = (2024, 10)

# társulások: assoc/apartment + a hónap-index bázisa (év, hó), ahol index = 0
OLD = {"assoc": 6093, "apt": 221, "base": (2024, 9)}    # Fortuna Park Brand SRL
NEW = {"assoc": 6079, "apt": 1281, "base": (2024, 5)}   # Asociatia Fortuna Brand
CUTOVER = (2026, 2)  # ettől a hónaptól az új társulás a forrás

ROMON = ["Ianuarie", "Februarie", "Martie", "Aprilie", "Mai", "Iunie", "Iulie",
         "August", "Septembrie", "Octombrie", "Noiembrie", "Decembrie"]


def months_between(a, b):
    return (b[0] - a[0]) * 12 + (b[1] - a[1])


def source_for(ym):
    """(év, hó) -> (assoc_id, apartment_id, month_index)"""
    src = NEW if ym >= CUTOVER else OLD
    return src["assoc"], src["apt"], months_between(src["base"], ym)


def table_url(ym):
    a, ap, n = source_for(ym)
    return f"https://homefile.ro/outgotable.html#/association/{a}/apartment/{ap}/month/{n}"


def expected_header(ym):
    """A „Lista de plată pe luna X, ÉÉÉÉ” fejléc kötelező darabja."""
    return f"pe luna {ROMON[ym[1] - 1]}, {ym[0]}"


def required_keywords(ym):
    """A jobb szélső oszlopok jelenlétét igazoló kulcsszavak."""
    if ym >= CUTOVER:
        # új társulás: Total General a jobb szél + fond rulment
        # (FOND DE REPARATII csak 2026-03-tól létezik, ezért nem követelmény)
        return ["General", "RULMENT"]
    # régi társulás tábláján nincs „Total General” — a Restanţe a jobb széli oszlop
    return ["Restan"]


def month_range(start, end):
    out, (y, m) = [], start
    while (y, m) <= end:
        out.append((y, m))
        m += 1
        if m == 13:
            y, m = y + 1, 1
    return out


def cdp_alive():
    try:
        urllib.request.urlopen(CDP_URL + "/json/version", timeout=2)
        return True
    except Exception:
        return False


def ensure_chrome():
    if cdp_alive():
        return
    print("Chrome indítása (dedikált profil)…")
    subprocess.Popen(
        [CHROME, f"--user-data-dir={PROFILE}", "--remote-debugging-port=9222",
         "--no-first-run", "--no-default-browser-check", "https://homefile.ro"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(30):
        time.sleep(1)
        if cdp_alive():
            return
    sys.exit("HIBA: nem indult el a Chrome CDP-vel a 9222-es porton.")


def page_text(page):
    return page.locator("body").inner_text()


def wait_for_login(page, ym):
    """Login-oldalon megvárja a bejelentkezést; lassú rendernél párszor újratölt.
    Üres (nem publikált) hónapnál visszatér — arról a hívó dönt."""
    for _ in range(3):
        t = page_text(page).lower()
        if "lista de plat" in t:
            return
        while "autentific" in t or "parol" in t:
            print(">> Jelentkezz be a homefile.ro-ra a felugró Chrome-ablakban — várok…")
            time.sleep(5)
            page.goto(table_url(ym))
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(2000)
            t = page_text(page).lower()
        time.sleep(2)
        page.goto(table_url(ym))
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(2500)


def print_month(ctx, page, ym, scale):
    """Betölti a hónap tábláját és PDF-bytes-t ad vissza, vagy None-t ha üres."""
    page.goto(table_url(ym))
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(2500)
    wait_for_login(page, ym)
    if expected_header(ym).lower() not in page_text(page).lower():
        return None  # nem publikált / üres hónap
    cdp = ctx.new_cdp_session(page)
    pdf = b""
    for _ in range(3):  # a render commit előtti nyomtatás üres PDF-et ad — újra
        r = cdp.send("Page.printToPDF", {
            "landscape": True, "scale": scale,
            "paperWidth": 11.69, "paperHeight": 8.27,   # A4 fekvő, inch
            "printBackground": True})
        pdf = base64.b64decode(r["data"])
        if pdf_text(pdf).strip():
            break
        page.wait_for_timeout(2000)
    cdp.detach()
    return pdf


def pdf_text(pdf_bytes):
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as t:
        t.write(pdf_bytes)
        tmp = t.name
    try:
        return subprocess.run(["pdftotext", "-layout", tmp, "-"],
                              capture_output=True, text=True).stdout
    finally:
        os.unlink(tmp)


def verify_pdf(pdf_bytes, ym):
    txt = pdf_text(pdf_bytes).upper()
    if expected_header(ym).upper() not in txt:
        return False
    return all(k.upper() in txt for k in required_keywords(ym))


def backup_existing(path):
    """A felülírandó (csonka) PDF egyszeri biztonsági másolata."""
    if not os.path.exists(path):
        return
    os.makedirs(BACKUP, exist_ok=True)
    dst = os.path.join(BACKUP, os.path.basename(path))
    if not os.path.exists(dst):
        shutil.copy2(path, dst)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--all", action="store_true", help="minden hónap újra")
    ap.add_argument("--month", help="csak egy hónap, ÉÉÉÉ-HH")
    args = ap.parse_args()

    today = datetime.date.today()
    end = (today.year, today.month)
    if args.month:
        y, m = args.month.split("-")
        targets = [(int(y), int(m))]
    else:
        targets = month_range(START, end)
        if not args.all:
            targets = [ym for ym in targets if ym == end or not
                       os.path.exists(os.path.join(SZAMLAK, f"{ym[0]}-{ym[1]:02d}.pdf"))]

    ensure_chrome()
    from playwright.sync_api import sync_playwright
    saved = skipped = 0
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(CDP_URL)
        ctx = browser.contexts[0]
        page = ctx.new_page()
        for ym in targets:
            name = f"{ym[0]}-{ym[1]:02d}.pdf"
            pdf = None
            for scale in (0.5, 0.45):
                pdf = print_month(ctx, page, ym, scale)
                if pdf is None or verify_pdf(pdf, ym):
                    break
                pdf = b""  # volt adat, de a verifikáció elbukott
            if pdf is None:
                print(f"   {name}: nincs publikált adat — kihagyva")
                skipped += 1
                continue
            if not pdf:
                page.close()
                sys.exit(f"HIBA: {name} verifikáció sikertelen (oszlopok nem férnek be?) — "
                         f"semmi nem lett felülírva.")
            dest = os.path.join(SZAMLAK, name)
            backup_existing(dest)
            with open(dest, "wb") as f:
                f.write(pdf)
            print(f"   {name}: mentve ({len(pdf) // 1024} KB)")
            saved += 1
        page.close()
        browser.close()

    print(f"Kész: {saved} mentve, {skipped} kihagyva.")
    if saved:
        subprocess.run([sys.executable, os.path.join(HERE, "build.py")], check=True)


if __name__ == "__main__":
    main()
