#!/usr/bin/env python3
"""
MyList.py – tiene solo canali / VOD realmente italiani.
Criteri:
1. Prefisso IT| o ITA| in tvg-name o group-title
2. tvg-language="it"   oppure   tvg-id termina con .it
3. Whitelist di nomi tipici (RAI, Canale 5…) *se* non compaiono altri prefissi lingua
Scrive:
  • LiveTV/MyList/LiveTV.m3u   (kept)
  • LiveTV/MyList/Skipped.m3u  (skipped, audit)
"""

import os, re, sys, pathlib, requests
from contextlib import suppress

URL        = os.environ["M3U_SOURCE"]
DIR        = pathlib.Path("LiveTV/MyList")
OUT_FILE   = DIR / "LiveTV.m3u"
SKIP_FILE  = DIR / "Skipped.m3u"
DIR.mkdir(parents=True, exist_ok=True)

# ───────── regex principali ─────────
RE_PREF_IT = re.compile(r'(^|\|)ita?\|', re.I)          # IT| o ITA|
RE_LANG_IT = re.compile(r'tvg-language\s*=\s*"(?:it|ita)"', re.I)
RE_TVG_ID  = re.compile(r'tvg-id\s*=\s*"[^\"]+\.it"', re.I)

# altri prefissi lingua comuni da ESCLUDERE se presenti
RE_OTHER_LANG = re.compile(r'(^|\|)(en|es|fr|de|pt|ar|tr|gr|ru|us)\|', re.I)

WHITELIST = [
    "rai ", "canale 5", "canale5", "italia 1", "italia1",
    "rete 4", "rete4", "boing", "yoyo", "yamat", "helbiz",
]

TIMEOUT = (15, 900)

decode = lambda b: b.decode("utf-8", "ignore")

def is_italian(extinf: str, display: str) -> bool:
    low = (extinf + display).lower()

    # 1. prefisso IT|
    if RE_PREF_IT.search(extinf) or RE_PREF_IT.search(display):
        return True

    # 2. meta-tag espliciti
    if RE_LANG_IT.search(extinf) or RE_TVG_ID.search(extinf):
        return True

    # 3. whitelist *solo se* non ci sono altri codici lingua
    if not RE_OTHER_LANG.search(extinf) and any(w in low for w in WHITELIST):
        return True

    return False

def process_playlist():
    kept = skipped = 0
    header_written = False
    buf = None

    with requests.get(URL, stream=True, timeout=TIMEOUT) as r,\
         OUT_FILE.open("w", encoding="utf-8") as out,\
         SKIP_FILE.open("w", encoding="utf-8") as skip:

        r.raise_for_status()

        for raw in r.iter_lines():
            if raw is None: continue
            line = decode(raw) + "\n"

            if not header_written and line.startswith("#EXTM3U"):
                header_written = True
                out.write(line); skip.write(line)
                continue

            if line.startswith("#EXTINF"):
                buf = line
                continue

            if buf is not None:
                keep = is_italian(buf, line)
                dest = out if keep else skip
                dest.write(buf); dest.write(line)
                kept += int(keep)
                skipped += int(not keep)
                buf = None

    return kept, skipped

def main():
    try:
        print("[INFO] Download & filter playlist …")
        kept, skipped = process_playlist()
        print(f"[INFO] Kept {kept}  –  Skipped {skipped}")
        if skipped:
            print("[INFO] Controlla Skipped.m3u (artifact) per verificare residui")
    except Exception as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        with suppress(Exception):
            OUT_FILE.unlink(missing_ok=True)
            SKIP_FILE.unlink(missing_ok=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
