#!/usr/bin/env python3
"""Собирает версию для Яндекс Игр.

Берёт index.html, заменяет Google Fonts на локальные шрифты из yandex/fonts,
подключает /sdk.js и пишет yandex/index.html и архив dist/lumina-yandex.zip,
который загружается в консоль разработчика Яндекс Игр.

Запуск: python3 tools/build_yandex.py
"""
import pathlib
import re
import zipfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "index.html"
OUT = ROOT / "yandex"
DIST = ROOT / "dist"
ZIP = DIST / "lumina-yandex.zip"

CYRILLIC = "U+0301,U+0400-045F,U+0490-0491,U+04B0-04B1,U+2116"
LATIN = (
    "U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+0304,"
    "U+0308,U+0329,U+2000-206F,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD"
)
FACES = [("Unbounded", "unbounded", 500), ("Golos Text", "golos-text", 400), ("Golos Text", "golos-text", 500)]


def font_css() -> str:
    rules = []
    for family, slug, weight in FACES:
        for subset, ranges in (("cyrillic", CYRILLIC), ("latin", LATIN)):
            file = OUT / "fonts" / f"{slug}-{subset}-{weight}-normal.woff2"
            if not file.exists():
                raise SystemExit(f"Нет файла шрифта: {file}")
            rules.append(
                f"  @font-face {{ font-family: '{family}'; font-style: normal; font-weight: {weight}; "
                f"font-display: swap; src: url(fonts/{file.name}) format('woff2'); unicode-range: {ranges}; }}"
            )
    return "<style>\n" + "\n".join(rules) + "\n</style>"


def main() -> None:
    html = SRC.read_text("utf-8")
    html, fonts = re.subn(r"<!-- fonts:start -->.*?<!-- fonts:end -->", lambda _: font_css(), html, flags=re.S)
    if fonts != 1 or html.count("<!-- sdk -->") != 1:
        raise SystemExit("В index.html не найдены метки fonts:start/fonts:end или sdk")
    html = html.replace("<!-- sdk -->", '<script src="/sdk.js"></script>')
    html = html.replace("<!-- page:start -->\n", "").replace("<!-- page:end -->\n", "")
    if "fonts.googleapis.com" in html:
        raise SystemExit("В сборке остались внешние шрифты")

    (OUT / "index.html").write_text(html, "utf-8")
    DIST.mkdir(exist_ok=True)
    with zipfile.ZipFile(ZIP, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(OUT / "index.html", "index.html")
        for f in sorted((OUT / "fonts").glob("*.woff2")):
            z.write(f, f"fonts/{f.name}")
    print(f"Готово: {OUT / 'index.html'}")
    print(f"Архив для загрузки: {ZIP} ({ZIP.stat().st_size // 1024} КБ)")


if __name__ == "__main__":
    main()
