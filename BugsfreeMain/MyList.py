#!/usr/bin/env python3
"""
MyList.py – genera una playlist con soli canali italiani
(riconosciuti da 'IT|' o '.it' nel tag #EXTINF)

• Usa l'URL sorgente memorizzato nel secret M3U_SOURCE
• Scrive il risultato in LiveTV/MyList/LiveTV.m3u
"""

import os, re, requests, pathlib, itertools

SOURCE_URLS = [os.environ["M3U_SOURCE"]]           # preso dal secret
TARGET_DIR   = pathlib.Path("LiveTV/MyList")
TARGET_FILE  = TARGET_DIR / "LiveTV.m3u"

# regex: match "IT|" (qualsiasi combinazione di maiuscole/minuscole)
#        oppure ".it" separato da fine parola
ITA_PATTERN = re.compile(r"(it\|)|(\.it\b)", re.IGNORECASE)


def fetch_lines(url: str) -> list[str]:
    resp = requests.get(url, timeout=45)
    resp.raise_for_status()
    return resp.text.splitlines(keepends=True)


def keep_only_ita(lines: list[str]) -> list[str]:
    """Restituisce solo le coppie EXTINF+URL che contengono la lingua ITA."""
    result = []
    it_lines = iter(enumerate(lines))
    header_done = False

    for idx, line in it_lines:
        if not header_done and line.strip().startswith("#EXTM3U"):
            result.append(line)
            header_done = True
            continue

        if line.startswith("#EXTINF"):
            if ITA_PATTERN.search(line):
                # mantieni #EXTINF e URL successiva
                result.append(line)
                try:
                    _, url_line = next(it_lines)
                    result.append(url_line)
                except StopIteration:
                    break
            else:
                # scarta anche la URL
                next(it_lines, None)

    return result


def main() -> None:
    TARGET_DIR.mkdir(parents=True, exist_ok=True)

    all_out = []
    for url in SOURCE_URLS:
        try:
            lines = fetch_lines(url)
            all_out.extend(keep_only_ita(lines))
        except Exception as exc:
            print(f"[WARN] Problema con {url}: {exc}")

    TARGET_FILE.write_text("".join(all_out), encoding="utf-8")
    print(f"[INFO] Salvati {len(all_out)//2} canali ITA in {TARGET_FILE}")


if __name__ == "__main__":
    main()
