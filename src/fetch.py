"""Camada de coleta (scraping). Pega o texto bruto de uma fonte oficial.

Separada de propósito do parser: trocar a FONTE (arquivo local, URL do Planalto,
outra base de legislação) não muda o parser. Por padrão o pipeline roda sobre o
fixture local (offline, reprodutível); aponte para uma URL quando quiser coletar ao
vivo da fonte oficial.

Aviso: respeite os termos de uso e o robots.txt do portal. Leis são atos oficiais
de domínio público (art. 8º da Lei de Direitos Autorais).
"""

from __future__ import annotations

import re
from html.parser import HTMLParser
from pathlib import Path


class _TextExtractor(HTMLParser):
    """Extrai texto visível de HTML, ignorando script/style."""
    def __init__(self) -> None:
        super().__init__()
        self._skip = False
        self.partes: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self._skip = True
        if tag in ("p", "br", "div", "tr"):
            self.partes.append("\n")

    def handle_endtag(self, tag):
        if tag in ("script", "style"):
            self._skip = False

    def handle_data(self, data):
        if not self._skip and data.strip():
            self.partes.append(data)


def html_para_texto(html: str) -> str:
    p = _TextExtractor()
    p.feed(html)
    txt = "".join(p.partes)
    txt = re.sub(r"[ \t]+", " ", txt)
    txt = re.sub(r"\n\s*\n+", "\n", txt)
    return txt.strip()


def fetch_arquivo(caminho: str | Path) -> str:
    """Lê o texto bruto de um arquivo local (o modo padrão, reprodutível)."""
    return Path(caminho).read_text(encoding="utf-8")


def fetch_url(url: str, timeout: int = 30) -> str:
    """Coleta o texto de uma URL oficial (ex.: Planalto). Uso sob demanda.

    Mantido fora dos testes para o pipeline rodar offline. Requer rede ao chamar.
    """
    import urllib.request

    req = urllib.request.Request(url, headers={"User-Agent": "ingestao-legislacao/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310
        bruto = resp.read()
    try:
        html = bruto.decode("utf-8")
    except UnicodeDecodeError:
        html = bruto.decode("latin-1")
    return html_para_texto(html)
