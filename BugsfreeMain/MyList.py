#!/usr/bin/env python3
"""
MyList.py – estrai solo i canali italiani da playlist molto grandi (>300 MB)
Il download avviene a streaming, senza caricare tutto in RAM.
"""

import os, re, pathlib, requests, sys
from contextlib import suppress

URL       = os.environ["M3U_SOURCE"]            # segreto GitHub
TARGET    = pathlib.Path("LiveTV/MyList/LiveTV.m3u")
TARGET.parent.mkdir(parents=True, exist_ok=True)

# pattern che identifica la lingua italiana
ITA_RE = re.compile(r"(it\|)|(\.it\b)", re.IGNORECASE)

def iter_ita_lines(resp):
    """Restituisce SOLO le righe (#EXTINF + URL) con lingua ITA."""
    keep_next = False
    header_emitted = False

    for raw in resp.iter_lines(decode_unicode=True):
        if raw is None:
            continue
        line = raw + "\n"

        # rilascio header una sola volta
        if not header_emitted and line.startswith("#EXTM3U"):
            header_emitted = True
            yield line
            continue

        if line.startswith("#EXTINF"):
            keep_next = bool(ITA_RE.search(line))
            if keep_next:
                yield line
            continue

        # questa è la riga-URL
        if keep_next:
            yield line
            keep_next = False

def main():
    try:
        print(f"[INFO] Scarico {URL[:80]}...")
        with requests.get(
            URL,
            stream=True,
            timeout=(15, 600),          # 15 s handshake, 10 min senza limiti di read
            headers={"User-Agent": "Mozilla/5.0 GithubRunner"},
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
        # scrivo file vuoto per far fallire il job se serve
        with suppress(Exception):
            TARGET.unlink()
        sys.exit(1)

if __name__ == "__main__":
    main()
