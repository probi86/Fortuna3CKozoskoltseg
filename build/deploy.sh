#!/usr/bin/env bash
# Build + publikálás a GitHub Pages-re. A web/ mappa MAGA a git repo.
# Használat:  bash build/deploy.sh
#   (új hónaphoz előbb:  python3 build/fetch_pdfs.py  — az is meghívja a buildet)
set -euo pipefail
cd "$(dirname "$0")/.."                      # web/ = repo gyökér
python3 build/build.py
git add -A
if git diff --cached --quiet; then echo "Nincs változás — nincs mit publikálni."; exit 0; fi
git -c user.email="1225983+probi86@users.noreply.github.com" -c user.name="probi86" \
    commit -q -m "Frissítés: $(date +%Y-%m-%d)"
git push -q
echo "Publikálva. Pár perc múlva frissül: https://probi86.github.io/Fortuna3CKozoskoltseg/"
