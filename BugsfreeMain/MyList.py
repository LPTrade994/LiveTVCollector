#!/usr/bin/env python3
"""
MyList.py – Estrae tutti i canali/VOD in lingua italiana da playlist molto grandi
e produce due file:
  • LiveTV/MyList/LiveTV.m3u   (canali italiani tenuti)
  • LiveTV/MyList/Skipped.m3u  (scartati, per controllo)

L’URL sorgente è passato via secret GitHub:  M3U_SOURCE
"""

import os, re, sys, pathlib, requests
from contextlib import suppress

# ─────────────────────── PARAMETRI PRINCIPALI ──────────────────────────────
URL       = os.environ["M3U_SOURCE"]
DIR       = pathlib.Path("LiveTV/MyList")
OUT_FILE  = DIR / "LiveTV.m3u"
SKIP_FILE = DIR / "Skipped.m3u"
DIR.mkdir(parents=True, exist_ok=True)

# Parole chiave aggiuntive che identificano quasi certamente un canale italiano
WHITELIST = [
    "rai ", "rai|", "canale 5", "canale5", "italia ", "italia1",
    "rete 4", "rete4", "sky ", "helbiz", "boing", "gulp", "yoyo",
    "nickelodeon", "cartoonito", "discovery", "dmax", "focus", "laeffe",
]

# Regex pre-compilate (case-insensitive)
RE_LANG_IT = re.compile(r'tvg-language\s*=\s*"(?:ita|it)"', re.I)
RE_TVG_ID  = re.compile(r'tvg-id\s*=\s*"[^\"]+\.it"', re.I)
RE_GROUP   = re.compile(r'group-title\s*=\s*"[^\"]*(it\||italia|italiano)', re.I)
RE_NAME_IT = re.compile(r'(^|\|)it\|', re.I)

TIMEOUT = (15, 900)  # 15 s handshake, 15 min read

# ───────────────────────── FUNZIONI AUSILIARIE ─────────────────────────────
decode = lambda b: b.decode("utf-8", "ignore")           # bytes → str UTF-8 safe

def is_italian(extinf: str, display: str) -> bool:
    """Determina se la coppia EXTINF/URL appartiene a un contenuto italiano."""
    low = extinf.lower()
    disp = display.lower()

    if RE_LANG_IT.search(extinf):          return True
    if RE_TVG_ID.search(extinf):           return True
    if RE_GROUP.search(extinf):            return True
    if RE_NAME_IT.search(extinf):          return True
    if any(k in low or k in disp for k in WHITELIST):
        return True
    return False

# ───────────────────────── PROCESSING STREAM ───────────────────────────────
def process_playlist():
    kept = skipped = 0
    header_written = False
    buf_extinf = None

    with requests.get(URL, stream=True, timeout=TIMEOUT) as r,\
         OUT_FILE.open("w", encoding="utf-8") as out,\
         SKIP_FILE.open("w", encoding="utf-8") as skp:

        r.raise_for_status()

        for raw in r.iter_lines():
            if raw is None:
                continue
            line = decode(raw) + "\n"

            # Scrive l'intestazione #EXTM3U solo una volta
            if not header_written and line.startswith("#EXTM3U"):
                out.write(line)
                skp.write(line)
                header_written = True
                continue

            # Bufferizza il tag #EXTINF in attesa della URL successiva
            if line.startswith("#EXTINF"):
                buf_extinf = line
                continue

            # Se buf_extinf è popolato, questa è la URL associata
            if buf_extinf is not None:
                keep = is_italian(buf_extinf, line)
                dest = out if keep else skp
                dest.write(buf_extinf)
                dest.write(line)

                kept += int(keep)
                skipped += int(not keep)
                buf_extinf = None

    return kept, skipped

# ───────────────────────── FUNZIONE PRINCIPALE ─────────────────────────────
def main():
    try:
        print(f"[INFO] Downloading playlist… (timeout read {TIMEOUT[1]} s)")
        kept, skipped = process_playlist()
        print(f"[INFO] Kept {kept} italian channels – Skipped {skipped}")
        if skipped:
            print(f"[INFO] Controlla {SKIP_FILE} per eventuali canali da aggiungere")
    except Exception as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        with suppress(Exception):
            OUT_FILE.unlink(missing_ok=True)
            SKIP_FILE.unlink(missing_ok=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
