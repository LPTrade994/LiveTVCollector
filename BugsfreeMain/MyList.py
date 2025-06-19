#!/usr/bin/env python3
"""
MyList.py – Estrae tutti i canali/VOD in lingua italiana da playlist molto grandi.
Scrive due file:
  • LiveTV/MyList/LiveTV.m3u   (tenuti)
  • LiveTV/MyList/Skipped.m3u  (scartati, per audit)
L’URL sorgente è nel secret GitHub  M3U_SOURCE.
"""

import os, re, sys, pathlib, requests
from contextlib import suppress

# ───────────────────── PARAMETRI PERSONALIZZABILI ──────────────────────────
URL          = os.environ["M3U_SOURCE"]                # secret GitHub
TARGET_DIR   = pathlib.Path("LiveTV/MyList")
OUT_FILE     = TARGET_DIR / "LiveTV.m3u"
SKIP_FILE    = TARGET_DIR / "Skipped.m3u"              # audit opzionale

WHITELIST = [
    "rai ", "rai|", "canale 5", "canale5", "tgcom",
    "italia ", "italia1", "italia 1", "rete 4", "rete4",
    "sky ", "helbiz", "boing", "gulp", "yoyo", "nickelodeon",
    "cartoonito", "discovery", "dmax", "focus", "laeffe",
]
# se vuoi aggiungere parole, mettile qui in minuscolo

# regex pronte (RE.VERBOSE per leggibilità)
RE_LANG_IT = re.compile(r'tvg-language\s*=\s*"(?:ita|it)"', re.I)
RE_TVG_ID  = re.compile(r'tvg-id\s*=\s*"[^\"]+\.it"', re.I)
RE_GROUP   = re.compile(r'group-title\s*=\s*"[^\"]*(it\||italia|italiano)', re.I)
RE_NAME    = re.compile(r'(^|\|)it\|', re.I)    # match "IT|" inizio o dopo pipe

# streaming sicuro
TIMEOUT = (15, 900)  # 15 s handshake, 15 min read

# ───────────────────── FUNZIONI DI UTILITÀ ─────────────────────────────────
def decode(line_bytes: bytes) -> str:
    """bytes → str UTF-8 safe"""
    return line_bytes.decode("utf-8", "ignore")

def is_italian(extinf: str, display: str) -> bool:
    """True se la riga EXTINF corrisponde a un canale italiano."""
    low = extinf.lower()
    disp = display.lower()

    if RE_LANG_IT.search(extinf):        return True
    if RE_TVG_ID.search(extinf):         return True
    if RE_GROUP.search(extinf):          return True
    if RE_NAME.search(extinf):           return True
    if any(k in low or k in disp for k in WHITELIST):  return True
    return False

# ───────────────────── PROCESSING STREAM ───────────────────────────────────
def process_playlist():
    TARGET_DIR.mkdir(parents=True, exist_ok=True)
    kept = skipped = 0
    header_written = False

    with requests.get(URL, stream=True, timeout=TIMEOUT) as r,\
         OUT_FILE.open("w", encoding="utf-8") as out,\
         SKIP_FILE.open("w", encoding="utf-8") as skp:

        r.raise_for_status()
        buf_extinf = None  # memorizza la #EXTINF in attesa del relativo URL

        for raw in r.iter_lines():
            if raw is None:
                continue
            line = decode(raw) + "\n"

            # header iniziale
            if not header_written and line.startswith("#EXTM3U"):
                out.write(line)
                skp.write(line)
                header_written = True
                continue

            if line.startswith("#EXTINF"):
                buf_extinf = line      # salva e valuta dopo
                continue

            # Se arriva qui, è (quasi sempre) la URL seguente
            if buf_extinf is not None:
                keep = is_italian(buf_extinf, line)

                dest = out if keep else skp
                dest.write(buf_extinf)
                dest.write(line)

                kept += keep
                skipped += not keep
                buf_extinf = None      # reset buffer

    return kept, skipped

# ───────────────────── MAIN ────────────────────────────────────────────────
def main():
    try:
        print(f"[INFO] Downloading playlist… (timeout read {TIMEOUT[1]} s)")
        kept, skipped = process_playlist()
        print(f"[INFO] Kept {kept} italian channels  –  Skipped {skipped}")
        if skipped:
            print(f"[INFO] Controlla {SKIP_FILE} per eventuali canali da aggiustare")
    except Exception as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        with suppress(Exception):
            OUT_FILE.unlink(missing_ok=True)
            SKIP_FILE.unlink(missing_ok=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
