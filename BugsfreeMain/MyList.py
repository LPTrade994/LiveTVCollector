#!/usr/bin/env python3
"""
MyList.py – Estrae tutti i canali/VOD in italiano da playlist molto grandi
e produce:
  • LiveTV/MyList/LiveTV.m3u   (kept)
  • LiveTV/MyList/Skipped.m3u  (skipped, per audit)
"""

import os, re, sys, pathlib, requests
from contextlib import suppress

# ───────────────────────── PARAMETRI ──────────────────────────
URL        = os.environ["M3U_SOURCE"]
DIR        = pathlib.Path("LiveTV/MyList")
OUT_FILE   = DIR / "LiveTV.m3u"
SKIP_FILE  = DIR / "Skipped.m3u"
DIR.mkdir(parents=True, exist_ok=True)

WHITELIST = [
    "rai ", "rai|", "canale 5", "canale5", "italia ", "italia1",
    "rete 4", "rete4", "sky ", "helbiz", "boing", "gulp", "yoyo",
    "nickelodeon", "cartoonito", "discovery", "dmax", "focus", "laeffe",
]

RE_LANG_IT = re.compile(r'tvg-language\s*=\s*"(?:ita|it)"', re.I)
RE_TVG_ID  = re.compile(r'tvg-id\s*=\s*"[^\"]+\.it"', re.I)
RE_GROUP   = re.compile(r'group-title\s*=\s*"[^\"]*(it\||italia|italiano)', re.I)
RE_NAME    = re.compile(r'(^|\|)it\|', re.I)

TIMEOUT = (15, 900)  # 15 s handshake, 15 min read

# ───────────────────────── HELPERS ────────────────────────────
decode = lambda b: b.decode("utf-8", "ignore")

def is_italian(extinf: str, display: str) -> bool:
    low, disp = extinf.lower(), display.lower()
    return (
        RE_LANG_IT.search(extinf)
        or RE_TVG_ID.search(extinf)
        or RE_GROUP.search(extinf)
        or RE_NAME.search(extinf)
        or any(k in low or k in disp for k in WHITELIST)
    )

# ───────────────────────── CORE ───────────────────────────────
def process():
    kept = skipped = 0
    header_written = False
    buf = None

    with requests.get(URL, stream=True, timeout=TIMEOUT) as r, \
         OUT_FILE.open("w", encoding="utf-8") as out, \
         SKIP_FILE.open("w", encoding="utf-8") as skp:

        r.raise_for_status()

        for raw in r.iter_lines():
            if raw is None: continue
            line = decode(raw) + "\n"

            if not header_written and line.startswith("#EXTM3U"):
                out.write(line); skp.write(line); header_written = True
                continue

            if line.startswith("#EXTINF"):
                buf = line
                continue

            if buf is not None:
                keep = is_italian(buf, line)
                (out if keep else skp).write(buf + line)
                kept += keep
                skipped += (not keep)
                buf = None

    return kept, skipped

def main():
    try:
        k, s = process()
        print(f"[INFO] Kept {k} IT ‖ Skipped {s} (vedi Skipped.m3u)")
    except Exception as e:
        print("[ERROR]", e, file=sys.stderr)
        with suppress(Exception): OUT_FILE.unlink(missing_ok=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
