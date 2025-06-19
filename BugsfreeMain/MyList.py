#!/usr/bin/env python3
"""
MyList.py – genera una playlist contenente solo i canali (live + VOD) in lingua italiana
da una sorgente M3U molto grande (anche >300 MB).

• L’URL sorgente viene passato via secret GitHub:  M3U_SOURCE
• Il file filtrato viene salvato in LiveTV/MyList/LiveTV.m3u
"""

import os
import re
import sys
import pathlib
import requests
from contextlib import suppress

# ──────────────────────────────────────────────────────────────────────────────
URL       = os.environ["M3U_SOURCE"]                            # segreto GitHub
TARGET    = pathlib.Path("LiveTV/MyList/LiveTV.m3u")            # output
TARGET.parent.mkdir(parents=True, exist_ok=True)

# pattern che identifica la lingua italiana (IT| … o .it nel tag)
ITA_RE = re.compile(r"(it\|)|(\.it\b)", re.IGNORECASE)


def iter_ita_lines(resp):
    """
    Generator: produce solo le righe (#EXTINF + URL) relative ai canali italiani.
    Gestisce sia bytes che str, evitando errori di concatenazione.
    """
    keep_next = False
    header_emitted = False

    for raw in resp.iter_lines():               # nessuna decodifica automatica
        if raw is None:
            continue

        # convertiamo in str UTF-8, ignorando caratteri non validi
        if isinstance(raw, bytes):
            line = raw.decode("utf-8", "ignore") + "\n"
        else:
            line = str(raw) + "\n"

        # header una sola volta
        if not header_emitted and line.startswith("#EXTM3U"):
            header_emitted = True
            yield line
            continue

        # tag EXTINF
        if line.startswith("#EXTINF"):
            keep_next = bool(ITA_RE.search(line))
            if keep_next:
                yield line
            continue

        # URL immediatamente dopo un EXTINF da tenere
        if keep_next:
            yield line
            keep_next = False


def main():
    try:
        print(f"[INFO] Scarico {URL[:120]}...")
        with requests.get(
            URL,
            stream=True,
            timeout=(15, 900),          # 15 s handshake, 15 min read
            headers={"User-Agent": "Mozilla/5.0 GitHubRunner"},
        ) as r:
            r.raise_for_status()

            with TARGET.open("w", encoding="utf-8") as out:
                count = 0
                for chunk in iter_ita_lines(r):
                    out.write(chunk)
                    if chunk.startswith("#EXTINF"):
                        count += 1

        print(f"[INFO] Salvati {count} canali ITA in {TARGET}")
    except Exception as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        with suppress(Exception):
            TARGET.unlink(missing_ok=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
